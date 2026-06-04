# Learning Dual Stabilization Design Notes

This document records the agreed design contract for adding a learning-based
dual stabilization mechanism to `BPC_future`. The goal is to use a GNN prior to
accelerate column generation while preserving the exact Branch-and-Price proof
boundary.

## Scope

The learning component is a heuristic pricing accelerator for the Moon Trek
journey-column Branch-and-Price solver. It predicts a stable task-cover dual
anchor and uses Wentges-style smoothing only for candidate journey generation.

The component must live under `BPC_future/learning/` and must not leak PyTorch or
PyTorch Geometric dependencies into `core`, `master`, or `pricing`.

Planned V1 files:

```text
BPC_future/learning/
  __init__.py
  graph_builder.py
  gnn_model.py
  dual_stabilizer.py
```

Optional V1 tests:

```text
BPC_future/tests/test_learning_graph_builder.py
BPC_future/tests/test_learning_gnn_model.py
BPC_future/tests/test_dual_stabilizer.py
```

The first implementation targets the `BPC_future` journey master only. It does
not support the old trip-time master time-occupation rows.

## Exactness Contract

- The GNN predicts only task-cover duals `pi_i`.
- Fleet-limit duals, SRC cut duals, branch-row duals, and time-bucket duals
  always come directly from the current RMP solution.
- Smoothed duals are used only to search for candidate journey columns.
- Smoothed duals must not affect official RMP bounds, node completion,
  branching decisions, or optimality certificates.
- If smoothed-dual pricing finds no negative reduced-cost column, the solver
  must set `alpha = 0` and rerun exact pricing with the original SCIP/RMP duals.
- A node LP is certified only when true-dual exact pricing exhausts and proves
  that no negative reduced-cost journey remains.
- GNN output never contributes to an official lower bound or optimality
  certificate.
- With GNN enabled or disabled, primal/dual optimal values and certificate
  semantics must remain identical.

The GNN-smoothed dual is therefore an advanced heuristic column generator, not a
mathematical proof object.

## Model Target

The model target is the stable dual center of task-cover rows:

```text
pi_anchor[i] ~= average of clean RMP task-cover duals from the last 5-10
                effective root-node convergence iterations
```

The label should not be a single final simplex extreme-point dual, because the
RMP is highly degenerate and the optimal dual is generally not unique. The
preferred label is a local dual center such as a sliding average of pure RMP
duals, or a representative selected from the optimal dual face.

The GNN output layer must remain a raw scalar regression head. Do not apply
`ReLU`, `Softplus`, or any nonnegative activation, because task-cover equality
duals are free variables and may be negative.

## Graph Definition

The graph is a directed, fully connected logical route network. The depot is
included for message passing, but its model output is masked out before loss
calculation and before returning the anchor dictionary.

V1 must preserve all physical path options. It must not collapse options into a
single cheapest edge, a weighted edge, or a min/mean/max aggregate before the
model sees them.

Required PyG `Data` fields:

```text
data.x
  shape: [num_nodes, node_dim]
  node features.

data.pair_edge_index
  shape: [2, num_pairs]
  one directed logical pair edge per ordered node pair.
  pair_edge_index[0] is source and pair_edge_index[1] is target.

data.option_feat
  shape: [num_options, option_dim]
  one row per physical path option.

data.option_pair_id
  shape: [num_options]
  option_pair_id[o] gives the directed pair edge id of option o.

data.task_ids
  shape: [num_tasks]
  real project task ids for task nodes only.

data.task_mask
  shape: [num_nodes]
  bool tensor. Task nodes are True; depot is False.

data.node_ids
  shape: [num_nodes]
  node id mapping for diagnostics.
```

Optional training label:

```text
data.y
  shape: [num_nodes] or [num_tasks]
  dual-center labels. Loss is computed only on task nodes.
```

Directedness is mandatory. The pair `i -> j` and `j -> i` must both exist and may
have different option features. They must not be merged into an undirected edge.

Every directed pair must have at least one path option. If a pair has no path
option, graph construction should raise a clear `ValueError`, because the
logical graph is expected to be a complete feasible directed graph.

## Feature Schema

V1 uses a fixed node feature schema and strong checkpoint-time validation.

Node feature schema:

```text
[
  demand,
  service_time,
  time_window_start,
  time_window_end,
  x_coord,
  y_coord,
  is_depot,
  service_energy,
  local_risk,
]
```

Depot feature convention:

```text
demand = 0
service_time = 0
time_window_start = 0
time_window_end = horizon
x_coord = depot x
y_coord = depot y
is_depot = 1
service_energy = 0
local_risk = 0
```

Task nodes use `is_depot = 0` and physical values from the instance. Missing
basic physical node fields should raise a clear `ValueError`.

Option feature schema:

```text
[
  distance,
  travel_time,
  energy,
  risk,
  generalized_cost,
  is_low_time,
  is_low_energy,
  is_low_risk,
  option_rank,
  option_count_for_pair,
]
```

Core physical option fields are required:

```text
distance, travel_time, energy, risk
```

If any core physical option field is missing, graph construction must raise a
clear `ValueError`.

Derived or diagnostic option fields may be absent:

```text
generalized_cost, is_low_time, is_low_energy, is_low_risk,
option_rank, option_count_for_pair
```

Missing derived fields may default to `0` with a warning so older data can still
be parsed.

The checkpoint must store the exact `feature_schema`. During inference,
`FutureGraphBuilder` must assert that the parsed schema and dimensions exactly
match the checkpoint schema. Normalizer or schema mismatches must never be
silently ignored.

## Graph Builder

`graph_builder.py` provides the translation boundary between the optimization
code and the learning code.

Recommended API:

```python
class FutureGraphBuilder:
    def __init__(
        self,
        node_feature_schema: Optional[List[str]] = None,
        option_feature_schema: Optional[List[str]] = None,
        include_depot: bool = True,
        normalize: bool = False,
        normalizer: Optional[Dict[str, Any]] = None,
    ) -> None:
        ...

    def build_from_logical_graph(
        self,
        logical_graph: Any,
        tasks: Any,
        depot: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> torch_geometric.data.Data:
        ...

    def build_from_json(
        self,
        json_path: Union[str, Path],
    ) -> torch_geometric.data.Data:
        ...
```

V1 priority:

1. Support current in-memory objects first (`FutureData` / logical graph object),
   because online BPC integration will pass graph and task state from memory.
2. Support `build_from_json` second for offline dataset generation.

The builder should search and reuse the repository's existing Moon Trek logical
graph loaders and field names. If field names cannot be determined exactly, it
should use compatible parsing helpers for common names and raise clear
`ValueError`s when required fields are missing.

## Hierarchical Option-GAT

The V1 model class is named:

```python
HierarchicalOptionGAT
```

This name is the project-wide replacement for the older working name
`DualPredictorGAT`. It directly names the methodological contribution: a
hierarchical path-option attention model for task-cover dual anchors.

The model has three stages:

1. Option-level attention over all physical path options belonging to the same
   directed pair edge `(i, j)`.
2. Physical extremum pooling over option features to preserve high-risk,
   high-energy, or long-time outliers that attention averaging might hide.
3. Directed neighbor-level `GATv2Conv` message passing over logical pair edges,
   using the learned pair edge embedding as `edge_attr`.

### `OptionEncoder`

Recommended class:

```python
class OptionEncoder(nn.Module):
    def __init__(
        self,
        node_hidden_dim: int,
        option_dim: int,
        option_hidden_dim: int,
        pair_edge_dim: int,
        phys_feature_indices: Optional[List[int]] = None,
        dropout: float = 0.0,
    ) -> None:
        ...

    def forward(
        self,
        node_h: torch.Tensor,
        pair_edge_index: torch.Tensor,
        option_feat: torch.Tensor,
        option_pair_id: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        ...
```

