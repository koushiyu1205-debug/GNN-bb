"""Hierarchical path-option GAT for task-cover dual-anchor prediction.

V1 intentionally keeps all path options in a flattened sparse representation.
There is no padding or masking path.  Option-level attention and physical
pooling are grouped by ``option_pair_id`` with ``torch_scatter`` primitives.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

try:  # pragma: no cover - import failure path is environment-dependent.
    import torch
    from torch import Tensor, nn
    import torch.nn.functional as F
    from torch_geometric.nn import GATv2Conv
    from torch_scatter import scatter_add, scatter_max, scatter_mean, scatter_min, scatter_softmax
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "BPC_future.learning.gnn_model requires torch, torch_geometric, and torch_scatter. "
        "Install a PyTorch/PyG stack with a torch_scatter wheel matching your torch version."
    ) from exc


class OptionEncoder(nn.Module):
    """Encode variable-size path-option sets into directed pair-edge features.

    Args:
        node_hidden_dim: Hidden dimension of node embeddings.
        option_dim: Dimension of ``data.option_feat``.
        option_hidden_dim: Hidden dimension for per-option messages.
        pair_edge_dim: Final directed pair-edge embedding dimension.
        phys_feature_indices: Option feature indices used for max/min/std pools.
            By convention V1 option schema starts with distance, travel_time,
            energy, risk, generalized_cost, so the default is ``[0, 1, 2, 3, 4]``.
        dropout: Dropout used inside option MLPs.
    """

    def __init__(
        self,
        node_hidden_dim: int,
        option_dim: int,
        option_hidden_dim: int,
        pair_edge_dim: int,
        phys_feature_indices: Optional[Sequence[int]] = None,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        if node_hidden_dim <= 0 or option_dim <= 0 or option_hidden_dim <= 0 or pair_edge_dim <= 0:
            raise ValueError("OptionEncoder dimensions must be positive")
        self.node_hidden_dim = int(node_hidden_dim)
        self.option_dim = int(option_dim)
        self.option_hidden_dim = int(option_hidden_dim)
        self.pair_edge_dim = int(pair_edge_dim)
        default_phys = tuple(range(min(5, int(option_dim))))
        self.phys_feature_indices = tuple(int(idx) for idx in (phys_feature_indices or default_phys))
        if not self.phys_feature_indices:
            raise ValueError("phys_feature_indices must not be empty")
        for idx in self.phys_feature_indices:
            if idx < 0 or idx >= int(option_dim):
                raise ValueError(f"physical feature index {idx} outside option_dim={option_dim}")

        context_dim = 3 * int(node_hidden_dim) + int(option_dim)
        self.option_message = nn.Sequential(
            nn.Linear(context_dim, int(option_hidden_dim)),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(option_hidden_dim), int(option_hidden_dim)),
            nn.ReLU(),
        )
        self.attention_score = nn.Sequential(
            nn.Linear(context_dim, int(option_hidden_dim)),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(option_hidden_dim), 1),
        )
        pooled_dim = int(option_hidden_dim) + 3 * len(self.phys_feature_indices) + 1
        self.pair_projector = nn.Sequential(
            nn.Linear(pooled_dim, int(pair_edge_dim)),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(pair_edge_dim), int(pair_edge_dim)),
        )

    def forward(
        self,
        node_h: Tensor,
        pair_edge_index: Tensor,
        option_feat: Tensor,
        option_pair_id: Tensor,
    ) -> Tuple[Tensor, Dict[str, Tensor]]:
        """Return pair-edge embeddings and option-attention diagnostics."""

        if option_pair_id.dtype != torch.long:
            option_pair_id = option_pair_id.long()
        self._validate_inputs(node_h, pair_edge_index, option_feat, option_pair_id)
        num_pairs = int(pair_edge_index.size(1))
        source_index = pair_edge_index[0]
        target_index = pair_edge_index[1]
        h_src = node_h[source_index]
        h_dst = node_h[target_index]

        # 关键防错：option_feat 是 [num_options, D]，而 h_src/h_dst 是
        # [num_pairs, H]。必须先用 option_pair_id 广播到 option 维度，
        # 才能拼接；否则会把 pair 维和 option 维错位。
        h_src_opt = h_src[option_pair_id]
        h_dst_opt = h_dst[option_pair_id]
        ctx = torch.cat([h_src_opt, h_dst_opt, h_dst_opt - h_src_opt, option_feat], dim=-1)

        option_message = self.option_message(ctx)
        raw_score = self.attention_score(ctx).squeeze(-1)
        _assert_finite(raw_score, "option attention scores")

        # 关键防错：严格使用 flattened option list + scatter_softmax。
        # 禁止 padding/masking，避免空 padding option 泄漏进 softmax 权重。
        option_attention = scatter_softmax(raw_score, option_pair_id, dim=0)
        _assert_finite(option_attention, "option attention weights")

        weighted_message = option_message * option_attention.unsqueeze(-1)
        attention_pool = scatter_add(weighted_message, option_pair_id, dim=0, dim_size=num_pairs)

        phys = option_feat[:, self.phys_feature_indices]
        max_pool = scatter_max(phys, option_pair_id, dim=0, dim_size=num_pairs)[0]
        min_pool = scatter_min(phys, option_pair_id, dim=0, dim_size=num_pairs)[0]
        mean_pool = scatter_mean(phys, option_pair_id, dim=0, dim_size=num_pairs)

        # 关键防错：这里用 scatter_mean((x-mean)^2) 的 N 分母偏估计，
        # 等价于 torch.std(unbiased=False)。safe sqrt 保持零方差 pair
        # 的 forward 值为 0，同时避免 sqrt(0) 在 backward 中产生 NaN。
        centered = phys - mean_pool[option_pair_id]
        var_pool = scatter_mean(centered * centered, option_pair_id, dim=0, dim_size=num_pairs)
        std_pool = _safe_sqrt_zero_forward(var_pool)
        std_pool = torch.nan_to_num(std_pool, nan=0.0, posinf=0.0, neginf=0.0)

        ones = torch.ones((option_feat.size(0), 1), dtype=option_feat.dtype, device=option_feat.device)
        option_count = scatter_add(ones, option_pair_id, dim=0, dim_size=num_pairs)
        if bool(torch.any(option_count <= 0)):
            raise ValueError("each directed pair must have at least one path option")

        pair_input = torch.cat([attention_pool, max_pool, min_pool, std_pool, option_count], dim=-1)
        pair_edge_attr = self.pair_projector(pair_input)
        _assert_finite(pair_edge_attr, "pair edge attributes")

        entropy_term = -option_attention * torch.log(torch.clamp(option_attention, min=1.0e-12))
        option_entropy = scatter_add(entropy_term, option_pair_id, dim=0, dim_size=num_pairs)

        aux = {
            "option_attention": option_attention,
            "option_entropy": option_entropy,
            "attention_pool": attention_pool,
            "max_pool": max_pool,
            "min_pool": min_pool,
            "std_pool": std_pool,
            "option_count": option_count.squeeze(-1),
        }
        return pair_edge_attr, aux

    def _validate_inputs(
        self,
        node_h: Tensor,
        pair_edge_index: Tensor,
        option_feat: Tensor,
        option_pair_id: Tensor,
    ) -> None:
        if node_h.dim() != 2 or node_h.size(1) != self.node_hidden_dim:
            raise ValueError(
                f"node_h must have shape [num_nodes, {self.node_hidden_dim}], got {tuple(node_h.shape)}"
            )
        if pair_edge_index.dim() != 2 or pair_edge_index.size(0) != 2:
            raise ValueError(f"pair_edge_index must have shape [2, num_pairs], got {tuple(pair_edge_index.shape)}")
        if option_feat.dim() != 2 or option_feat.size(1) != self.option_dim:
            raise ValueError(
                f"option_feat must have shape [num_options, {self.option_dim}], got {tuple(option_feat.shape)}"
            )
        if option_pair_id.dim() != 1 or option_pair_id.size(0) != option_feat.size(0):
            raise ValueError("option_pair_id must be a vector with one id per option")
        if option_feat.size(0) == 0:
            raise ValueError("option_feat must contain at least one path option")
        if pair_edge_index.size(1) == 0:
            raise ValueError("pair_edge_index must contain at least one directed pair")
        if bool(torch.any(option_pair_id < 0)) or bool(torch.any(option_pair_id >= pair_edge_index.size(1))):
            raise ValueError("option_pair_id contains ids outside [0, num_pairs)")
        _assert_finite(node_h, "node embeddings")
        _assert_finite(option_feat, "option features")


class HierarchicalOptionGAT(nn.Module):
    """Predict task-cover dual anchors from directed logical graphs.

    Expected ``data`` fields:
    - ``x``: ``[num_nodes, node_dim]`` node features;
    - ``pair_edge_index``: ``[2, num_pairs]`` directed logical edges;
    - ``option_feat``: ``[num_options, option_dim]`` flattened path options;
    - ``option_pair_id``: ``[num_options]`` directed pair id for each option;
    - ``task_mask``: ``[num_nodes]`` bool mask selecting task nodes.
    """

    def __init__(
        self,
        node_dim: int,
        option_dim: int,
        hidden_dim: int = 128,
        option_hidden_dim: int = 128,
        pair_edge_dim: int = 128,
        num_gnn_layers: int = 2,
        heads: int = 4,
        dropout: float = 0.1,
        use_layer_norm: bool = True,
    ) -> None:
        super().__init__()
        if int(num_gnn_layers) < 1 or int(num_gnn_layers) > 3:
            raise ValueError("num_gnn_layers must be in [1, 3] for V1")
        if int(hidden_dim) <= 0 or int(node_dim) <= 0 or int(option_dim) <= 0:
            raise ValueError("node_dim, option_dim, and hidden_dim must be positive")
        if int(heads) <= 0:
            raise ValueError("heads must be positive")
        if int(hidden_dim) % int(heads) != 0:
            raise ValueError("hidden_dim must be divisible by heads when GATv2Conv concat=True")

        self.node_dim = int(node_dim)
        self.option_dim = int(option_dim)
        self.hidden_dim = int(hidden_dim)
        self.option_hidden_dim = int(option_hidden_dim)
        self.pair_edge_dim = int(pair_edge_dim)
        self.num_gnn_layers = int(num_gnn_layers)
        self.heads = int(heads)
        self.dropout_p = float(dropout)
        self.use_layer_norm = bool(use_layer_norm)

        self.node_proj = nn.Sequential(
            nn.Linear(self.node_dim, self.hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(self.hidden_dim) if self.use_layer_norm else nn.Identity(),
        )
        self.option_encoder = OptionEncoder(
            node_hidden_dim=self.hidden_dim,
            option_dim=self.option_dim,
            option_hidden_dim=self.option_hidden_dim,
            pair_edge_dim=self.pair_edge_dim,
            dropout=self.dropout_p,
        )

        out_channels = self.hidden_dim // self.heads
        self.gat_layers = nn.ModuleList(
            [
                GATv2Conv(
                    in_channels=self.hidden_dim,
                    out_channels=out_channels,
                    heads=self.heads,
                    concat=True,
                    edge_dim=self.pair_edge_dim,
                    dropout=self.dropout_p,
                    add_self_loops=False,
                )
                for _ in range(self.num_gnn_layers)
            ]
        )
        self.norms = nn.ModuleList(
            [nn.LayerNorm(self.hidden_dim) if self.use_layer_norm else nn.Identity() for _ in range(self.num_gnn_layers)]
        )
        self.dropout = nn.Dropout(self.dropout_p)
        self.out_mlp = nn.Sequential(
            nn.Linear(2 * self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Dropout(self.dropout_p),
            nn.Linear(self.hidden_dim, 1),
        )

    def encode(self, data: Any) -> Dict[str, Tensor]:
        """Return graph embeddings without applying the dual-anchor output head."""

        x = getattr(data, "x")
        pair_edge_index = getattr(data, "pair_edge_index")
        option_feat = getattr(data, "option_feat")
        option_pair_id = getattr(data, "option_pair_id")
        task_mask = getattr(data, "task_mask")

        self._validate_data_tensors(x, pair_edge_index, option_feat, option_pair_id, task_mask)
        h0 = self.node_proj(x)
        pair_edge_attr, aux = self.option_encoder(h0, pair_edge_index, option_feat, option_pair_id.long())

        h = h0
        for gat, norm in zip(self.gat_layers, self.norms):
            msg = gat(h, pair_edge_index, pair_edge_attr)
            msg = F.elu(msg)
            h = norm(h + self.dropout(msg))
            _assert_finite(h, "GAT node state")

        return {
            "node_h": h,
            "initial_node_h": h0,
            "task_h": h[task_mask],
            "initial_task_h": h0[task_mask],
            "pair_edge_attr": pair_edge_attr,
            "option_attention": aux["option_attention"],
            "option_entropy": aux["option_entropy"],
            "max_pool": aux["max_pool"],
            "min_pool": aux["min_pool"],
            "std_pool": aux["std_pool"],
        }

    def forward(self, data: Any) -> Dict[str, Tensor]:
        encoded = self.encode(data)
        h = encoded["node_h"]
        h0 = encoded["initial_node_h"]
        task_mask = getattr(data, "task_mask")

        pred_all = self.out_mlp(torch.cat([h, h0], dim=-1)).squeeze(-1)
        _assert_finite(pred_all, "dual predictions")
        pred_task = pred_all[task_mask]
        if pred_task.numel() != int(task_mask.sum().item()):
            raise ValueError("pred_task length does not match task_mask")

        return {
            "pred_all_nodes": pred_all,
            "pred_task": pred_task,
            "option_attention": encoded["option_attention"],
            "option_entropy": encoded["option_entropy"],
            "pair_edge_attr": encoded["pair_edge_attr"],
            "max_pool": encoded["max_pool"],
            "min_pool": encoded["min_pool"],
            "std_pool": encoded["std_pool"],
        }

    def _validate_data_tensors(
        self,
        x: Tensor,
        pair_edge_index: Tensor,
        option_feat: Tensor,
        option_pair_id: Tensor,
        task_mask: Tensor,
    ) -> None:
        if x.dim() != 2 or x.size(1) != self.node_dim:
            raise ValueError(f"data.x must have shape [num_nodes, {self.node_dim}], got {tuple(x.shape)}")
        if pair_edge_index.dim() != 2 or pair_edge_index.size(0) != 2:
            raise ValueError("data.pair_edge_index must have shape [2, num_pairs]")
        if option_feat.dim() != 2 or option_feat.size(1) != self.option_dim:
            raise ValueError(
                f"data.option_feat must have shape [num_options, {self.option_dim}], got {tuple(option_feat.shape)}"
            )
        if option_pair_id.dim() != 1 or option_pair_id.size(0) != option_feat.size(0):
            raise ValueError("data.option_pair_id must have one id per option")
        if task_mask.dim() != 1 or task_mask.size(0) != x.size(0):
            raise ValueError("data.task_mask must be a bool vector with one entry per node")
        if task_mask.dtype != torch.bool:
            raise ValueError("data.task_mask must have dtype torch.bool")
        _assert_finite(x, "node features")
        _assert_finite(option_feat, "option features")


def dual_prediction_loss(
    pred_task: Tensor,
    y_task: Tensor,
    loss_type: str = "huber",
    huber_delta: float = 0.5,
) -> Tensor:
    """Compute task-only dual prediction loss.

    ``huber_delta`` is exposed because labels may be standardized to a small
    scale; using the default PyTorch delta of 1.0 can make Huber behave too much
    like L2 in that setting.
    """

    if pred_task.shape != y_task.shape:
        raise ValueError(f"pred_task shape {tuple(pred_task.shape)} != y_task shape {tuple(y_task.shape)}")
    _assert_finite(pred_task, "pred_task")
    _assert_finite(y_task, "y_task")
    normalized_loss = loss_type.strip().lower()
    if normalized_loss == "huber":
        if huber_delta <= 0:
            raise ValueError("huber_delta must be positive")
        return F.huber_loss(pred_task, y_task, delta=float(huber_delta))
    if normalized_loss == "mse":
        return F.mse_loss(pred_task, y_task)
    raise ValueError("loss_type must be 'huber' or 'mse'")


def _assert_finite(tensor: Tensor, name: str) -> None:
    if not bool(torch.all(torch.isfinite(tensor))):
        raise ValueError(f"{name} contains NaN or Inf")


def _safe_sqrt_zero_forward(var: Tensor, *, eps: float = 1.0e-8) -> Tensor:
    """Return sqrt(var) with finite zero-variance backward behavior."""

    return torch.sqrt(torch.clamp(var, min=0.0) + float(eps)) - float(eps) ** 0.5
