# PDF and LaTeX Build Report

## Source

- Markdown source: `paper_rewriting_output/manuscript_draft.md`
- Source SHA-256: `1649e7a6c26fbc78e6d5219d5abe0cc375de72e6ce2b924e16b510634c626e03`
- Source content was not rewritten during conversion.

## PDF Build

- Output: `paper_rewriting_output/manuscript_draft.pdf`
- Canonical PaperSpine copy: `paper_rewriting_output/final_paper/paper.pdf`
- Build path: Pandoc self-contained HTML5 conversion, local MathJax SVG
  formula rendering, and headless Chrome PDF output
- Status: passed
- Page size: A4
- Pages: 42
- File size: 2,013,915 bytes
- PDF SHA-256: `47bfc5bf4cab7570e4223bc1f4a78d5af566c08eaa51b2eeeda8097f7d847e35`

## LaTeX Source

- Generated source: `paper_rewriting_output/final_paper/main.tex`
- Local TeX engine available: no
- LaTeX compilation: not attempted
- Structural guard: 0 errors and 160 warnings
- Warning interpretation: the guard flags alignment markers in generated math and table environments; the delivered PDF was built through the independently validated HTML/MathJax path.
- Full guard output: `paper_rewriting_output/pdf_build/latex_guard_output.md`

## Content Integrity

- All top-level manuscript sections and Appendices A–E present: yes
- Tables present: yes
- Equations rendered: yes
- PDF text layer present and searchable: yes
- No raw LaTeX control sequences detected in the extracted PDF text: yes
- The two delivered PDF copies are byte-identical: yes
- Editorial working citation keys preserved: yes
- Explicit TBD placeholders preserved: yes
- Source figure placeholders preserved: yes

## Known Author Tasks

- The source still uses locked working keys such as `[@C054]`; final BibTeX and publisher formatting remain pending.
- The source contains explicit figure and experiment placeholders. They were intentionally preserved and were not converted into unsupported final figures or results.
