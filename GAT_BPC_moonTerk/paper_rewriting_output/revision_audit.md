# Revision Audit

## Scope

- Original: repository `HEAD` version of `manuscript_draft.md`
- Revised: active Phase 4 `manuscript_draft.md`
- Audit date: 2026-07-24
- Audit tool: PaperSpine `revision_audit.py`

## Automated Result

| Measure | Value |
|---|---:|
| Original paragraphs | 13 |
| Revised paragraphs | 260 |
| Near-identical revised paragraphs | 0 (0.0%) |
| Mostly new revised paragraphs | 254 (97.7%) |
| Likely deleted original paragraphs | 7 (53.8%) |
| Addition-heavy warning | No |
| Shallow-revision warning | No |

The repository baseline contained a Section 3-centered draft, whereas the
active file is a complete working manuscript. The automated comparison
therefore evaluates the full Phase 4 build rather than only the latest
Introduction edit.

## Targeted Introduction Check

The current Introduction contains exactly six prose paragraphs. Their
functions are:

1. lunar-water evidence and the remaining in-situ characterization gap;
2. south-pole operating conditions and coupled path/fleet decisions;
3. the routing model, fixed mission-epoch treatment, objective, and benchmark
   scope;
4. exact-pricing difficulty and the limit of learned ordering;
5. the proposed exact framework and its fixed-instance proof boundary; and
6. three contributions—model, algorithm, and benchmark/evaluation
   package—and the paper roadmap.

No self-posed research question, `snapshot` wording, first-person construction,
or completed learning/seasonal result appears in the Introduction.

## Verdict

**PASS — substantive revision, not append-only or shallow.** The six-paragraph
funnel is a genuine restructuring, while the model, objective, exactness, and
evidence boundaries remain traceable to the active project materials.

## 2026-08-03 Chinese narrative rewrite

The author-facing source `manuscript_zh_trc.md` was revised across the whole manuscript rather than through an appended explanation. The visible argument now follows: lunar in-situ evidence need → multi-path and multi-trip routing structure → route-column model → exact-pricing burden → deterministic accelerators → local GAT ordering → whole-algorithm exactness → paired evaluation.

The revision removed internal algorithm version names, development failures, qualification/checkpoint language and visible author task blocks from the paper argument. It retained all classical topology, timing and resource constraints, the normalized objective, the exact-result table and the fail-closed interpretation of incomplete pricing. An independent methods review also triggered a substantive mathematical addition: Equation (15c) now closes the pricing recursion to Equation (13), and Equations (26)–(27) no longer reuse the load symbol for reduced cost.

**Verdict: PASS for the requested narrative rewrite.** The manuscript remains a working paper rather than a submission-ready final because deterministic ablations, learning results, mission-epoch results, figures and final references are still missing.
