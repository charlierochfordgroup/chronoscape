# Adding a country

One JSON file per country. Drop it in, run the build, commit. There is no
database and no admin UI - the file **is** the content.

Written up 14/08/2026 after adding Greece and Peru, which is when the
conventions below were actually pinned down. Ireland and Japan were built
ad hoc and predate this.

## The shape

```jsonc
{
  "country": { "name": "Greece", "center_lat": 38.4, "center_lng": 23.6, "default_zoom": 6 },
  "eras":   [ /* 10 of these, in chronological order */ ],
  "events": [ /* 100-130 of these, sorted by sort_year */ ]
}
```

### Era

| Field | Notes |
|---|---|
| `name` | Full name. Events reference it **exactly** - see the era-matching note below |
| `short_name` | Timeline band label. Keep under ~15 characters or it crowds |
| `sort_order` | `0..n`, ascending, no gaps or duplicates |
| `year_start` / `year_end` | Numbers. **Negative for BCE.** Start must not exceed end |
| `date_label` | Human text under the band, e.g. `"146 BCE-330 CE"` |
| `width_pct` | Share of timeline width. **Must sum to exactly 100** across all eras |
| `color` | From the ramp below, in order |

### Event

| Field | Notes |
|---|---|
| `era_name` | Must match an era `name` exactly |
| `sort_year` | Number, negative for BCE. A fraction orders events inside a year (`1944.4` = May 1944) |
| `display_date` | What the reader sees: `"c. 800"`, `"28 July 1821"`, `"1912"` |
| `title` | Short. **Must be unique within the country** |
| `description` | One to three sentences |
| `categories` | Subset of the valid list; most events want one or two |
| `source` | Wikipedia article slug. **Required on every `is_major` event**, optional elsewhere |
| `lat` / `lng` | Both or neither. `null`/`null` for diffuse national events |
| `is_major` | The key events. Aim for **35-45%** |

Valid categories: `Military`, `Political`, `Economic`, `Indigenous`,
`Aboriginal`, `Foreign Relations`, `Cultural`, `Social`, `Scientific`,
`Religious`.

## The palette

Ten eras, these colours, in this order. Every existing country uses it, so a
new one that deviates looks broken next to the others.

```
#5a8a9a  #6b7f9e  #7a6fa0  #8a6b93  #9c6a7d
#a87356  #b08a45  #8f9a4a  #5f9a6a  #4fa3a0
```

## Conventions that are not obvious

- **Ten eras. Enforced** - `validate.py` errors on any other number, on both
  tails. The palette has exactly ten entries and the legend is laid out for ten.
- **`width_pct` is editorial, not proportional to time.** Greece's Bronze Age
  covers two thousand years and gets 8; the Classical era covers 157 years and
  gets 12. Weight by how much there is to show, or antiquity swallows the strip.
- **`default_zoom` has to be checked by eye. Nothing validates it, and the
  arithmetic is easy to get wrong by a factor of two.** The map pane measures
  **569 x 447 CSS px** at a 1440x900 viewport, and **MapLibre uses 512px tiles**,
  so the longitude a page actually shows is

      360 * 569 / (512 * 2**zoom)

  which is 50 degrees at zoom 3, 25 at 4, 12.5 at 5, 6.3 at 6 and 3.1 at 7.
  Using 256px tiles doubles every one of those and makes every setting look fine.
  On 26/08/2026 that error produced three different verdicts in a row, each
  contradicted by a screenshot, before the tile size was checked.

  Current values, all confirmed against rendered pages: **3** China, India,
  Australia, Norway; **4** Mexico, Italy, Japan; **5** Egypt, Peru, Greece,
  Ireland; **6** Iceland, Taiwan.

  Two things the formula will not tell you. **Frame the country, not every
  event** - Gallipoli on the Australian timeline and a UN vote in New York on the
  Chinese one are meant to be off-screen until clicked, so size on roughly the
  10th to 90th percentile of the coordinates and ignore the outliers. And **check
  that the preselected opening event is actually visible**: Greece sat at zoom 6
  opening on Knossos with Crete outside the frame, which is the failure worth
  catching. Load the page and look.