Return values:

```text
pair_edge_attr: [num_pairs, pair_edge_dim]
aux:
  option_attention: [num_options]
  option_entropy: scalar or [num_pairs]
  max_pool, min_pool, std_pool: optional debug tensors
```

The option context must preserve direction:

```text
ctx = concat(h_src_opt, h_dst_opt, h_dst_opt - h_src_opt, option_feat)
```

where:

```text
h_src = node_h[pair_edge_index[0]]
h_dst = node_h[pair_edge_index[1]]
h_src_opt = h_src[option_pair_id]
h_dst_opt = h_dst[option_pair_id]
```

Do not use symmetric expressions such as `h_src + h_dst` as the only pair
context. The embeddings for `i -> j` and `j -> i` must be able to differ.

### Flattened Option Attention

V1 strongly depends on `torch_scatter`. Do not implement a padded fallback.

The option set must stay flattened:

```text
option_feat: [num_options, option_dim]
option_pair_id: [num_options]
```

Grouped softmax, max, mean, and related reductions should use scatter
operations. Padding-based option tensors are forbidden because they waste memory
and make softmax masking easy to get wrong.

If `torch_scatter` is unavailable, imports should fail with a clear dependency
message and the implementation should stop until the environment is fixed.

Each directed pair must have at least one option. Empty groups are invalid.

### Physical Extremum Pooling

`pair_edge_attr` must include at least:

- attention pool: `sum_k beta_ijk * option_message_ijk`;
- max pool over selected physical option features;
- min pool over selected physical option features;
- std pool over selected physical option features;
- option count feature.

Physical pooling must cover at least:

```text
distance, travel_time, energy, risk, generalized_cost
```

For pairs with a single option, `std_pool` is `0`. Use biased variance/std
(`unbiased=False`) and apply `torch.nan_to_num(..., nan=0.0)` defensively so
single-option groups cannot produce NaNs.

Padding options must never participate in attention, max/min, std, or count
statistics. V1 avoids this by forbidding padding entirely.

### `HierarchicalOptionGAT`

Recommended class:

```python
class HierarchicalOptionGAT(nn.Module):
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
        ...

    def forward(self, data: Any) -> Dict[str, torch.Tensor]:
        ...
```

Forward output:

```python
{
    "pred_all_nodes": Tensor[num_nodes],
    "pred_task": Tensor[num_tasks],
    "option_attention": Tensor[num_options],
    "pair_edge_attr": Tensor[num_pairs, pair_edge_dim],
}
```

GNN requirements:

- use `torch_geometric.nn.GATv2Conv`;
- pass `edge_dim=pair_edge_dim`;
- set `add_self_loops=False`;
- default `num_gnn_layers=2`;
- forbid default depth above `3`;
- use residual connections to reduce oversmoothing risk;
- use `LayerNorm` and `Dropout` by default;
- final output layer is raw scalar regression, with no `ReLU` or `Softplus`.

Forward outline:

```text
h0 = node_proj(data.x)
pair_edge_attr, aux = option_encoder(
    h0,
    data.pair_edge_index,
    data.option_feat,
    data.option_pair_id,
)
h = h0
for each GATv2 layer:
    msg = gat(h, data.pair_edge_index, pair_edge_attr)
    h = norm(h + dropout(msg))
pred_all = out_mlp(concat(h, h0)).squeeze(-1)
pred_task = pred_all[data.task_mask]
```

### Loss Helper

Recommended helper:

```python
def dual_prediction_loss(
    pred_task: torch.Tensor,
    y_task: torch.Tensor,
    loss_type: str = "huber",
    huber_delta: float = 0.5,
) -> torch.Tensor:
    ...
```

The default loss is Huber loss, with MSE support. Loss is computed only on task
nodes. Since labels may be normalized, `huber_delta` must be configurable;
reasonable defaults are `0.1` or `0.5` in standardized dual scale.

## Checkpoint Format

Use a flat top-level checkpoint dictionary:

```python
checkpoint = {
    "model_state_dict": model.state_dict(),
    "model_config": {
        "node_dim": 9,
        "option_dim": 10,
        "hidden_dim": 128,
        "option_hidden_dim": 128,
        "pair_edge_dim": 128,
        "num_gnn_layers": 2,
        "heads": 4,
        "dropout": 0.1,
        "use_layer_norm": True,
    },
    "node_feature_mean": [...],
    "node_feature_std": [...],
    "option_feature_mean": [...],
    "option_feature_std": [...],
    "label_mean": ...,
    "label_std": ...,
    "feature_schema": {
        "node": [...],
        "option": [...],
    },
    "version": "v1",
}
```

Loading rules:

- initialize `HierarchicalOptionGAT` from `model_config`;
- call `load_state_dict` with `model_state_dict`;
- normalize `data.x` and `data.option_feat` using checkpoint statistics before
  inference;
- denormalize predictions using `label_mean` and `label_std` when present;
- raise clear errors if required checkpoint fields are missing;
- raise clear errors if schema, normalizer dimensions, or data tensor
  dimensions do not match.

Do not silently ignore normalizer mismatch.

## Wentges Smoothing Policy

Let `pi_anchor` be the GNN-predicted task-cover dual center and `pi_rmp` be the
current true RMP task-cover dual. The pricing task-cover dual is:

```text
pi_smoothed = alpha * pi_anchor + (1 - alpha) * pi_rmp
```

Only task-cover duals are smoothed. All other dual components remain true RMP
values.

At iteration 0, the initial RMP dual can be dominated by artificial columns or
be effectively zero. In that case the large initial `alpha` intentionally makes
pricing rely mostly on the learned anchor.

Alpha policy:

- initial `alpha = 0.8`;
- early decay subtracts `0.05` per iteration;
- cruise lower bound is `0.2`;
- if no stagnation is detected, keep `alpha >= 0.2`;
- if three consecutive RMP relative improvements are below `1e-3`, set
  `alpha = 0.0` immediately.

Relative improvement:

```text
(last_obj - current_obj) / max(abs(last_obj), eps)
```

Once alpha is forced to zero, the solver has entered the proof tail and should
use only true RMP duals.

## Dual Stabilizer

Recommended config:

```python
@dataclass
class DualStabilizerConfig:
    checkpoint_path: str
    device: str = "cpu"
    alpha_init: float = 0.8
    alpha_min_active: float = 0.2
    alpha_decay: float = 0.05
    stagnation_patience: int = 3
    stagnation_rel_improve: float = 1e-3
    disable_on_branch_depth_gt: int = 0
    filter_true_rc: bool = False
    rc_filter_tol: float = 1e-8
    debug_checks: bool = False
```

Recommended API:

```python
class DualStabilizer:
    def __init__(self, config: DualStabilizerConfig) -> None:
        ...

    def predict_anchor(self, data: Any) -> Dict[int, float]:
        ...

    def smooth_task_duals(
        self,
        true_task_duals: Dict[int, float],
        predicted_anchor: Dict[int, float],
        alpha: Optional[float] = None,
    ) -> Dict[int, float]:
        ...

    def update_alpha(
        self,
        rmp_obj_history: Sequence[float],
        pricing_stats: Optional[Dict[str, Any]] = None,
        branch_depth: int = 0,
    ) -> float:
        ...

    def should_disable(
        self,
        branch_depth: int,
        certificate_mode: bool = False,
    ) -> bool:
        ...
```

Rules:

- `predict_anchor` returns `Dict[int, float]` where keys come from
  `data.task_ids`.
- `smooth_task_duals` returns only smoothed task-cover duals.
- branch depth greater than `disable_on_branch_depth_gt` disables learning
  smoothing. With the V1 default of `0`, learning is enabled only at the root.
