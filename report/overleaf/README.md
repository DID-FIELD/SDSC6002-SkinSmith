# SkinSmith Overleaf report

Upload the contents of this directory as one Overleaf project and set
`main.tex` as the main document. The project uses pdfLaTeX and BibTeX.

Local build:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Main editable metadata is in `metadata.tex`. Figures copied from formal experiment
runs are under `figures/`; machine-readable table sources are under `data/`.

The report deliberately distinguishes:

- the formal paired Route A/B/C experiment;
- the separate edge-width and selection-policy sub-ablation;
- the human-selected real Gemini showcase run;
- the M4A4 adapter transfer case.

Do not merge these candidate pools or replace reported values without updating the
evidence audit in the repository.
