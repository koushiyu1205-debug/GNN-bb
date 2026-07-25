# Motivation Thread Model

## Confirmed Motivation Source

Derived from `confirmed_motivation.md` and the user's revised Introduction
source text supplied on 2026-07-24.

## One-Sentence Red Thread

This paper addresses the exact coordination of repeated, resource-constrained
lunar water-ice prospecting trips over predeclared terrain-aware paths by
placing pricing-led and branch-candidate learning guidance inside a
Branch-Price-and-Cut framework whose feasibility, bounds, pruning and
optimality proof remain entirely exact.

## Problem-Solution Arc

| Arc Element | Content | Evidence Source | Required Section |
|---|---|---|---|
| Field problem | Remote and sample evidence identifies water-related candidates but does not establish candidate-site abundance, physical occurrence or operational accessibility | C054, C061, C062; CL038 | Introduction P1 |
| Lunar operating bottleneck | Terrain, shadow exposure, energy, service requirements and repeated returns couple access to spatially dispersed sites | C042, C054, C055; EV029, EV032 | Introduction P2 |
| Transportation decision | Assign heterogeneous tasks, trips and path options to a rover fleet under time-window, load, energy, shadow, recharge and mission-horizon constraints | EV002, EV003, EV009--EV011 | Introduction P3 |
| Computational gap | Rich multi-trip route columns create a large pricing state and search space; learned priorities cannot replace proof-producing pricing exhaustion | C001, C002, C009, C021, C028--C030, C059; EV004, EV007 | Introduction P4 |
| Design response | Pricing-led, branching-assisted learning guidance with deterministic valid inequalities, mandatory exact fallback and exact tree closure | EV001, EV004--EV008 | Introduction P5 and Section 4 |
| Environmental evaluation boundary | Seasonal phases are compared through independently fixed mission-epoch instances; path attributes do not change with departure time inside one solve | C063, C064; EV033; CL039 | Introduction P5 and Sections 5--6 |
| Evidence promise | Exactness is proved conditionally for each fixed logical-path instance; learning effects and seasonal rankings require their designated frozen experiments | EV027, EV031, EV033 | Introduction P6, Sections 6--8 |

## Introduction-to-Results Promise Map

| Final Introduction Promise | Results Subsection That Tests It | Required Evidence | Result Narrative Boundary |
|---|---|---|---|
| Exact BPC closes declared fixed instances without assigning proof authority to learning | Sections 6.1--6.3 | EV012--EV024 and proof audits | Separate formal exact closure, deterministic-cut evidence and benchmark-only diagnostics |
| Learning may alter search order while preserving exact conclusions | Section 6.4 | M001--M005; EXP-L0/L1/L2/G | Remains `TBD` until checkpoints, overhead, fallback and paired results are frozen |
| Operating phases may alter path and route outcomes under common controls | Section 6.5 | M006; EXP-EPOCH | Remains `TBD`; no fastest phase is inferred before paired exact-feasible results exist |
| Exactness does not extend to continuous terrain or cross-phase robust routing | Sections 7.4--7.7 | EV009, EV031, EV033 | State the fixed logical-path and independently fixed-instance limits explicitly |