- certificate mode always disables smoothing.
- alpha decays from `alpha_init` to `alpha_min_active` and then cruises.
- if stagnation is detected, alpha is forced to `0.0`.
- if true-dual verification failure rate is high, alpha may also be forced to
  `0.0`.

## Candidate Column Filtering

Columns found under smoothed duals are feasible columns, so adding them cannot
break exactness. For performance, candidates should still be filtered by true
RMP reduced cost before insertion:

```text
true_rc < -1e-5
```

This prevents positive true-RC columns from bloating the RMP basis. Rejected
columns should be logged for diagnostics, but not treated as correctness
failures.

## Integration Order

The intended column-generation loop order is:

```python
graph_data = build_pyg_graph(data)
pi_anchor = stabilizer.predict_anchor(graph_data)

while not done:
    rmp_solution = solve_journey_rmp(...)
    pi_rmp = rmp_solution.duals.cover

    pricing_task_duals = stabilizer.smooth_task_duals(
        true_task_duals=pi_rmp,
        predicted_anchor=pi_anchor,
    )
    alpha = stabilizer.update_alpha(
        rmp_obj_history=rmp_objectives,
        pricing_stats=pricing_stats,
        branch_depth=branch_depth,
    )

    pricing_result = price_journeys(
        ...,
        task_duals=pricing_task_duals,
        other_duals=rmp_solution.duals,
    )

    filtered_journeys = filter_by_true_reduced_cost(
        pricing_result.journeys,
        true_duals=rmp_solution.duals,
    )

    if not filtered_journeys:
        stabilizer.force_exact_mode()
        true_pricing_result = price_journeys(
            ...,
            task_duals=pi_rmp,
            other_duals=rmp_solution.duals,
        )
        if true_pricing_result.exhausted and not true_pricing_result.journeys:
            certify_node_lp()
```

This sequence preserves the exact-safe closure: the GNN can guide candidate
generation, but true-dual pricing is the only certificate path.

## Numerical Checks

The implementation should support debug checks for:

- NaN / Inf in input features;
- NaN / Inf in attention scores;
- NaN / Inf in model predictions;
- option attention summing to approximately `1` per directed pair;
- every pair having at least one option;
- `pred_task` length matching `task_ids` length;
- depot participating in message passing but not in loss or stabilizer output;
- final output remaining free to be negative.

Log fields should include:

- `alpha`;
- dual source;
- anchor norm;
- smoothed-vs-true dual distance;
- true-RC rejected candidate count;
- true-dual fallback trigger;
- option attention entropy.

## Toy Graph V1 Tests

V1 is toy-graph driven. Do not connect real benchmarks until the toy tests are
green.

Toy graph:

- 1 depot + 3 tasks;
- directed complete graph;
- each directed pair has 1-3 path options;
- `i -> j` and `j -> i` have different time/energy/risk values;
- at least one pair has a high-risk option to test max pooling;
- at least one pair has exactly one option to test `std_pool = 0`.

Test groups:

1. `graph_builder`
   - `data.x` shape is correct;
   - `data.pair_edge_index` shape is `[2, num_pairs]`;
   - `data.option_feat` shape is `[num_options, option_dim]`;
   - `data.option_pair_id` shape is `[num_options]`;
   - depot has `task_mask=False` and tasks have `task_mask=True`;
   - every pair has at least one option;
   - both `i -> j` and `j -> i` exist and can have different features.

2. `OptionEncoder`
   - option attention sums to `1` within each pair group;
   - pair edge embedding shape is correct;
   - max pooling preserves the high-risk option value;
   - single-option groups produce finite zero std values.

3. `HierarchicalOptionGAT`
   - forward pass does not fail;
   - `pred_task` shape equals number of tasks;
   - `pred_all_nodes` shape equals number of nodes;
   - output is not forced nonnegative by activation;
   - `loss.backward()` works on toy labels.

4. `DualStabilizer`
   - loads a fake checkpoint;
   - `predict_anchor` returns `Dict[int, float]`;
   - `smooth_task_duals` matches the Wentges formula;
   - `branch_depth > 0` disables smoothing by default;
   - alpha decay and stagnation logic follow config.

## Do Not Do

- Do not modify `BPC_future/master` or `BPC_future/pricing` exact proof logic
  while building the learning component.
- Do not predict time-bucket duals, SRC duals, branch-row duals, or fleet duals.
- Do not collapse multiple path options into a single edge feature before the
  model.
- Do not take only the cheapest path option.
- Do not make the graph undirected.
- Do not use symmetric-only source/target encodings.
- Do not implement padding-based option attention.
- Do not let padding or fake options participate in softmax or pooling.
- Do not use `ReLU` or `Softplus` on the final dual output.
- Do not let smoothed duals trigger `OPTIMAL` or node completion.
- Do not record a smoothed-dual value as an official mathematical bound.

## Open Implementation Checks

- Search the current `BPC_future` loaders before implementing graph parsing.
- Keep feature construction deterministic across training and inference.
- Make dependency failures for `torch_geometric` and `torch_scatter` explicit
  and actionable.
- Add tests proving that GNN-enabled and GNN-disabled runs return identical
  certified objectives on small instances after integration.
- Add tests proving that a smoothed-dual no-negative result cannot certify a
  node without true-dual exact pricing.

## Current Smoke Implementation Snapshot (2026-06-03)

Environment:

- CUDA stack is installed in the active Python environment:
  `torch==2.12.0+cu130`, `torch_geometric==2.7.0`,
  `torch_scatter==2.1.2+pt212cu130`.
- `torch.cuda.is_available()` is true on the RTX 3080 Ti.

Training data:

- Dataset directory:
  `BPC_future/data/learning_dual/v1_trace_5_10_selected`.
- Data source:
  all 20 optimal 5-task trace runs plus 11 selected optimal 10-task trace
  runs.
- Dataset size is small smoke-scale only: 31 samples, about 0.84 MB on disk.
- Labels are tail averages of true RMP task-cover duals from
  `journey_learning_dual_trace` events.
- This dataset is only an end-to-end plumbing dataset, not a final production
  training corpus.

Checkpoint:

- Smoke checkpoint:
  `BPC_future/data/learning_dual/v1_trace_5_10_selected/hierarchical_option_gat_smoke.pt`.
- It was trained for 20 epochs with a smaller 64-dimensional
  `HierarchicalOptionGAT`.
- It proves that graph construction, normalization, CUDA training, checkpoint
  save/load, anchor prediction, smoothing, and true-RC filtering work together.
- It must not be treated as the final speed model.

Solver integration:

- `journey_learning_enabled=True` creates a `DualStabilizer` runtime at each
  journey branch node.
- Learning smoothing is used only for heuristic pricing. Exact pricing and
  certificates still use the true SCIP/RMP dual path.
- Smoothed pricing candidates are filtered with the original true RMP duals
  before insertion into the RMP.
- The loaded stabilizer is cached by checkpoint path, device, and smoothing
  configuration. The cached model weights are reused across instances, while
  alpha, forced-exact state, and the last anchor are reset for every solve.

Smoke results:

- GNN-enabled full 5-task smoke:
  `BPC_future/results/learning_smoke_tasks05_all.csv`.
- Result: 20/20 `OPTIMAL`, maximum solving time 2.994976 seconds.
- Certified objective comparison against
  `BPC_future/results/all_tasks05_current_fulltest.csv` had 0 mismatches.
- Cache behavior in the full 5-task smoke: 1 cold load, 19 cache hits.
- True-RC filter totals in that smoke: 76 smoothed candidates, 37 kept as true
  negative, 39 rejected.

Observed limitation:

- On `apollo15_20km_tasks10_01_seed11000`, the smoke checkpoint preserved the
  exact objective but did not add useful true-RC negative columns. It mainly
  demonstrated safety and integration, not speedup.
