# Methods and Exactness Reviewer

## Final verdict

**PASS.** No unresolved serious, major, or minor mathematical issue remains.

## Checks completed

- Equation (3) enforces arrival-equals-service-start timing and retains the
  prescribed service duration in task completion.
- Equations (6a), (16), and (17) consistently exclude task-site and en-route
  waiting, permit only depot departure delay, disable open-trip dominance, and
  guard depot subset dominance by nonempty visited sets, cut state, branch
  compatibility, resources, and reduced cost.
- Equation (18) now matches the implementation: an active branch context is
  admissible because it only restricts continuations, whereas an active cut
  disables the bound because the cut-dual term is not represented.
- The mathematical equality used for path-option substitution is separated
  from the proof-bearing native tolerance of \(10^{-12}\) and the
  non-certifying Python seed/reference tolerance of \(10^{-9}\).
- The frozen 80-instance baseline disables the optional completion bound, so
  its contextual scope cannot affect Table 1.
- Replacing the exposed task-risk conversion by the frozen input
  \(\rho_i^{\mathrm{srv}}\) is algebraically exact. It changes neither column
  costs, reduced costs, feasibility, pricing, dominance, bounds, nor the
  frozen results.

## Evidence boundary

The proof is conditional in exact arithmetic. Executable conclusions remain
qualified by the recorded numerical tolerances and frozen source, engine,
configuration, and instance bindings.
