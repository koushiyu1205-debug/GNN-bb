"""Exact-safe learning dual stabilizer.

The stabilizer is deliberately outside the RMP/pricing proof logic.  It can
produce smoothed task-cover duals for heuristic pricing, but it cannot certify
node LP completion.  If heuristic pricing with smoothed duals fails to find a
negative column, callers must use the returned fallback marker and rerun exact
pricing with the original true RMP duals.
"""

from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

try:  # pragma: no cover - import failure path is environment-dependent.
    import torch
    from torch import Tensor
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "BPC_future.learning.dual_stabilizer requires torch. Install the learning stack before use."
    ) from exc

from BPC_future.learning.gnn_model import HierarchicalOptionGAT


REQUIRED_CHECKPOINT_FIELDS: tuple[str, ...] = (
    "model_state_dict",
    "model_config",
    "node_feature_mean",
    "node_feature_std",
    "option_feature_mean",
    "option_feature_std",
    "feature_schema",
    "version",
)


@dataclass(frozen=True)
class DualStabilizerConfig:
    checkpoint_path: str
    device: str = "cpu"
    alpha_init: float = 0.8
    alpha_min_active: float = 0.2
    alpha_decay: float = 0.05
    stagnation_patience: int = 3
    stagnation_rel_improve: float = 1.0e-3
    disable_on_branch_depth_gt: int = 0
    filter_true_rc: bool = False
    rc_filter_tol: float = 1.0e-8
    debug_checks: bool = False


@dataclass(frozen=True)
class PricingFallbackDecision:
    """Marker returned after smoothed pricing when true-dual fallback is needed."""

    use_true_dual_exact_pricing: bool
    alpha: float
    reason: str