- Next learning work should improve label volume/quality and evaluate whether
  GNN columns reduce RMP iterations or find incumbents earlier before enabling
  this by default in benchmark configs.

## V2 Trace/Guard Update (2026-06-03)

Additional data:

- Dataset directory:
  `BPC_future/data/learning_dual/v1_trace_5_10_optimal_all`.
- Data source:
  all 20 optimal 5-task trace runs plus all 15 strict-`OPTIMAL` 10-task trace
  runs from the current 10-task benchmark pass.
- Dataset size: 35 samples, about 1.8 MB including checkpoint/metrics files.
- Do not include unfinished `TIME_LIMIT` traces as labels, even if they contain
  a good incumbent, unless a later run proves a true-dual certificate.

Checkpoint:

- V2 checkpoint:
  `BPC_future/data/learning_dual/v1_trace_5_10_optimal_all/hierarchical_option_gat_v2.pt`.
- Training metrics:
  `BPC_future/data/learning_dual/v1_trace_5_10_optimal_all/hierarchical_option_gat_v2_metrics.json`.
- Offline metrics on the random validation split:
  `mae = 10.777438`, `rmse = 14.035151`, baseline mean `mae = 17.735065`.

True-RC concentration:

- Smoothed-pricing candidates are now sorted by true reduced cost before being
  inserted into the RMP.
- `journey_learning_true_rc_max_kept_per_round` optionally caps the number of
  true-negative GNN candidates kept per round. The conservative online default
  is `4`. A value of `0` means unlimited and should be used only in controlled
  experiments, because too many safe columns can still perturb the simplex and
  branch path.
- `journey_learning_pricing_max_rounds` controls how many root CG rounds may use
  smoothed-dual heuristic pricing. The conservative online default is `1`.
  A value of `0` means unlimited.
- Filter logs distinguish:
  `true_negative_journeys` before the cap, `kept_journeys` after the cap, and
  `cap_dropped_journeys`.

Certificate guard:

- `journey_learning_disable_on_certificate_candidate` defaults to `True`.
- When the current node is already a certificate candidate, learning heuristic
  pricing is skipped and the `DualStabilizer` is not loaded lazily. This avoids
  paying CUDA checkpoint load time or perturbing the proof path.
- Set `journey_learning_disable_on_certificate_candidate=False` only for
  controlled experiments that explicitly study learning columns in the proof
  face.

Empirical notes:

- Forced V2 learning on all 5-task instances preserved exact objectives:
  20/20 `OPTIMAL`, max time `2.758444`, 0 objective mismatches versus
  `BPC_future/results/all_tasks05_current_fulltest.csv`.
- Forced V2 learning on all 5-task instances produced 105 smoothed candidates,
  with 53 true-RC negative kept before any cap and 52 rejected.
- Forced V2 learning harmed
  `tranquillitatis_balmer_like_20km_tasks10_06_seed11090`: the baseline proved
  `OPTIMAL` in about `51.6s`, while forced learning timed out around `60s`.
- With the certificate guard enabled, the same 10-task instance returned to
  `OPTIMAL` in `51.116912s` without loading learning, matching the intended
  exact-safe behavior.

## V2 Conservative Online Gate (2026-06-03)

Full 5/10-task reruns after CUDA setup showed that unbounded V2 learning is
exact-safe but not performance-safe:

- Default exact rerun:
  - 5-task: 20/20 `OPTIMAL`, mean `0.311037s`, max `1.425483s`.
  - 10-task: 15/20 strict `OPTIMAL`, 16/20 closed if counting `gap=0`
    time-limit cases, mean `28.835830s`, max `61.658013s`.
- GNN V2 with certificate guard but unlimited true-RC insertion:
  - 5-task: 20/20 `OPTIMAL`, mean `0.311795s`, max `1.420921s`.
  - 10-task: 14/20 strict `OPTIMAL`, 15/20 closed, mean `29.935421s`.
  - Regression: `apollo15_20km_tasks10_09` changed from default
    `OPTIMAL 19.525203s` to `TIME_LIMIT 22.982798s`, with the same primal
    incumbent but weaker dual bound.

The regression came from excessive safe-column insertion, not from violating
the exactness boundary.  On `apollo15_20km_tasks10_09`, unbounded learning kept
70 true-negative GNN journeys over five rounds, including 47 in the first round.
The conservative cap `journey_learning_true_rc_max_kept_per_round=4` and
`journey_learning_pricing_max_rounds=1` restored and improved that case:

```text
apollo15_20km_tasks10_09:
  default exact:       OPTIMAL, 19.525203s, 7 nodes
  unlimited GNN:       TIME_LIMIT, 22.982798s, 7 nodes, gap 0.027172
  cap4/round1 GNN:     OPTIMAL, 15.005025s, 5 nodes
```

Mixed 10-task sample with cap4/round1:

```text
apollo10_04: TIME_LIMIT, unchanged hard branch case
apollo10_07: OPTIMAL, 25.906958s, slower than default but better than unbounded GNN
apollo10_09: OPTIMAL, 15.005025s, faster than default
tranq10_01:  TIME_LIMIT, unchanged root certificate hard case
tranq10_06:  OPTIMAL, 52.119221s, approximately unchanged
tranq10_08:  OPTIMAL, 20.741430s, mild slowdown
```

Therefore V2 online defaults are intentionally conservative:

```text
journey_learning_pricing_max_rounds = 1
journey_learning_true_rc_max_kept_per_round = 4
journey_learning_disable_on_certificate_candidate = True
journey_learning_disable_on_branch_depth_gt = 0
```

This keeps learning as an early root-node heuristic column generator.  The
remaining 10-task failures are still true-dual exact-pricing certificate
bottlenecks and should be attacked by NG-route+DSSR and completion-bound work,
not by pushing more learning columns into the RMP.

Implementation note from the 2026-06-04 gate audit:

- `journey_learning_pricing_max_rounds` must gate the smoothing call itself, not
  only the decision to run a heuristic pricing round.  If base heuristic pricing
  is enabled, passing the cached learning runtime after the round limit silently
  keeps using smoothed duals in later CG iterations.
- The solver now routes learning through an active-runtime gate before calling
  smoothing, so `journey_learning_pricing_max_rounds=1` means exactly one
  learning-smoothed pricing round even when normal heuristic pricing remains
  enabled.
- Forced 5-task smoke after the fix:
  `BPC_future/results/learning_smoke_forced_gatefix_5_20260604.csv`.
  It preserved the exact objective and logged learning-smoothed pricing only at
  `cg_iter=1`.
- 10-task representative smoke after the fix:
  `BPC_future/results/learning_gatefix_apollo10_09_20260604.csv`.
  `apollo15_20km_tasks10_09` solved `OPTIMAL` with objective `289.437655`,
  time `16.153808s`, `5` nodes, and `184` columns.  The first learning round
  produced `53` smoothed candidates, `47` true-RC negative candidates, and the
  cap kept the best `4`.

## Certificate-Face Learning Probe (2026-06-04)

`tranquillitatis_balmer_like_20km_tasks10_04` is a root certificate hard case:
the RMP objective equals the incumbent from the first CG round, but true-dual
pricing continues finding negative columns and the node cannot prove
optimality within 60 seconds.

Controlled probes allowed learning on this certificate face:

```text
journey_learning_enabled = True
journey_learning_checkpoint_path =
  BPC_future/data/learning_dual/v1_trace_5_10_optimal_all/hierarchical_option_gat_v2.pt
journey_learning_device = cuda
journey_learning_disable_on_certificate_candidate = False
journey_learning_pricing_max_rounds = 3
```

Results:

```text
max true-RC kept per round = 8:
  BPC_future/results/probe_t04_learning_cert_allowed_20260604.csv
  TIME_LIMIT, time = 61.171365s, columns = 351

max true-RC kept per round = 16:
  BPC_future/results/probe_t04_learning_cert_keep16_20260604.csv
  TIME_LIMIT, time = 61.179842s, columns = 382
```

