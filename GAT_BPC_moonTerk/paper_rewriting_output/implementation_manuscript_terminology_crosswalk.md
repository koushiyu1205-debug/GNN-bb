# Implementation-to-Manuscript Terminology Crosswalk

Purpose: internal drafting and audit aid only. This file is not part of the
manuscript, appendices, tables, or supplementary text intended for submission.
Implementation identifiers may be used here to preserve traceability to source
code and experiment records. In the manuscript, they must be replaced by the
mathematical condition or scholarly conclusion in the third column.

| Implementation identifier or record value | Exact internal meaning | Approved manuscript expression | Usage boundary |
|---|---|---|---|
| `FOUND_NEGATIVE` | Pricing has produced at least one audited, feasible, addable route with negative true reduced cost | one or more exact-addable negative-reduced-cost routes are found | Do not describe this as pricing closure. |
| `CERTIFIED_NO_NEGATIVE` | Exhaustive true-dual pricing has covered the complete active pricing context, passed all audits, and left no unresolved proof debt | exhaustive pricing proves that no negative-reduced-cost route exists in the complete pricing set | The word “proves” is allowed only when all completion and audit conditions hold. |
| `INCOMPLETE_LIMIT` | Pricing ended before exhaustive coverage, commonly because of a resource or search limit | pricing terminates without a closure proof; the pricing search remains incomplete | Never paraphrase as “no improving route exists.” |
| `NODE_INCOMPLETE` | A required node operation is unresolved, so the node cannot be closed exactly | node processing terminates without an exact conclusion; the node remains unresolved | Do not call the node infeasible, integral, or fathomed. |
| `PRUNED_BY_BOUND` | A valid node lower bound is no better than the incumbent under the declared tolerance | the node is fathomed by a valid lower bound | State the lower-bound validity conditions when the proof context matters. |
| `INTEGER_INCUMBENT` | The closed RMP solution is integral and exact-feasible | the integral solution is accepted as an incumbent candidate and the node is fathomed | “Candidate” is retained because incumbent replacement still depends on objective comparison. |
| `BRANCHED` | Two validated child contexts have been constructed from an exact disjunction | both child nodes are passed to the tree search | Branch selection order may be learned; child validity may not. |
| `NO_FRACTIONAL_RF_PAIR` | The current fractional solution supplies no admissible Ryan–Foster pair | no fractional Ryan–Foster pair is available | This condition is not an integrality proof. Without an exact alternative disjunction or aggregation proof, the node remains unresolved. |
| `BPC_TREE_OPTIMAL` | All tree-closure, bound, feasibility, pricing, branch, audit, and proof-debt conditions have passed | the closed branch-and-price tree establishes global optimality of the best exact-feasible incumbent over the fixed logical-path solution space | The theorem must state the mathematical conditions directly; the identifier must not appear in the manuscript. |
| `BPC_INFEASIBLE_CERTIFIED` | Exact Phase-I reasoning proves that the node or declared problem scope has no feasible solution | exact Phase-I pricing proves that the feasible set is empty | Always state the scope of infeasibility. |
| `BPC_INCOMPLETE_PRICING` | A run ends while exact pricing remains incomplete | the run terminates during an incomplete pricing search and yields no exact conclusion | Report the limiting resource and nonempty frontier when available. |
| `FAIL_CLOSED` | The implementation withholds a proof-bearing conclusion after an unresolved condition | the solver correctly withholds an exact conclusion | Use as an explanatory principle, not as a reported algorithmic status. |
| `NOT_PROMOTED` | The candidate fails at least one condition of the complete promotion rule | the candidate is not promoted because it does not satisfy the complete promotion criterion | Report the failed scale or gate beside the conclusion. |
| `no_cut` | The production configuration separates no optional cut family | the production configuration omits the optional SRI-3 cut family | Root-node SRI-3 remains a deterministic evaluated candidate, not the production default. |
| `no_model_shadow_v1` | Deterministic shadow-only guidance path; no trained model is loaded | a deterministic shadow-only execution path | This does not establish that a trained GAT exists or has been evaluated. |
| `P0`, `P0V2`, `P0V2BPC` | Internal names for successive deterministic root-only SRI-3 policies or studies | the predefined deterministic root-only SRI-3 separation and retention policy; the formal root-only SRI-3 study | Use the more specific expression required by context; do not expose the internal version label in the manuscript. |
| `ProofDebtQueue`, proof-debt fields | Implementation container for delayed pricing work that must be resolved before a proof-bearing event | the set of unresolved deferred-pricing obligations, denoted by $\mathcal{D}_n$ | The manuscript defines the mathematical set and closure condition, not the container type or field names. |
| `benchmark_only=true` | The record is admissible only as exploratory benchmark evidence | the study is benchmark-only | Do not call it a formal promotion experiment. |
| `formal_design_complete=false` | The formal promotion design is not complete | the formal design is incomplete | Keep distinct from algorithmic correctness. |
| `all_scales_promoted=false` | At least one tested scale fails the promotion criterion | not all tested scales satisfy the promotion criterion | Name the failed scale when reported in the main text. |
| `default_switch_allowed=false` | The evidence does not authorize a production-default change | a change to the default production policy is not permitted | Do not infer deployment approval from favorable local ratios. |
| `low_time` | Path alternative generated to minimize travel time | minimum-travel-time path alternative | Treat as an instance category, not as a code value. |
| `low_energy` | Path alternative generated to minimize the recorded energy proxy | minimum-energy path alternative | Do not imply physical energy optimality beyond the frozen generator. |
| `low_risk` | Path alternative generated to minimize the recorded traversal-risk measure | minimum-traversal-risk path alternative | Keep the risk measure bounded by its declared preprocessing model. |
| The superseded `service_start = max(arrival, ready_time)` transition | Historical route construction permitted early-arrival waiting at a candidate task | the predecessor implementation permits candidate-site waiting | This is legacy evidence only and must not be used to describe the revised formulation. |
| Current common-departure and latest-feasible-departure fields | Pricing represents the common feasible depot-departure interval and shifts the whole trip when a later release requires it | the feasible depot-departure interval and no-wait timing state | Use mathematical timing terms in the manuscript, not field names. |
| Current rejected no-wait extension | An extension is infeasible when the accumulated task windows have no common feasible depot departure | the trip's feasible depot-departure interval is empty | Early arrival under a provisional departure is not itself infeasible; the whole trip is first shifted at the depot. |

