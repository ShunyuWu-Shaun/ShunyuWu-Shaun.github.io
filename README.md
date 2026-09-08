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
| `index.qmd` | Home: profile column, research overview figure, three directions, news, selected papers, latest note |
| `news/index.qmd` | News timeline |
| `research/index.qmd` | Research program: physical intelligence, the governing dynamics as substrate, directions A, B, C |
| `publications/index.qmd` | Publications grouped by direction, with a branch tag on each |
| `projects/` | Research projects grouped by direction, with source-linked summaries |
| `thinking/index.qmd` | Short working notes, newest first |
| `service/index.qmd`, `contact/index.qmd` | Service, contact |

The three directions are A, the physical systems in science and engineering;
B, solving the dynamics with neural networks; and C, the model-to-decision
gap. Keep the letters and the names identical across the home page, the
research page, the publication groups, and the project headings.

## The research architecture figure

The figure on the home page is HTML and CSS (the `.arch` rules in
`assets/css/site.css`) with three Matplotlib panels embedded as inline SVG, so
the page font and the page colours apply to everything in it. It is built from
`assets/figures/research-overview/`:

- `00_figure_contract.md` states what the figure must say before anything is drawn;
- `panels.py` computes the three panels (illustrative demand and price, a solved
  advection-diffusion field, and the decision error of a bistable system);
- `build.py` writes `_includes/research-overview.qmd`, which `index.qmd` includes;
- `01_figure_notes.md` records the QA run.

Rebuild with `python3 panels.py && python3 build.py` inside that folder. The
folder itself is excluded from rendering and from the published resources.

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
Google Fonts. Three colours from the top-conference figure library carry the
three directions everywhere, in the figure, the direction list, and the tags:
purple `#9467BD` for A, teal `#31859A` for B, coral `#EA7F6F` for C. Links use
the teal.

## Citation geography

The home-page map covers the publications listed in the public Google Scholar
profile, with affiliation geography from OpenAlex. Refresh the SVG with:

```bash
python3 scripts/build_citation_geography.py
```

## Publishing

Push to `main`. `.github/workflows/publish.yml` renders the site, deploys
`_site` to GitHub Pages, and submits the core URLs to IndexNow.