True-RC filter quality for the `max_kept=8` run:

```text
cg1: 64 GNN candidates, 17 true-negative, 8 kept, best true RC = -43.579086
cg2: 64 GNN candidates,  8 true-negative, 8 kept, best true RC = -20.908194
cg3:  0 GNN candidates
```

Interpretation:

- The GNN checkpoint is not useless; it can produce true-negative columns even
  on a certificate-face hard case.
- Those columns did not reduce the proof tail.  They changed the column path
  and reduced/increased final column counts depending on the cap, but neither
  setting produced an official true-dual certificate under the 60-second limit.
- Keep `journey_learning_disable_on_certificate_candidate=True` as the default.
  Re-enable certificate-face learning only for controlled data-collection
  experiments, not for production benchmark configs.

## Expanded Bootstrap Checkpoint And Budgeted Probe (2026-06-04)

A small but real dual-center dataset was regenerated from trace logs, keeping
only runs with `finish.status = OPTIMAL`:

```text
BPC_future/data/learning_dual/expanded_20260604
  samples = 38
  task counts = {5, 10}
  sample bytes = 593362
  directory size ~= 700 KB
```

The expanded set combines:

- all 20 closed 5-task instances;
- 18 closed 10-task instances;
- excludes the two current 10-task failures
  `apollo15_20km_tasks10_04_seed11055` and
  `tranquillitatis_balmer_like_20km_tasks10_04_seed11054`.

Training output:

```text
BPC_future/data/learning_dual/expanded_20260604/hierarchical_option_gat_expanded.pt
validation MAE          = 12.680718
validation baseline MAE = 18.527985
```

This is a better checkpoint than the first bootstrap model, but it is still a
small-data model.  It should be treated as an online plumbing and data-quality
checkpoint, not as a final generalization model.

Certificate-face forced probe:

```text
BPC_future/results/learning_expanded_forced_probe10_20260604.csv
journey_learning_disable_on_certificate_candidate = False
journey_learning_pricing_max_rounds = 2
journey_learning_true_rc_max_kept_per_round = 16
alpha ~= 0.75 then 0.70
```

Results:

```text
apollo10_01: OPTIMAL, 264.024007, time = 3.758322s
tranq10_09:  TIME_LIMIT, primal = 203.263873, no certificate
apollo10_04: TIME_LIMIT, primal = 288.332462, dual = 268.585633
tranq10_04:  TIME_LIMIT, primal = 207.893439, no certificate
```

The model found true-negative columns, but default-enabling this is not
performance-safe:

```text
tranq10_09 cg1: 17 candidates,  6 true-negative,  6 kept
tranq10_09 cg2: 64 candidates, 21 true-negative, 16 kept
tranq10_04 cg1: 57 candidates, 18 true-negative, 16 kept
tranq10_04 cg2: 64 candidates, 20 true-negative, 16 kept
```

Low-alpha and budgeted probes were also tested:

```text
BPC_future/results/learning_expanded_lowalpha_probe10_20260604.csv
  alpha ~= 0.20, one learning round, keep <= 4:
  tranq10_09 TIME_LIMIT, primal = 203.102839
  tranq10_04 TIME_LIMIT, primal = 207.893439

BPC_future/results/learning_expanded_budgeted_probe10_20260604.csv
  alpha ~= 0.20, one learning round, keep <= 4,
  journey_learning_pricing_time_limit = 0.8:
  tranq10_09 TIME_LIMIT, primal = 203.711779
  tranq10_04 TIME_LIMIT, primal = 207.893439
```

The budgeted helper worked technically: learning pricing used a separate
`0.8s` limit and returned in about `0.18s`, keeping `3-4` true-negative
journeys.  Even this small perturbation still damaged the `tranq10_09`
certificate path.

Current policy:

- keep `journey_learning_disable_on_certificate_candidate=True` by default;
- keep certificate-face learning as an explicit experiment-only mode;
- use learning traces to improve anchor quality, but do not expect learning
  columns alone to solve the true-dual proof tail;
- move the next performance effort back to exact pricing, especially
  NG-route/DSSR and certificate-tail profile generation.

Implementation note:

- `journey_learning_pricing_time_limit` and related
  `journey_learning_*` streaming knobs now provide a separate opt-in budget for
  learning-smoothed pricing.  These knobs are exact-safe because learning
  candidates are still filtered by true reduced cost and official completion
  still requires true-dual exact pricing.

## Hard-Tail Trace Augmentation (2026-06-04)

The remaining root hard case `tranquillitatis_balmer_like_20km_tasks10_04` was
rerun with learning dual tracing enabled and a 90-second limit:

```text
BPC_future/results/learning_trace_hard_tranq10_04_90_20260604.csv
  status = OPTIMAL
  primal = dual = 207.893439
  solving_time = 65.650663s
  journey_learning_dual_trace events = 7
```

This trace was added to a new hard-tail dataset:

```text
BPC_future/data/learning_dual/hardtail_20260604
  samples = 39
  task counts = {5: 20, 10: 19}
  total sample bytes = 616037
  directory size ~= 1.1 MB after checkpoint training
  includes tranquillitatis_balmer_like_20km_tasks10_04_seed11054
```

Training output:

```text
BPC_future/data/learning_dual/hardtail_20260604/hierarchical_option_gat_hardtail.pt
train MAE      = 7.483345
validation MAE = 18.625275
validation baseline mean MAE = 25.311796
```

Controlled certificate-face probes used this checkpoint with true-RC filtering:

```text
BPC_future/results/learning_hardtail_cert_t04_20260604.csv
  journey_learning_pricing_time_limit = 1.5
  TIME_LIMIT, primal = 207.893439, no certificate dual
  learning candidates kept:
    cg1: 0 true-negative
    cg2: 0 true-negative
  max RSS about 1.5 GB due CUDA model load

BPC_future/results/learning_hardtail_cert_t04_nobudget_20260604.csv
  no learning-specific pricing time limit
  TIME_LIMIT, primal = 207.893439, no certificate dual
  learning true-RC filter:
    cg1: 40 candidates, 17 true-negative, 16 kept
    cg2: 33 candidates, 12 true-negative, 12 kept
  max RSS about 1.5 GB due CUDA model load
```

Interpretation:

- Adding the hard-tail trace improves the data coverage and confirms that the
  GNN can produce true-negative columns for `tranq10_04`.
- The extra learning columns still did not shorten the true-dual certificate
  tail, and a tight learning budget can miss candidates entirely.
- Keep certificate-face learning disabled by default.
- The next `tranq10_04` work should target exact pricing itself, especially
  NG-route/DSSR certificate behavior or a stronger profile-generation/tail
  completion mechanism.

## Solve-Level Trace Grouping And Instance Holdout (2026-06-04)

The dataset builder previously grouped all `journey_learning_dual_trace` events
by `instance_path`.  That is unsafe once the same instance is traced in multiple
solver runs: the tail-average label can accidentally mix duals from different
solve trajectories.

Implementation change:

```text
BPC_future/scripts/build_learning_dual_dataset.py
  _collect_traces now returns one group per log file and instance path.
  Manifest samples include log_path.
  Graph samples store learning_log_path.
```

This means repeated runs of the same instance become separate solve-level
samples instead of one merged pseudo-sample.

The training script now defaults to instance-level validation splitting:

```text
BPC_future/scripts/train_learning_dual_model.py
  --split-by-instance / --no-split-by-instance
```

With `--split-by-instance` enabled, all samples sharing the same
`learning_instance_path` stay on the same side of the train/validation split.
This avoids optimistic validation metrics when the dataset includes repeated
solve traces for one graph.

Unit coverage:

