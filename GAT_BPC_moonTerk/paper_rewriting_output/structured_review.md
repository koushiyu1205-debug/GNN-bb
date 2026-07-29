# Phase 4 Structured Review

## Review boundary

Three independent reviews were completed against the synchronized
no-task-wait manuscript, implementation evidence, generated LaTeX, and PDF:

1. mathematical exactness and implementation consistency;
2. contribution structure and evidence maturity;
3. terminology, narrative clarity, and rendering.

The standalone records are stored under `reviews/`.

## Findings and dispositions

### Mathematical exactness

The reviewer found one implementation--proof scope mismatch in the optional
completion bound and one imprecise tolerance statement. Both were corrected.
Equation (18) now admits branch restrictions but requires an empty active-cut
context, matching the executable. The text also distinguishes the
proof-bearing native \(10^{-12}\) path-equality comparison from the
non-certifying Python seed/reference \(10^{-9}\) comparison. The frozen
80-instance baseline has the optional completion bound disabled. A final
review confirmed that Equations (3), (6a), and (16)--(18), Lemmas 1--5, and
Theorem 1 are mutually consistent under their displayed assumptions.

### Contribution and evidence boundary

The reviewer confirmed exactly three Introduction contributions: model,
algorithm, and benchmark/evaluation package. To remove a possible ambiguity,
Table 1 is now called the frozen implementation baseline and is explicitly
separated from the pending strictly paired L0 learning control. The English
and Chinese contribution statements now say directly that learning-guidance
and seasonal comparison results remain pending. Historical wait-permitted
results remain a separate evidence class.

### Clarity, terminology, and presentation

The reviewer confirmed the uniform “arrival equals service start” meaning,
the service-versus-wait distinction, and the `trip` / `multi-trip route`
terminology. The first task-window definition now states that \(r_i\) is an
earliest service-start time and \(D_i\) a latest service-completion time.
The exposed task-risk conversion was replaced by the frozen preprocessing
input \(\rho_i^{\mathrm{srv}}\), with the code mapping retained only in the
internal notation ledger. The duplicate PDF title was removed and algorithm
tables were reformatted with a narrow line-number column. Formula rendering
and the PDF text layer passed direct inspection.

## Final verdict

**PASS FOR THE SYNCHRONIZED ENGLISH WORKING DRAFT.**

No unresolved mathematical, evidence-boundary, terminology, or rendering
defect remains within the present scope. This verdict does not activate the
still-missing learning, held-out/OOD, or mission-epoch results, and it does
not convert historical wait-permitted evidence into evidence for the revised
model.
