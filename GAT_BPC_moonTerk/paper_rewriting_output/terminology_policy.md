# Terminology Policy

## Required Paper-Facing Terms

| Avoid | Use | Scope |
|---|---|---|
| 认证; generic certification language | 证明; proof; prove; requiring an exact proof | Default wording for formal correctness, no-negative-column reasoning, optimality and algorithm status |
| 宇宙; universe | 固定逻辑路径解空间; fixed logical-path solution space | The set of feasible multi-trip route solutions induced by the fixed logical graph and its declared path options |
| universe when referring to labels | 状态空间; state space | Label resources, dynamic-programming states and GAT/solver states |
| 骨架; backbone | 框架; framework | The exact BPC algorithm and its deterministic components |
| sortie as a paper-facing mathematical term | trip | One depot-to-depot task sequence; retain `TimedSortie` only when mapping to a literal code identifier |
| journey as the master-column term | multi-trip route; route column | One rover's ordered, time-compatible sequence of one or more trips |

## Context-Specific Terms

- Use **path-option space** for the three predeclared alternatives on a directed
  logical edge.
- Use **candidate set** for pricing or branching candidates.
- Use **feasible multi-trip route space** for the complete route set searched
  by exact pricing.
- Use **proof scope**, **proof record**, **proof ledger**, **proof validity** and
  **proof-preserving** in paper prose.
- Use **exact framework** for the implemented RMP, pricing, deterministic cuts,
  branching and proof logic.

## Application Narrative Boundary

- Describe the application through candidate-site coverage, terrain-dependent
  access, repeated trips, resource feasibility, and the scientific value of
  task completion order.
- Treat science-weighted completion time only as an objective component; do
  not turn it into a territorial, ownership-priority, or competition narrative.
- Do not introduce a newly named problem class based on the urgency or timing
  of resource exploration.

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
multi-trip route space has been searched under the active branch and cut
context. A learned pricing ranker cannot certify that statement.

## Definition and Logic Notation

- Introduce definitions explicitly in prose and use the ordinary equality sign
  \(=\) in the displayed formula.
- Write Boolean algorithmic rules as cases: value \(1\) when the stated
  condition holds and \(0\) otherwise.
- Use the compact implication \(A\Rightarrow B\) for a one-way logical
  consequence, including MILP indicator constraints.
- Use \(A\Leftrightarrow B\) only after both directions are justified. Prefer
  ordinary equality, a plain-language case distinction, or a set-builder
  definition for named rules and candidate sets.

## Separation of Implementation and Manuscript Terminology

Literal code identifiers, enum values, Boolean record fields, configuration
values, and file paths must not be used as paper-facing names for an algorithmic
condition or conclusion. The manuscript states the mathematical activation
conditions and their consequences directly. For example, it describes
exhaustive pricing over the complete active route set and the resulting
nonnegative-reduced-cost conclusion, rather than naming the corresponding
implementation enum.

Literal identifiers remain unchanged only inside source inventories, evidence
ledgers, implementation audits, and the internal
`implementation_manuscript_terminology_crosswalk.md`. That crosswalk is
excluded from the manuscript and preserves traceability between code records
and approved scholarly expressions.
