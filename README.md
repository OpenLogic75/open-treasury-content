# Open Treasury content

Live content for the Open Treasury apps (Android and iOS). The apps download these
files from GitHub Pages, so news posts, Spotlights and headline figures can change
without a new app release.

Base URL: `https://openlogic75.github.io/open-treasury-content/v1/`

## How to publish

1. Edit or add files under `v1/`.
2. **Bump the `version`** of every file you changed, both inside the file and in
   its entry in `v1/manifest.json`. The apps only download a file again when its
   version in the manifest changes.
3. Run `python tools/validate.py`. Fix anything it reports.
4. Commit and push. GitHub Pages serves it within a minute or two, and apps pick it
   up next time they open (at most every 15 minutes) or on pull-to-refresh.

**Versions only ever go up.** A phone that already has version 5 of a file ignores a
manifest that says version 4. To undo a change, put the old content back *and* give
it a new, higher version (6). `git revert` restores the old text; then bump the version.

To withdraw something, remove it from the manifest (Spotlight or tracker) or from
`feed.json` (post) and bump the versions.

The apps ship with a copy of `v1/` bundled in, so they work offline and on first
launch. Refresh that copy in each app release (`tools/sync_bundled.sh`).

## Files

| File | What it holds |
|---|---|
| `v1/manifest.json` | Index: versions of the feed and figures, and the list of remote Spotlights |
| `v1/feed.json` | News posts shown in "Latest" on the home screen |
| `v1/figures.json` | Headline figures used across the app (Bank Rate headline) |
| `v1/spotlights/<id>.json` | One file per remote Spotlight |

## Schema (version 1)

Everything is plain JSON. Apps **ignore fields and block types they don't
recognise**, so adding new optional fields is always safe. If a Spotlight needs a
block type older apps can't show, raise its `minSchema` in the manifest; apps below
that schema hide it.

### manifest.json

```json
{
  "schema": 1,
  "updatedAt": "2026-10-31T09:00:00Z",
  "feed":    { "path": "feed.json",    "version": 1 },
  "figures": { "path": "figures.json", "version": 1 },
  "spotlights": [
    { "id": "budget-2026", "title": "Budget 2026", "subtitle": "October 2026 Spotlight",
      "icon": "business_center", "color": "red", "access": "plus",
      "path": "spotlights/budget-2026.json", "version": 1, "minSchema": 1, "order": 10 }
  ]
}
```

- `access`: `"free"` or `"plus"` (Plus subscribers only; the app enforces it).
- `order`: Spotlights are listed in ascending order, after the built-in ones.

### feed.json

```json
{ "schema": 1, "version": 1, "posts": [ Post, ... ] }
```

Post fields: `id` (unique, never reused), `publishedAt` (ISO 8601 UTC), `tag`
(short label, e.g. "Budget 2026"), `title`, `summary` (one or two sentences, shown on
the card), `icon`, `color`, `blocks` (the full post body), optional `pinned: true`
(keeps it at the top), optional `access: "plus"`, optional `expiresAt`.
Posts show newest first.

### Spotlight document

```json
{
  "schema": 1, "id": "budget-2026", "version": 1, "updatedAt": "2026-10-31",
  "theme": { "primary": "#C62828", "deep": "#8E0000", "light": "#E53935" },
  "hero": { "kicker": "SPOTLIGHT SERIES · OCTOBER 2026", "title": "Budget 2026",
            "summary": "...", "stats": [ { "value": "£133bn", "label": "..." } ] },
  "tabs": [ { "title": "Overview", "icon": "assessment",
              "header": { "title": "Overview", "subtitle": "..." },
              "blocks": [ Block, ... ] } ],
  "sources": [ { "title": "HM Treasury", "detail": "..." } ]
}
```

### Blocks

| type | fields | renders as |
|---|---|---|
| `card` | `title`, `blocks` | Rounded card with a title and nested blocks |
| `heading` | `title`, `subtitle?` | Section heading |
| `text` | `text` | Body paragraph (`\n\n` for paragraph breaks) |
| `row` | `label`, `value`, `detail?` | Label on the left, bold value on the right, small detail below |
| `divider` | none | Thin line |
| `bullet` | `title`, `text` | Coloured dot with bold title and explanation |
| `bar` | `label`, `value`, `max`, `valueText`, `color?` | Horizontal bar, `value / max` filled |
| `note` | `text` | Orange highlighted note |
| `source` | `text` | Small grey source line |
| `myth` | `myth`, `reality` | "Myth: …" box with the reality underneath |
| `stats` | `items: [{value, label}]` | Grid of headline numbers, two per row |
| `link` | `title`, `subtitle?`, `action` | Button that opens something (see Actions) |
| `widget` | `widget`, `params` | A built-in interactive tool (see Widgets) |
| `table` | `columns`, `rows` | Table; each row is a list of cells, one per column. Scrolls sideways if wide |
| `line_chart` | `labels`, `series: [{name, values, color?}]`, `title?`, `prefix?`, `suffix?`, `decimals?` | Line chart; each series has one value per label. Shows first/middle/last labels and min/max values |
| `factcheck` | `claim`, `verdict`, `summary`, `speaker?`, `context?` | Claim, verdict badge and the short answer |

