"""Build one static HTML page per country from countries/*.json.

Python + Jinja2 -> static HTML, no JS toolchain. The event list is rendered
SERVER-SIDE (real HTML in the source, so it is indexable - the thing Streamlit
could not do), while the timeline and map get the data as embedded JSON for
client-side interactivity.

Usage:
    python site/build.py            # build every country in countries/
    python site/build.py taiwan     # build just one (still validates all)

Output goes to site/dist/, which Cloudflare Pages serves as-is.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape

from validate import validate_all

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
COUNTRIES = ROOT / "countries"
DIST = SITE / "dist"

# Canonical origin, used for <link rel=canonical>, og:url and the sitemap.
# Override with SITE_URL when building for a preview deployment.
SITE_URL = os.environ.get("SITE_URL", "https://charlietrenorden.com/chronoscape").rstrip("/")

# The path SITE_URL sits at, with both slashes: "/" at a domain root,
# "/chronoscape/" when the site is served under the hub domain. The 404 page needs it,
# because a 404 can be served at any depth and so cannot use a relative prefix.
ROOT_PATH = (urlsplit(SITE_URL).path or "").rstrip("/") + "/"

# Major version. v2.x was the Streamlit app; the static rewrite is v3.
MAJOR_MINOR = "v3"

# The country the site opens on at /. Its page is rendered twice: once at
# /<slug>/ (the canonical URL) and once at /.
DEFAULT_COUNTRY = "taiwan"


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], stderr=subprocess.DEVNULL, cwd=ROOT
    ).decode().strip()


def version() -> str:
    """v3.<commit count>, matching the convention the Streamlit app used.

    Cloudflare Pages clones shallow, so a naive `rev-list --count` returns 1
    and every deploy claims to be v3.1. Try to deepen the clone first; if that
    is not possible, fall back to the commit date so the footer still
    identifies the build rather than lying about it.
    """
    try:
        if _git("rev-parse", "--is-shallow-repository") == "true":
            try:
                _git("fetch", "--unshallow", "--quiet")
            except Exception:
                pass  # no credentials in CI - fall through to the date

        if _git("rev-parse", "--is-shallow-repository") != "true":
            return f"{MAJOR_MINOR}.{_git('rev-list', '--count', 'HEAD')}"

        # Still shallow: a count would be meaningless, so date-stamp instead.
        return f"{MAJOR_MINOR}.{_git('log', '-1', '--format=%cd', '--date=format:%Y%m%d')}"
    except Exception:
        return f"{MAJOR_MINOR}.0"

# Mirrors timeline_component.py so the ported JS keeps identical geometry.
TOTAL_WIDTH = 6000


def proportional_position(sort_year: float, year_start: float, year_end: float) -> float:
    """Where a dot sits inside its era segment, as a percentage."""
    if year_end == year_start:
        return 50.0
    y = max(year_start, min(year_end, sort_year))
    pct = (y - year_start) / (year_end - year_start)
    return 6 + pct * 88


def format_year(year: float) -> str:
    """A numeric year as a reader-facing string: -3200 -> '3200 BCE'.

    Thousands separators only from 10,000, so Taiwan reads '450,000 BCE' while
    Egypt stays '5000 BCE' rather than the fussier '5,000 BCE'.
    """
    y = int(year)
    n = abs(y)
    s = f"{n:,}" if n >= 10_000 else str(n)
    return f"{s} BCE" if y < 0 else f"{s} CE"


def country_date_range(eras: list[dict]) -> str:
    """The 'X - present' line under the country name.

    Built from the first era's numeric year_start, NOT its date_label. The
    label is written for the timeline band, where 'to 1100 BCE' means "this
    band runs up to 1100 BCE" - concatenating it produced the nonsense
    'to 1100 BCE - present' in the subtitle, and 'to 250 CE - present' on
    Japan. Every country's last era currently runs to 2025 or 2026, so the
    right-hand side is 'present'.
    """
    if not eras:
        return ""
    return f"{format_year(eras[0].get('year_start', 0))} - present"


def match_era(event_era: str, era_names: list[str]) -> str:
    """Resolve an event's era_name to a canonical era (exact, then fuzzy)."""
    lower = event_era.lower()
    for name in era_names:
        if name.lower() == lower:
            return name
    for name in era_names:
        if name.lower() in lower or lower in name.lower():
            return name
    return era_names[-1] if era_names else event_era


# Everything in dist/ that is not a country page. Anything else at the top level
# is assumed to be a country directory and is fair game for pruning.
DIST_KEEP = {"static"}


