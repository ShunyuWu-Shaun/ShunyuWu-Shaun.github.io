# Shunyu Wu Academic Website

Quarto site for **Shunyu Wu** (吴舜禹), published to GitHub Pages.

## Local development

Install Quarto (<https://quarto.org/docs/get-started/>), then:

```bash
quarto preview
```

`quarto render` writes the static site to `_site/`, which is what the
GitHub Actions workflow deploys. Nothing in `_site/` is committed.

## Content

| Path | Page |
|---|---|
| `index.qmd` | Home: profile column, research figure, news, selected papers, latest note |
| `news/index.qmd` | News timeline |
| `research/index.qmd` | Research program |
| `publications/index.qmd` | First- and last-author publications |
| `projects/` | Research projects and source-linked summaries |
| `thinking/index.qmd` | Short working notes, newest first |
| `service/index.qmd`, `contact/index.qmd` | Service, contact |

## Adding a note to Thinking

Copy an `<article class="note">` block to the **top** of the `.notes`
container in `thinking/index.qmd` and edit it. Three rules:

- Two or three sentences. A note states a position, not a defense of it.
- Give the article a stable `id`; the home page links to the newest one.
- Date it in the time zone you were in, both machine-readable and in words:

```html
<time datetime="2026-09-07T11:40:00-04:00">7 September 2026, EDT (UTC−04:00)</time>
```

Then update the note shown in the Thinking section of `index.qmd`, which is
the last section on the home page, so it carries the newest one.

## Design

One stylesheet, `assets/css/site.css`, organised in numbered sections and
driven by custom properties at the top. A sticky profile column on the left
holds the portrait, appointment and links; the right column holds the prose.
Body text is IBM Plex Sans and headings are IBM Plex Serif, both loaded from
Google Fonts. Four accent colours mark the four research directions and are
reused in the home-page figure: blue for decision-focused forecasting, teal
for neural operators, indigo for learning-based control, and rust for
materials processing.

The home-page figure is hand-written SVG inside `index.qmd`. Its three panels
are drawn to scale from real quantities, so edits should keep the axes, the
capacity limit and the return path consistent with the key below the figure.

## Citation geography

The home-page map covers the publications listed in the public Google Scholar
profile, with affiliation geography from OpenAlex. Refresh the SVG with:

```bash
python3 scripts/build_citation_geography.py
```

## Publishing

Push to `main`. `.github/workflows/publish.yml` renders the site, deploys
`_site` to GitHub Pages, and submits the core URLs to IndexNow.
