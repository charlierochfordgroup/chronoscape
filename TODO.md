# TODO - Chronoscape (multi-country history timeline)

Last updated: 2026-08-20
Current branch: `master` (also the GitHub default). Streamlit is gone - see Deployed below.
GitHub: `charlie-tren/chronoscape`
Deployed: **https://charlietrenorden.com/chronoscape/** - the static build (`site/`) on
**GitHub Pages**, published automatically by `.github/workflows/deploy.yml` on every push
to master. Migrated off Streamlit Community Cloud on 06/08/2026 (it slept after 12h of no
traffic), then off Cloudflare Pages on 20/08/2026. The old
`chronoscape.charlietrenorden.com` subdomain still resolves and 301s here; the Cloudflare
project `chronoscape-timeline` serves nothing but that redirect. **Do not run
`wrangler pages deploy` against it** - see the header of `deploy.yml`.

Thirteen countries: Australia, China, Egypt, Greece, Iceland, India, Ireland, Italy,
Japan, Mexico, Norway, Peru, Taiwan. Data in `countries/*.json`.

`/` is NOT a picker. It renders the `DEFAULT_COUNTRY` timeline (currently Taiwan) from
`site/build.py`, with the canonical pointing at `/taiwan/` so the two copies are not rival
pages. The old `index.html.j2` welcome card is deleted.

Architecture: **no live database.** Country data is checked into `countries/<name>.json`
and rendered to static HTML by `site/build.py`. Supabase was retired 2026-07-03 (the
free-tier project quota was needed for `rochford-news-monitor`, and this data is small and
read-only) and `db.py` went with the Streamlit app in `83384d6`.
Adding a country: see `countries/README.md`. Tests: `python -m pytest tests -q`.

---

## Outstanding

- [ ] **The retired subdomain never became a redirect - it is still serving a stale second
      copy of the whole site.** Found 26/08/2026 at a hub wrap. `deploy.yml`'s header says
      this was RESOLVED on 20/08/2026, with `chronoscape-timeline` reduced to a `_redirects`
      file that 301s to `charlietrenorden.com/chronoscape/:splat`. It is not doing that.
      MEASURED, not inferred:
        - `curl -I https://chronoscape.charlietrenorden.com/` returns **200, no Location
          header**. Following it lands back on the subdomain, not the canonical URL.
        - That copy is genuinely OLD: no Australia (added the same morning in `0a2a73a`)
          and no `beacon.charlietrenorden.com/b.js` (added in `24a959c`). 173,879 bytes
          against the canonical page's 172,962.
      LIMITED DAMAGE, worth stating so this is not over-read: both copies declare the SAME
      `<link rel="canonical">` pointing at `charlietrenorden.com/chronoscape/taiwan/`, so
      the duplicate-canonical problem the 20/08 change was fixing has NOT come back. The
      harm is a visitor arriving on the old URL getting a stale site that reports no
      returning-visitor data.
      THE FIX IS THE ONE THIS REPO ALREADY PRESCRIBES: deploy a directory containing ONLY
      `_redirects` to `chronoscape-timeline`. Do NOT `wrangler pages deploy site/dist`
      against it - see the `deploy.yml` header for why that recreates the worse problem.
      NOT DONE HERE because it is a Cloudflare deploy against a project this repo's own
      workflow deliberately holds no token for.
      THE CLASS WORTH REMEMBERING: a comment saying a thing was resolved is not evidence
      it is resolved. This one had been wrong for six days and the header read as settled.


- [x] **Two dead Supabase secrets on this repo.** DELETED 14/08/2026. `SUPABASE_ANON_KEY`
      and `SUPABASE_URL` (set 19/05/2026) were removed with `gh secret delete` after
      grepping the whole repo - no code, template or workflow referenced either, and
      `deploy.yml` is the only workflow left. `CLOUDFLARE_ACCOUNT_ID` is now the only secret.
      Note this removed them from **GitHub**, not from Supabase: the underlying project
      `xbhhdpcbrsgmactfuxlq` is paused, and deleting it is still a dashboard job (below).
      The anon key is public-by-design anyway, so this was hygiene rather than a leak.

### The site is now live TWICE, at two URLs, each claiming to be canonical (found 20/08/2026)

This supersedes the framing of the two items below, which were written when the
question was "which Pages project" rather than "which URL".

- [x] **Decide which URL is the site, and stop the other being indexed.** DONE 20/08/2026 - kept the Pages path, turned the subdomain into a 301. Detail below was the position before the fix. Both of
      these serve a complete, current copy:
        - `https://chronoscape.charlietrenorden.com/` - Cloudflare `chronoscape-timeline`,
          direct upload, needs a hand `wrangler` deploy on every push.
        - `https://charlietrenorden.com/chronoscape/` - GitHub Pages, auto-deploys on
          push, added by another session on 20/08/2026.
      Each serves `robots.txt` with `Allow: /`, its own `sitemap.xml`, and a
      `<link rel="canonical">` pointing at ITSELF. That is duplicate content: a search
      engine will pick one arbitrarily and split whatever authority the pages have.
      Nothing about this is recorded elsewhere, and no redirect exists between them.

      **The evidence already points one way.** The hub card was repointed to
      `/chronoscape/` by another session, with a comment in `index.html` saying the
      subdomain serves a stale build. The `personal-site-style` skill states the house
      pattern outright: every project is a subdirectory of `charlie-tren.github.io`,
      not a Cloudflare subdomain, and names Chronoscape's split as the cautionary tale.

      **Recommendation: retire the Cloudflare project and keep `/chronoscape/`.** It
      removes the CLOUDFLARE_API_TOKEN requirement, the hand deploy, and the duplicate
      indexing in one move, and matches the pattern every other project follows. The
      cost is the nicer subdomain URL. If the subdomain is kept instead, it needs the
      token AND a canonical pointing at the survivor from the copy that loses.

      Either way six files reference the subdomain and would need updating:
      `deploy.yml` (three places, including the drift check), `site/build.py`
      (`SITE_URL` default), `site/README.md`, and `tools/make_og_image.py`.

