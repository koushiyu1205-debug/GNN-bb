# Terminology Policy

## Required Paper-Facing Terms

| Avoid | Use | Scope |
|---|---|---|
| 认证; generic certification language | 证明; proof; prove; requiring an exact proof | Default wording for formal correctness, no-negative-column reasoning, optimality and algorithm status |
| 宇宙; universe | 固定逻辑路径解空间; fixed logical-path solution space | The set of feasible journey solutions induced by the fixed logical graph and its declared path options |
| universe when referring to labels | 状态空间; state space | Label resources, dynamic-programming states and GAT/solver states |
| 骨架; backbone | 框架; framework | The exact BPC algorithm and its deterministic components |

## Context-Specific Terms

- Use **path-option space** for the three predeclared alternatives on a directed
  logical edge.
- Use **candidate set** for pricing or branching candidates.
- Use **feasible journey solution space** for the complete journey set searched
  by exact pricing.
- Use **proof scope**, **proof record**, **proof ledger**, **proof validity** and
  **proof-preserving** in paper prose.
- Use **exact framework** for the implemented RMP, pricing, deterministic cuts,
  branching and proof logic.

## Restricted Use of `certify`

The English verbs **certify** and **certified** are permitted only when all of
the following hold:

1. an explicit derivation, exhaustive search, or formal proof chain is stated;
2. the exact scope is named, such as the fixed logical-path solution space;
3. the responsible exact mechanism is identified;
4. the statement is not based on a learned score, diagnostic signal,
   heuristic result, replay observation, or benchmark gate.

For example, native true-dual exact completion may be described as certifying
the absence of negative-reduced-cost columns only after the complete feasible
journey solution space has been searched under the active branch and cut
context. A learned pricing ranker cannot certify that statement.

## Literal Implementation Names

Literal code identifiers, enum values and file paths are not renamed. Examples
include `certificate_scope`, `CERTIFIED_NO_NEGATIVE`,
`false_certificate_count`, directories named `certificates/`, and source files
whose names contain `certificate`. When they appear in the paper, introduce
them as implementation-level proof-status or proof-record fields.
