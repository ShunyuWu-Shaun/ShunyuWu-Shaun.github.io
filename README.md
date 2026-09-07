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
| `index.qmd` | Home: masthead, research programme diagram, latest note, news, selected papers |
| `news/index.qmd` | News timeline |
| `thinking/index.qmd` | Working notes, newest first |
| `research/index.qmd` | Research programme |
| `publications/index.qmd` | First- and last-author publications |
| `projects/` | Research projects and source-linked summaries |
| `service/index.qmd`, `contact/index.qmd` | Service, contact |

## Adding a note to Thinking

Copy an `<article class="note">` block to the **top** of the `.notes`
container in `thinking/index.qmd` and edit it. Two rules:

- Give the article a stable `id`; the home page links to the newest one.
- Date it in the time zone you were in, both machine-readable and in words:

```html
<time datetime="2026-09-07T11:40:00-04:00">7 September 2026, 11:40 EDT (UTC−04:00)</time>
```

Accent options are `note--forecasting` (amber), `note--operators` (teal) and
`note--control` (indigo); omit the modifier for crimson. After adding a note,
update the `.note-preview` block in the Thinking section of `index.qmd` so the
home page shows the newest one.

## Design

One stylesheet, `assets/css/site.css`, organised in numbered sections and
driven by custom properties at the top. The four accent colours are semantic:
amber for decision-focused forecasting, teal for neural operators, indigo for
learning-based control, crimson for materials processing. They recur in the
home-page diagram, the research cards, the news timeline and the navbar spine.
Type is EB Garamond throughout, loaded from Google Fonts.

## Citation geography

The home-page map covers the publications listed in the public Google Scholar
profile, with affiliation geography from OpenAlex. Refresh the SVG with:

```bash
python3 scripts/build_citation_geography.py
```

## Publishing

Push to `main`. `.github/workflows/publish.yml` renders the site, deploys
`_site` to GitHub Pages, and submits the core URLs to IndexNow.
