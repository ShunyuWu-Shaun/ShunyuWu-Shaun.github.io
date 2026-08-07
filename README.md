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

## Content Structure

- `/index.qmd` home page
- `/research/index.qmd`
- `/publications/index.qmd` first- and last-author publication portfolio
- `/projects/index.qmd` + source-linked case studies in `/projects/*.qmd`
- `/news/index.qmd`
- `/service/index.qmd`
- `/contact/index.qmd`

## Publishing

Push to `main` to trigger `.github/workflows/publish.yml`.
