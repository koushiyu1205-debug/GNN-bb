# Humanize Check Report

- Matrix path: `paper_rewriting_output/humanize_matrix.md`
- Matrix rows: 77
- Manuscript paragraphs: 327
- Coverage: 24%
- Sentence length stddev: 22.64
- Connector density: 0.04/1k chars
- Status: FAIL

## Findings

- Coverage 24%: 77 rows for 327 paragraphs. Minimum 50%.
- Long dash separators detected (e.g. '————'). These are a strong AI-generation signal — replace with section headings or blank lines.

## Stage-Aware Interpretation

The configured tier is `light`, and the active task is a targeted technical
revision rather than the final all-paragraph humanization pass. The coverage
failure records that the teaching matrix has not yet been expanded to every
final-paper paragraph. The reported long-dash match is produced by Markdown
table separator rows (`---`); no Chinese or English long-dash separator occurs
in the manuscript prose.

Direct source checks passed for the current revision: no first-person
construction, no `snapshot`, no internal status enum, consistent terminology,
and no unsupported learning or seasonal result sentence. Full matrix coverage
remains a later production-stage task after the empirical placeholders are
activated, so it is not represented as complete here.
