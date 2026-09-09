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
| `index.qmd` | Home: profile column, research logic figure, three directions, news, selected papers, latest note |
| `news/index.qmd` | News timeline |
| `research/index.qmd` | Research program: physical intelligence, its substrate, directions A, B, C |
| `publications/index.qmd` | Publications by year, with direction tags |
| `projects/` | Research projects grouped by direction, with source-linked summaries |
| `thinking/index.qmd` | Short working notes, newest first |
| `service/index.qmd`, `contact/index.qmd` | Service, contact |

The three directions are A, physical dynamics in science and engineering;
B, neural solvers for physical dynamics; and C, Model2Action. Keep the letters
and the names identical across the home page, the research page, the
publication tags, and the project headings. Publications are listed by year,
and a paper can carry more than one direction tag.

## The research logic figure

The figure on the home page is an inline SVG in `_includes/research-overview.qmd`,
styled by the `.logic` and `.lg-*` rules in `assets/css/site.css`. It draws the
research line as six numbered steps on one rail, with a return loop from step 6
to step 3. Edit the text in the include directly; each line is one `<text>`
element, so keep a line under about 70 characters. The badge colours follow the
three direction colours.

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

The interactive map aggregates citing papers by state/province or institution.
It uses local Leaflet assets and Natural Earth boundaries. The full citation
ledger, author affiliations, source snapshots, and coverage audit live in
[`_data/citations/`](./_data/citations/README.md). This folder is excluded from
site rendering, resources, search, and navigation; it remains readable in this
public Git repository.

Refresh OpenAlex records and rebuild the ledger and GIS data:

```bash
python3 scripts/update_citations.py
quarto render
```

For a reproducible rebuild from the checked-in response snapshots:

```bash
python3 scripts/update_citations.py --offline
```

No API key is required for the saved-data rebuild. If needed for fresh API
access, `OPENALEX_API_KEY` is read from the environment and never written to
snapshots. Google Scholar cross-checks are dated source snapshots, refreshed
separately after verifying each citation match; the command does not claim to
refresh Scholar. The map excludes direct self-citations and non-research
paratext records, which are retained and labeled in the ledger. See the data
README for counting rules, source coverage, and unresolved affiliations.

## Publishing

Push to `main`. `.github/workflows/publish.yml` renders the site, deploys
`_site` to GitHub Pages, and submits the core URLs to IndexNow.