- [x] **There are TWO Cloudflare Pages projects for this repo - consolidate to one.**
      SUPERSEDED 20/08/2026 - neither serves the site now, so which one is Git-connected
      no longer matters. `chronoscape-timeline` serves a redirect; the other is unused.
      The `CLOUDFLARE_API_TOKEN` this depended on is no longer needed by anything.
      Original analysis kept below for the account-access finding, which still holds.
      Confirmed 07/08/2026 by comparing the version footer across hostnames:
        - `chronoscape-timeline.pages.dev`  -> v3.49   (direct upload via wrangler; the
          custom domain points HERE, so this is what visitors get)
        - `chronoscape-8m5.pages.dev`       -> v3.50   (project `chronoscape`, Git-connected,
          auto-deploys on push, currently has no custom domain)
      The split is why the live domain lagged the repo: the domain is served by the project
      that does NOT rebuild on push.

      **CORRECTION 14/08/2026 - the two projects are in DIFFERENT Cloudflare accounts.**
      This item previously said both were in the gmail account, and that is wrong. Queried
      via the API with the stored wrangler OAuth:
        - gmail account `44cfa6587359438d51d8066072439432` holds exactly two Pages projects,
          `chronoscape-timeline` and `site-stats`. `chronoscape-timeline` carries the custom
          domain `chronoscape.charlietrenorden.com` and has `source: null` (direct upload).
        - `GET /accounts/44cfa.../pages/projects/chronoscape` returns **404**, and
          `GET /accounts` lists only this one account. So the Git-connected `chronoscape`
          project - live and current at `chronoscape-8m5.pages.dev` - sits in an account
          this credential cannot see.
      That kills option (b) as a thing anyone can do from this machine: you cannot attach
      the domain to a project in an account you have no token for. Whoever owns that other
      account would have to do it, or the project would have to be recreated in the gmail
      account.

      **The fix that is actually reachable: finish wiring `deploy.yml`.** Everything lives
      in the gmail account already, so publishing from CI sidesteps the split entirely and
      makes it irrelevant which project is Git-connected.
        - `CLOUDFLARE_ACCOUNT_ID` - **already set 14/08/2026** (it is an account identifier,
          not a credential).
        - `CLOUDFLARE_API_TOKEN` - **still needed, Charlie only.** Create at
          https://dash.cloudflare.com/profile/api-tokens with the **Cloudflare Pages: Edit**
          permission on the gmail account, then:
            `gh secret set CLOUDFLARE_API_TOKEN -R charlie-tren/chronoscape`
          An agent must not create or handle the token value.
      Once that lands, every push to `master` builds and publishes to the custom domain, and
      the manual `wrangler pages deploy` step below is no longer needed.

      Older framing, kept because it still describes the shape of the problem:
        (a) Connect Git on `chronoscape-timeline` (see the item below) and delete
            `chronoscape`; or
        (b) Move the custom domain onto `chronoscape` - NOT POSSIBLE from here, see the
            correction above.

      **All three agent-driveable routes are now closed - tested 14/08/2026, do not retry:**
        1. *Move the domain to the Git-connected project* - the project is in another
           Cloudflare account (404 + single-account `GET /accounts`). Needs that account.
        2. *Create a Git-connected project in the gmail account via the API* - `POST
           /pages/projects` with a `source.type=github` returns **error 8000011, "There is an
           internal issue with your Cloudflare Pages Git installation"**. No Pages GitHub App
           installation exists on that account, and the API cannot create one. Nothing was
           left behind by the attempt. Only the dashboard's "Connect to Git" can fix this,
           and that is a GitHub OAuth grant, which an agent must not perform.
        3. *Mint a Cloudflare API token programmatically* - deliberately not attempted.
           Creating and storing a credential is Charlie's to do.
      So the single remaining action really is: create the token, `gh secret set
      CLOUDFLARE_API_TOKEN`. Everything else is done.

      Until then, `deploy.yml` measures the drift on every push and reports it in the
      "Not deployed" annotation ("live is N versions behind"), so a stale domain announces
      itself instead of going unnoticed for months as it did between May and August.
      Diagnostic note for next time: a direct-upload Pages project emits **no GitHub
      check-runs**, so scanning commit check-runs will not reveal it. List the projects via
      `/api/v4/accounts/<id>/pages/projects` instead.
      **11/08/2026 - the case for (b) is now much stronger, and it is measured.** Pushing the
      favicon fix (`aa473ec`) to `master` auto-deployed the Git-connected project and it is
      fully correct there: `/`, `/taiwan/`, `/iceland/`, `/ireland/` and `/sitemap.xml` all
      200, and the new icon serves.
      **So visitors sit N versions behind the repo, and every fix will keep missing the
      live domain until this is done.** (b) is a domain move onto a project already proven
      complete and current - not a migration.
      **14/08/2026 - the split bit for real, and was hand-patched.** Charlie asked why Japan
      and Egypt were not visible. They were committed (`5898ea4`), built and serving 200 on
      `chronoscape-8m5` - but the custom domain was on v3.51 and 404ed both. Fixed by a manual
      `wrangler pages deploy` (below); the domain now serves all five at v3.63 and
      `/favicon.ico` 200s. **That was a patch, not the fix - the split is still there and the
      next push will strand the domain again.** Do (b).
      **A manual deploy IS possible from the `charl` machine - the earlier note that it was
      not is wrong.** There is a stored wrangler OAuth token at
      `%APPDATA%/xdg.config/.wrangler/config/default.toml` with `pages:write` scope. It carries
      a `refresh_token`, and wrangler renews it silently even when `expiration_time` has long
      passed (it was ~20h stale on 14/08 and the deploy still went through with no browser
      prompt). So do not read an expired `expiration_time` as "no credential". The command:
        `python site/build.py && npx -y wrangler pages deploy site/dist --project-name chronoscape-timeline --commit-dirty=true`
      No `CLOUDFLARE_API_TOKEN` env var is needed for that path. Per
      `feedback-machine-scoped-findings` this is a statement about THIS machine only.
      **Edge-cache tail:** right after a deploy, a path that previously 404ed can keep 404ing
      on the custom domain for a minute or two while the old 404 ages out (`cf-cache-status:
      DYNAMIC`). `/egypt/` did exactly this on 14/08 and cleared itself. Confirm against the
      `*.pages.dev` host and `/sitemap.xml` before calling a page genuinely missing.
      **A deploy workflow now exists** (`.github/workflows/deploy.yml`, added 11/08/2026) so
      this needs no dashboard at all. It builds on every push to `master` and publishes to
      `chronoscape-timeline` with `wrangler`. It is inert until TWO repo secrets are set:
        `gh secret set CLOUDFLARE_API_TOKEN -R charlie-tren/chronoscape`
        `gh secret set CLOUDFLARE_ACCOUNT_ID -R charlie-tren/chronoscape`
      The token needs the **Cloudflare Pages: Edit** permission. **Charlie sets these - an
      agent must not create or handle the token value.** Until then the build still runs and
      the run goes GREEN, but it writes a "Not deployed" warning annotation rather than
      skipping silently, so a green tick can never be misread as published (same principle as
      the Consensus Drift publish guard).
      Once the secrets are in, the pending favicon fix (`aa473ec`) publishes on the next push
      with no further work.
      **Wrong-hostname trap, cost me a probe:** the Git-connected project's host is
      `chronoscape-8m5.pages.dev`, NOT `chronoscape.pages.dev`. The latter exists, returns
      200, and serves a COMPLETELY DIFFERENT site (uppercase "CHRONOSCAPE", `/logo.png`), so
      probing it looks like a real answer and is not. Read the hostname off this item rather
      than guessing it from the project name.

- [x] **Connect Git auto-deploy on Cloudflare Pages.** SUPERSEDED 20/08/2026 - auto-deploy
      now happens on GitHub Pages, which needs no credentials. Original text below. The project was created by direct
      upload (`wrangler pages deploy`), so it does NOT rebuild when this repo is pushed.
      Adding a country currently needs a manual redeploy:
        `python site/build.py && npx wrangler pages deploy site/dist --project-name chronoscape-timeline`
      To automate: Cloudflare dashboard -> Workers & Pages -> chronoscape-timeline ->
      Settings -> Builds -> Connect to Git, branch `master`, build command
      `pip install -r requirements-build.txt && python site/build.py`, output `site/dist`.
      Dashboard-only - wrangler has no command for it. About five clicks.
      If the Python version trips the build, set `PYTHON_VERSION=3.13.3` in the project's
      build environment variables.
      **NOT DONE BY AN AGENT ON PURPOSE (10/08/2026).** "Connect" opens a **GitHub OAuth
      grant**, handing Cloudflare persistent access to the repositories. That is a
      third-party authorisation rather than a config toggle, so it needs Charlie's own hand
      even when the rest of a dashboard job has been delegated. Everything after the grant -
      branch, build command, output directory - is fine to automate.

- [x] **Confirm the map panel renders in a real browser.** CLOSED 12/08/2026 - it renders.
      Served over http to a real Chrome, the Japan page paints coastline, place names and
      the era-coloured event markers, and `#map canvas` exists. This corroborates the
      10/08 Playwright capture of `/iceland/`; the original report was a false alarm twice
      over. Two separate artefacts produced the blank captures: headless not painting WebGL
      without a settle delay, and `file://` refusing the ES-module import of `app.js` (which
      blanks the timeline as well as the map). **Always verify this site over http, never
      `file://`.** Not a regression - do not rewrite the map.

- [x] **No `og:image` anywhere.** DONE 14/08/2026 - one static 1200x630 card at
      `site/static/og.png`, generated by `tools/make_og_image.py` (committed PNG, not a
      build step) and wired into `country.html.j2` with an absolute `{{ site_url }}` URL,
      `og:image:width/height/alt` and `twitter:card: summary_large_image`. Per-country
      cards were rejected: seven files to regenerate whenever the wordmark moves, for a
      thumbnail most people never look at twice. The card deliberately carries no country
      list, so it does not go stale when an eighth lands.
      Original note, 12/08/2026: neither template emits one and
      `twitter:card` is `summary`, so every link shared to Slack, WhatsApp or LinkedIn
      renders as text with no picture. Cheapest fix is one static 1200x630 card for the whole
      site; the better one is per-country, which the build could generate from the era
      palette without adding a dependency. Bump `twitter:card` to `summary_large_image` at
      the same time, and remember the URL must be absolute (`{{ site_url }}/...`) - relative
      og:image URLs are ignored by most scrapers.

- [ ] **Verification gotcha, cost me a wrong conclusion on 12/08/2026.** Chrome caches ES
      modules SEPARATELY from the normal HTTP cache, so a reload with cache disabled still
      re-executes the OLD `app.js`. I changed the map code, reloaded with `ignoreCache`,
      saw no change and reported the fix as not working - it was working; the browser was
      running the previous module. Cache-busting the **page** URL (`/japan/?bust=1`) forces
      a fresh module graph. Applies to checking the live site after a deploy too: a hard
      refresh is not proof that a change shipped. Confirm against the version footer.