def prune_orphan_pages(dist: Path, slugs: set[str]) -> list[str]:
    """Delete country directories in dist/ that no longer have a JSON file.

    The build otherwise only ever ADDS, so deleting or renaming a country left
    its old page in dist/, uploaded by the next deploy and reachable forever -
    missing from the sitemap but live and indexable. Found 14/08/2026 when a
    scaffolded test country outlived its data file.

    Deliberately surgical rather than wiping dist/ wholesale: on this machine
    the repo lives under OneDrive, which holds directory handles and makes a
    full rmtree fail with WinError 5 partway through, leaving a half-built
    site. For the same reason a failure here only warns - a stale orphan page
    is a much smaller problem than a build that will not run.
    """
    removed = []
    if not dist.exists():
        return removed
    for child in sorted(dist.iterdir()):
        if not child.is_dir() or child.name in DIST_KEEP or child.name in slugs:
            continue
        if _rmtree_windows_safe(child):
            removed.append(child.name)
            print(f"  pruned stale page /{child.name}/")
        else:
            print(f"  warn: could not remove stale page {child.name}/. "
                  f"Delete it by hand or it will keep being published.")
    return removed


def _rmtree_windows_safe(path: Path, attempts: int = 5) -> bool:
    """rmtree, retried.

    On Windows file deletion is asynchronous: rmtree unlinks the contents and
    then immediately rmdirs the directory, which fails with WinError 5 because
    the handle has not been released yet. Verified on this repo - the failing
    rmtree left the directory empty, and a plain rmdir a moment later worked.
    OneDrive makes it likelier by scanning what just changed. Retrying with a
    short back-off clears it; CI on Linux gets it first time.
    """
    for i in range(attempts):
        try:
            shutil.rmtree(path)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            if i == attempts - 1:
                return False
            time.sleep(0.15 * (i + 1))
    return False


def build_segments(eras: list[dict], events: list[dict]) -> list[dict]:
    """Group events into era swimlanes with pre-computed dot positions."""
    era_names = [e["name"] for e in eras]
    by_era: dict[str, list[dict]] = {}
    for ev in events:
        by_era.setdefault(match_era(ev["era_name"], era_names), []).append(dict(ev))

    segments = []
    for era in eras:
        evts = sorted(by_era.get(era["name"], []), key=lambda e: e["sort_year"])
        segments.append({
            "width_pct": era.get("width_pct", 8),
            "color": era.get("color", "#666666"),
            "era_label": era.get("short_name", era["name"]),
            "date_label": era.get("date_label", ""),
            "dots": [
                {
                    "id": ev["id"],
                    "left": round(
                        proportional_position(
                            ev["sort_year"], era.get("year_start", 0), era.get("year_end", 1)
                        ),
                        2,
                    ),
                    "major": bool(ev.get("is_major")),
                    "tooltip": f"{ev['display_date']}: {ev['title']}",
                }
                for ev in evts
            ],
        })
    return segments