## Drafting rule

When a new implementation status appears in a source record, first add it to
this crosswalk with its exact activation conditions. The manuscript should then
state those conditions and their mathematical consequence directly. A code
identifier may appear in an internal evidence ledger, but not as the subject or
predicate of a scientific claim in the manuscript.
# 2026-08-03 P0V4+V5/QG2 update

| Project/internal term | English manuscript term | Chinese manuscript term | Use rule |
|---|---|---|---|
| `P0V4` | memory-compact exhaustive exact-pricing fallback | 内存紧凑的原生穷举精确定价回退 | Define once; use the conceptual term thereafter |
| `V5 midpoint` | bidirectional midpoint negative-column prepass | 双向中点负列预处理 | Explicitly state no certificate authority |
| `V5 group screen` | deterministic root SRI-3 candidate-group screening | 根节点 SRI-3 候选分组筛选 | A commitment heuristic over valid rows, not learned cuts |
| `Q0` | deterministic partial-reduced-cost label queue | 确定性部分约化成本标签队列 | Literal runtime fallback |
| `QG2` | within-bucket label-state ordering | 约化成本桶内的标签状态学习排序 | No filtering, dominance, bound, pruning, branch, cut, or proof action |
| `exact_negative_escape` | enlarged negative pool with frozen diverse batch admission | 扩大负列池后的确定性多样化批量接纳 | Distinguish raw negatives from master-ready columns |
| fail-closed statuses | incomplete outcome without the corresponding exact conclusion | 不给出相应精确结论的安全终止 | Do not print raw status enums in prose |
| proof debt | unresolved proof obligation | 未解决证明义务 | Use mathematical conditions rather than queue field names |

This table is internal and must remain outside both the English and Chinese
manuscript bodies.
