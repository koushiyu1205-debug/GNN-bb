# Introduction Revision Audit

## Revision Goal

Replace the former constraint-led opening with an evidence-led argument:
lunar-water observations identify where investigation may be valuable, but
site-level characterization still requires coordinated in-situ operations.
The introduction must then narrow from the south-pole operating environment to
multi-trip fleet routing, exact pricing, and the bounded role of learning.

## Reverse Outline

| Paragraph | Message | Evidence | Exit Function |
|---:|---|---|---|
| 1 | A mapped water-related signal is not yet site-level evidence of abundance, physical occurrence, or accessibility | C054, C061, C062; CL038 | Defines detection, sampling, and drilling at preidentified candidates as the planning task |
| 2 | South-pole terrain, PSRs, static task windows, shadow exposure and alternative paths make evidence acquisition timing- and resource-dependent | C042, C054, C055; EV029, EV032, EV034; CL040 | Converts the lunar environment into joint service-timing and path decisions without adding a dynamic communication model |
| 3 | The heterogeneous multi-path, multi-trip capacitated formulation integrates task assignment, repeated trips, resource feasibility, the normalized objective and a forward-looking real-map benchmark | EV002--EV003, EV009--EV011, EV032; CL036 | Defines the mathematical decision and resolves the user's data placeholder through verified LOLA-derived raster provenance |
| 4 | Retaining one inter-site path loses operational trade-offs, while complete multi-trip route columns make exact pricing resource-rich; learned ordering cannot replace proof-producing completion | C001, C002, C009, C021, C028--C030, C059; EV002, EV004--EV008, EV030 | Establishes both the representation and computational gaps addressed by the paper |
| 5 | The proposed BPC uses pricing-first and branch-second guidance while all validity, bounds, pruning, and closure remain exact; seasonal comparisons solve independent fixed instances | EV004--EV009, EV033; CL005--CL011, CL035, CL039 | States the method and its exactness and environmental boundaries without self-questioning prose |
| 6 | Four contributions and the paper organization follow the same funnel: formulation, exact framework, bounded guidance, and correctness-first evaluation with four seasonal phases | CL001--CL011, CL035--CL039; section blueprints | Leaves both learning effects and seasonal differences explicitly open |

## User-Provided Material Transfer

| Input idea | Treatment in the revised introduction | Reason |
|---|---|---|
| Water supports sustained lunar activity | Retained as the opening context | Supported background and concise entry point |
| Remote/sample evidence does not replace local characterization | Retained as the opening tension | Directly motivates candidate-site in-situ operations |
| Chang'E-5 shows heterogeneous host and retention conditions | Retained with C061--C062 | Primary sample evidence supports the bounded claim |
| PSR access creates thermal, energy, and return considerations | Retained with a benchmark-model qualifier | Explains shadow exposure without treating it as solar generation |
| Direct sunlight is not required for service; task windows represent instrument, communication and mission-schedule restrictions | Retained as a bounded static model interpretation | EV034 and CL040 record the user-confirmed interpretation; communication is explicitly not a separate dynamic constraint |
| Several alternative paths may trade time, energy, shadow, and risk | Retained | Matches the three fixed path options |
| Use a 50 km by 50 km real lunar region, 30 km/h modeled speed and `xxxxx` lunar data | Retained after resolving `xxxxx` as locally available LOLA-derived elevation, slope, roughness, PSR and average solar-visibility rasters | EV011 and EV032 support the provenance; the extent and speed remain forward-looking experimental assumptions |
| Path attributes vary with departure time | Not attributed to the current model | Attributes may differ across independently generated mission epochs, but remain immutable within one solve; departure time changes schedule feasibility only |
| Define a time-dependent multi-path VRP | Not adopted | The current formulation is static multi-path routing with temporal scheduling |
| Use `journey column` | Replaced by `multi-trip route column` | Follows the approved paper terminology |
| Claim GAT plus nearest-neighbor acceleration | Not adopted as a completed mechanism | No frozen checkpoint, retrieval design, or learning experiment exists |
| Claim improved large-scale search efficiency | Left as an empirical question | M001--M005 and paired learning ablations remain unavailable |

## Claim--Evidence Check

| Claim | Evidence | Status |
|---|---|---|
| Lunar surface water occurs in multiple host materials and is affected by mineral/exposure factors | C061, C062 | Supported |
| These studies determine abundance or accessibility at benchmark sites | None | Excluded |
| PSRs and adjacent terrain motivate path-resource trade-offs | C042, C054, C055; EV032 | Supported with scope qualifier |
| Shadow exposure accumulates during movement and service in the benchmark | EV029; Eq. (6b) | Supported |
| Static task windows can represent externally specified instrument, communication-schedule and mission-planning restrictions without modeling communication dynamics | EV034; CL040 | Supported as a bounded model interpretation, not measured schedule evidence |
| Current path attributes depend on departure time | Contradicted by EV029 and Lemma 1 assumptions | Excluded |
| The benchmark uses a 50 km by 50 km area and configured 30 km/h maximum modeled speed | EV010--EV011, EV032 | Supported as uncalibrated scenario design |
| The real-map benchmark uses locally available LOLA-derived elevation, slope, roughness, PSR and average solar-visibility rasters | EV011; source catalog and real-map preview | Supported with native-resolution and proxy qualifiers |
| Learning improves performance | M004--M005 missing | Open; no claim |
| One south-polar seasonal phase is fastest | M006 and paired phase results missing | Open; no claim |

## Self-Review

- **Clarity:** the introduction contains exactly six prose paragraphs, each
  with one leading message and no self-posed research question.
- **Flow:** the sequence is evidence gap, lunar environment, routing model,
  exact-solution gap, proposed framework, and contributions plus roadmap.
- **Terminology:** `trip`, `multi-trip route`, fixed logical-path solution
  space, proof, and framework follow the manuscript policy.
- **Unsupported claims:** no time-dependent path model, trained GAT,
  nearest-neighbor module, learning speedup, measured communication schedule,
  south-pole abundance, or current rover capability is claimed.
- **Missing evidence:** learning effectiveness remains explicitly tied to
  M001--M005 and the planned paired ablations.

## Five-Dimension Reviewer Check

| Dimension | Reviewer Question | Assessment |
|---|---|---|
| Contribution | Does the introduction identify a specific transportation and optimization contribution rather than relying on lunar novelty alone? | PASS: it connects candidate-site evidence acquisition to multi-path, multi-trip routing and then to pricing-led, branch-assisted exact BPC |
| Writing clarity | Can a reader follow the argument before encountering solver terminology? | PASS: the first three paragraphs establish the evidence gap, environment, and routing model before decomposition or learning |
| Experimental strength | Does the introduction imply a learning improvement that the present experiments cannot support? | PASS: learning effectiveness is explicitly left open pending M001--M005 |
| Evaluation completeness | Are the future learning comparisons and safety checks visible at contribution level? | PASS: the fourth contribution names the correctness-first benchmark and audit order without inserting results |
| Method soundness | Does the introduction match the implemented model and exactness proof? | PASS: path attributes are fixed, the objective is unchanged, learning is ordering-only, cuts are deterministic, and the exactness proof is stated as conditional |

## Verdict

**PASS.** The six-paragraph revision uses a broad-to-narrow funnel, removes
self-questioning and code-oriented prose, and preserves the implemented
static-path model, exactness scope, and current evidence boundaries.