- [ ] **The hub card reads "In progress" - and that is now a DECISION, not an oversight.**
      I flipped it to `s-live` / "Live" on 17/08/2026 (`5d2940d`), on the grounds that seven
      countries on a custom domain cleared the bar this item set. It was deliberately put
      back 42 minutes later by `9de2e67` "Reorder the project cards; Chronoscape back to In
      progress", and three later commits build on that ordering - the hub now sorts
      "In progress" cards last, so the status also drives position on the page.
      **Do not re-apply the flip.** If Chronoscape should read Live, that is Charlie's call
      to make in the hub repo, and it needs the card reordering to be considered with it.
      (Unrelated and healthy: the hub's weekly `Refresh card thumbnails` workflow last ran
      16/08/2026, so the card's screenshot keeps itself current either way.)

- [x] **Japan and Egypt are not live until a deploy runs.** DONE 14/08/2026 - published by
      hand with wrangler; all seven countries now 200 on the custom domain. The underlying
      cause (no auto-publish) is still open above. Original note: They are committed here, but
      the custom domain is served by the direct-upload project, so the two new timelines -
      and the new landing page, the Oswald wordmark and the bigger map - will not appear
      until either the two repo secrets above are set (then `deploy.yml` publishes on the
      next push, no further work) or someone runs the manual `wrangler pages deploy`.


### Test coverage - no test suite exists (added 07/08/2026, estate-wide test audit)

- [x] **Add tests for the two surviving modules.** DONE 14/08/2026 - `tests/` has 39
      pytest tests over `build_segments`, `proportional_position`, `match_era`, `version()`
      (all three shallow-clone branches) and the validator's error/warning split. Wired
      into `deploy.yml` ahead of the build, and mutation-checked: four deliberate bugs were
      each confirmed to turn the suite red. Original note:  The migration is done - the
      Streamlit app was removed in `83384d6`, so the surface is now just
      `site/build.py` and `site/validate.py`. That makes this small and worth
      doing now rather than deferring: five pure functions and a validator.

      - `build_segments(eras, events)` - the timeline layout. Assert event-to-era
        assignment and ordering against a fixture, including an event that falls
        on an era boundary and one that matches no era at all.
      - `proportional_position(sort_year, year_start, year_end)` - the positioning
        maths. Assert the endpoints, the midpoint, a BC (negative) year, and a
        zero-width range (which should not divide by zero).
      - `match_era(event_era, era_names)` - assert the miss case returns something
        sane rather than raising.
      - `validate(data, label)` - it is the build gate, so test that it actually
        FAILS a malformed country rather than passing it through. Cover a missing
        required key, a bad year type, and an event outside every era. Assert the
        errors/warnings split, not just that something was returned.
      - `version()` - it reads git and has already shipped one bug on a shallow
        clone (fixed in `b0a1c38`). Test the shallow-repo branch, since Cloudflare
        builds are shallow and this is the code path that broke in production.

      NOTE: the header block at the top of this file is stale post-migration - it
      still describes the Streamlit Cloud deploy and `db.py`. Worth a tidy.

### MIGRATION PLAN: Streamlit -> static site (written 2026-08-05, after the spike)

Stack decided, proven, and now built in `site/`: **Python + Jinja2 -> static HTML,
MapLibre + OpenFreeMap for the map, ported vanilla JS for the timeline, hosted free
on Cloudflare Pages.** No database, no auth, no JS toolchain - accounts were dropped
on 2026-08-05 (see phase 5), so this is the final shape rather than a stepping stone.

**Deploy mechanism resolved:** Cloudflare Pages' build image ships **Python 3.13.3**
and can run `pip install` plus a build script, so the whole thing builds natively on
Cloudflare with **no GitHub Actions workflow file**. That matters practically - the
agent's GitHub token lacks `workflow` scope and local `gh` is not logged in, so any
`.github/workflows/*` change needs the web editor. Cloudflare-native build avoids it.

**Design decision - the COUNTRY page is the indexable unit, not the event.** One page
per event would be ~6,500 pages at 50 countries and ~25,900 at 200, past the ~5,000
where `next build`-class tooling starts to struggle, for pages of one paragraph each.
So: 200 country pages for SEO, and events get `#event-<id>` hash deep links for
sharing. This is a change from the earlier loose talk of "200+ indexable pages" -
the win is 1 -> 200, not 1 -> 26,000.

#### Phase 1 - turn the spike into a real site  ** DONE 2026-08-05 **
- [x] Promoted `spike/` -> `site/`.
- [x] **Hash deep links** - `/taiwan/#event-80` opens with that event selected; `replaceState` so 166 clicks do not bury the back button; clearing selection strips the hash. Verified in-browser.
- [x] **Canonical + Open Graph + Twitter card** on country and landing pages. `SITE_URL` env var overrides the origin for preview builds.
- [x] **`sitemap.xml` + `robots.txt`** generated by the build.
- [x] **404 page** (`/404.html`, which Cloudflare Pages serves automatically), listing the available timelines.
- [x] **`site/validate.py`, wired as a build gate** - bad data fails the build. Verified by injecting a bad era_name and a bad category: build refused. Splits errors (fail) from warnings (report).
- [x] **A11y** - visually-hidden timeline instructions wired via `aria-describedby`, `.visually-hidden` utility, keyboard help text. The server-rendered event list already serves as the text alternative.
- [x] Favicon: SUPERSEDED 11/08/2026 - a real favicon shipped (`site/static/favicon.svg` + PNG/ICO), replacing the inline emoji data URI this line settled for.

**Two things worth knowing from doing it:**
- The validator initially flagged 12 "problems". Six were a **bug in the validator**, not the data: `sort_year` carries a fraction to order events within a year (1944.4 = May 1944) and was being compared against an integer era end. The other six are **legitimate editorial placements** - precursor events sitting in the era they belong to narratively (Iceland's pre-874 voyages, Taiwan's Koxinga-father events). Hence errors vs warnings. The data was not touched.
- Accounts were dropped from the roadmap on 2026-08-05, which **settles the framework question permanently** - they were the only argument for Astro or Next over plain Python + Jinja. No future migration pressure.

#### Phase 2 - deploy
- [x] Create the Cloudflare Pages project against the repo. DONE - project `chronoscape`, Git-connected, host `chronoscape-8m5.pages.dev`. Build command `pip install -r requirements-build.txt && python site/build.py`, output dir `site/dist`.
- [x] `requirements-build.txt` and `.python-version` added.
- [x] Point **`chronoscape.charlietrenorden.com`** at it. DONE - returns 200 and serves the static build. Note it is attached to the OTHER Pages project (`chronoscape-timeline`), so it only updates on a manual `wrangler pages deploy`; last done 14/08/2026, footer v3.63, all five countries 200.
      Original note: DNS is already at Cloudflare, so this is a CNAME and automatic TLS. (A path like `/chronoscape` on the hub is harder: GitHub Pages serves the hub at the apex and a real subpath needs a proxy that breaks the cert. Subdomain is the clean answer.)
- [ ] **Verify the TIMELINE DRAG on a real phone.** Narrowed 17/08/2026 from the old vague
      "verify on a real phone" - most of it is now done, and what is left is one specific
      question you can answer in ten seconds.
      **Checked and passing** (Playwright device emulation against the live site, iPhone 13 /
      Pixel 7 / iPad Mini, `/`, `/greece/`, `/peru/`): no horizontal page scroll anywhere, map
      canvas renders, chips wrap onto two rows on phones, full event list present, touch
      pointer detected. The `.tl-*` elements do extend past the viewport, but that is the
      6000px ribbon inside its own `overflow-x` container and does not scroll the page.
      **The open question: does dragging the timeline move about right, or fly?**
      `#tl-container` has NO `touch-action`, and `pointermove` sets `scrollLeft` with a **1.5x
      multiplier** (`app.js`). On a touch device the browser may also pan the container
      natively, and the two would compound - roughly 2.5x finger travel, which feels broken.
      I could not settle this: CDP touch events do not produce native scrolling in headless
      Chromium. Proved by controls - the same synthetic drag moved page `scrollY` 578 -> 578
      and `.list-pane` `scrollTop` 0 -> 0, i.e. nothing, while the timeline still moved 150px
      for a 120px drag purely via the JS handler. So the JS drag definitely works on touch;
      whether native panning adds to it is untestable this way.
      **If it does fly, the fix is one line** in `style.css`:
        `.tl-container { touch-action: pan-y; }`
      which stops the browser panning it horizontally and leaves the JS as the only driver,
      while still letting a vertical swipe scroll the page. NOT applied blind: if some browser
      does not deliver pointer events for touch, removing native panning would make the
      timeline completely unscrollable there, and I cannot test Safari from here. A worse
      failure than the one it fixes, so it wants your thumb on a real screen first.

#### Phase 3 - cut over
- [x] Run both in parallel for ~a week. SUPERSEDED - the Streamlit app was deleted outright rather than run alongside.
- [x] Update the hub card/link to the new domain. DONE - the hub's `index.html` links to `chronoscape.charlietrenorden.com/`. Verified 12/08/2026.
- [x] Delete the Streamlit app. DONE - verified 12/08/2026, none of these files exist: `app.py`, `db.py`, `styles.py`, `data_parser.py`, `event_data.py`, `event_list_component.py`, `map_component.py`, `timeline_component.py`, `timeline_files/`, `requirements.txt`, `taiwan_timeline.md` - about **2,090 lines**. Keep `countries/*.json` (the data) and `PLAN.md`/`TODO.md` (the history).
- [ ] Delete the Streamlit Cloud app. **This also retires the CARTO basemap problem** below, since the new site is on OpenFreeMap.
- [x] `.github/workflows/keep-alive.yml` removed. DONE - verified 12/08/2026, `.github/workflows/` now contains only `deploy.yml`. It was dead weight (Supabase retired 2026-07-03) - remove it in the same pass. Needs the web editor, per the scope note above.

#### Phase 4 - the content workflow (this is what makes 50+ countries actually happen)
- [x] DONE 14/08/2026 - `countries/README.md`. Write down the repeatable process for adding a country: source -> structured JSON -> validate -> commit -> auto-deploy. Ireland was built ad hoc; that does not scale to 50.
- [x] DONE 14/08/2026 - `countries/README.md`, written straight after doing Greece and Peru. Nail the conventions in one place: 10 eras, `width_pct` summing to 100, palette colours in order, ~35-40% of events flagged `is_major`, era names matching exactly (see the Taiwan normalisation), coordinates only where genuinely known.
- [x] **DONE 14/08/2026 - `tools/new_country.py`.** Emits ten eras on the house palette with `width_pct` already summing to 100 and one placeholder event per era, so the file validates and the page renders immediately; then runs the validator. Landed in `tools/` rather than `scripts/` to sit with `make_og_image.py`, since neither is part of the build.
- Japan and Egypt (12/08/2026) were written as throwaway generator scripts: a flat list of
  `(era, sort_year, display_date, title, description, categories, lat, lng)` tuples, plus an
  explicit `MAJOR = {...}` set of titles, dumped with `json.dumps(indent=2,
  ensure_ascii=False)`. Two things that pattern got right and are worth keeping in the
  scaffold: assertions in the generator (widths sum to 100, sorted by `sort_year`, no
  duplicate titles, every `MAJOR` name matches a real event), and choosing the key events
  as a **named list** rather than flagging them while writing - flagging by feel produced
  63% majors on the first pass, which makes the stars meaningless.

#### Phase 5 - accounts: **DROPPED 2026-08-05**
Charlie decided accounts are not wanted. This removes the only reason to consider
Astro or Next over plain Python + Jinja, and removes the need for Neon and Clerk
entirely. The site stays fully static and fully free. The auth research below is
kept only in case this is ever revisited.

**Rough effort:** phase 1 is a solid session, phase 2 an hour or two mostly waiting on DNS, phase 3 trivial once soaked. Phase 4 is the one that pays off repeatedly.

### Basemap licensing: the app is currently outside CARTO's terms (found 2026-08-05)

`map_component.py` uses `tiles="cartodbdark_matter"`, i.e. CARTO's hosted basemap service. CARTO changed its licence on **2025-10-16** (commit `c2b1c18` on `CartoDB/basemap-styles`, amended 2025-11-11): access to the hosted tile service is now "restricted to CARTO enterprise customers and Non-Profit GRANTS only and is **not available for free public use**". The style code (BSD-3) and design (CC-BY) are still open - only the hosted tiles are restricted.

The tiles **still serve** (verified HTTP 200 on 2026-08-05), so nothing is visibly broken. But this is exactly the kind of thing that gets rate-limited or 403'd without warning, and it is a live term-of-service issue on a public site, not a hypothetical.

- [x] **DONE - already on OpenFreeMap, so the CARTO terms problem is gone.** Verified 17/08/2026 in `site/static/app.js` and in the live bundle: the style URL is `https://tiles.openfreemap.org/styles/dark`. (Recorded as done on 14/08 too, but that edit silently missed - the search string omitted the markdown bold and `str.replace` matched nothing. Assert your replacements.) Original note: Move to OpenFreeMap (no key, no account, no limits) or another genuinely-free provider. Note every free dark basemap in 2026 is **vector-tile only**, which needs MapLibre - so on Streamlit this is awkward, and it is a further argument for doing the Next.js migration rather than patching folium. Interim option if staying on Streamlit: a raster OSM style, accepting it will not be dark.

### The alternative that was never tested: just rehost Streamlit (researched 2026-08-05)

Before committing to a rewrite, the cheap option was finally evaluated. It is stronger than expected and the framing in this TODO was wrong: **four of the five complaints are Streamlit COMMUNITY CLOUD problems, not Streamlit problems.**

- Community Cloud **sleeps after 12 hours** of no traffic (not days), has **no custom domain support at any tier** (only `*.streamlit.app` subdomains), is **US-only**, and rate-limits GitHub-triggered updates. The stalled deploys are a known, widely-reported issue, not something we were doing wrong.
- **US-only hosting matters a lot here**: from Australia every interaction pays ~200-300ms RTT *before* Python runs. Hosting in Sydney would cut the per-click latency substantially on its own.
- **Rehosting = about half a day and $3-7/mo. Verified: NO host offers a usable FREE always-on tier.** Render's free tier spins down after 15 min (~1 min cold start, cannot be disabled); Railway's free plan gives $1/mo of credit against ~$5/mo for 0.5 GB; **Fly.io removed its free tier entirely in Oct 2024** (2-hour trial only). Cheapest real always-on: **Fly ~$3.32/mo** (512 MB, no plan fee, but must set `auto_stop_machines="off"` and certs cost $0.10/mo), **Railway Hobby $5 + usage** (best-documented websocket support - explicitly exempt from all timeouts), **Render $7/mo** (simplest, never sleeps on paid, but Hobby bandwidth was cut to 5 GB in Apr 2026). Azure Container Apps ~$4-14; Cloud Run ~$46-50 (an open websocket is billed active all month); Hugging Face **deprecated the Streamlit SDK in Apr 2025** and now requires a paid plan for compute Spaces. Streamlit in Snowflake is enterprise-only (~$1,400+/mo always-on) - out of scope.
- **This is the structural point: "free" and "always-on" are incompatible for anything running a server process.** A free tier keeping a Python process warm 24/7 is giving away continuous compute, which is exactly why every free option sleeps. Static hosting is free AND always-on because there is no process.
- Streamlit self-hosting needs websocket support: proxy must forward upgrade headers, `_stcore` paths must be excluded from rewrites, sticky sessions are mandatory behind a load balancer, and `--server.enableCORS=false --server.enableXsrfProtection=false` is usually needed behind a proxy (fine read-only, a real relaxation once auth exists).

**What Streamlit genuinely fixed in 2025-26** (the gap narrowed more than this TODO assumed): **Components v2 (1.51, Oct 2025) made custom components frameless - no iframe**, Shadow DOM style scoping, bidirectional data flow. That directly addresses the timeline's awkward scroll/drag. Plus real theming config (no CSS hacks), horizontal flex containers (1.48), matured `st.fragment` incl. `parallel=True` (1.58), and Tornado replaced by Starlette/Uvicorn (1.57).

**What rehosting can NEVER fix:** (a) the rerun round-trip - every interaction re-executes the script server-side; fragments shrink the Python term, not the network term; (b) **mobile layout - `st.columns` auto-stacks below ~640px and there is still no breakpoint API. The feature request has been open since July 2022.**

**Decision: still go static, but the deciding factor is the budget constraint, not effort.** Rehosting is the better effort-to-benefit trade in isolation, but it costs $2-7/mo forever versus $0 forever for static hosting, and it can never fix mobile. Given "must be fully free" plus a public-facing portfolio site where polish matters, static wins. Rehosting remains the correct fallback if the rewrite stalls - and it is non-destructive, so it can be done first if the migration is going to take a while.

## SUPERSEDED - the framework question was answered by shipping (marked 14/08/2026)

> Everything from here to "If Anthropic-generated countries come back" is **history, not a
> backlog.** It was left as unchecked checkboxes, which reads as work queued up - it is not.
>
> The record settles it without needing a fresh decision: accounts were **dropped 2026-08-05**,
> which removed the only argument for Next or Astro over plain Python + Jinja2; the RE-OPEN
> note directly below listed "Python-generated HTML (Jinja2) + ~150 lines of vanilla JS" as an
> option; and that is precisely what was then built and shipped. The site has been live on it
> since 06/08/2026, now serving seven countries.
>
> Kept because the research is genuinely good - the Next.js 16 `proxy.ts` rename, the Clerk
> CVE, the `ssr: false` App Router trap, the react-leaflet staleness - and would be worth
> re-reading if a rewrite is ever revisited. **Do not treat any of it as pending.**

### ⚠️ RE-OPEN before scaffolding: is it actually Next.js? (2026-08-05)

The Astro rejection above was written when **on-demand generation and API routes were assumed**. That premise died on 2026-08-05 when generation was dropped. Two independent analyses have now concluded Next.js is overkill for "static JSON + one timeline + one map".

Options to weigh properly before running `create-next-app`:
- **Astro** - islands model, ships almost no JS, content collections fit `countries/*.json` exactly. Supports SSR + Clerk when accounts land.
- **Eleventy, or plain HTML + vanilla JS** - lowest ceremony.
- **Python-generated HTML (Jinja2) + ~150 lines of vanilla JS** for the two interactive bits. Plays directly to existing skills and avoids the JS toolchain almost entirely. Genuinely worth considering.
- **Next.js** - still the safest choice *if* accounts are definitely coming, since auth + SSR are first-class and Vercel integration is tightest.

Hosting is free on all of these (Cloudflare Pages / GitHub Pages / Netlify / Vercel), so the choice is purely about which is least painful to build and maintain. Note: whichever wins, the map still needs MapLibre (all free dark basemaps are vector-only) and the timeline is still hand-rolled SVG + `d3-scale` - those two decisions are framework-independent.

### Stack investigation: migrate to Next.js + Vercel before scaling up (2026-07-03, decisions resolved 2026-08-05)

Chronoscape is heading toward 50+ countries and user-facing features (search across countries, saved views, share links). Streamlit is fine for the current read-only shape but doesn't scale where the project is going: CSS scoping fights, no server-side API surface, no real auth story, mobile layout limits. Add to that the operational pain seen repeatedly on 2026-08-05 - **no custom domain** (so the personal site can only redirect), **deploys that stall and need a manual Reboot** (twice in one session), and the app **sleeping on inactivity**.

**Recommended target: Next.js on Vercel** (same pattern as `macro-signals-web`, already live). Fit at scale:
- **Content** - `countries/*.json` -> one dynamic route with `generateStaticParams()`, plain SSG on push. No ISR, no DB. See resolved decision 1.
- **User features** - Clerk for accounts + a small Neon Postgres for saved views and share links. See resolved decisions 2 and 3.
- **Perf** - edge caching, static shells. The binding constraint is the RSC payload, not Vercel.
- **Ecosystem** - largest React community, deepest AI-code-gen coverage, MapLibre for the map, hand-rolled SVG + `d3-scale` for the timeline.

*(Note: on-demand Anthropic generation was dropped from the roadmap on 2026-08-05 - too much work, and Wikipedia sources barely change. Countries are generated offline in batches and committed. This removes the write path entirely and is why no database is needed for content.)*

Rejected alternatives (documented so the decision doesn't get relitigated):
- **Astro** - great for read-only static, but loses to Next as dynamic features (generation API, auth, DB queries) enter the picture.
- **Vanilla HTML + D3 + Leaflet** - falls off past a few countries; no component model.
- **Observable Framework** - purpose-built for data storytelling but not for multi-page apps with auth.
- **SvelteKit** - technically a peer of Next but smaller ecosystem and Charlie has no Svelte experience.
- **T3 stack (Next + tRPC + Prisma + NextAuth + Tailwind)** - worth considering if the answer to "will there be user accounts + typed API calls" is a firm yes. Otherwise plain Next is enough.

**Decisions RESOLVED by research 2026-08-05.** Product intent confirmed same day: on-demand generation is OFF (too hard, and Wikipedia sources are near-static - countries get generated offline in batches and committed); user accounts ARE wanted; target 50+ countries; must fix domain / stalled deploys / sleeping / mobile.

**Budget constraint (2026-08-05): must be FULLY FREE at current scale.** Paying is acceptable only if the project actually grows into it. This is a real input to the architecture, not a footnote:
- Every piece of the recommended stack is free at this scale: Vercel Hobby (static hosting + custom domains + auto-deploy), Clerk (50k users), Neon (0.5 GB / 100 CU-hours), OpenFreeMap (no key, no account, no limits).
- **It also argues against the "just rehost Streamlit elsewhere" alternative.** "Free" and "never sleeps" are structurally in tension for anything running a server process - a free tier keeping a Python process warm 24/7 is giving away continuous compute, which is exactly why Streamlit Community Cloud sleeps. A static site is free AND always-on because there is no process. Always-on Python hosting generally costs a few dollars a month and still would not fix the per-interaction rerun latency.
- **One watch item: Vercel Hobby is licensed for personal, NON-COMMERCIAL use.** A portfolio project is fine. Ads, payments or client work would force Pro at $20/user/mo regardless of traffic.
- No cliff edges in this stack at realistic scale. Neon's first paid tier has had no monthly minimum since Dec 2025, so overage degrades to cents rather than a $25 step (which is what Supabase Pro would have been).

1. **Content model - keep JSON in git. No database for content, at any realistic scale.**
   The old "JSON stops scaling past ~50-100 countries" assumption was wrong by 1-2 orders of magnitude. Vercel has **no cap on statically generated pages**; the 2048 limit people hit is on the *routing table*, and one `app/[country]/page.tsx` with `generateStaticParams()` is ONE route entry whether it renders 3 countries or 10,000. Measured from our own data: avg country = 67 KB / 129 events, so 200 countries is ~13 MB and ~26k events. Build stays under a minute. Hard fail is a 45-min build, ~22x away.
   Move to a DB only when one of these fires: (a) cross-cutting queries across all countries (global search / "all events 1900-1950") - though the first fix is a pre-computed index JSON, not a DB; (b) someone other than Charlie edits content, or editing moves into a browser; (c) build exceeds ~10 min or `next build` OOMs (~5,000+ pages); (d) repo over ~500 MB including history; (e) content must change without a deploy.
   Discipline to adopt now: serialise with `sort_keys=True, indent=2, ensure_ascii=False`; validate against a JSON Schema **in the Python generator** so bad content never reaches git; `.gitattributes` with `*.json text eol=lf` on day one or Windows CRLF rewrites turn one-event changes into whole-file diffs. Optional later upgrade if hand-edited JSON starts costing time: **Velite** or **Content Collections** for build-time Zod validation + generated TS types (Contentlayer is abandoned - do not use).

2. **DB for USER data only - Neon, via the Vercel Marketplace.** Content stays static, so the DB holds only `users` / `saved_views` / `share_links`.
   - **Vercel Postgres no longer exists** - discontinued, folded into the Marketplace, existing stores migrated to Neon. Remove it from consideration.
   - **Neon** - 100 free projects (no org-wide cap), 0.5 GB + 100 CU-hours per project. Scales to zero after 5 min idle but **auto-wakes in ~sub-second on the next query**; hostname keeps resolving, no dashboard click. Paid tier has no monthly minimum since Dec 2025, so overage degrades to cents rather than a $25 step.
   - **Turso** is the runner-up and the only option that never idles at all (a DB is a file, not a process); $4.99/mo first paid tier. Cost: SQLite dialect, smaller ecosystem.
   - **Supabase stays rejected.** Both failure modes are still live policy: free projects pause after ~1 week with **manual-only** restore, and the free-project cap is **2 across the whole account**, not per org. This also explains why our keep-alive cron could never have worked: Supabase measures activity as *"user requests to the database"*, i.e. the Postgres query path - not HTTP hits on the project. A REST ping was never going to reset the timer.

3. **Auth - Clerk. Defer it to phase 2; ship the static site first.**
   **"NextAuth or Clerk" is no longer a live choice**: Auth.js/NextAuth was absorbed into Better Auth (Sep 2025) and is security-patch-only, and Auth.js v5 never went stable (npm `latest` is still 4.24.15, v5 at `beta.32` after 3 years). Vercel then acquired Better Auth (Jul 2026). Lucia is deprecated.
   - **Clerk** - 50,000 free MRU (tier changed Feb 2026; note MRU is narrower than MAU). No database or schema needed for auth itself, and no hand-written session / cookie / CSRF code. Best App Router docs. Accept: MFA is Pro-only ($25/mo), 7-day fixed sessions on free.
   - **Better Auth** is the runner-up if data ownership matters - MIT, now a Vercel property, ~6.6M weekly downloads. Cost: you provision Postgres and run migrations, and its CVEs cluster in *plugins*, so enable the minimum set.
   - Clerk user metadata is capped at **8 KB/user** (1.2 KB if in the session token), so saved views still need the Neon tables. Share links are not user-scoped anyway - an anonymous visitor resolves a token - so they need a real lookup table regardless.

**Security rules that must be followed once auth lands** (they do not apply to the static phase):
- **Middleware is NOT an authorisation boundary.** Beyond CVE-2025-29927 there have been six further Next.js middleware bypasses, the latest patched in 16.2.11. Enforce authorisation in the **data access layer** - a `verifySession()` wrapped in React `cache()`, called by every data function, Server Component, Server Action and Route Handler. Middleware does optimistic redirects only.
- **Next.js 16 renamed `middleware.ts` to `proxy.ts`.** Migrating without running `npx @next/codemod@canary middleware-to-proxy` makes route protection **silently stop running**.
- **Clerk CVE-2026-41248**: `createRouteMatcher` could be evaded. Declare which routes are **public** and protect everything else - never allowlist the protected ones.
- Do not put auth checks in a layout (layouts do not re-render on navigation and do not gate sibling segments).

**Migration checklist** (updated 2026-08-05 with research findings):

*Phase 0 - environment (Windows).* Verified: `C:\Users\charl\Documents` is a real local folder, NOT OneDrive-redirected, so Known Folder Move is off. But `C:\Users\charl\OneDrive\Documents` exists, so do not scaffold there - OneDrive + `node_modules` is an open, unfixed conflict (Files On-Demand placeholders break `stat`/`open`; per-folder exclusion is Group-Policy-only and arrives GA ~Aug 2026 for organisations, not personal accounts).
- Project at **`C:\dev\chronoscape-web`**, outside OneDrive.
- Add `C:\dev` to **Microsoft Defender exclusions** - this is step 1 of Next.js's own local-development guide.
- **Node 24 LTS** (Node 20 is EOL and Vercel deprecates it 2026-10-01; Vercel's default is 24.x). `fnm` if you want a version manager - **Volta is unmaintained**, nvm-windows is mid-rewrite. A plain MSI install of Node 24 is also fine for one project. Pin with `.node-version` + `"engines": {"node": "24.x"}` so local matches Vercel.
- `git config --global core.longpaths true`.
- **Skip WSL2.** Microsoft's own docs recommend native Windows for JS beginners, and Turbopack uses native NTFS watching so HMR is fine.

*Phase 1 - static site (no DB, no auth).*
- `npx create-next-app@latest --typescript --app` (Next 16.3: App Router, RSC and Turbopack are all default).
- Copy `countries/*.json` across as-is - same shape.
- `app/page.tsx` (chip picker), `app/[country]/page.tsx` + `generateStaticParams()`. **`params` is async in Next 16** (`const { country } = await params`) - most tutorials and AI-generated code predate this.
- Load the countries directory ONCE into a module-level cache in `lib/content.ts`; do not re-read files per page.
- **Slim the data before it crosses into any `'use client'` component.** This is the real perf bottleneck, not Vercel: a 150 KB country JSON serialised into the RSC payload is downloaded by every visitor. Bites at 3 countries, not 200.
- **Map: MapLibre, not Leaflet.** `maplibre-gl@6` + `react-map-gl@8` (`react-map-gl/maplibre`). react-leaflet has not shipped a release in 20 months and Leaflet core in 3 years, its Next.js `window is not defined` issue has been open since Jan 2025, and it is pure ESM so it needs `transpilePackages`. Render the ~50-200 markers as a **GeoJSON source + `circle` layer** with one `map.on('click', ...)` handler, not N React `<Marker>` nodes. Remember `import 'maplibre-gl/dist/maplibre-gl.css'`.
- **Basemap: move off CARTO** (see the separate item below - this is a live licensing problem, not just a migration task). Use **OpenFreeMap** (`https://tiles.openfreemap.org/styles/dark`) - unlimited, no API key, no account. Two caveats: no SLA, and its style JSON has `attribution: null` so you must add the credit manually via `AttributionControl customAttribution="OpenFreeMap © OpenMapTiles Data from OpenStreetMap"`. Fallback if it ever dies: self-hosted Protomaps PMTiles on Cloudflare R2 (needs HTTP range requests - Vercel is not a supported PMTiles host).
- **`ssr: false` is NOT allowed in a Server Component in the App Router** - it throws a build error. Needs a three-file sandwich: `page.tsx` (server) renders `MapLoader.tsx` (`'use client'`, does the `dynamic(..., {ssr:false})`) which renders `Map.tsx` (`'use client'`). Any tutorial putting `dynamic(..., {ssr:false})` straight in `page.tsx` is pre-App-Router.
- **Timeline: hand-rolled SVG + `d3-scale` only** (`scaleTime`, ~16 kB). Rejected: react-chrono (wrong shape, explicitly no zoom/drag), vis-timeline (imperative, 10 peer deps incl. deprecated `moment`), Nivo (15 months stale, no timeline primitive), full D3 (fights React for DOM ownership), visx (viable but an extra abstraction for one component). "D3 for maths, React for DOM" is still the 2026 consensus. Being weak at React argues *for* hand-rolling - one thing to learn, not two. `scaleTime()` is basically `np.interp` with a nicer API.
- Timeline a11y from the start: **roving tabindex** (container `tabIndex=0`, dots `tabIndex={i===active?0:-1}`, arrows/Home/End) - this also makes keyboard focus auto-scroll the strip for free; `role` + `aria-label` on each dot (SVG shapes have no implicit name); `aria-selected`; tooltip on **focus** as well as hover; keep native `overflow-x:auto` under the drag handler; add a visually-hidden `<ul>` of the same events as a text alternative.
- Reuse the dark theme + Inter + cyan accent; Tailwind absorbs the tokens from `styles.py DARK_CSS`.
- Deploy: connect the repo in Vercel. **Plain SSG on git push - no ISR** (ISR solves content changing between deploys, which we do not have, and it is incompatible with static export). Hobby is 1 concurrent deployment / 100 per day.
- Consider staying **static-export-compatible** as a discipline (no Server Actions, no middleware, no rewrites): it keeps the app portable and permanently outside the entire class of Next.js server CVEs.
- Confirm parity on Taiwan, then Iceland + Ireland, then point the domain at Vercel. Keep Streamlit live during the swap; soak a week.

*Phase 2 - accounts (only after phase 1 is live).* Clerk + Neon, following the security rules above.

- Once retired, archive the Streamlit repo (the JSON files stay useful as the data source either way).

**When to trigger:** Before the next substantive feature push. Doing more work in the Streamlit shell now creates rework at migration time. If a new country is the next task, migrate first, then add the country in Next.

### UI ideas reviewed 17/08/2026 - the ones NOT taken

A design pass produced five items. Charlie took the two biggest (era colour on key events,
visible era bands) plus the subtitle bug and the column rebalance, all shipped. These are
the remainder, kept because they were assessed rather than imagined - each was looked at on
the live page:

- [ ] **The search box is ~40% of the filter row** for a control most visitors never touch.
      Halving it would give the era and category selects room and calm the row down.
- [ ] **Eyeball `default_zoom` on the other ten countries.** Added 26/08/2026. China, India
      and Australia all shipped at 4 and all three opened on a province rather than a
      country; they are now 3, and `countries/README.md` records the calibration. The
      existing ten were never checked the same way - Italy is 5 and Norway is 4, and Norway
      in particular spans more latitude than anything the value was tuned on. Nothing
      validates this field, so it needs one pass of loading each built page and looking.
- [ ] **Eleven legend chips in one row is noisy.** Now that the era bands are actually
      visible, the legend may be redundant - or could fold into the bands themselves.
- [ ] **The key-event star in the list is easy to miss.** A small era-coloured pill on the
      date line would carry it better, and would match the ring the timeline now uses.
- [ ] **"Clear selection" is a bare text link** adrift in whitespace; it wants to be a
      subtle bordered button like the chips.
- [ ] **Bigger bets, not costed:** an events-per-decade density strip so you can see WHEN a
      country was eventful; hovering a legend item dimming every other era; the map
      auto-zooming to the selected event's region.

### No test coverage for the JS or CSS - and that is where the last two bugs were

- [ ] **Add a browser-level test.** `tests/` covers the Python well (47 tests, mutation
      checked), but every recent user-visible bug lived outside it: the map ResizeObserver,
      and on 17/08 a CSS rule that outranked `[hidden]` and painted the empty state over the
      real detail panel. Both were caught by screenshotting by hand; neither could have been
      caught by pytest. A small Playwright suite over the built `site/dist` - detail panel
      switches across initial/selected/cleared, no horizontal overflow at three viewports,
      map canvas present, timeline dot count matches the event count - would have caught
      both. The scratchpad scripts written this session are a working starting point.
      Note it needs a built site and a local server, so it is a separate job from `pytest`,
      not an addition to it.

### Conventions promoted into hard validator errors - DONE 20/08/2026

- [x] **All three landed in `validate.py`, each mutation-checked.** DONE 20/08/2026.
      - **Ten eras** - error, on both tails. Nine looks unfinished beside the others,
        eleven silently reuses a palette colour.
      - **`is_major` two-tailed** - warns outside 35-45%, errors outside 25-55%. The
        old check only fired above 55%, which is exactly why Taiwan sat at 13%
        unnoticed.
      - **No en or em dashes** in `display_date`, `title`, `description` or the three
        rendered era fields. `source` is explicitly exempt - a slug must match the
        Wikipedia title, and some titles contain an en dash.
      Nine mutations were each confirmed to turn the suite red, and both exemptions
      (dash inside a slug, 49% warning without erroring) confirmed not to fire.
      13 new tests. The `_doc()` fixtures in both test files needed widening to ten
      eras and five events, because a two-event fixture cannot express a 40% ratio.

- [x] **The content the new checks exposed, all fixed.** DONE 20/08/2026.
      - Taiwan 13% -> 40%: 46 events promoted, each given an API-verified citation.
        Only events with intact titles were chosen (see the item below).
      - Iceland and Peru were both at 34.8%, a rounding hair under the band, which
        would have warned forever and trained everyone to ignore warnings. Promoted
        one genuinely-key event each - the Sagas of Icelanders, and the Spanish entry
        into Cusco.
      - All ten countries now sit at 36-43% with every slug resolving.

### Taiwan's titles - fixed 20/08/2026

Taiwan was the only country affected; the other nine had zero truncated titles
and zero over 70 characters. **Root cause:** the titles were taken by splitting
each description on `.`, so they cut mid-sentence, mid-decimal and at closing
quote marks. That is why `"Taiwan receives $1"` existed for $1.5 billion.

- [x] **95 titles rewritten.** DONE 20/08/2026.
      - 4 asserting a wrong number, recovered from the figures already in their
        own descriptions (events 48, 124, 126, 156).
      - 58 ending in an ellipsis.
      - 22 running 70 to 101 characters, i.e. a description used as a title.
      - 11 reading as sub-bullet headings, including five that duplicated the date
        `display_date` already shows.
      - 2 cut at a closing quote mark (47, 138) and one with a doubled colon (121).
      Taiwan's median title is now 38 characters against 22-27 for the others,
      with nothing over 70.

- [x] **Five validator checks so an import cannot reintroduce it.** DONE 20/08/2026.
      A title ending in `...` or a colon, stopping mid-number after `$`, `(` or `~`,
      or carrying an unbalanced quote mark, is an error. Each was mutation-checked,
      plus a negative case confirming a title legitimately ending in a figure
      ("Koxinga dies at age 37") still passes. 70 tests.

- [ ] **Nine events are section headings, not events** - 69, 75, 77, 84, 86, 99,
      104, 111, 136, titled "May 29", "October 21", "Significance", "Japan brings",
      "Average lifespan", "Total casualties", "Name-changing campaign", "Wall
      posters", "Military spending". They are sub-bullets of a neighbouring event
      that got promoted into events of their own, so a new title cannot fix them:
      each needs folding into its parent's description, or deleting. Deleting nine
      drops Taiwan to 157 events and nudges is_major from 40% to about 43%, which
      stays in band. Event 19 ("Early 7th century", whose description is the same
      three words) belongs in this group.

- [ ] **56 Taiwan descriptions still open with a `Heading:` prefix** - "Tapani
      Incident: Yu Qingfang's religious group defies...", "Dutch legacy:
      Introduced...". They read as redundant now the titles carry that content.
      Mechanical to strip in the cases where the prefix duplicates the new title,
      but roughly half need a judgement call, so it is not a blind regex. Not
      urgent: the detail panel is readable, just repetitive. The other nine
      countries have none.

### If Anthropic-generated countries come back

The old on-demand Wikipedia -> Claude pipeline (`pipeline.py`, `worker.py`) was deleted along with the Supabase backend. To bring it back:

- [ ] Rewrite `pipeline.py` to output a `countries/<name>.json` file instead of writing to Supabase (same schema).
- [ ] Add either a "generate" button in the app that calls the pipeline synchronously and commits/pushes the JSON, OR a local-only CLI (`python pipeline.py Japan`) that Charlie runs by hand and then commits.
- [ ] Add `anthropic` back to `requirements.txt`.
- [ ] Set `ANTHROPIC_API_KEY` in `.env` locally.

For a side project this "generate locally, commit, push" flow is probably fine - the deployed app never needs write access. The Supabase `generating`/`failed`/`retry` UI states and the failed-state retry button are gone with the DB.

### The workflow's actions are on deprecated Node 20 (added 20/08/2026)

- [x] **Bump the four GitHub Actions off Node 20.** DONE 26/08/2026 - `checkout@v4->v7`,
      `setup-python@v5->v7`, `upload-pages-artifact@v3->v5`, `deploy-pages@v4->v5`, and
      the run confirmed green with the live-version guard passing. Node runtimes were
      checked rather than assumed: `checkout`, `setup-python` and `deploy-pages` all
      declared `using: node20` on the old pins and `node24` on the new ones.
      **Correcting this item as written:** the third action was `upload-pages-artifact@v3`,
      not `upload-artifact@v4`, and it is a `composite` action that declares no Node
      runtime at all - it was never a source of the deprecation, it just wraps
      `upload-artifact` internally. Its v4 has the one real breaking change in the set,
      dropping hidden files from the artifact; `site/dist` has no dotfiles and no
      `_`-prefixed paths, so nothing is lost, and there is now a comment in `deploy.yml`
      saying to revisit if a `.nojekyll` is ever added.
- [ ] **Bump the same actions in the other repos.** Split out 26/08/2026 from the item
      above, which closed on Chronoscape only. The estate pins the same versions
      everywhere, so `charlie-tren.github.io`, `consensus-drift`, `lindy-effect`,
      `crowdwise`, `dcf-studio`, `the-aftertimes` and `photocopy` are all likely still on
      Node 20 actions and carrying the same deprecation. Same check as above: confirm
      each repo's artifact directory has no dotfiles before taking
      `upload-pages-artifact` past v3.

### The orphaned Pages project in the other Cloudflare account (added 20/08/2026)

- [ ] **`chronoscape` at `chronoscape-8m5.pages.dev` is now definitively dead weight.**
      It is the Git-connected project that used to auto-build, it sits in a Cloudflare
      account the wrangler credential on this machine cannot see (`GET /accounts`
      returns only the gmail one), and it has no custom domain. Nothing points at it and
      nothing depends on it. Deleting it needs whoever owns that account; it costs
      nothing to leave, so this is tidiness, not risk. Recorded so a future session does
      not rediscover it and assume it matters.

### Cleanup that needs a browser session

- [ ] **Streamlit Cloud**: delete the app `chronoscape.streamlit.app`, which also disposes of
      the `SUPABASE_URL` and `SUPABASE_KEY` entries in its Secrets. Recommended 26/08/2026
      after checking the things that would argue against it, none of which held:
      the app's source (`app.py` and the rest) was removed from this repo in `83384d6`, so
      it points at a repo that can no longer build it; **nothing links to it** - zero hits
      for `streamlit.app` across the whole `charlie-tren.github.io` repo, and the only
      surviving mentions anywhere are historical prose in `PLAN.md` / `README.md` / here;
      and it is login-gated (`GET /` 303s to `/-/login`), so it is not even publicly
      serving a broken page. The timelines it served now live in `countries/*.json`.
      Charlie's hand - it is a browser flow behind his login, and irreversible.
- [ ] **Supabase dashboard**: delete the paused project `xbhhdpcbrsgmactfuxlq`
      ("History Timeline", us-east-1). Charlie's hand: the Supabase MCP exposes
      pause/restore/create but NOT delete, so it is the dashboard UI
      (Project Settings -> General -> Danger Zone -> Delete Project). Irreversible.

      **State verified live 26/08/2026 via the MCP, not taken from this note:** status
      `INACTIVE`, org `sqdcjfiocaqljpunwing`, sitting alongside `rochford-hub`,
      `rochford-news-monitor` and `Vantage`. **That org is the ROCHFORD one, and this is
      the real argument, which the earlier version of this item did not make:** a personal
      side project's database is parked in a work organisation. The freed slot is a
      secondary benefit, though `lexicon/TODO.md` does name Supabase as its persistence
      plan, so it has somewhere to go.

      **The one thing not verified:** the project is paused, and reading its tables would
      mean restoring it, which is a state change. So "the data is safe" rests on
      `countries/taiwan.json` and `countries/iceland.json` existing and serving live, plus
      this file's record of the dump - not on a fresh diff against the database. If that
      is not good enough before an irreversible delete, restore it once, dump, compare,
      then delete.

---

## Done

### JSON migration (2026-07-03)
- Free-tier Supabase quota was needed for `rochford-news-monitor` (created 20/05/2026), so the History Timeline project was paused. Rather than shuffle quotas indefinitely, moved to flat JSON files.
- Dumped Supabase state -> `countries/taiwan.json` (166 events, 10 eras) + moved `iceland_data.json` -> `countries/iceland.json` (92 events, 10 eras).
- Rewrote `db.py` as a JSON loader (~90 lines, was ~200 lines of Supabase queries). Same public surface (`list_countries`, `load_country_data`) so `app.py` needed only a small edit to drop the try/except DB fallback and remove the generating/failed/retry branches.
- Simplified `app.py`: no worker recovery on startup, no `_build_taiwan_fallback_eras`. Charlie's June UI redesign (Inter font, gradient theme, scoped chip pills, clickable event cards) is preserved.
- `requirements.txt` stripped to `streamlit`, `folium`, `streamlit-folium` (removed supabase, python-dotenv, anthropic).
- Deleted: `pipeline.py`, `worker.py`, `seed_country.py`, `seed_taiwan.py`, `.github/workflows/keep-alive.yml`. Note: the Supabase project (`xbhhdpcbrsgmactfuxlq`) is still on the account but paused - safe to fully delete when Charlie's ready.
- Streamlit Cloud Secrets `SUPABASE_URL` / `SUPABASE_KEY` still set but now unused (see Outstanding).

### UI redesign + bug fixes + DB restore + keep-alive fix (2026-06-21)
- **Sleeker UI** (`styles.py`, `app.py`): Inter font, deeper gradient theme, rounded filter inputs, scoped chip pills (chips no longer wrap), polished detail panel + welcome/loading cards. Live as v2.16.
- **Event list rows are now single clickable card buttons** (dim date over bold title, star for key events, per-era colour stripe down the left edge). FIXES the "card click doesn't select" bug - the whole card selects; removed the redundant "Select event" button.
- **Verified via Claude in Chrome** (local run): chips, event-card click -> detail panel, timeline-dot click, clear selection, detail panel rendering. Map markers respond to hover/tooltip (click path unchanged from prior verification).
- **DB had auto-paused** (down since ~late May) -> restored via Supabase MCP `restore_project` + `NOTIFY pgrst, 'reload schema'` + a Streamlit Cloud reboot (auto-deploy lagged ~10 min).
- **keep-alive cron changed from every-6-days to DAILY** (`0 3 * * *`) - 6 days of slack vs the 7-day pause window. Root cause of the pause: the 6-day cadence had <1 day of slack and GitHub cron delays pushed the gap >7 days. Manual `workflow_dispatch` run succeeded (first green since 2026-05-25). Edited via the GitHub web editor (local `gh` not logged in; tokens lack `workflow` scope).

### Phase 1 - Database Foundation (2026-04-14)
- Created Supabase project `xbhhdpcbrsgmactfuxlq` (us-east-1, free tier).
- Created 4 tables with indexes + FK cascades: countries, eras, events, generation_jobs.
- Built `db.py` with full query wrapper.
- Seeded Taiwan data from existing markdown (166 events, 10 eras, status=ready, centre 23.7/121.0).

### Phase 2 - Code generalisation + verification (2026-04-22, verified 2026-05-19)
- Stripped Taiwan-specific data out of `event_data.py`, `styles.py`, `timeline_component.py`, `map_component.py`.
- Added runtime-config pattern: `set_era_config(eras)` populates `_era_color_map` / `_era_short_map`.
- 15-colour `ERA_PALETTE` for dynamic assignment.
- Universal category list (added Social, Scientific, Religious; kept Aboriginal as alias to Indigenous).
- `render_timeline()` now takes `eras_config` param, `render_map()` takes `country_config`.
- `app.py` rewritten with country search bar at top, dynamic header + filters + colour key, loading/error state UI.
- **Verified end-to-end (2026-05-19)** via Claude in Chrome: Taiwan loads from DB (166 events, 10 eras, all renderers work), Iceland loads from DB (92 events, 10 eras), country-switch via search bar works, event selection via list works, detail panel populates, map markers render with tooltip-encoded IDs.

### Iceland seeded (2026-05-19)
- Hand-extracted 92 events / 10 eras from the Wikipedia History of Iceland article (Charlie pasted the text in chat).
- Pre-Settlement -> Settlement Age (874-930) -> Commonwealth (930-1262) -> Norwegian Rule -> Kalmar Union -> Danish Rule and Trade Monopoly -> Path to Independence -> Kingdom of Iceland -> Cold War Republic -> Modern Republic.
- 32 major events, 25 with map coordinates, centre 64.96 / -19.02, zoom 6.
- Created `iceland_data.json` (raw structured data) and generic `seed_country.py` (loads a JSON of this shape and inserts into Supabase) - the latter is the storage-layer prototype that Phase 4 `pipeline.py` will reuse.

### Phase 4 - Data pipeline shipped (2026-05-19)
- `pipeline.py` with `fetch_wikipedia()` (4-5 articles, 1 req/sec, 80k char cap), `extract_with_claude()` (claude-sonnet-4-6, structured output via `output_config.format` with full JSON schema enforcement, thinking disabled, max_tokens 16000), `store_results()` (reuses save_eras / save_events from db.py), `run_pipeline()` orchestrator with full job tracking in `generation_jobs` (input_tokens, output_tokens, cost_usd, wiki_pages, error_message).
- `worker.py` with `generate_in_background()` (threading.Thread daemon, dedupe via `_active_threads` so duplicate clicks don't spawn parallel workers), `recover_stuck_jobs()` (resets `status='generating'` rows older than 10min to `'failed'` so UI offers retry).
- `app.py` calls `recover_stuck_jobs()` once per Streamlit process on first load (gated by session_state flag, doesn't block on failure).
- Per-country cost ~$0.25 (Sonnet 4.6 pricing). 50-country monthly refresh ~$13.
- **Untested end-to-end** because ANTHROPIC_API_KEY is still empty in `.env` - that's the only blocker.

### Hardening (2026-05-19)
- **RLS enabled** on all 4 tables. anon + authenticated roles get SELECT only; service_role bypasses for writes. Future seeds and `pipeline.py` writes need the service_role key locally.
- **db.py updated** to prefer `SUPABASE_SERVICE_ROLE_KEY` if set, else fall back to `SUPABASE_KEY`. No app code changes required.
- **Service role key added to local `.env`** as `SUPABASE_SERVICE_ROLE_KEY`. Verified writes work.
- **GitHub Actions keep-alive cron** added (`.github/workflows/keep-alive.yml`) - hits Supabase REST API every 6 days to stop free-tier 7-day auto-pause.
- **GitHub repo secrets** `SUPABASE_URL` and `SUPABASE_ANON_KEY` added via `gh secret set` so the cron actually works.
- One-off discovery: the project had auto-paused. Restore took ~2 minutes via `restore_project`. PostgREST schema cache had to be reloaded post-restore (`NOTIFY pgrst, 'reload schema';`) before writes worked again. Worth noting for future restores.

### Deploy + Rename (2026-05-19)
- **Merged `multi-country-refactor` -> `master` -> pushed to GitHub `master`.** Streamlit Cloud auto-deploys from master. (Originally pushed to `main`; the `main` branch was deleted 19/05/2026 once we realised Streamlit Cloud was wired to master.)
- **Repo renamed**: `taiwan-history-timeline` -> `country-timelines` -> `chronoscape` (final). Local remote updated. GitHub redirects old URLs.
- **Repo description** updated to reflect multi-country scope.

### Infrastructure
- `.env` file for local secrets (gitignored).
- `.gitignore` updated (.env, __pycache__, .claude).
- `requirements.txt` updated: +supabase, +python-dotenv, +anthropic, +folium, +streamlit-folium, +branca.
- `PLAN.md` saved in project root.