**Fact-check verdicts**: `accurate`, `mostly_accurate`, `missing_context`,
`misleading`, `false`, `unproven`.

**Colours** (`color`): `red`, `orange`, `yellow`, `green`, `mint`, `teal`, `cyan`,
`blue`, `indigo`, `purple`, `pink`, `brown`, `grey`, or a hex value like `"#C62828"`.
Omitted on a bar means the Spotlight's theme colour.

**Icons** (`icon`): `assessment`, `show_chart`, `payments`, `store`, `construction`,
`balance`, `business_center`, `campaign`, `account_balance`, `trending_up`,
`trending_down`, `savings`, `home`, `elderly`, `school`, `medical`, `shield`, `eco`,
`bolt`, `work`, `public`, `info`, `calendar`, `flag`, `gavel`, `receipt`. Unknown
names fall back to an article icon.

### Actions (on `link` blocks)

- `{ "type": "spotlight", "id": "budget-2026" }`: opens a remote Spotlight
- `{ "type": "tracker", "id": "immigration" }`: opens a tracker
- `{ "type": "route", "route": "economy_pulse" }`: opens an app screen. Allowed
  routes: `overview`, `economy_pulse`, `revenue`, `spending`, `debt`,
  `global_comparison`, `spotlight`, `calculator`, `cost_of_living`, `heatmaps`,
  `simulator`, `pound_health`, `data_sources`, `faq`, and the built-in Spotlights
  `spotlight_immigration`, `spotlight_nhs`, `spotlight_defence`, `spotlight_climate`,
  `spotlight_housing`, `spotlight_brexit`, `spotlight_taxation`,
  `spotlight_education`, `spotlight_pensions`
- `{ "type": "url", "url": "https://..." }`: opens a web page (https only)

### Widgets

Interactive tools are code in the app. Content can place them and set their numbers,
but a new kind of widget needs an app release.

**`savings_rent_tax_estimator`**: savings interest and rental profit tax estimator.

```json
{ "type": "widget", "widget": "savings_rent_tax_estimator", "params": {
    "title": "Savings & rent tax estimator", "intro": "...",
    "nowLabel": "Tax now (2026/27)",
    "bands": [ { "band": "Basic", "rates": [0.20, 0.22, 0.24] } ],
    "steps": ["From April 2027: Budget 2025 rise", "From April 2027: Budget 2026 rise"],
    "totalLabel": "Total tax from 2027/28", "note": "..." } }
```

`rates[0]` is today's rate; each later rate is one step in `steps`.

### Trackers

Listed in the manifest under `trackers` (same fields as Spotlights; `access`
defaults to `"free"`). A tracker file holds headline figures grouped into sections,
plus optional blocks underneath (links to Spotlights, tables, notes).

```json
{
  "schema": 1, "id": "immigration", "version": 1, "updatedAt": "2026-10-31",
  "title": "Immigration & Asylum", "summary": "...", "theme": { "primary": "#007AFF" },
  "sections": [ { "title": "Asylum", "metrics": [ Metric, ... ] } ],
  "blocks": [ Block, ... ]
}
```

Metric fields:

| field | required | meaning |
|---|---|---|
| `id` | yes | Unique within the tracker |
| `label` | yes | What the number is |
| `value` | yes | Display text, already formatted ("40,168", "£4.36bn") |
| `asOf` | yes | Period or date the figure covers |
| `source` | yes | Who publishes it |
| `detail` | no | A second line under the value |
| `change` | no | `{ "text", "direction": up/down/flat, "sentiment": good/bad/neutral }`. Sentiment sets the colour (green/red/grey); use neutral where "good" is a matter of opinion |
| `definition` | no | Plain-English meaning, shown when the ⓘ is tapped |
| `series` | no | `{ "labels": [...], "values": [...] }` for a small chart, with `seriesPrefix` / `seriesSuffix` |
| `ticker` | no | `true` puts it on the home-screen ticker, using `tickerLabel` if given |

The home screen shows each tracker's tile using its **first metric**.

### figures.json

```json
{ "schema": 1, "version": 1,
  "bankRate": { "rate": 3.75, "since": "Unchanged since 18 December 2025",
                "nextDecision": "Next decision: 5 November 2026" } }
```
