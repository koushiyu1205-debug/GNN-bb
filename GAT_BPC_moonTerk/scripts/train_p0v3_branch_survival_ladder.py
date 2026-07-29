#!/usr/bin/env python3
"""Train and grouped-test the smallest-first P0 V3 branch ranker ladder."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
from statistics import mean, median
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402

from lunar_ice_bpc.guidance.branch_survival import (  # noqa: E402
    BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2,
    BRANCH_NODE_FEATURE_SCHEMA_V2,
    BRANCH_PAIR_CONTEXT_SCHEMA_V1,
    BRANCH_SURVIVAL_ARCHITECTURE_VERSION,
    BRANCH_SURVIVAL_MODEL_LADDER,
    REAL_MAP_SP50_DOMAIN,
    SYNTHETIC_POLAR_GRID_DOMAIN,
    branch_survival_checkpoint_payload,
    branch_survival_losses,
    build_branch_survival_model,
    validate_branch_survival_row,
)


SCHEMA_VERSION = "lunar_ice_bpc.branch_survival_ladder_training.v2"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_rows(path: Path) -> list[dict]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for row in rows:
        validate_branch_survival_row(row)
        if str(row.get("branch_node_feature_schema") or "") != (
            BRANCH_NODE_FEATURE_SCHEMA_V2
        ):
            raise ValueError("branch node feature schema mismatch")
        if str(row.get("branch_pair_context_schema") or "") != (
            BRANCH_PAIR_CONTEXT_SCHEMA_V1
        ):
            raise ValueError("branch pair context schema mismatch")
    return rows


def _aggregate_feature_moments(
    rows: list[dict],
    key: str,
) -> tuple[list[float], list[float]]:
    by_domain_scale: dict[
        str,
        dict[
            int,
            dict[str, list[tuple[torch.Tensor, torch.Tensor]]],
        ],
    ] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for row in rows:
        values = torch.tensor(row[key], dtype=torch.float64)
        if values.ndim != 2 or values.shape[0] == 0:
            raise ValueError(f"{key} must be a non-empty matrix")
        by_domain_scale[
            str(row["instance_generator_domain"])
        ][int(row["scale"])][
            str(row["instance_content_hash"])
        ].append(
            (
                values.mean(dim=0),
                (values * values).mean(dim=0),
            )
        )
    domain_means = []
    domain_seconds = []
    for domain in sorted(by_domain_scale):
        scale_means = []
        scale_seconds = []
        for scale in sorted(by_domain_scale[domain]):
            instance_means = []
            instance_seconds = []
            for instance_hash in sorted(
                by_domain_scale[domain][scale]
            ):
                moments = by_domain_scale[domain][scale][instance_hash]
                instance_means.append(
                    torch.stack(
                        [value[0] for value in moments]
                    ).mean(dim=0)
                )
                instance_seconds.append(
                    torch.stack(
                        [value[1] for value in moments]
                    ).mean(dim=0)
                )
            scale_means.append(
                torch.stack(instance_means).mean(dim=0)
            )
            scale_seconds.append(
                torch.stack(instance_seconds).mean(dim=0)
            )
        domain_means.append(torch.stack(scale_means).mean(dim=0))
        domain_seconds.append(
            torch.stack(scale_seconds).mean(dim=0)
        )
    feature_mean = torch.stack(domain_means).mean(dim=0)
    feature_second = torch.stack(domain_seconds).mean(dim=0)
    feature_std = torch.sqrt(
        (feature_second - feature_mean * feature_mean).clamp_min(1.0e-16)
    ).clamp_min(1.0e-8)
    return feature_mean.tolist(), feature_std.tolist()


def _fit_normalization(rows: list[dict]) -> dict:
    result = {}
    for prefix, key in (
        ("node", "node_features"),
        ("edge", "edge_features"),
        ("branch_context", "branch_context"),
    ):
        feature_mean, feature_std = _aggregate_feature_moments(rows, key)
        result[f"{prefix}_mean"] = feature_mean
        result[f"{prefix}_std"] = feature_std
    result["fit_scope"] = "fold_training_only"
    result["weighting"] = (
        "generator_domain_equal_scale_equal_instance_equal_state_equal"
    )
    return result


def _tensor_row(row: dict, normalization: dict) -> dict:
    def normalized(key: str, prefix: str) -> torch.Tensor:
        values = torch.tensor(row[key], dtype=torch.float32)
        return (
            values
            - torch.tensor(
                normalization[f"{prefix}_mean"],
                dtype=torch.float32,
            )
        ) / torch.tensor(
            normalization[f"{prefix}_std"],
            dtype=torch.float32,
        )

    gold_rank = row.get("branch_e2e_gold_rank_index")
    wall_by_rank = row.get("branch_e2e_wall_sec_by_rank") or {}
    return {
        "inputs": {
            "node_features": normalized("node_features", "node"),
            "edge_index": torch.tensor(
                row["edge_index"],
                dtype=torch.long,
            ),
            "edge_features": normalized("edge_features", "edge"),
            "branch_pairs": torch.tensor(
                row["branch_pairs"],
                dtype=torch.long,
            ),
            "branch_context": normalized(
                "branch_context",
                "branch_context",
            ),
        },
        "times": torch.tensor(
            row["branch_child_observed_time_fractions"],
            dtype=torch.float32,
        ),
        "events": torch.tensor(
            row["branch_child_event_observed"],
            dtype=torch.float32,
        ),
        "mask": torch.tensor(
            row["branch_child_observed_mask"],
            dtype=torch.float32,
        ),
        "e2e_gold_rank": (
            None
            if gold_rank is None
            else torch.tensor([int(gold_rank)], dtype=torch.long)
        ),
        "e2e_walls": (
            None
            if gold_rank is None
            else torch.tensor(
                [float(wall_by_rank[str(rank)]) for rank in range(3)],
                dtype=torch.float32,
            )
        ),
        "e2e_p0_control_wall": (
            None
            if gold_rank is None
            else torch.tensor(
                [float(row["branch_e2e_p0_control_wall_sec"])],
                dtype=torch.float32,
            )
        ),
        "e2e_pairwise_preferences": torch.tensor(
            row.get("branch_e2e_trusted_pairwise_preferences")
            or [],
            dtype=torch.long,
        ).reshape(-1, 2),
    }


def _row_weights(rows: list[dict]) -> list[float]:
    by_domain_scale_instance = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    for row in rows:
        by_domain_scale_instance[
            str(row["instance_generator_domain"])
        ][int(row["scale"])][
            str(row["instance_content_hash"])
        ] += 1
    domains = sorted(by_domain_scale_instance)
    weights = []
    for row in rows:
        domain = str(row["instance_generator_domain"])
        scale = int(row["scale"])
        instance_hash = str(row["instance_content_hash"])
        scales = sorted(by_domain_scale_instance[domain])
        weights.append(
            1.0
            / len(domains)
            / len(scales)
            / len(by_domain_scale_instance[domain][scale])
            / by_domain_scale_instance[domain][scale][instance_hash]
        )
    return weights


def _shared_encoder_parameters(model) -> list[torch.nn.Parameter]:
    parameters = []
    seen = set()
    for module_name in (
        "node_encoder",
        "edge_encoder",
        "attention_layers",
    ):
        module = getattr(model, module_name, None)
        if module is None:
            continue
        for parameter in module.parameters():
            if parameter.requires_grad and id(parameter) not in seen:
                seen.add(id(parameter))
                parameters.append(parameter)
    return parameters


def _weighted_objectives(
    model,
    rows: list[dict],
    normalization: dict,
    *,
    survival_aux_weight: float,
    e2e_listwise_weight: float,
    e2e_regret_weight: float,
) -> dict:
    survival_weights = _row_weights(rows)
    e2e_rows = [
        row
        for row in rows
        if (
            row.get("branch_e2e_gold_rank_index") is not None
            or bool(
                row.get(
                    "branch_e2e_trusted_pairwise_preferences"
                )
            )
        )
    ]
    e2e_weights = {
        (
            str(row["instance_content_hash"]),
            str(row["path_hash"]),
        ): weight
        for row, weight in zip(
            e2e_rows,
            _row_weights(e2e_rows) if e2e_rows else (),
            strict=True,
        )
    }
    survival_total = None
    e2e_total = None
    for row, survival_weight in zip(
        rows,
        survival_weights,
        strict=True,
    ):
        tensors = _tensor_row(row, normalization)
        output = model(**tensors["inputs"])
        losses = branch_survival_losses(
            output,
            observed_time_fractions=tensors["times"],
            event_observed=tensors["events"],
            observed_mask=tensors["mask"],
            e2e_gold_rank_index=tensors["e2e_gold_rank"],
            e2e_wall_sec_by_rank=tensors["e2e_walls"],
            e2e_p0_control_wall_sec=tensors[
                "e2e_p0_control_wall"
            ],
            e2e_trusted_pairwise_preferences=tensors[
                "e2e_pairwise_preferences"
            ],
        )
        weighted_survival = (
            losses["branch_child_survival_nll"]
            * float(survival_weight)
            * float(survival_aux_weight)
        )
        survival_total = (
            weighted_survival
            if survival_total is None
            else survival_total + weighted_survival
        )
        e2e_parts = []
        if tensors["e2e_gold_rank"] is not None:
            e2e_parts.extend(
                (
                    float(e2e_listwise_weight)
                    * losses["branch_e2e_gold_listwise"],
                    float(e2e_regret_weight)
                    * losses[
                        "branch_e2e_expected_normalized_regret"
                    ],
                )
            )
        if "branch_e2e_trusted_censored_pairwise" in losses:
            e2e_parts.append(
                losses["branch_e2e_trusted_censored_pairwise"]
            )
        if not e2e_parts:
            continue
        e2e_weight = e2e_weights[
            (
                str(row["instance_content_hash"]),
                str(row["path_hash"]),
            )
        ]
        e2e_loss = sum(e2e_parts)
        weighted_e2e = e2e_loss * float(e2e_weight)
        e2e_total = (
            weighted_e2e
            if e2e_total is None
            else e2e_total + weighted_e2e
        )
    if survival_total is None:
        raise ValueError("branch training rows are empty")
    return {
        "survival_aux": survival_total,
        "e2e_primary": e2e_total,
        "gold_state_count": sum(
            row.get("branch_e2e_gold_rank_index") is not None
            for row in rows
        ),
        "trusted_pairwise_state_count": sum(
            bool(
                row.get(
                    "branch_e2e_trusted_pairwise_preferences"
                )
            )
            for row in rows
        ),
    }


def _objective_gradients(
    objective: torch.Tensor | None,
    parameters: list[torch.nn.Parameter],
) -> list[torch.Tensor | None]:
    if objective is None or not parameters:
        return [None] * len(parameters)
    return list(
        torch.autograd.grad(
            objective,
            parameters,
            retain_graph=True,
            allow_unused=True,
        )
    )


def _gradient_diagnostics(
    first: list[torch.Tensor | None],
    second: list[torch.Tensor | None],
) -> dict:
    if len(first) != len(second):
        raise ValueError("gradient lists differ in length")
    first_norm_sq = 0.0
    second_norm_sq = 0.0
    dot = 0.0
    shared_coordinate_count = 0
    for left, right in zip(first, second, strict=True):
        if left is not None:
            first_norm_sq += float(torch.sum(left.detach() ** 2))
        if right is not None:
            second_norm_sq += float(torch.sum(right.detach() ** 2))
        if left is not None and right is not None:
            dot += float(torch.sum(left.detach() * right.detach()))
            shared_coordinate_count += int(left.numel())
    denominator = (first_norm_sq * second_norm_sq) ** 0.5
    return {
        "e2e_encoder_gradient_norm": first_norm_sq**0.5,
        "survival_encoder_gradient_norm": second_norm_sq**0.5,
        "encoder_gradient_dot": dot,
        "encoder_gradient_cosine": (
            None if denominator <= 1.0e-20 else dot / denominator
        ),
        "shared_gradient_coordinate_count": shared_coordinate_count,
    }


def _pcgrad_project(
    first: list[torch.Tensor | None],
    second: list[torch.Tensor | None],
) -> tuple[list[torch.Tensor | None], list[torch.Tensor | None]]:
    diagnostics = _gradient_diagnostics(first, second)
    dot = float(diagnostics["encoder_gradient_dot"])
    if dot >= 0.0:
        return first, second
    first_norm_sq = sum(
        float(torch.sum(value.detach() ** 2))
        for value in first
        if value is not None
    )
    second_norm_sq = sum(
        float(torch.sum(value.detach() ** 2))
        for value in second
        if value is not None
    )
    projected_first = []
    projected_second = []
    for left, right in zip(first, second, strict=True):
        if left is None and right is None:
            projected_first.append(None)
            projected_second.append(None)
            continue
        left_value = (
            torch.zeros_like(right) if left is None else left
        )
        right_value = (
            torch.zeros_like(left) if right is None else right
        )
        projected_first.append(
            left_value
            - (
                dot / max(1.0e-20, second_norm_sq)
            )
            * right_value
        )
        projected_second.append(
            right_value
            - (
                dot / max(1.0e-20, first_norm_sq)
            )
            * left_value
        )
    return projected_first, projected_second


def _train(
    model,
    rows: list[dict],
    normalization: dict,
    *,
    validation_rows: list[dict] | None = None,
    epochs: int,
    learning_rate: float,
    survival_aux_weight: float = 0.25,
    e2e_listwise_weight: float = 1.0,
    e2e_regret_weight: float = 1.0,
) -> dict:
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(learning_rate),
    )
    if not any(
        row.get("branch_e2e_gold_rank_index") is not None
        for row in rows
    ):
        raise ValueError(
            "action-aligned branch training requires E2E gold"
        )
    epoch_diagnostics = []
    pcgrad_active = False
    consecutive_validation_conflicts = 0
    pcgrad_activated_after_epoch = None
    shared_parameters = _shared_encoder_parameters(model)
    for epoch in range(max(1, int(epochs))):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        objectives = _weighted_objectives(
            model,
            rows,
            normalization,
            survival_aux_weight=float(survival_aux_weight),
            e2e_listwise_weight=float(e2e_listwise_weight),
            e2e_regret_weight=float(e2e_regret_weight),
        )
        survival_total = objectives["survival_aux"]
        e2e_total = objectives["e2e_primary"]
        if e2e_total is None:
            raise ValueError(
                "action-aligned branch training requires E2E gold"
            )
        e2e_gradients = _objective_gradients(
            e2e_total,
            shared_parameters,
        )
        survival_gradients = _objective_gradients(
            survival_total,
            shared_parameters,
        )
        train_gradient = _gradient_diagnostics(
            e2e_gradients,
            survival_gradients,
        )
        total = survival_total + e2e_total
        total.backward()
        if pcgrad_active and shared_parameters:
            projected_e2e, projected_survival = _pcgrad_project(
                e2e_gradients,
                survival_gradients,
            )
            for parameter, left, right in zip(
                shared_parameters,
                projected_e2e,
                projected_survival,
                strict=True,
            ):
                if left is None and right is None:
                    continue
                parameter.grad = (
                    (0.0 if left is None else left)
                    + (0.0 if right is None else right)
                ).detach().clone()
        optimizer.step()

        validation_gradient = {
            "e2e_encoder_gradient_norm": None,
            "survival_encoder_gradient_norm": None,
            "encoder_gradient_dot": None,
            "encoder_gradient_cosine": None,
            "shared_gradient_coordinate_count": 0,
        }
        validation_gold_count = 0
        validation_pairwise_count = 0
        if validation_rows:
            model.train()
            validation_objectives = _weighted_objectives(
                model,
                validation_rows,
                normalization,
                survival_aux_weight=float(survival_aux_weight),
                e2e_listwise_weight=float(e2e_listwise_weight),
                e2e_regret_weight=float(e2e_regret_weight),
            )
            validation_gold_count = int(
                validation_objectives["gold_state_count"]
            )
            validation_pairwise_count = int(
                validation_objectives[
                    "trusted_pairwise_state_count"
                ]
            )
            if validation_objectives["e2e_primary"] is not None:
                validation_gradient = _gradient_diagnostics(
                    _objective_gradients(
                        validation_objectives["e2e_primary"],
                        shared_parameters,
                    ),
                    _objective_gradients(
                        validation_objectives["survival_aux"],
                        shared_parameters,
                    ),
                )
        validation_cosine = validation_gradient[
            "encoder_gradient_cosine"
        ]
        if (
            validation_cosine is not None
            and float(validation_cosine) < -0.2
        ):
            consecutive_validation_conflicts += 1
        else:
            consecutive_validation_conflicts = 0
        activates_next = bool(
            not pcgrad_active
            and consecutive_validation_conflicts >= 3
        )
        if activates_next:
            pcgrad_active = True
            pcgrad_activated_after_epoch = epoch + 1
        epoch_diagnostics.append(
            {
                "epoch": epoch + 1,
                "total_loss": float(total.detach()),
                "e2e_primary_loss": float(e2e_total.detach()),
                "survival_aux_loss": float(
                    survival_total.detach()
                ),
                "train_encoder_gradients": train_gradient,
                "validation_encoder_gradients": validation_gradient,
                "validation_gold_state_count": validation_gold_count,
                "validation_trusted_pairwise_state_count": (
                    validation_pairwise_count
                ),
                "consecutive_validation_gradient_conflicts": (
                    consecutive_validation_conflicts
                ),
                "pcgrad_active_for_epoch": bool(
                    pcgrad_active and not activates_next
                ),
                "pcgrad_activated_for_next_epoch": activates_next,
            }
        )
    return {
        "total_loss_history": [
            row["total_loss"] for row in epoch_diagnostics
        ],
        "epoch_diagnostics": epoch_diagnostics,
        "pcgrad_activated_after_epoch": pcgrad_activated_after_epoch,
        "pcgrad_active_at_end": pcgrad_active,
        "pcgrad_trigger": (
            "three_consecutive_validation_encoder_cosines_below_-0.2"
        ),
    }


def _evaluate(model, rows: list[dict], normalization: dict) -> list[dict]:
    model.eval()
    results = []
    with torch.no_grad():
        for row in rows:
            tensors = _tensor_row(row, normalization)
            output = model(**tensors["inputs"])
            nll = branch_survival_losses(
                output,
                observed_time_fractions=tensors["times"],
                event_observed=tensors["events"],
                observed_mask=tensors["mask"],
            )["branch_child_survival_nll"]
            selected = int(torch.argmax(output["branch_scores"]).item())
            pairwise_preferences = list(
                row.get(
                    "branch_e2e_trusted_pairwise_preferences"
                )
                or ()
            )
            pairwise_accuracy = (
                None
                if not pairwise_preferences
                else mean(
                    float(
                        output["branch_scores"][int(winner)]
                        > output["branch_scores"][int(loser)]
                    )
                    for winner, loser in pairwise_preferences
                )
            )
            gold = row.get("branch_e2e_gold_rank_index")
            walls = row.get("branch_e2e_wall_sec_by_rank") or {}
            model_wall = walls.get(str(selected))
            p0_wall = row.get("branch_e2e_p0_control_wall_sec")
            oracle_wall = min(walls.values()) if walls else None
            normalized_regret = (
                None
                if model_wall is None
                or p0_wall is None
                or oracle_wall is None
                or float(p0_wall) <= 0.0
                else (
                    float(model_wall) - float(oracle_wall)
                )
                / float(p0_wall)
            )
            results.append(
                {
                    "instance_content_hash": row[
                        "instance_content_hash"
                    ],
                    "instance_generator_domain": row[
                        "instance_generator_domain"
                    ],
                    "path_hash": row["path_hash"],
                    "scale": int(row["scale"]),
                    "survival_nll": float(nll),
                    "predicted_rank_index": selected,
                    "gold_rank_index": gold,
                    "gold_top1_match": (
                        None if gold is None else selected == int(gold)
                    ),
                    "trusted_censored_pairwise_accuracy": (
                        pairwise_accuracy
                    ),
                    "model_e2e_wall_sec": model_wall,
                    "p0_e2e_wall_sec": p0_wall,
                    "oracle_e2e_wall_sec": oracle_wall,
                    "model_normalized_e2e_regret": normalized_regret,
                    "model_to_p0_wall_ratio": (
                        None
                        if model_wall is None
                        or p0_wall is None
                        or float(p0_wall) <= 0.0
                        else float(model_wall) / float(p0_wall)
                    ),
                }
            )
    return results


def _summary(results: list[dict]) -> dict:
    def balanced(field: str, rows: list[dict]) -> float | None:
        by_domain_scale_instance = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        for row in rows:
            value = row.get(field)
            if value is None:
                continue
            by_domain_scale_instance[
                str(row["instance_generator_domain"])
            ][int(row["scale"])][
                str(row["instance_content_hash"])
            ].append(float(value))
        domain_values = []
        for by_scale in by_domain_scale_instance.values():
            scale_values = []
            for by_instance in by_scale.values():
                if not by_instance:
                    continue
                scale_values.append(
                    mean(
                        mean(values)
                        for values in by_instance.values()
                        if values
                    )
                )
            if scale_values:
                domain_values.append(mean(scale_values))
        return None if not domain_values else mean(domain_values)

    gold = [
        row for row in results if row["gold_top1_match"] is not None
    ]
    by_scale = {}
    for scale in sorted({int(row["scale"]) for row in results}):
        rows = [row for row in results if int(row["scale"]) == scale]
        scale_gold = [
            row for row in rows if row["gold_top1_match"] is not None
        ]
        by_scale[str(scale)] = {
            "row_count": len(rows),
            "instance_count": len(
                {
                    str(row["instance_content_hash"])
                    for row in rows
                }
            ),
            "mean_survival_nll": balanced(
                "survival_nll",
                rows,
            ),
            "gold_top1_accuracy": balanced(
                "gold_top1_match",
                scale_gold,
            ),
            "trusted_censored_pairwise_accuracy": balanced(
                "trusted_censored_pairwise_accuracy",
                rows,
            ),
            "mean_model_to_p0_wall_ratio": balanced(
                "model_to_p0_wall_ratio",
                rows,
            ),
            "mean_model_normalized_e2e_regret": balanced(
                "model_normalized_e2e_regret",
                rows,
            ),
        }
    by_domain = {}
    for domain in sorted(
        {
            str(row["instance_generator_domain"])
            for row in results
        }
    ):
        domain_rows = [
            row
            for row in results
            if str(row["instance_generator_domain"]) == domain
        ]
        domain_gold = [
            row
            for row in domain_rows
            if row["gold_top1_match"] is not None
        ]
        by_domain[domain] = {
            "row_count": len(domain_rows),
            "instance_count": len(
                {
                    str(row["instance_content_hash"])
                    for row in domain_rows
                }
            ),
            "mean_survival_nll": balanced(
                "survival_nll", domain_rows
            ),
            "gold_top1_accuracy": balanced(
                "gold_top1_match", domain_gold
            ),
            "mean_model_to_p0_wall_ratio": balanced(
                "model_to_p0_wall_ratio", domain_rows
            ),
            "mean_model_normalized_e2e_regret": balanced(
                "model_normalized_e2e_regret", domain_rows
            ),
        }
    return {
        "row_count": len(results),
        "weighting": (
            "generator_domain_equal_scale_equal_instance_equal_state_equal"
        ),
        "mean_survival_nll": balanced("survival_nll", results),
        "gold_count": len(gold),
        "gold_top1_accuracy": balanced(
            "gold_top1_match",
            gold,
        ),
        "trusted_censored_pairwise_accuracy": balanced(
            "trusted_censored_pairwise_accuracy",
            results,
        ),
        "mean_model_to_p0_wall_ratio": balanced(
            "model_to_p0_wall_ratio",
            results,
        ),
        "mean_model_normalized_e2e_regret": balanced(
            "model_normalized_e2e_regret",
            results,
        ),
        "by_scale": by_scale,
        "by_domain": by_domain,
    }


def _benchmark_forward(model, row: dict, normalization: dict) -> dict:
    tensors = _tensor_row(row, normalization)
    model.eval()
    with torch.no_grad():
        for _ in range(5):
            model(**tensors["inputs"])
        durations = []
        for _ in range(50):
            started = perf_counter()
            model(**tensors["inputs"])
            durations.append(perf_counter() - started)
    return {
        "forward_p50_sec": median(durations),
        "forward_p90_sec": sorted(durations)[44],
        "call_count": len(durations),
    }


def _paired_clustered_regret_improvement(
    previous: list[dict],
    current: list[dict],
) -> dict:
    def keyed(rows: list[dict]) -> dict[tuple[str, str], dict]:
        return {
            (
                str(row["instance_content_hash"]),
                str(row["path_hash"]),
            ): row
            for row in rows
        }

    previous_by_key = keyed(previous)
    current_by_key = keyed(current)
    if set(previous_by_key) != set(current_by_key):
        raise ValueError("model rung held-out state sets differ")
    by_domain_scale_instance = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for key in sorted(previous_by_key):
        before = previous_by_key[key]
        after = current_by_key[key]
        before_regret = before.get("model_normalized_e2e_regret")
        after_regret = after.get("model_normalized_e2e_regret")
        if before_regret is None or after_regret is None:
            continue
        if int(before["scale"]) != int(after["scale"]):
            raise ValueError("model rung held-out scale binding differs")
        if str(before["instance_generator_domain"]) != str(
            after["instance_generator_domain"]
        ):
            raise ValueError("model rung held-out domain binding differs")
        by_domain_scale_instance[
            str(before["instance_generator_domain"])
        ][int(before["scale"])][key[0]].append(
            float(before_regret) - float(after_regret)
        )
    clusters = {
        domain: {
            scale: [
                mean(values)
                for values in by_instance.values()
                if values
            ]
            for scale, by_instance in by_scale.items()
        }
        for domain, by_scale in by_domain_scale_instance.items()
    }
    clusters = {
        domain: {
            scale: values
            for scale, values in by_scale.items()
            if values
        }
        for domain, by_scale in clusters.items()
    }
    clusters = {
        domain: by_scale
        for domain, by_scale in clusters.items()
        if by_scale
    }
    if not clusters:
        return {
            "balanced_mean_improvement": None,
            "one_sided_sign_flip_p_value": None,
            "instance_cluster_count": 0,
            "by_scale_instance_cluster_bootstrap": {},
            "by_domain_scale_instance_cluster_bootstrap": {},
        }
    observed = mean(
        mean(mean(values) for values in by_scale.values())
        for by_scale in clusters.values()
    )
    flattened = [
        (domain, scale, value)
        for domain, by_scale in sorted(clusters.items())
        for scale, values in sorted(by_scale.items())
        for value in values
    ]
    generator = random.Random(20260726 + len(flattened))
    sample_count = 20000
    greater_or_equal = 0
    for _ in range(sample_count):
        signed_by_domain_scale = defaultdict(
            lambda: defaultdict(list)
        )
        for domain, scale, value in flattened:
            signed_by_domain_scale[domain][scale].append(
                value if generator.random() < 0.5 else -value
            )
        statistic = mean(
            mean(
                mean(values)
                for values in by_scale.values()
            )
            for by_scale in signed_by_domain_scale.values()
        )
        greater_or_equal += statistic >= observed - 1.0e-15
    by_scale_bootstrap = {}
    scales = sorted(
        {
            scale
            for by_scale in clusters.values()
            for scale in by_scale
        }
    )
    for scale in scales:
        by_domain = {
            domain: by_scale[scale]
            for domain, by_scale in clusters.items()
            if scale in by_scale
        }
        scale_generator = random.Random(
            20260726
            + 1009 * int(scale)
            + sum(len(values) for values in by_domain.values())
        )
        draws = sorted(
            mean(
                mean(
                    scale_generator.choice(values)
                    for _ in values
                )
                for values in by_domain.values()
            )
            for _ in range(sample_count)
        )
        by_scale_bootstrap[str(scale)] = {
            "instance_cluster_count": sum(
                len(values) for values in by_domain.values()
            ),
            "generator_domain_count": len(by_domain),
            "mean_improvement": mean(
                mean(values) for values in by_domain.values()
            ),
            "bootstrap_95ci": [
                draws[int(0.025 * len(draws))],
                draws[
                    max(
                        0,
                        int(0.975 * len(draws)) - 1,
                    )
                ],
            ],
        }
    by_domain_scale_bootstrap = {}
    for domain, by_scale in sorted(clusters.items()):
        for scale, values in sorted(by_scale.items()):
            domain_generator = random.Random(
                20260726
                + 1009 * int(scale)
                + int.from_bytes(
                    hashlib.sha256(domain.encode()).digest()[:4],
                    "big",
                )
                + len(values)
            )
            draws = sorted(
                mean(
                    domain_generator.choice(values)
                    for _ in values
                )
                for _ in range(sample_count)
            )
            by_domain_scale_bootstrap[f"{domain}:scale{scale}"] = {
                "instance_cluster_count": len(values),
                "mean_improvement": mean(values),
                "bootstrap_95ci": [
                    draws[int(0.025 * len(draws))],
                    draws[
                        max(
                            0,
                            int(0.975 * len(draws)) - 1,
                        )
                    ],
                ],
            }
    return {
        "balanced_mean_improvement": observed,
        "weighting": (
            "generator_domain_equal_scale_equal_instance_cluster_equal"
        ),
        "one_sided_sign_flip_p_value": (
            (greater_or_equal + 1.0) / (sample_count + 1.0)
        ),
        "instance_cluster_count": len(flattened),
        "sign_flip_sample_count": sample_count,
        "by_scale_instance_cluster_bootstrap": by_scale_bootstrap,
        "by_domain_scale_instance_cluster_bootstrap": (
            by_domain_scale_bootstrap
        ),
    }


def _gold_results(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if row.get("model_normalized_e2e_regret") is not None
    ]


def _p0_baseline_results(rows: list[dict]) -> list[dict]:
    baseline = []
    for row in _gold_results(rows):
        p0_wall = float(row["p0_e2e_wall_sec"])
        oracle_wall = float(row["oracle_e2e_wall_sec"])
        baseline.append(
            {
                **row,
                "predicted_rank_index": 0,
                "model_e2e_wall_sec": p0_wall,
                "model_normalized_e2e_regret": (
                    p0_wall - oracle_wall
                )
                / p0_wall,
                "model_to_p0_wall_ratio": 1.0,
            }
        )
    return baseline


def _worst_scale_lower(comparison: dict) -> float | None:
    rows = comparison.get(
        "by_scale_instance_cluster_bootstrap"
    ) or {}
    if not rows:
        return None
    return min(
        float(payload["bootstrap_95ci"][0])
        for payload in rows.values()
    )


def _linear_vs_p0_gate(results: list[dict], timing: dict) -> dict:
    gold = _gold_results(results)
    baseline = _p0_baseline_results(gold)
    comparison = _paired_clustered_regret_improvement(
        baseline,
        gold,
    )
    real_gold = [
        row
        for row in gold
        if str(row["instance_generator_domain"])
        == REAL_MAP_SP50_DOMAIN
    ]
    real_comparison = _paired_clustered_regret_improvement(
        _p0_baseline_results(real_gold),
        real_gold,
    )
    summary = _summary(gold)
    every_scale = {
        scale: bool(
            payload.get("mean_model_to_p0_wall_ratio") is not None
            and float(payload["mean_model_to_p0_wall_ratio"]) <= 1.0
        )
        for scale, payload in summary["by_scale"].items()
    }
    every_domain = {
        domain: bool(
            payload.get("mean_model_to_p0_wall_ratio") is not None
            and float(payload["mean_model_to_p0_wall_ratio"]) <= 1.0
        )
        for domain, payload in summary["by_domain"].items()
    }
    real_summary = summary["by_domain"].get(
        REAL_MAP_SP50_DOMAIN
    ) or {}
    checks = {
        "real_map_gold_present": bool(real_gold),
        "real_map_mean_wall_strictly_better_than_p0": (
            real_summary.get("mean_model_to_p0_wall_ratio") is not None
            and float(real_summary["mean_model_to_p0_wall_ratio"]) < 1.0
        ),
        "real_map_worst_scale_bootstrap_lower_nonnegative": (
            _worst_scale_lower(real_comparison) is not None
            and float(_worst_scale_lower(real_comparison)) >= 0.0
        ),
        "every_scale_wall_non_degradation": (
            bool(every_scale) and all(every_scale.values())
        ),
        "every_generator_domain_wall_non_degradation": (
            bool(every_domain) and all(every_domain.values())
        ),
        "forward_p50_at_most_20ms": (
            float(timing["forward_p50_sec"]) <= 0.020
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "every_scale_wall_non_degradation": every_scale,
        "every_generator_domain_wall_non_degradation": every_domain,
        "vs_p0": comparison,
        "real_map_vs_p0": real_comparison,
        "real_map_worst_scale_bootstrap_lower95": (
            _worst_scale_lower(real_comparison)
        ),
    }


def _holm_rejections(
    p_values: dict[tuple[str, str], float | None],
    *,
    alpha: float = 0.05,
) -> dict[tuple[str, str], bool]:
    valid = sorted(
        (
            (key, float(value))
            for key, value in p_values.items()
            if value is not None
        ),
        key=lambda item: (item[1], item[0]),
    )
    result = {key: False for key in p_values}
    reject_remaining = True
    total = len(valid)
    for index, (key, value) in enumerate(valid):
        threshold = float(alpha) / max(1, total - index)
        if reject_remaining and value <= threshold:
            result[key] = True
        else:
            reject_remaining = False
    return result


def _readiness_gate(path: Path, records_path: Path) -> dict:
    gate = json.loads(path.read_text(encoding="utf-8"))
    if str(gate.get("schema_version") or "") != (
        "lunar_ice_bpc.branch_training_readiness.v1"
    ):
        raise SystemExit("branch training readiness schema mismatch")
    if str(gate.get("records_sha256") or "") != _file_sha256(records_path):
        raise SystemExit("branch training readiness records hash mismatch")
    if not bool(gate.get("training_authorized")):
        raise SystemExit("branch training readiness gate did not pass")
    return gate


def _complexity_expansion_authorization(
    *,
    model_kinds: list[str],
    previous_report_path: Path | None,
    records_sha256: str,
    split_manifest_hash: str,
    readiness_report_sha256: str,
    training_regime: str,
) -> dict | None:
    if len(model_kinds) == 1:
        if previous_report_path is not None:
            raise SystemExit(
                "linear-only run must not inherit a complexity authorization"
            )
        return None
    if previous_report_path is None:
        raise SystemExit(
            "complexity expansion requires a passed previous ladder "
            "report; the first run is linear-only"
        )
    previous = json.loads(
        previous_report_path.read_text(encoding="utf-8")
    )
    previous_models = list(
        previous.get("requested_model_kinds") or ()
    )
    if (
        str(previous.get("schema_version") or "") != SCHEMA_VERSION
        or str(previous.get("records_sha256") or "")
        != str(records_sha256)
        or str(previous.get("split_manifest_hash") or "")
        != str(split_manifest_hash)
        or str(previous.get("readiness_report_sha256") or "")
        != str(readiness_report_sha256)
        or str(previous.get("training_regime") or "")
        != str(training_regime)
        or previous.get("next_rung_authorized") is not True
        or previous.get("next_rung_kind") != model_kinds[-1]
        or model_kinds != [*previous_models, model_kinds[-1]]
    ):
        raise SystemExit(
            "previous ladder report did not authorize exactly this rung"
        )
    return previous


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--readiness-report", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--previous-ladder-report",
        default="",
        help=(
            "Required to add exactly one rung beyond a previously passed "
            "smallest-first report."
        ),
    )
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument(
        "--model",
        action="append",
        choices=BRANCH_SURVIVAL_MODEL_LADDER,
        default=None,
    )
    parser.add_argument("--torch-threads", type=int, default=2)
    args = parser.parse_args()

    torch.set_num_threads(max(1, int(args.torch_threads)))
    records_path = Path(args.records_jsonl)
    rows = _load_rows(records_path)
    readiness = _readiness_gate(
        Path(args.readiness_report),
        records_path,
    )
    pilot = dict(readiness.get("cross_domain_pilot") or {})
    training_regime = str(
        pilot.get("selected_training_regime") or ""
    )
    if not bool(pilot.get("passed")):
        raise SystemExit(
            "cross-domain pilot did not authorize branch training"
        )
    if training_regime == "REAL_ONLY":
        rows = [
            row
            for row in rows
            if str(row["instance_generator_domain"])
            == REAL_MAP_SP50_DOMAIN
        ]
    elif training_regime == "JOINT_DOMAIN_BALANCED":
        if not bool(pilot.get("synthetic_inclusion_authorized")):
            raise SystemExit(
                "joint training lacks synthetic-inclusion authorization"
            )
    elif training_regime == "SYNTHETIC_PRETRAIN_REAL_FINETUNE":
        raise SystemExit(
            "two-stage pretrain/finetune must use the dedicated transfer "
            "trainer; silent joint training is prohibited"
        )
    else:
        raise SystemExit("unknown or missing branch training regime")
    if not rows:
        raise SystemExit("selected branch training regime has no rows")
    manifest = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((manifest.get("audit") or {}).get("passed")):
        raise SystemExit("grouped split manifest audit failed")
    if manifest.get("calibration_read_authorized") is not False:
        raise SystemExit("training manifest calibration lock is not closed")
    if str(pilot.get("split_manifest_hash") or "") != str(
        manifest.get("manifest_hash") or ""
    ):
        raise SystemExit(
            "cross-domain pilot split binding does not match training"
        )
    assignment = {
        str(row["instance_content_hash"]): int(row["fold"])
        for row in manifest.get("development") or ()
    }
    forbidden = {
        str(row["instance_content_hash"])
        for partition in ("calibration", "protected_final_test")
        for row in manifest.get(partition) or ()
    }
    for row in rows:
        content_hash = str(row["instance_content_hash"])
        if content_hash in forbidden or content_hash not in assignment:
            raise SystemExit("training record partition violation")
    model_kinds = args.model or ["linear"]
    expected_prefix = list(BRANCH_SURVIVAL_MODEL_LADDER)[
        : max(
            BRANCH_SURVIVAL_MODEL_LADDER.index(kind)
            for kind in model_kinds
        )
        + 1
    ]
    if model_kinds != expected_prefix:
        raise SystemExit(
            "model ladder must be requested in complete smallest-first order"
        )
    previous_ladder = _complexity_expansion_authorization(
        model_kinds=model_kinds,
        previous_report_path=(
            None
            if not args.previous_ladder_report
            else Path(args.previous_ladder_report)
        ),
        records_sha256=_file_sha256(records_path),
        split_manifest_hash=str(manifest["manifest_hash"]),
        readiness_report_sha256=_file_sha256(
            Path(args.readiness_report)
        ),
        training_regime=training_regime,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": SCHEMA_VERSION,
        "model_architecture_version": (
            BRANCH_SURVIVAL_ARCHITECTURE_VERSION
        ),
        "records_sha256": _file_sha256(records_path),
        "split_manifest_hash": manifest["manifest_hash"],
        "readiness_report_sha256": _file_sha256(
            Path(args.readiness_report)
        ),
        "readiness_gate": readiness,
        "training_regime": training_regime,
        "target_domain": REAL_MAP_SP50_DOMAIN,
        "source_domain": SYNTHETIC_POLAR_GRID_DOMAIN,
        "domain_weighting": (
            "generator_domain_equal_scale_equal_instance_equal_state_equal"
        ),
        "calibration_used": False,
        "protected_final_test_used": False,
        "e2e_gold_used_for_backpropagation": True,
        "primary_training_objective": (
            BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2
        ),
        "training_loss": (
            "e2e_listwise_ce_plus_expected_normalized_regret"
            "_or_trusted_censored_pairwise_plus_0.25_child_survival_aux"
        ),
        "selection_metric": (
            "grouped_heldout_e2e_top1_and_wall_then_survival_nll"
        ),
        "fold_count": int(manifest["fold_count"]),
        "requested_model_kinds": model_kinds,
        "previous_ladder_report_sha256": (
            None
            if previous_ladder is None
            else _file_sha256(Path(args.previous_ladder_report))
        ),
        "models": [],
        "training_authorized": True,
        "deployment_authorized": False,
    }
    all_model_results = {}
    for model_index, kind in enumerate(model_kinds):
        fold_rows = []
        for fold in range(int(manifest["fold_count"])):
            train_rows = [
                row
                for row in rows
                if assignment[str(row["instance_content_hash"])] != fold
            ]
            validation_rows = [
                row
                for row in rows
                if assignment[str(row["instance_content_hash"])] == fold
            ]
            if not train_rows or not validation_rows:
                raise SystemExit(
                    f"fold {fold} lacks train or validation branch rows"
                )
            normalization = _fit_normalization(train_rows)
            torch.manual_seed(20260726 + 100 * model_index + fold)
            model = build_branch_survival_model(
                kind,
                node_input_dim=len(train_rows[0]["node_features"][0]),
                edge_input_dim=len(train_rows[0]["edge_features"][0]),
                pair_context_dim=len(train_rows[0]["branch_context"][0]),
            )
            history = _train(
                model,
                train_rows,
                normalization,
                validation_rows=validation_rows,
                epochs=int(args.epochs),
                learning_rate=float(args.learning_rate),
            )
            validation = _evaluate(
                model,
                validation_rows,
                normalization,
            )
            checkpoint_path = output_dir / (
                f"{kind}_fold{fold}.pt"
            )
            torch.save(
                branch_survival_checkpoint_payload(
                    model,
                    metadata={
                        "fold": fold,
                        "normalization": normalization,
                        "records_sha256": report["records_sha256"],
                        "split_manifest_hash": report[
                            "split_manifest_hash"
                        ],
                        "training_loss": report["training_loss"],
                        "calibration_used": False,
                        "deployment_authorized": False,
                    },
                ),
                checkpoint_path,
            )
            fold_rows.append(
                {
                    "fold": fold,
                    "train_state_count": len(train_rows),
                    "validation_state_count": len(validation_rows),
                    "training_loss_history": history[
                        "total_loss_history"
                    ],
                    "training_gradient_diagnostics": history[
                        "epoch_diagnostics"
                    ],
                    "pcgrad_activated_after_epoch": history[
                        "pcgrad_activated_after_epoch"
                    ],
                    "pcgrad_active_at_end": history[
                        "pcgrad_active_at_end"
                    ],
                    "pcgrad_trigger": history["pcgrad_trigger"],
                    "validation": validation,
                    "validation_summary": _summary(validation),
                    "checkpoint_path": str(
                        checkpoint_path.resolve()
                    ),
                    "checkpoint_sha256": _file_sha256(
                        checkpoint_path
                    ),
                }
            )
        combined = [
            row
            for fold_row in fold_rows
            for row in fold_row["validation"]
        ]
        combined.sort(
            key=lambda row: (
                row["instance_content_hash"],
                row["path_hash"],
            )
        )
        full_normalization = _fit_normalization(rows)
        torch.manual_seed(20260726 + 100 * model_index + 99)
        timing_model = build_branch_survival_model(
            kind,
            node_input_dim=len(rows[0]["node_features"][0]),
            edge_input_dim=len(rows[0]["edge_features"][0]),
            pair_context_dim=len(rows[0]["branch_context"][0]),
        )
        timing = _benchmark_forward(
            timing_model,
            rows[0],
            full_normalization,
        )
        model_report = {
            "model_kind": kind,
            "parameter_count": sum(
                parameter.numel()
                for parameter in timing_model.parameters()
            ),
            "folds": fold_rows,
            "grouped_heldout": combined,
            "grouped_heldout_summary": _summary(combined),
            "fresh_forward_timing": timing,
        }
        if kind == "linear":
            model_report["linear_vs_p0_gate"] = (
                _linear_vs_p0_gate(combined, timing)
            )
        report["models"].append(model_report)
        all_model_results[kind] = model_report

    # Complexity promotion is fail-closed and action aligned. Child-survival
    # NLL is auxiliary and therefore cannot promote a more complex rung.
    # A later rung must materially reduce held-out E2E regret, preserve every
    # represented scale, keep the auxiliary target sane, and meet latency.
    paired_improvements = {}
    for previous, current in zip(model_kinds, model_kinds[1:]):
        paired_improvements[(previous, current)] = (
            _paired_clustered_regret_improvement(
                all_model_results[previous]["grouped_heldout"],
                all_model_results[current]["grouped_heldout"],
            )
        )
    holm_rejections = _holm_rejections(
        {
            key: value["one_sided_sign_flip_p_value"]
            for key, value in paired_improvements.items()
        }
    )
    ladder_decisions = []
    linear_gate = all_model_results["linear"]["linear_vs_p0_gate"]
    selected_kind = "linear" if linear_gate["passed"] else None
    for previous, current in zip(model_kinds, model_kinds[1:]):
        previous_summary = all_model_results[previous][
            "grouped_heldout_summary"
        ]
        current_summary = all_model_results[current][
            "grouped_heldout_summary"
        ]
        previous_wall = previous_summary[
            "mean_model_to_p0_wall_ratio"
        ]
        current_wall = current_summary[
            "mean_model_to_p0_wall_ratio"
        ]
        paired = paired_improvements[(previous, current)]
        relative_nll_change = (
            float(current_summary["mean_survival_nll"])
            - float(previous_summary["mean_survival_nll"])
        ) / max(
            1.0e-12, float(previous_summary["mean_survival_nll"])
        )
        scale_non_degradation = {}
        for scale in sorted(
            set(previous_summary["by_scale"])
            | set(current_summary["by_scale"])
        ):
            previous_scale = previous_summary["by_scale"].get(scale) or {}
            current_scale = current_summary["by_scale"].get(scale) or {}
            previous_scale_regret = previous_scale.get(
                "mean_model_normalized_e2e_regret"
            )
            current_scale_regret = current_scale.get(
                "mean_model_normalized_e2e_regret"
            )
            scale_non_degradation[scale] = bool(
                previous_scale_regret is not None
                and current_scale_regret is not None
                and float(current_scale_regret)
                <= float(previous_scale_regret) + 1.0e-12
            )
        domain_non_degradation = {}
        for domain in sorted(
            set(previous_summary["by_domain"])
            | set(current_summary["by_domain"])
        ):
            previous_domain = (
                previous_summary["by_domain"].get(domain) or {}
            )
            current_domain = (
                current_summary["by_domain"].get(domain) or {}
            )
            previous_domain_regret = previous_domain.get(
                "mean_model_normalized_e2e_regret"
            )
            current_domain_regret = current_domain.get(
                "mean_model_normalized_e2e_regret"
            )
            domain_non_degradation[domain] = bool(
                previous_domain_regret is not None
                and current_domain_regret is not None
                and float(current_domain_regret)
                <= float(previous_domain_regret) + 1.0e-12
            )
        checks = {
            "mean_e2e_regret_improvement_at_least_1pct_of_p0": (
                paired["balanced_mean_improvement"] is not None
                and float(paired["balanced_mean_improvement"]) >= 0.01
            ),
            "paired_instance_cluster_significance_after_holm": (
                bool(holm_rejections[(previous, current)])
            ),
            "e2e_wall_non_degradation": (
                previous_wall is not None
                and current_wall is not None
                and float(current_wall) <= float(previous_wall)
            ),
            "every_scale_e2e_regret_non_degradation": (
                bool(scale_non_degradation)
                and all(scale_non_degradation.values())
            ),
            "every_generator_domain_e2e_regret_non_degradation": (
                bool(domain_non_degradation)
                and all(domain_non_degradation.values())
            ),
            "real_map_target_domain_non_degradation": bool(
                domain_non_degradation.get(
                    REAL_MAP_SP50_DOMAIN, False
                )
            ),
            "worst_scale_bootstrap_lower_bound_nonnegative": (
                bool(
                    paired[
                        "by_scale_instance_cluster_bootstrap"
                    ]
                )
                and all(
                    float(payload["bootstrap_95ci"][0])
                    >= -1.0e-12
                    for payload in paired[
                        "by_scale_instance_cluster_bootstrap"
                    ].values()
                )
            ),
            "worst_generator_domain_scale_bootstrap_lower_nonnegative": (
                bool(
                    paired[
                        "by_domain_scale_instance_cluster_bootstrap"
                    ]
                )
                and all(
                    float(payload["bootstrap_95ci"][0])
                    >= -1.0e-12
                    for payload in paired[
                        "by_domain_scale_instance_cluster_bootstrap"
                    ].values()
                )
            ),
            "auxiliary_survival_nll_increase_at_most_5pct": (
                relative_nll_change <= 0.05
            ),
            "forward_p50_at_most_20ms": (
                float(
                    all_model_results[current][
                        "fresh_forward_timing"
                    ]["forward_p50_sec"]
                )
                <= 0.020
            ),
        }
        advanced = all(checks.values())
        ladder_decisions.append(
            {
                "from": previous,
                "to": current,
                "mean_e2e_regret_improvement": (
                    paired["balanced_mean_improvement"]
                ),
                "paired_instance_cluster_test": paired,
                "holm_family_size": len(paired_improvements),
                "holm_rejected_null": bool(
                    holm_rejections[(previous, current)]
                ),
                "relative_auxiliary_survival_nll_change": (
                    relative_nll_change
                ),
                "scale_e2e_regret_non_degradation": (
                    scale_non_degradation
                ),
                "generator_domain_e2e_regret_non_degradation": (
                    domain_non_degradation
                ),
                "checks": checks,
                "advanced": advanced,
            }
        )
        if selected_kind != previous or not advanced:
            break
        selected_kind = current
    report["ladder_decisions"] = ladder_decisions
    report["selected_smallest_model_kind"] = selected_kind
    report["linear_vs_p0_gate"] = linear_gate
    last_requested = model_kinds[-1]
    last_index = BRANCH_SURVIVAL_MODEL_LADDER.index(last_requested)
    selected_reached_last = selected_kind == last_requested
    report["next_rung_authorized"] = bool(
        selected_reached_last
        and last_index + 1 < len(BRANCH_SURVIVAL_MODEL_LADDER)
    )
    report["next_rung_kind"] = (
        BRANCH_SURVIVAL_MODEL_LADDER[last_index + 1]
        if report["next_rung_authorized"]
        else None
    )
    report["selected_checkpoint_is_shadow_only"] = True
    destination = output_dir / "branch_survival_training_report.json"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    print(
        json.dumps(
            {
                "report": str(destination),
                "selected_smallest_model_kind": selected_kind,
                "model_count": len(model_kinds),
                "deployment_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
