# Imaginary paper: RE as multi-objective optimization

A short LaTeX pitch document for the multi-objective-RE research direction. Intended to
share with the advisor for a quick read-through.

## Files

- `main.tex` — the paper itself (~3 pages, two-column, with two TikZ Pareto-frontier
  figures and one Nano Banana placeholder).
- `references.bib` — bibliography.
- `figures/nano_banana_prompt.txt` — prompt to generate the concept diagram (Figure 1).
- `figures/concept.png` — drop the generated image here (path the LaTeX expects).

## Compile

```bash
cd docs/imaginary_paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Requires `pgfplots` (TikZ), `caption`, `natbib`, `multicol` — all standard in any
modern TeX Live / MacTeX install.

## Concept figure

The placeholder box on page 1 (Figure 1) will be replaced by the image at
`figures/concept.png`. Generate it via Nano Banana using the prompt in
`figures/nano_banana_prompt.txt`. The LaTeX auto-detects whether the file is present
(see `\IfFileExists` in `main.tex`) and falls back to the placeholder otherwise.
