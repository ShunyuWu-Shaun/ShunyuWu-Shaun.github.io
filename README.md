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
- `/publications/index.qmd` + publication entry files in `/publications/*.qmd`
- `/projects/index.qmd` + project files in `/projects/*.qmd`
- `/cv/index.qmd`
- `/service/index.qmd`
- `/contact/index.qmd`

## Publishing

Push to `main` to trigger `.github/workflows/publish.yml`.