```text
test_collect_traces_keeps_repeated_instance_runs_separate
test_training_split_keeps_same_instance_samples_together
```

Validation:

```text
python -m py_compile \
  BPC_future/scripts/build_learning_dual_dataset.py \
  BPC_future/scripts/train_learning_dual_model.py \
  BPC_future/tests/test_learning_components.py

python -m unittest BPC_future.tests.test_learning_components
```

Grouped smoke dataset:

```text
BPC_future/data/learning_dual/grouped_20260604
  samples = 43
  task counts = {5: 20, 10: 23}
  unique instances = 39
  total sample bytes = 716209
```

The extra four samples are repeated optimal solve traces for instances that
already appeared in earlier datasets; they are now explicit repeated samples
rather than silently merged labels.

Short training smoke with instance holdout:

```text
BPC_future/data/learning_dual/grouped_20260604/
  hierarchical_option_gat_grouped_instance_split_smoke.pt
  train instances = 31
  validation instances = 8
  train samples = 35
  validation samples = 8
  train MAE = 10.651299
  validation MAE = 21.157984
  validation baseline mean MAE = 26.746532
```

The instance-holdout metric is deliberately more conservative than the random
sample split smoke (`validation MAE = 14.988445`).  The higher holdout error is
a useful signal: anchor quality is still the bottleneck for learning, and future
metrics should prefer instance-level splits when repeated solve traces exist.

Controlled 10-task probe with the grouped smoke checkpoint:

```text
BPC_future/results/learning_grouped_smoke_probe10_20260604.csv
  settings:
    journey_learning_enabled = True
    journey_learning_pricing_max_rounds = 1
    journey_learning_true_rc_max_kept_per_round = 4
    journey_learning_disable_on_certificate_candidate = True
    journey_learning_pricing_time_limit = 0.8

  apollo10_09:
    OPTIMAL, time = 19.867686s, columns = 196
    learning produced 0 candidates in cg1

  tranq10_09:
    OPTIMAL, time = 53.951040s, columns = 435
    learning was disabled by the certificate-candidate gate

  tranq10_04:
    TIME_LIMIT, primal = 207.893439, no certificate dual, columns = 446
    learning was disabled by the certificate-candidate gate
```

Interpretation:

- The grouped smoke checkpoint is useful for validating the data pipeline, not
  for default performance.
- Conservative learning remains exact-safe, but the current checkpoint does not
  improve the 10-task certificate tail.
- Do not enable this checkpoint by default.
- Next learning work should collect broader solve-level traces and optimize for
  true-RC negative-column concentration, while the main speed work should
  continue on exact pricing and NG-route/DSSR.

## Alpha And Integration Smoke Update (2026-06-04)

Implementation correction:

- `DualStabilizer.update_alpha()` now keeps the initial alpha unchanged until
  at least two RMP objective values are available.
- This prevents the first learning-smoothed pricing pass from using
  `alpha = 0.75` when the configured `alpha_init` is `0.8`.
- After the first comparable objective transition, the slow decay policy still
  applies normally.

Driver integration correction:

- `journey_learning_filter_true_rc` is now represented in the learning runtime.
- Default remains `True`: smoothed-pricing candidates are filtered by true RMP
  reduced cost before being added to the RMP.
- The override `journey_learning_filter_true_rc: False` is now reflected by the
  driver instead of being ignored.  This is not recommended for default
  experiments because positive true-RC columns can bloat the RMP basis.

Validation:

```text
python -m py_compile \
  BPC_future/learning/dual_stabilizer.py \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_learning_components.py \
  BPC_future/tests/test_bpc_future.py

python -m unittest \
  BPC_future.tests.test_learning_components \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_learning_defaults_are_conservative_but_overridable \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_learning_runtime_for_pricing_honors_round_gate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_learning_pricing_config_has_separate_budget_overrides
```

Result: 11 tests passed.

End-to-end CUDA smoke with grouped checkpoint:

```text
BPC_future/results/learning_integration_smoke_tasks05_alphafix_20260604.csv
  instance = apollo15_20km_tasks05_02_seed6018
  status = OPTIMAL
  objective = 155.666693
  time = 1.693644s
  first smoothing alpha = 0.8
  true-RC filter event present

BPC_future/results/learning_integration_smoke_apollo10_01_alphafix_20260604.csv
  instance = apollo15_20km_tasks10_01_seed11000
  status = OPTIMAL
  objective = 264.024007
  time = 3.182830s
  first smoothing alpha = 0.8
  true-RC filter event present
```

Interpretation:

- The CUDA learning path initializes, predicts anchors, applies smoothing, and
  falls back to exact true-dual pricing without changing final exact objectives.
- In these two smoke runs, the current grouped checkpoint did not add useful
  true-RC negative columns, so it remains a validation checkpoint rather than a
  performance default.

## Mainline Level-1 Anchor Activation (2026-06-04)

The Apollo20 dual diagnostics in
`exact_pricing_completion_bounds_design.md` confirmed that column generation has
a real dual-oscillation component:

```text
baseline 20-task representative:
  adjacent dual hash changes = 26 / 26
  adjacent support hash changes = 23 / 26
  dual_l1_delta mean/median/max = 101.15 / 95.86 / 220.13
  rounds with |objective_delta| < 1 and dual_l1_delta > 50 = 9
```

This is enough evidence to promote learning from pure smoke plumbing into the
mainline Level-1 column-search funnel, with strict exactness guards.  The GNN
anchor's responsibility is narrow:

- predict only task-cover dual anchors `pi_i`;
- smooth only task-cover duals for early heuristic/profile pricing;
- keep fleet, SRC, branch, and other non-task duals at true RMP values;
- filter every smoothed-dual candidate by true RMP reduced cost before insertion;
- allow certificate-candidate heuristic pricing, because dual oscillation often
  appears on the certificate face;
- disable below branch depth `> 0` by default;
- never certify a node and never contribute to an official bound.

Mainline trial configs now enable the hard-tail checkpoint as a conservative
root-only Level-1 prior:

```text
BPC_future/configs/moon_trek_5_journey_branch_trial.yaml
BPC_future/configs/moon_trek_10_journey_branch_trial.yaml
BPC_future/configs/apollo20_physical_branch_upperfilter_fleetslack_partialbound_trial.yaml

journey_learning_enabled = True
journey_learning_checkpoint_path =
  BPC_future/data/learning_dual/hardtail_20260604/hierarchical_option_gat_hardtail.pt
journey_learning_device = cpu
journey_learning_disable_on_certificate_candidate = False
journey_learning_disable_on_branch_depth_gt = 0
journey_learning_pricing_max_rounds = 1
journey_learning_filter_true_rc = True
```

`journey_learning_pricing_max_rounds` counts actual learning-smoothed pricing
attempts, not raw CG iterations.  This matters because early CG iterations can
be consumed by cut separation before any pricing call is made; 20-task root runs
often initialize the anchor at `cg_iter = 2`.

The default device is `cpu` even though the local environment has CUDA support.
The model is small and inference is not the bottleneck; avoiding the CUDA
context keeps memory lower for long 20-task branch-price runs.  CUDA remains an
explicit override for training or batch inference.

20-task caveat: there is still no 20-task dual-center training set.  The
hard-tail checkpoint is trained on 5/10-task traces and is exact-safe on 20 only
because true-RC filtering and true-dual certificate fallback are mandatory.  Do
not interpret a 20-task smoothed-dual no-column result as evidence of
optimality.

Exactness guard: when learning is active, the exact-pricing path uses
`scip_learning_certificate`, and the generic certificate guard also forces
`scip_certificate` on certificate candidates and completion-bound probes.  This
allows the GNN anchor to search for columns on a certificate face without
polluting the official proof.

Validation added:

```text
BPCFutureTests.test_mainline_learning_anchor_configs_are_exact_safe
```