- **35-45% `is_major`. Enforced** - warns outside 35-45%, errors outside 25-55%,
  on both tails. If most dots are key events, none of them are.

  **Do not set this flag while writing the events.** Every country where it was
  set inline came in far too high - Greece and Peru near 60%, then Norway 65%,
  Italy 76% and Mexico 59% - and hand-counting the correction was wrong twice
  more. Write the events without the flag, then build an explicit list of the
  beats you would use to tell the story in forty moments, and assert the ratio
  before you emit the file. Taiwan is the reason the check is two-tailed: it sat
  at 13% for months because the old check only looked at the high end.
- **Australian English, hyphens only. Enforced** - `validate.py` errors on an en
  or em dash in `display_date`, `title` or `description`, and in an era's `name`,
  `short_name` or `date_label`. All six are rendered text. `source` is the one
  exemption, for the reason given above.
- **Precursor events may sit in the era they belong to narratively.** Iceland's
  pre-874 voyages live in the Settlement Age. The validator *warns* and the
  build continues; the dot clamps to the segment edge. This is allowed on
  purpose - do not "fix" it by moving the event.
- **`source` is a slug, not a URL.** `"Battle_of_Clontarf"`, never
  `"https://en.wikipedia.org/wiki/Battle_of_Clontarf"` - the renderer builds the
  URL. It must match the article title exactly, which makes this the one field
  where the no-dash rule does not apply: the article really is
  `Egyptian-en-dash-Hittite_peace_treaty`, and the hyphen spelling does not
  exist. Diacritics the same (`Jomon` is a redirect at best; write
  `Jōmon_period`). The validator rejects spaces, URLs and `%` escapes, but it
  cannot tell you the article exists - see below.
- **Check the slugs resolve before committing.** A citation that 404s or lands
  on a disambiguation page is worse than none, and nobody re-reads 45 of them.
  Batch them through the API:

  ```
  https://en.wikipedia.org/w/api.php?action=query&titles=A|B|C
      &redirects=1&prop=pageprops&ppprop=disambiguation&format=json&formatversion=2
  ```

  A `missing` page means the slug is wrong; `pageprops.disambiguation` means it
  resolves to a dab page and needs a more specific article. Of the 290 written
  on 20/08/2026, six were missing and two were dab pages - about 3%, which is
  the rate to expect from writing them by hand.
- **Era matching is exact.** `build.py` will fuzzy-match as a fallback and an
  unmatched event silently lands in the **last** era, so a typo hides rather
  than erroring. `validate.py` catches it - do not skip validation.

## Workflow

A title must be a real title. Taiwan's were generated by splitting the
description on `.`, which cut them mid-sentence and mid-number, and 67 of its 166
are still wrong - see `TODO.md`. Do not copy that pattern.

```bash
python site/validate.py greece     # one country
python site/validate.py            # all of them
python site/build.py               # validates, then renders to site/dist/
python -m pytest tests -q          # the code, not the data
```

Then commit the JSON and push. **Publishing is automatic**: the Deploy workflow
runs the tests, builds, and publishes to GitHub Pages at
`charlietrenorden.com/chronoscape/`, then fails if the live page is not serving
the version it just built.

Do **not** run `wrangler pages deploy` against `chronoscape-timeline`. That
project now serves only a `_redirects` file sending the old
`chronoscape.charlietrenorden.com` subdomain to the path above; deploying the
site over it would put two canonical copies back online.

## Sourcing the content

Both Greece and Peru were written by hand from general knowledge and checked
against Wikipedia, then emitted from a throwaway script holding the events as
compact tuples - far easier to review and reorder than raw JSON, and it makes
the `width_pct` sum and the sort trivial to get right. The scripts were not
kept; the JSON is the artefact.

An automated Wikipedia-to-JSON pipeline existed (`pipeline.py`) and was deleted
with the Supabase backend. `TODO.md` records what bringing it back would take.
