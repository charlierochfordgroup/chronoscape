"""Integration test for main(): what actually lands in dist/.

Covers the orphan-page bug found 14/08/2026 - the build only added files, so a
deleted country stayed live. Points COUNTRIES and DIST at temp dirs; templates
and static assets still come from the real site/.
"""

import json
import sys

import pytest

import build
import validate as validate_mod


def _country(name):
    return {
        "country": {"name": name, "center_lat": 0, "center_lng": 0, "default_zoom": 5},
        # Ten eras and a 40% is_major ratio, because validate.py enforces both
        # and build.py runs the validator before it renders anything.
        "eras": [{"name": f"Era {i}", "short_name": f"E{i}", "sort_order": i,
                  "year_start": 100 * i, "year_end": 100 * i + 99,
                  "date_label": f"{100 * i}-{100 * i + 99}", "width_pct": 10,
                  "color": "#5a8a9a"}
                 for i in range(10)],
        "events": [{"id": i, "era_name": "Era 0", "sort_year": 10 + i, "display_date": str(10 + i),
                    "title": f"{name} event {i}", "categories": ["Political"],
                    "lat": None, "lng": None, "is_major": i < 2,
                    **({"source": f"{name}_article_{i}"} if i < 2 else {})}
                   for i in range(5)],
    }


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    countries = tmp_path / "countries"
    countries.mkdir()
    dist = tmp_path / "dist"
    monkeypatch.setattr(build, "COUNTRIES", countries)
    monkeypatch.setattr(build, "DIST", dist)
    # validate_all() reads validate.py's own COUNTRIES, not build's - without this
    # the sandbox build validates the real repo instead.
    monkeypatch.setattr(validate_mod, "COUNTRIES", countries)
    # main() renders whatever DEFAULT_COUNTRY names at "/", so it must exist here.
    monkeypatch.setattr(build, "DEFAULT_COUNTRY", "alpha")
    # main() takes its country filter from argv, which under pytest is full of
    # test paths.
    monkeypatch.setattr(sys, "argv", ["build.py"])
    return countries, dist


def write(countries, slug, name=None):
    (countries / f"{slug}.json").write_text(
        json.dumps(_country(name or slug.title())), encoding="utf-8")


def test_build_emits_a_page_per_country(sandbox):
    countries, dist = sandbox
    write(countries, "alpha")
    write(countries, "beta")
    build.main()

    assert (dist / "alpha" / "index.html").exists()
    assert (dist / "beta" / "index.html").exists()
    assert (dist / "index.html").exists()          # DEFAULT_COUNTRY at the root
    assert (dist / "sitemap.xml").exists()
    assert (dist / "404.html").exists()
    assert (dist / "static" / "style.css").exists()


def test_deleting_a_country_removes_its_page(sandbox):
    """The bug: dist was never cleaned, so the page outlived its data file and
    kept being deployed."""
    countries, dist = sandbox
    write(countries, "alpha")
    write(countries, "gone")
    build.main()
    assert (dist / "gone" / "index.html").exists()

    (countries / "gone.json").unlink()
    build.main()

    assert not (dist / "gone").exists(), "stale country page survived a rebuild"
    assert (dist / "alpha" / "index.html").exists()


def test_sitemap_lists_only_current_countries(sandbox):
    countries, dist = sandbox
    write(countries, "alpha")
    write(countries, "gone")
    build.main()
    (countries / "gone.json").unlink()
    build.main()

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
    assert "/alpha/" in sitemap
    assert "/gone/" not in sitemap