This test asserts that the enabled mainline configs keep true-RC filtering on,
allow certificate-face heuristic pricing only under true-RC filtering, keep the
default root-only branch depth gate, and point at an existing checkpoint.

Mainline smoke validation:

```text
BPC_future/results/learning_mainline_certface_tasks05_20260604.csv
  status = OPTIMAL
  primal/dual = 102.041475
  time = 2.773470s
  memory RSS ~= 849 MB
  learning:
    candidates = 1
    true-negative = 1
    kept/added = 1
    best true RC = -53.072744

BPC_future/results/learning_mainline_certface_tasks10_20260604.csv
  status = OPTIMAL
  primal/dual = 264.024007
  time = 3.132734s
  memory RSS ~= 866 MB
  learning:
    candidates = 16
    true-negative = 2
    kept/added = 2
    best true RC = -0.406502
```

The 20-task representative was run for a 120-second component smoke after
fixing the learning-round gate:

```text
BPC_future/results/learning_mainline_smoke_apollo20_gatefix_120s_20260604.csv
  status = TIME_LIMIT
  primal = 487.624693
  nodes = 1
  columns = 600
  memory RSS ~= 999 MB
  learning:
    cg_iter = 2
    candidates = 24
    true-negative = 19
    kept/added = 8
    best true RC = -70.412440
```

Earlier in the same config, when the round gate still counted raw `cg_iter`,
the anchor initialized on 20-task but never smoothed because `cg_iter = 1` was
consumed by cut separation.  That run ended at 120 seconds with
`primal = 492.883420`.  After the gate fix, the smoothed pass is active and the
120-second incumbent improved to `487.624693`.  This is not a certificate result
and does not prove the 20-task target, but it confirms that the GNN anchor can
produce concentrated true-RC negative columns on the 20-task graph.

Memory note: even CPU inference imports the PyTorch/PyG stack and raises process
RSS to about 0.85-1.0 GB in these smoke runs.  Keep learning benchmarks
single-process unless the memory profile is intentionally being tested.

## Strong True-RC Learning Gate (2026-06-04)

The full 10-task learning-on run exposed an important failure mode: the GNN
anchor was active, exact-safe, and true-RC filtered, but the filter threshold was
only the numerical tolerance `1e-5`.  That allowed weak true-negative columns to
enter the RMP.  On several Tranquillitatis instances those columns changed the
column-generation trajectory, bloated the tail proof, and caused regressions or
timeouts.

Diagnosis:

```text
BPC_future/results/all_tasks10_learning_mainline_120s_20260604.csv
  20 rows
  OPTIMAL = 18 / 20
  TIME_LIMIT = 2 / 20
  slow regressions concentrated on Tranquillitatis tasks10_01/04/05/06/09/10
```

The controlled probe kept learning enabled but changed only the online
acceptance policy:

```text
journey_learning_alpha_init = 0.5
journey_learning_true_rc_keep_threshold = 1.0
journey_learning_true_rc_max_kept_per_round = 4
```

Probe result:

```text
BPC_future/results/probe_tasks10_learning_quality_tol1_alpha05_20260604.csv

tranq10_04:
  previous learning mainline = OPTIMAL, 104.682362s, 509 columns
  stricter learning gate     = OPTIMAL,  73.658087s, 448 columns

tranq10_05:
  previous learning mainline = TIME_LIMIT, 120.207442s, 302 columns
  stricter learning gate     = OPTIMAL,    19.595720s, 304 columns

tranq10_06:
  previous learning mainline = TIME_LIMIT, 120.919857s, 412 columns
  stricter learning gate     = OPTIMAL,    47.549628s, 407 columns
```

After exact-safe cache isolation, the `1.0` threshold still allowed
medium-strength learning columns on `tranq10_04` and the full 10-task run hit
the 120-second limit on that instance.  A second probe raised only the learning
candidate quality gate:

```text
journey_learning_true_rc_keep_threshold = 10.0

BPC_future/results/probe_tasks10_learning_threshold10_isolated_20260604.csv

tranq10_04:
  threshold 1 isolated = TIME_LIMIT, 120.620316s, 416 columns
  threshold 10         = OPTIMAL,     70.941678s, 441 columns

tranq10_05:
  threshold 10         = OPTIMAL,     24.121163s, 309 columns

tranq10_06:
  threshold 10         = OPTIMAL,     53.314876s, 350 columns
```

The mainline configs therefore use `journey_learning_true_rc_keep_threshold =
10.0`.  This keeps learning active but restricts online column insertion to
very strong true-RC negatives.  We should revisit this threshold only after
training a better terrain-balanced checkpoint and measuring candidate quality
by instance family.

Interpretation: this does not prove the checkpoint is high quality across the
whole distribution, but it does argue against the simpler hypothesis that "the
GAT is useless."  The model can produce strong true-RC negative journeys; the
mainline problem was that weak true-negative journeys were allowed to perturb
the RMP.  The online role of the GNN is therefore narrowed to a high-confidence
candidate injector.

Mainline contract after this probe:

- `journey_learning_enabled` stays `True`; do not disable learning to fix a
  regression.
- `journey_learning_true_rc_tol` remains the numerical tolerance.
- `journey_learning_true_rc_keep_threshold` is the heuristic quality gate for
  learning-smoothed candidates.
- Learning candidates must satisfy
  `true_rc < -max(true_rc_tol, true_rc_keep_threshold)` before insertion.
- Exact certificate pricing remains true-dual only and is not affected by this
  stronger heuristic gate.
- If a smoothed pass produces no strong true-RC column, the current round still
  falls back to true-dual exact pricing, but alpha is not permanently forced to
  zero.  A later RMP dual can still use the GNN anchor while the configured
  learning round budget remains.
- Learning-smoothed pricing must use isolated one-shot pricing caches.  It must
  not write label-resume or physical-catalog state into the cache later reused
  by true-dual exact pricing, because those states are reduced-cost-vector
  dependent.
- Learning logs record `kept_best_true_reduced_cost`,
  `kept_worst_true_reduced_cost`, and `kept_mean_true_reduced_cost` so future
  failures can distinguish anchor quality from candidate-selection quality.

Regression note: before cache isolation, `tranq10_03` could finish with
`201.321909` when learning was enabled, while the same current config with
`journey_learning_enabled=False` finished at `197.875013`.  That is an exactness
violation and must be treated as integration-cache contamination, not as a GAT
training-quality issue.

Final 5/10 validation after strong gate and cache isolation:

```text
BPC_future/results/all_tasks05_learning_threshold10_isolated_120s_20260604.csv
  OPTIMAL = 20 / 20
  TIME_LIMIT = 0 / 20
  max time = 2.337395s
  mean time = 0.406981s
  objective mismatches vs resource-bound baseline = 0
  target status: all 5-task instances are below 5s

BPC_future/results/all_tasks10_learning_threshold10_isolated_120s_20260604.csv
  OPTIMAL = 20 / 20
  TIME_LIMIT = 0 / 20
  max time = 75.512124s
  mean time = 28.721814s
  objective mismatches vs resource-bound baseline = 0
  learning true-RC filter events = 20
  total GNN columns kept = 40
  target status: 17 / 20 10-task instances are below 60s
```

Remaining 10-task slow instances:

```text
apollo15_20km_tasks10_04_seed11055:
  learning threshold10 isolated = 75.512124s
  resource-bound baseline       = 66.758771s

tranquillitatis_tasks10_01_seed11000:
  learning threshold10 isolated = 67.842055s
  resource-bound baseline       = 55.865s

tranquillitatis_tasks10_04_seed11054:
  learning threshold10 isolated = 70.088245s
  resource-bound baseline       = 60.255424s
```

These remaining misses are not learning exactness failures.  They are tail
certificate/runtime problems and should be attacked through exact-pricing and
completion-bound improvements.  Keep learning enabled while doing that work.

