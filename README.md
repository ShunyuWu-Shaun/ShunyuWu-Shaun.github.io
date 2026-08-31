# Shunyu Wu Academic Website

This repository contains a Quarto-based personal academic website for **Shunyu Wu**.

## Tech Stack

- Quarto (website)
- GitHub Pages (deployment via GitHub Actions)

## Local Development

1. Install Quarto: <https://quarto.org/docs/get-started/>
2. Preview locally:

```bash
quarto preview
```

3. Render static output:

```bash
quarto render
```

## Citation geography

The homepage map is a dated OpenAlex snapshot generated before deployment. Refresh the JSON and SVG together with:

```bash
python3 scripts/build_citation_geography.py --retrieved-on YYYY-MM-DD
```

The generator validates the displayed date, totals, and country table in `index.qmd`; it stops if the homepage and snapshot differ. The published page does not request citation data or visitor data at runtime.

## Content Structure

- `/index.qmd` home page
- `/research/index.qmd`
- `/publications/index.qmd` first- and last-author publication portfolio
- `/projects/index.qmd` + source-linked research summaries in `/projects/*.qmd`
- `/news/index.qmd`
- `/service/index.qmd`
- `/contact/index.qmd`

## Publishing

Push to `main` to trigger `.github/workflows/publish.yml`.
