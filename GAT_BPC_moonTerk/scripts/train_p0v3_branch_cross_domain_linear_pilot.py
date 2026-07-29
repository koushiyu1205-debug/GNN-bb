#!/usr/bin/env python3
"""Compare branch-data transfer regimes before any MLP/GAT expansion."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import torch  # noqa: E402

import train_p0v3_branch_survival_ladder as core  # noqa: E402
from lunar_ice_bpc.guidance.branch_survival import (  # noqa: E402
    REAL_MAP_SP50_DOMAIN,
    SYNTHETIC_POLAR_GRID_DOMAIN,
    branch_survival_checkpoint_payload,
    build_branch_survival_model,
)


SCHEMA_VERSION = (
    "lunar_ice_bpc.branch_cross_domain_transfer_evaluation.v1"
)
REGIMES = (
    "REAL_ONLY",
    "SYNTHETIC_ONLY_ZERO_SHOT",
    "SYNTHETIC_PRETRAIN_REAL_FINETUNE",
    "JOINT_DOMAIN_BALANCED",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _p0_results(rows: list[dict]) -> list[dict]:
    baseline = []
    for row in rows:
        walls = row.get("branch_e2e_wall_sec_by_rank") or {}
        if not walls:
            continue
        p0_wall = float(row["branch_e2e_p0_control_wall_sec"])
        oracle_wall = min(float(value) for value in walls.values())
        baseline.append(
            {
                "instance_content_hash": row[
                    "instance_content_hash"
                ],
                "instance_generator_domain": row[
                    "instance_generator_domain"
                ],
                "path_hash": row["path_hash"],
                "scale": int(row["scale"]),
                "model_normalized_e2e_regret": (
                    p0_wall - oracle_wall
                )
                / p0_wall,
            }
        )
    return baseline


def _gold_results(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if row.get("model_normalized_e2e_regret") is not None
    ]


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


def _train_regime(
    *,
    regime: str,
    fold: int,
    train_rows: list[dict],
    validation_rows: list[dict],
    epochs: int,
    pretrain_epochs: int,
    learning_rate: float,
    output_dir: Path,
) -> dict:
    target_train = [
        row
        for row in train_rows
        if str(row["instance_generator_domain"])
        == REAL_MAP_SP50_DOMAIN
    ]
    source_train = [
        row
        for row in train_rows
        if str(row["instance_generator_domain"])
        == SYNTHETIC_POLAR_GRID_DOMAIN
    ]
    target_validation = [
        row
        for row in validation_rows
        if str(row["instance_generator_domain"])
        == REAL_MAP_SP50_DOMAIN
    ]
    if not target_train or not target_validation:
        raise SystemExit(
            f"fold {fold} lacks target rows for real-map linear pilot"
        )
    if regime != "REAL_ONLY" and not source_train:
        raise SystemExit(
            f"fold {fold} lacks source rows for synthetic transfer"
        )
    if regime == "REAL_ONLY":
        normalization_rows = target_train
        phases = (("REAL_FINETUNE", target_train, epochs),)
    elif regime == "SYNTHETIC_ONLY_ZERO_SHOT":
        normalization_rows = source_train
        phases = (("SYNTHETIC_PRETRAIN", source_train, pretrain_epochs),)
    elif regime == "SYNTHETIC_PRETRAIN_REAL_FINETUNE":
        normalization_rows = train_rows
        phases = (
            ("SYNTHETIC_PRETRAIN", source_train, pretrain_epochs),
            ("REAL_FINETUNE", target_train, epochs),
        )
    elif regime == "JOINT_DOMAIN_BALANCED":
        normalization_rows = train_rows
        phases = (("JOINT_TRAIN", train_rows, epochs),)
    else:
        raise ValueError(f"unknown transfer regime {regime}")

    normalization = core._fit_normalization(normalization_rows)
    torch.manual_seed(
        20260726 + 1009 * REGIMES.index(regime) + fold
    )
    model = build_branch_survival_model(
        "linear",
        node_input_dim=len(train_rows[0]["node_features"][0]),
        edge_input_dim=len(train_rows[0]["edge_features"][0]),
        pair_context_dim=len(train_rows[0]["branch_context"][0]),
    )
    phase_reports = []
    for phase_name, phase_rows, phase_epochs in phases:
        history = core._train(
            model,
            phase_rows,
            normalization,
            validation_rows=target_validation,
            epochs=int(phase_epochs),
            learning_rate=float(learning_rate),
        )
        phase_reports.append(
            {
                "phase": phase_name,
                "row_count": len(phase_rows),
                "epoch_count": int(phase_epochs),
                "loss_history": history["total_loss_history"],
            }
        )
    validation = core._evaluate(
        model, target_validation, normalization
    )
    checkpoint_path = output_dir / f"{regime}_fold{fold}.pt"
    torch.save(
        branch_survival_checkpoint_payload(
            model,
            metadata={
                "development_only": True,
                "deployment_authorized": False,
                "transfer_regime": regime,
                "target_domain": REAL_MAP_SP50_DOMAIN,
                "fold": fold,
                "normalization": normalization,
            },
        ),
        checkpoint_path,
    )
    return {
        "fold": fold,
        "phase_reports": phase_reports,
        "target_validation": validation,
        "target_validation_summary": core._summary(validation),
        "checkpoint_path": str(checkpoint_path.resolve()),
        "checkpoint_sha256": _file_sha256(checkpoint_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--headroom-pilot-report", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--pretrain-epochs", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--torch-threads", type=int, default=2)
    args = parser.parse_args()

    torch.set_num_threads(max(1, int(args.torch_threads)))
    records_path = Path(args.records_jsonl)
    rows = core._load_rows(records_path)
    headroom_path = Path(args.headroom_pilot_report)
    headroom = json.loads(headroom_path.read_text(encoding="utf-8"))
    if (
        str(headroom.get("schema_version") or "")
        != "lunar_ice_bpc.branch_cross_domain_pilot.v1"
        or str(headroom.get("records_sha256") or "")
        != _file_sha256(records_path)
        or headroom.get("target_headroom_pilot_passed") is not True
        or headroom.get("linear_real_map_pilot_authorized") is not True
        or headroom.get("calibration_used") is not False
        or headroom.get("protected_final_test_used") is not False
    ):
        raise SystemExit(
            "headroom pilot did not authorize linear transfer"
        )
    manifest = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if (
        str(manifest.get("schema_version") or "")
        != "lunar_ice_bpc.branch_grouped_split_manifest.v2"
        or not bool((manifest.get("audit") or {}).get("passed"))
        or manifest.get("calibration_read_authorized") is not False
        or str(headroom.get("split_manifest_hash") or "")
        != str(manifest.get("manifest_hash") or "")
    ):
        raise SystemExit("cross-domain grouped split is invalid")
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
            raise SystemExit("transfer record partition violation")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    regimes = ["REAL_ONLY"]
    if headroom.get("synthetic_transfer_pilot_authorized") is True:
        regimes.extend(
            regime
            for regime in REGIMES
            if regime != "REAL_ONLY"
        )
    regime_reports = {}
    combined_by_regime = {}
    target_folds = sorted(
        {
            assignment[str(row["instance_content_hash"])]
            for row in rows
            if str(row["instance_generator_domain"])
            == REAL_MAP_SP50_DOMAIN
        }
    )
    for regime in regimes:
        folds = []
        for fold in target_folds:
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
            folds.append(
                _train_regime(
                    regime=regime,
                    fold=fold,
                    train_rows=train_rows,
                    validation_rows=validation_rows,
                    epochs=int(args.epochs),
                    pretrain_epochs=int(args.pretrain_epochs),
                    learning_rate=float(args.learning_rate),
                    output_dir=output_dir,
                )
            )
        combined = [
            row
            for fold in folds
            for row in fold["target_validation"]
        ]
        combined.sort(
            key=lambda row: (
                row["instance_content_hash"],
                row["path_hash"],
            )
        )
        combined_gold = _gold_results(combined)
        baseline = _p0_results(
            [
                row
                for row in rows
                if str(row["instance_generator_domain"])
                == REAL_MAP_SP50_DOMAIN
            ]
        )
        comparison = core._paired_clustered_regret_improvement(
            baseline, combined_gold
        )
        regime_reports[regime] = {
            "folds": folds,
            "real_map_heldout": combined,
            "real_map_heldout_gold": combined_gold,
            "real_map_heldout_summary": core._summary(combined),
            "real_map_vs_p0": comparison,
            "real_map_vs_p0_worst_scale_lower95": (
                _worst_scale_lower(comparison)
            ),
        }
        combined_by_regime[regime] = combined_gold

    real_only = combined_by_regime["REAL_ONLY"]
    eligible = []
    for regime in regimes:
        payload = regime_reports[regime]
        ratio = payload["real_map_heldout_summary"][
            "mean_model_to_p0_wall_ratio"
        ]
        lower = payload["real_map_vs_p0_worst_scale_lower95"]
        if (
            ratio is not None
            and float(ratio) < 1.0
            and lower is not None
            and float(lower) >= 0.0
        ):
            eligible.append(regime)
    preference = {
        "REAL_ONLY": 0,
        "SYNTHETIC_PRETRAIN_REAL_FINETUNE": 1,
        "JOINT_DOMAIN_BALANCED": 2,
        "SYNTHETIC_ONLY_ZERO_SHOT": 3,
    }
    selected = (
        None
        if not eligible
        else min(
            eligible,
            key=lambda regime: (
                float(
                    regime_reports[regime][
                        "real_map_heldout_summary"
                    ]["mean_model_normalized_e2e_regret"]
                ),
                preference[regime],
            ),
        )
    )
    if selected == "SYNTHETIC_ONLY_ZERO_SHOT":
        selected = (
            "REAL_ONLY" if "REAL_ONLY" in eligible else None
        )
    selected_vs_real = None
    selected_vs_real_lower = None
    if selected is not None:
        selected_vs_real = (
            core._paired_clustered_regret_improvement(
                real_only,
                combined_by_regime[selected],
            )
        )
        selected_vs_real_lower = _worst_scale_lower(
            selected_vs_real
        )
        if (
            selected
            in {
                "SYNTHETIC_PRETRAIN_REAL_FINETUNE",
                "JOINT_DOMAIN_BALANCED",
                "SYNTHETIC_ONLY_ZERO_SHOT",
            }
            and (
                selected_vs_real_lower is None
                or float(selected_vs_real_lower) < 0.0
            )
        ):
            selected = (
                "REAL_ONLY"
                if "REAL_ONLY" in eligible
                else None
            )
            selected_vs_real = None
            selected_vs_real_lower = 0.0 if selected else None

    selected_payload = (
        None if selected is None else regime_reports[selected]
    )
    selected_summary = (
        {}
        if selected_payload is None
        else selected_payload["real_map_heldout_summary"]
    )
    selected_comparison = (
        {}
        if selected_payload is None
        else selected_payload["real_map_vs_p0"]
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "model_kind": "linear",
        "records_sha256": _file_sha256(records_path),
        "split_manifest_hash": manifest["manifest_hash"],
        "headroom_pilot_report_sha256": _file_sha256(
            headroom_path
        ),
        "target_domain": REAL_MAP_SP50_DOMAIN,
        "source_domain": SYNTHETIC_POLAR_GRID_DOMAIN,
        "evaluated_regimes": regimes,
        "synthetic_transfer_evaluated": len(regimes) > 1,
        "calibration_used": False,
        "protected_final_test_used": False,
        "regimes": regime_reports,
        "selected_training_regime": selected,
        "real_map_mean_model_to_p0_wall_ratio": (
            selected_summary.get("mean_model_to_p0_wall_ratio")
        ),
        "real_map_vs_p0_improvement_bootstrap_lower95": (
            _worst_scale_lower(selected_comparison)
        ),
        "selected_vs_real_only": selected_vs_real,
        "selected_vs_real_only_real_map_improvement_lower95": (
            selected_vs_real_lower
        ),
        "synthetic_inclusion_authorized": bool(
            selected
            in {
                "SYNTHETIC_PRETRAIN_REAL_FINETUNE",
                "JOINT_DOMAIN_BALANCED",
            }
            and selected_vs_real_lower is not None
            and float(selected_vs_real_lower) >= 0.0
        ),
        "expanded_collection_authorized": selected is not None,
        "gat_training_authorized": False,
        "deployment_authorized": False,
    }
    destination = output_dir / "cross_domain_linear_pilot_report.json"
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
                "selected_training_regime": selected,
                "expanded_collection_authorized": (
                    report["expanded_collection_authorized"]
                ),
                "gat_training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0 if selected is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