class DualStabilizer:
    """Load ``HierarchicalOptionGAT`` and produce exact-safe smoothed task duals."""

    def __init__(self, config: DualStabilizerConfig) -> None:
        self.config = config
        self.device = torch.device(config.device)
        self.alpha = float(config.alpha_init)
        self._forced_exact = False
        self.checkpoint = self._load_checkpoint(Path(config.checkpoint_path))
        self.feature_schema = self._validate_feature_schema(self.checkpoint["feature_schema"])
        self.node_mean = self._normalizer_tensor("node_feature_mean", expected_dim=self._node_dim)
        self.node_std = self._normalizer_tensor("node_feature_std", expected_dim=self._node_dim)
        self.option_mean = self._normalizer_tensor("option_feature_mean", expected_dim=self._option_dim)
        self.option_std = self._normalizer_tensor("option_feature_std", expected_dim=self._option_dim)
        self.label_mean = _optional_scalar(self.checkpoint.get("label_mean"), default=0.0)
        self.label_std = _optional_scalar(self.checkpoint.get("label_std"), default=1.0)
        if self.label_std <= 0:
            raise ValueError("checkpoint label_std must be positive when present")

        self.model = self._build_model(self.checkpoint["model_config"])
        self.model.load_state_dict(self.checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()
        self.last_anchor: Dict[int, float] | None = None

    def reset_runtime_state(self) -> None:
        """Reset per-solve mutable state while keeping loaded model weights.

        ``DualStabilizer`` may be cached across multiple solver runs to avoid
        repeatedly loading the same CUDA checkpoint.  The model and normalizers
        are immutable during inference, but alpha annealing and the latest
        anchor are solve-local state and must not leak between instances.
        """

        self.alpha = float(self.config.alpha_init)
        self._forced_exact = False
        self.last_anchor = None

    @property
    def _node_dim(self) -> int:
        return len(self.feature_schema["node"])

    @property
    def _option_dim(self) -> int:
        return len(self.feature_schema["option"])

    def predict_anchor(self, data: Any) -> Dict[int, float]:
        """Return ``task_id -> predicted_pi`` on the original dual scale."""

        num_graphs = int(getattr(data, "num_graphs", 1))
        if num_graphs != 1:
            raise ValueError(
                "DualStabilizer.predict_anchor supports exactly one PyG graph. "
                "Use HierarchicalOptionGAT.forward directly for offline batches."
            )
        self._validate_data_schema(data)
        inference_data = self._normalized_data_copy(data)
        with torch.no_grad():
            output = self.model(inference_data)
            pred_task = output["pred_task"].detach().cpu()
        pred_task = pred_task * float(self.label_std) + float(self.label_mean)
        task_ids = _tensor_to_int_list(getattr(data, "task_ids"))
        if len(task_ids) != int(pred_task.numel()):
            raise ValueError(
                f"task_ids length {len(task_ids)} does not match pred_task length {int(pred_task.numel())}"
            )
        if self.config.debug_checks:
            _assert_finite(pred_task, "denormalized predicted task duals")
        anchor = {int(task_id): float(value) for task_id, value in zip(task_ids, pred_task.tolist())}
        self.last_anchor = anchor
        return anchor

    def smooth_task_duals(
        self,
        true_task_duals: Dict[int, float],
        predicted_anchor: Dict[int, float],
        alpha: Optional[float] = None,
    ) -> Dict[int, float]:
        """Apply Wentges-style smoothing to task-cover duals only."""

        active_alpha = self.alpha if alpha is None else float(alpha)
        active_alpha = max(0.0, min(float(active_alpha), 1.0))
        if active_alpha <= 0.0:
            return {int(task_id): float(value) for task_id, value in true_task_duals.items()}

        missing = sorted(int(task_id) for task_id in true_task_duals if int(task_id) not in predicted_anchor)
        if missing:
            raise ValueError(f"predicted_anchor missing task ids required for smoothing: {missing}")

        one_minus_alpha = 1.0 - active_alpha
        return {
            int(task_id): active_alpha * float(predicted_anchor[int(task_id)])
            + one_minus_alpha * float(true_dual)
            for task_id, true_dual in true_task_duals.items()
        }

    def update_alpha(
        self,
        rmp_obj_history: Sequence[float],
        pricing_stats: Optional[Dict[str, Any]] = None,
        branch_depth: int = 0,
    ) -> float:
        """Update alpha with slow decay plus stagnation/certificate cutoffs."""

        if self._forced_exact:
            self.alpha = 0.0
            return self.alpha

        if self.should_disable(branch_depth=branch_depth, certificate_mode=bool((pricing_stats or {}).get("certificate_mode", False))):
            self.force_exact_mode()
            return self.alpha

        if self._pricing_verification_failed(pricing_stats or {}):
            self.force_exact_mode()
            return self.alpha

        if self._is_stagnating(rmp_obj_history):
            self.force_exact_mode()
            return self.alpha

        if len(rmp_obj_history) < 2:
            return self.alpha

        self.alpha = max(float(self.config.alpha_min_active), float(self.alpha) - float(self.config.alpha_decay))
        return self.alpha

    def should_disable(self, branch_depth: int, certificate_mode: bool = False) -> bool:
        """Return whether learning smoothing must be disabled."""

        if certificate_mode:
            return True
        return int(branch_depth) > int(self.config.disable_on_branch_depth_gt)

    def force_exact_mode(self) -> None:
        """Force alpha to zero; subsequent smoothing returns true RMP duals."""

        self.alpha = 0.0
        self._forced_exact = True

    def handle_smoothed_pricing_result(
        self,
        *,
        found_negative_column: bool,
        certificate_mode: bool = False,
    ) -> PricingFallbackDecision:
        """Return a special marker when true-dual exact pricing must be rerun."""

        if certificate_mode:
            self.force_exact_mode()
            return PricingFallbackDecision(
                use_true_dual_exact_pricing=True,
                alpha=self.alpha,
                reason="certificate_mode_requires_true_dual",
            )
        if found_negative_column:
            return PricingFallbackDecision(
                use_true_dual_exact_pricing=False,
                alpha=self.alpha,
                reason="smoothed_pricing_found_candidate",
            )
        if self.alpha > 0.0:
            return PricingFallbackDecision(
                use_true_dual_exact_pricing=True,
                alpha=self.alpha,
                reason="smoothed_pricing_no_strong_true_rc_column",
            )
        return PricingFallbackDecision(
            use_true_dual_exact_pricing=True,
            alpha=self.alpha,
            reason="already_in_true_dual_mode",
        )

    def _load_checkpoint(self, path: Path) -> Mapping[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"learning checkpoint not found: {path}")
        checkpoint = torch.load(path, map_location=self.device)
        if not isinstance(checkpoint, Mapping):
            raise ValueError("checkpoint must be a mapping")
        missing = [field for field in REQUIRED_CHECKPOINT_FIELDS if field not in checkpoint]
        if missing:
            raise ValueError(f"checkpoint missing required fields: {missing}")
        return checkpoint

    def _build_model(self, model_config: Any) -> HierarchicalOptionGAT:
        if not isinstance(model_config, Mapping):
            raise ValueError("checkpoint model_config must be a mapping")
        config = dict(model_config)
        config.setdefault("node_dim", self._node_dim)
        config.setdefault("option_dim", self._option_dim)
        if int(config["node_dim"]) != self._node_dim:
            raise ValueError("model_config.node_dim does not match feature_schema.node length")
        if int(config["option_dim"]) != self._option_dim:
            raise ValueError("model_config.option_dim does not match feature_schema.option length")
        return HierarchicalOptionGAT(**config)

    def _validate_feature_schema(self, feature_schema: Any) -> Dict[str, list[str]]:
        if not isinstance(feature_schema, Mapping):
            raise ValueError("checkpoint feature_schema must be a mapping")
        node_schema = _schema_list(feature_schema.get("node"), "feature_schema.node")
        option_schema = _schema_list(feature_schema.get("option"), "feature_schema.option")
        return {"node": node_schema, "option": option_schema}

    def _normalizer_tensor(self, field: str, *, expected_dim: int) -> Tensor:
        values = self.checkpoint[field]
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise ValueError(f"checkpoint {field} must be a numeric sequence")
        if len(values) != expected_dim:
            raise ValueError(f"checkpoint {field} length {len(values)} != expected dim {expected_dim}")
        tensor = torch.tensor([float(value) for value in values], dtype=torch.float32, device=self.device)
        _assert_finite(tensor, field)
        if field.endswith("_std") and bool(torch.any(tensor <= 0)):
            raise ValueError(f"checkpoint {field} must be strictly positive")
        return tensor

    def _validate_data_schema(self, data: Any) -> None:
        node_schema = _schema_list(getattr(data, "node_feature_schema", None), "data.node_feature_schema")
        option_schema = _schema_list(getattr(data, "option_feature_schema", None), "data.option_feature_schema")
        if node_schema != self.feature_schema["node"]:
            raise ValueError(
                f"data node schema does not match checkpoint: {node_schema} != {self.feature_schema['node']}"
            )
        if option_schema != self.feature_schema["option"]:
            raise ValueError(
                f"data option schema does not match checkpoint: {option_schema} != {self.feature_schema['option']}"
            )
        if int(getattr(data, "x").size(1)) != self._node_dim:
            raise ValueError("data.x width does not match checkpoint node feature dim")
        if int(getattr(data, "option_feat").size(1)) != self._option_dim:
            raise ValueError("data.option_feat width does not match checkpoint option feature dim")

    def _normalized_data_copy(self, data: Any) -> Any:
        graph = data.clone() if hasattr(data, "clone") else copy(data)
        graph = graph.to(self.device) if hasattr(graph, "to") else graph
        already_normalized = bool(getattr(graph, "learning_features_normalized", False))
        if not already_normalized:
            graph.x = (graph.x - self.node_mean) / self.node_std
            graph.option_feat = (graph.option_feat - self.option_mean) / self.option_std
            graph.learning_features_normalized = True
        if self.config.debug_checks:
            _assert_finite(graph.x, "normalized node features")
            _assert_finite(graph.option_feat, "normalized option features")
        return graph

    def _is_stagnating(self, rmp_obj_history: Sequence[float]) -> bool:
        patience = int(self.config.stagnation_patience)
        if patience <= 0 or len(rmp_obj_history) < patience + 1:
            return False
        recent = [float(value) for value in rmp_obj_history[-(patience + 1) :]]
        improvements: list[float] = []
        eps = 1.0e-12
        for last_obj, current_obj in zip(recent[:-1], recent[1:]):
            denom = max(abs(float(last_obj)), eps)
            improvements.append((float(last_obj) - float(current_obj)) / denom)
        return all(improvement < float(self.config.stagnation_rel_improve) for improvement in improvements)

    def _pricing_verification_failed(self, pricing_stats: Mapping[str, Any]) -> bool:
        if bool(pricing_stats.get("true_dual_verification_failed", False)):
            return True
        failure_rate = pricing_stats.get("true_dual_verification_failure_rate")
        if failure_rate is None:
            return False
        return float(failure_rate) > 0.25


def _schema_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    return [str(item) for item in value]


def _optional_scalar(value: Any, *, default: float) -> float:
    if value is None:
        return float(default)
    if isinstance(value, Tensor):
        if value.numel() != 1:
            raise ValueError("scalar checkpoint field contains more than one value")
        value = value.detach().cpu().item()
    return float(value)


def _tensor_to_int_list(value: Any) -> list[int]:
    if isinstance(value, Tensor):
        return [int(item) for item in value.detach().cpu().tolist()]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [int(item) for item in value]
    raise ValueError("task_ids must be a tensor or sequence of ints")


def _assert_finite(tensor: Tensor, name: str) -> None:
    if not bool(torch.all(torch.isfinite(tensor))):
        raise ValueError(f"{name} contains NaN or Inf")