## Anchor Diagnostics and MLP Ablation (2026-06-04)

The hypothesis "maybe the GAT is trained badly" was split into measurable
checks instead of judging only by wall-clock time.

Zero-dual/dead-task check:

```text
script:
  BPC_future/scripts/diagnose_learning_dual_anchor.py

hardtail dataset:
  sample_count = 39
  task_count = 290
  checkpoint label mean/std = 34.693942 / 23.024107
  label min/q05/q50/q95/max = 2.766059 / 5.203244 / 30.932669 / 76.059602 / 129.058990
  zero_dual_count(|pi| <= 1e-8) = 0
  near_zero_count(|pi| <= 1.0) = 0 across all existing learning datasets
```

Interpretation: the current dual-center datasets do not contain true zero-dual
task labels.  The observed online failures are therefore not simply "the model
predicts 5 or 10 for many exact zero labels."  The stronger issue is a label
coverage gap: if future RMP variants or instances have dead task-cover rows, the
current checkpoints have not been trained to represent that regime.  Adding a
zero-label penalty will not help until the data builder can produce such labels.

Scaler/outlier check:

```text
hardtail checkpoint on hardtail dataset:
  MAE = 9.596469
  MAE without top 5% |label| = 9.431465
  MAE without top 1% |label| = 9.532514

v1_trace_5_10_optimal_all checkpoint on hardtail dataset:
  MAE = 6.972546
  MAE without top 5% |label| = 7.074173
  MAE without top 1% |label| = 6.997609
```

Interpretation: a few huge outliers are not the main source of MAE.  The
standard-scaler variance is not hiding a "nearly perfect on normal nodes, bad on
one pi=2000 outlier" pattern; the largest label in these datasets is only about
129.

Node-only MLP ablation:

```text
script:
  BPC_future/scripts/train_learning_dual_mlp_baseline.py

dataset:
  BPC_future/data/learning_dual/hardtail_20260604
  split = instance split, seed 7
  validation instances = 8
  validation task_count = 65

node-only MLP validation:
  MAE = 15.078762
  RMSE = 20.235743
  Pearson = 0.487973
  Spearman = 0.334135

GAT hardtail on the same validation split:
  MAE = 10.302677
  RMSE = 14.713701
  Pearson = 0.755550
  Spearman = 0.673951

GAT v1_trace_5_10_optimal_all on the same validation split:
  MAE = 7.107132
  RMSE = 9.653681
  Pearson = 0.923364
  Spearman = 0.911014
```

Interpretation: the graph/option model is doing real work.  A node-only MLP can
fit some scale information, but it is much worse at ranking task duals.  This is
a useful ablation result for the learning component: path-option topology and
message passing materially improve dual-anchor ranking.  However, the better
offline v1 checkpoint did not uniformly improve online wall-clock time, so
future checkpoint selection must use both offline ranking metrics and online
true-RC column-quality metrics.

## Learning Funnel Refinement (2026-06-04)

The 10-task slow-instance probes showed that weak true-negative columns can hurt
the column-generation trajectory even when they are exact-safe.

Bad probe:

```text
fallback rule:
  if strong true-RC columns == 0, keep one best weak true-negative with true_rc < -1

Tranq10_04:
  before fallback = 71.120770s, columns = 440, exact pricing calls = 14
  with fallback  = 82.495508s, columns = 478, exact pricing calls = 15
```

This fallback is not a mainline setting.  It is kept as an off-by-default
diagnostic hook only.

Accepted rule:

```text
journey_learning_pricing_max_rounds = 2
journey_learning_min_kept_to_continue = 2
journey_learning_stop_after_no_strong_round = True
```

The GNN remains enabled, but a later smoothed pass is suppressed when the
previous learning pass kept too few strong true-RC columns.  This avoids wasting
pricing time or perturbing the RMP with weak learning guidance.

Validation:

```text
BPC_future/results/all_tasks10_learning_min2_120s_full_20260604.csv
  OPTIMAL = 20 / 20
  max time = 76.377088s
  mean time = 29.037943s
  median time = 19.690474s
  over 60s = 3 / 20
  max RSS ~= 1.0 GB

notable effects:
  Tranq10_09 returns to 58.965776s after suppressing the second learning round
  Tranq10_04 remains around 69s in full-run context
  Apollo10_04 remains the dominant 10-task branch/tree bottleneck at ~76s
```

Current learning conclusion: the GAT anchor is useful but should act as a
high-confidence Level-1 injector.  Online success is better predicted by strong
true-RC kept columns than by offline MAE alone.

## Rank/Zero Loss Probe (2026-06-04)

The training and evaluation scripts now support the first version of a
column-quality-oriented objective without changing the solver exactness
contract.

Added training knobs:

```text
--ranking-loss-weight
--ranking-temperature
--ranking-min-gap
--zero-label-weight
--zero-label-threshold
--zero-anchor-regularization-weight
```

The regression loss is still Huber on standardized task-cover duals.  The
optional ranking term is graph-local pairwise logistic ranking: task pairs with
a larger true dual are penalized if the model ranks them lower.  This pushes the
anchor toward better pricing priorities even when absolute dual MAE is not the
most important signal.

The data builder now treats missing `cover` entries in a dual trace as zero.
This is important because logs may omit zero-valued task-cover duals, and
omitting them would silently remove dead-task labels from the dataset.  The
builder also records zero/near-zero label counts in the manifest and supports
an off-by-default low-weight synthetic zero-anchor clone:

```text
--synthetic-zero-sample-fraction
--synthetic-zero-sample-weight
```

This synthetic option is experimental.  It must not be used as proof of
generalization; it is only a regularizer to expose the model to dead-task dual
patterns when collected traces contain no zero labels.

Train/test leakage rule:

- `train_learning_dual_model.py` defaults to `--split-by-instance=True`, so
  training and validation do not mix solve samples from the same instance.
- Full-dataset `diagnose_learning_dual_anchor.py` runs are replay diagnostics,
  not held-out tests, unless the caller explicitly points it at a held-out
  dataset.
- The held-out slow-instance probe with
  `hierarchical_option_gat_rankzero_probe2.pt` checked that `Apollo10_04`,
  `Tranq10_04`, and `Tranq10_01` had zero hits in
  `v1_trace_5_10_optimal_all/manifest.json`.

Probe result on three held-out 10-task slow instances:

```text
Baseline current min2 run:
  Apollo10_04: 76.377s, 17 nodes, 242 cols
  Tranq10_04: 69.364s, 1 node, 443 cols
  Tranq10_01: 62.646s, 1 node, 427 cols

Rank/zero probe2:
  Apollo10_04: 63.591s, 13 nodes, 247 cols
  Tranq10_04: 88.749s, 1 node, 480 cols
  Tranq10_01: 58.385s, 1 node, 430 cols
```

The online true-RC funnel for the same three held-out runs:

```text
candidate_journeys = 54
true_negative_journeys = 23
kept_journeys = 20
kept_rate = 0.370
true_negative_rate = 0.426
```

Compared with the current min2 all-10 run, the rank/zero objective produced a
more concentrated true-RC funnel on these three cases and improved two of the
three wall-clock times.  It also made `Tranq10_04` worse by generating a deeper
best true-RC column but more columns/pricing work.  Therefore this checkpoint is
not a mainline replacement yet.

Current conclusion:

- The method is worth keeping and optimizing.
- Offline MAE/top-k is insufficient; model selection must include online
  `true_negative_rate`, `kept_rate`, `kept_best_true_reduced_cost`, pricing
  calls, columns, and wall-clock.
- The next iteration should tune ranking weight and true-RC filter interaction
  together, because stronger columns can still slow the branch-price path if
  they increase RMP column volume or alter branching unfavorably.