def build_country(
    path: Path, env: Environment, all_countries: list[dict], at_root: bool = False
) -> dict:
    """Render one country page.

    at_root writes the same page to DIST/index.html instead of DIST/<slug>/,
    so the site opens on a live timeline rather than an empty picker. Relative
    asset and chip links shift by one level, and the canonical still points at
    the country's own URL so the two copies are not treated as rival pages.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    country, eras, events = data["country"], data["eras"], data["events"]

    # The id is stored in the data and is PERMANENT. It used to be the array
    # index, which meant moving or inserting an event silently renumbered every
    # later one and broke their /country/#event-N links. validate.py requires it.
    ids = [ev.get("id") for ev in events]
    if any(i is None for i in ids):
        sys.exit(f"{path.name}: every event needs an explicit id - see countries/README.md")
    if len(set(ids)) != len(ids):
        sys.exit(f"{path.name}: duplicate event ids")

    era_colors = {e["name"]: e.get("color", "#666666") for e in eras}
    era_shorts = {e["name"]: e.get("short_name", e["name"]) for e in eras}
    era_names = [e["name"] for e in eras]
    for ev in events:
        canonical = match_era(ev["era_name"], era_names)
        ev["era_color"] = era_colors.get(canonical, "#666666")
        ev["era_short"] = era_shorts.get(canonical, canonical)

    # GeoJSON for MapLibre - only events that actually have coordinates.
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [ev["lng"], ev["lat"]]},
            "properties": {
                "id": ev["id"],
                "color": ev["era_color"],
                "major": bool(ev.get("is_major")),
                "title": ev["title"],
                "date": ev["display_date"],
            },
        }
        for ev in events
        if ev.get("lat") is not None and ev.get("lng") is not None
    ]

    categories = sorted({c for ev in events for c in (ev.get("categories") or [])})

    slug = path.stem
    html = env.get_template("country.html.j2").render(
        country=country,
        slug=slug,
        eras=eras,
        events=events,
        categories=categories,
        all_countries=all_countries,
        base="" if at_root else "../",
        canonical=f"{SITE_URL}/{slug}/",
        version=version(),
        site_url=SITE_URL,
        date_range=country_date_range(eras),
        payload=json.dumps(
            {
                "segments": build_segments(eras, events),
                "totalWidth": TOTAL_WIDTH,
                "geojson": {"type": "FeatureCollection", "features": features},
                "center": [country.get("center_lng", 0), country.get("center_lat", 0)],
                "zoom": country.get("default_zoom", 5),
                "events": [
                    {
                        "id": ev["id"],
                        "title": ev["title"],
                        "date": ev["display_date"],
                        "description": ev.get("description", ""),
                        "era": ev["era_name"],
                        "eraShort": ev["era_short"],
                        "eraColor": ev["era_color"],
                        "categories": ev.get("categories") or [],
                        "source": ev.get("source"),
                        "major": bool(ev.get("is_major")),
                        "lat": ev.get("lat"),
                        "lng": ev.get("lng"),
                        "sortYear": ev["sort_year"],
                    }
                    for ev in events
                ],
            },
            separators=(",", ":"),
        ),
    )

    if at_root:
        (DIST / "index.html").write_text(html, encoding="utf-8")
    else:
        out = DIST / slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(html, encoding="utf-8")
    return {"slug": slug, "name": country["name"], "count": len(events)}


def main() -> None:
    only = sys.argv[1].lower() if len(sys.argv) > 1 else None

    # Validation gate: bad data fails the build rather than shipping quietly.
    errors, warnings = validate_all()
    for w in warnings:
        print(f"  warn: {w}")
    if errors:
        print(f"\n{len(errors)} validation error(s) - not building:\n")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    files = sorted(COUNTRIES.glob("*.json"))
    if only:
        files = [f for f in files if f.stem == only]
        if not files:
            sys.exit(f"No such country: {only}")

    manifest = [
        {"slug": f.stem, "name": json.loads(f.read_text(encoding="utf-8"))["country"]["name"]}
        for f in sorted(COUNTRIES.glob("*.json"))
    ]

    env = Environment(
        loader=FileSystemLoader(SITE / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    DIST.mkdir(parents=True, exist_ok=True)
    prune_orphan_pages(DIST, {f.stem for f in COUNTRIES.glob("*.json")})
    shutil.copytree(SITE / "static", DIST / "static", dirs_exist_ok=True)
    # Browsers and Google probe /favicon.ico at the domain root regardless of what the
    # <link> tags say, so put a copy there as well as in static/.
    shutil.copyfile(SITE / "static" / "favicon.ico", DIST / "favicon.ico")

    built = [build_country(f, env, manifest) for f in files]

    # Landing page. Not a picker - the site opens straight onto a real
    # timeline, because an empty "pick a country" card is a wasted screen.
    root = COUNTRIES / f"{DEFAULT_COUNTRY}.json"
    if not root.exists():
        sys.exit(f"DEFAULT_COUNTRY={DEFAULT_COUNTRY!r} has no countries/{DEFAULT_COUNTRY}.json")
    build_country(root, env, manifest, at_root=True)

    # 404 - Cloudflare Pages serves /404.html for unmatched paths automatically.
    (DIST / "404.html").write_text(
        env.get_template("404.html.j2").render(
            all_countries=manifest, site_url=SITE_URL, version=version(),
            root=ROOT_PATH,
        ),
        encoding="utf-8",
    )

    # sitemap.xml - the country page is the indexable unit. One page per event
    # would be ~26,000 URLs at 200 countries, for a paragraph each.
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/{c['slug']}/" for c in manifest]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n"
    )
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )

    for b in built:
        print(f"  built /{b['slug']}/  ({b['name']}, {b['count']} events)")
    print(f"  built /, /404.html, /sitemap.xml ({len(urls)} urls), /robots.txt")
    print(f"\n{len(built)} country page(s) -> {DIST}   [{SITE_URL}]")


if __name__ == "__main__":
    main()
