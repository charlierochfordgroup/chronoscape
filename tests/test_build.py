"""Tests for the pure functions in site/build.py.

Deliberately weighted towards the cases CLAUDE.md calls out: BC (negative)
years and zero-width ranges in proportional_position, and the shallow-clone
branch of version(), which has already shipped a production bug.
"""

import subprocess

import pytest

import build
from build import build_segments, match_era, proportional_position


# --------------------------------------------------------------------------
# proportional_position
# --------------------------------------------------------------------------
# The function maps a year onto 6..94 per cent of its era segment, leaving a
# 6% margin at each end so dots never sit on the segment border.

def test_position_endpoints_and_midpoint():
    assert proportional_position(1000, 1000, 2000) == 6.0
    assert proportional_position(2000, 1000, 2000) == 94.0
    assert proportional_position(1500, 1000, 2000) == 50.0


def test_position_zero_width_range_does_not_divide_by_zero():
    # An era whose start and end are the same year - Republic of Formosa in
    # taiwan.json is exactly this (1895 to 1895).
    assert proportional_position(1895, 1895, 1895) == 50.0


def test_position_handles_bc_years():
    # Wholly BC era: -1000 to 0, midpoint -500.
    assert proportional_position(-1000, -1000, 0) == 6.0
    assert proportional_position(0, -1000, 0) == 94.0
    assert proportional_position(-500, -1000, 0) == 50.0


def test_position_spanning_bc_to_ad():
    # Greece's Roman era spans -146 to 330, which straddles zero.
    assert proportional_position(-146, -146, 330) == 6.0
    assert proportional_position(330, -146, 330) == 94.0
    assert proportional_position(92, -146, 330) == pytest.approx(50.0)


def test_position_clamps_events_outside_their_era():
    # Precursor events are deliberately filed in the era they belong to
    # narratively (validate.py warns rather than errors). They must clamp to
    # the segment edge, not fly off it.
    assert proportional_position(860, 874, 930) == 6.0
    assert proportional_position(9999, 874, 930) == 94.0


def test_position_fractional_year_orders_within_a_year():
    # sort_year carries a fraction to order events inside one year.
    early = proportional_position(1944.1, 1900, 2000)
    late = proportional_position(1944.9, 1900, 2000)
    assert early < late


# --------------------------------------------------------------------------
# match_era
# --------------------------------------------------------------------------

ERAS = ["Classical Greece", "Hellenistic Age", "Roman Greece"]


def test_match_era_exact_and_case_insensitive():
    assert match_era("Hellenistic Age", ERAS) == "Hellenistic Age"
    assert match_era("hellenistic age", ERAS) == "Hellenistic Age"


def test_match_era_prefers_exact_over_substring():
    # "Roman Greece" is a substring of nothing here, but "Greece" appears in
    # two names - an exact hit must win rather than the first fuzzy one.
    eras = ["Greece", "Roman Greece"]
    assert match_era("Roman Greece", eras) == "Roman Greece"


def test_match_era_fuzzy_both_directions():
    assert match_era("Roman", ERAS) == "Roman Greece"          # event shorter
    assert match_era("Late Hellenistic Age", ERAS) == "Hellenistic Age"  # event longer


def test_match_era_miss_falls_back_to_last_era():
    # Documented fallback: an unmatched era lands in the final one rather than
    # vanishing from the timeline.
    assert match_era("Cretaceous", ERAS) == "Roman Greece"


def test_match_era_with_no_eras_returns_input():
    assert match_era("Anything", []) == "Anything"


# --------------------------------------------------------------------------
# build_segments
# --------------------------------------------------------------------------

def _eras():
    return [
        {"name": "First", "short_name": "1st", "year_start": 0, "year_end": 100,
         "date_label": "0-100", "width_pct": 40, "color": "#111111"},
        {"name": "Second", "short_name": "2nd", "year_start": 100, "year_end": 200,
         "date_label": "100-200", "width_pct": 60, "color": "#222222"},
    ]


def _events():
    # Deliberately out of chronological order, and skewed to one era.
    return [
        {"id": 0, "era_name": "Second", "sort_year": 150, "display_date": "150", "title": "B", "is_major": True},
        {"id": 1, "era_name": "First", "sort_year": 50, "display_date": "50", "title": "A", "is_major": False},
        {"id": 2, "era_name": "Second", "sort_year": 120, "display_date": "120", "title": "C", "is_major": False},
    ]


def test_segments_are_one_per_era_in_era_order():
    segs = build_segments(_eras(), _events())
    assert [s["era_label"] for s in segs] == ["1st", "2nd"]


def test_segment_carries_era_presentation_fields():
    seg = build_segments(_eras(), _events())[0]
    assert seg["width_pct"] == 40
    assert seg["color"] == "#111111"
    assert seg["date_label"] == "0-100"


def test_dots_are_sorted_by_year_within_an_era():
    segs = build_segments(_eras(), _events())
    second = segs[1]
    assert [d["tooltip"] for d in second["dots"]] == ["120: C", "150: B"]


def test_dot_ids_are_global_not_per_era():
    # The id addresses the whole events list, not a position within the era,
    # because the event list, the map geojson and the deep link all use that
    # number. Getting it wrong selects the wrong event from the timeline.
    segs = build_segments(_eras(), _events())
    assert segs[0]["dots"][0]["id"] == 1          # "A" is events[1]
    assert [d["id"] for d in segs[1]["dots"]] == [2, 0]   # "C" then "B"


def test_dot_ids_come_from_the_data_not_the_array_position():
    # The id used to be assigned by enumerate(), so moving or inserting an
    # event renumbered every later one and broke their #event-N deep links.
    # It is now whatever the data says, and the array order is irrelevant.
    events = _events()
    events[0]["id"], events[1]["id"], events[2]["id"] = 77, 88, 99
    segs = build_segments(_eras(), events)
    assert segs[0]["dots"][0]["id"] == 88                 # "A"
    assert [d["id"] for d in segs[1]["dots"]] == [99, 77]  # "C" then "B"


def test_major_flag_survives():
    segs = build_segments(_eras(), _events())
    assert [d["major"] for d in segs[1]["dots"]] == [False, True]


def test_era_with_no_events_still_produces_a_segment():
    segs = build_segments(_eras(), [_events()[1]])
    assert len(segs) == 2
    assert segs[1]["dots"] == []


def test_segments_use_defaults_when_era_fields_are_missing():
    eras = [{"name": "Bare"}]
    segs = build_segments(eras, [{"id": 0, "era_name": "Bare", "sort_year": 5,
                                  "display_date": "5", "title": "X"}])
    assert segs[0]["width_pct"] == 8
    assert segs[0]["color"] == "#666666"
    assert segs[0]["era_label"] == "Bare"


# --------------------------------------------------------------------------
# version() - the shallow-clone branch is the one that broke in production
# --------------------------------------------------------------------------

def _git(cwd, *args):
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


@pytest.fixture
def origin_repo(tmp_path):
    """A real repo with three commits."""
    repo = tmp_path / "origin"
    repo.mkdir()
    _git(repo, "init", "-q")
    for i in range(3):
        (repo / f"f{i}.txt").write_text(str(i), encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-qm", f"c{i}")
    return repo


def test_version_counts_commits_in_a_full_clone(monkeypatch, origin_repo):
    monkeypatch.setattr(build, "ROOT", origin_repo)
    assert build.version() == "v3.3"


def test_version_unshallows_when_the_origin_is_reachable(monkeypatch, tmp_path, origin_repo):
    shallow = tmp_path / "shallow"
    subprocess.check_call(
        ["git", "clone", "--depth", "1", origin_repo.as_uri(), str(shallow)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    monkeypatch.setattr(build, "ROOT", shallow)
    # It should deepen the clone and recover the true count, not report v3.1.
    assert build.version() == "v3.3"


def test_version_date_stamps_when_it_cannot_unshallow(monkeypatch, tmp_path, origin_repo):
    """The production case: Cloudflare clones shallow with no credentials to
    fetch more. Reporting v3.1 for every build was the bug - a date stamp at
    least identifies the build honestly."""
    shallow = tmp_path / "nofetch"
    subprocess.check_call(
        ["git", "clone", "--depth", "1", origin_repo.as_uri(), str(shallow)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    _git(shallow, "remote", "remove", "origin")   # nothing left to fetch from
    monkeypatch.setattr(build, "ROOT", shallow)

    v = build.version()
    assert v != "v3.1", "a shallow clone must not report a commit count of 1"
    assert v.startswith("v3.")
    assert len(v.split(".")[1]) == 8 and v.split(".")[1].isdigit(), f"expected a YYYYMMDD stamp, got {v}"


def test_version_falls_back_when_there_is_no_repo_at_all(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "ROOT", tmp_path)
    assert build.version() == "v3.0"


# --------------------------------------------------------------------------
# format_year / country_date_range
# --------------------------------------------------------------------------
# The subtitle used to concatenate the first era's date_label, which is written
# for the timeline band ("to 1100 BCE" = this band runs UP TO 1100 BCE). That
# produced "to 1100 BCE - present" on Greece and "to 250 CE - present" on Japan.

from build import country_date_range, format_year


def test_format_year_bce_and_ce():
    assert format_year(-3200) == "3200 BCE"
    assert format_year(1912) == "1912 CE"


def test_format_year_separates_thousands_only_from_ten_thousand():
    assert format_year(-5000) == "5000 BCE"        # Egypt - no comma
    assert format_year(-14000) == "14,000 BCE"     # Japan
    assert format_year(-450000) == "450,000 BCE"   # Taiwan


def test_format_year_truncates_fractional_years():
    # sort_year carries a fraction to order within a year; a year label must not.
    assert format_year(-3200.7) == "3200 BCE"


def test_date_range_uses_the_numeric_start_not_the_band_label():
    eras = [{"year_start": -1100, "date_label": "to 1100 BCE"}]
    assert country_date_range(eras) == "1100 BCE - present"
    assert "to 1100 BCE - present" not in country_date_range(eras)


def test_date_range_is_empty_without_eras():
    assert country_date_range([]) == ""
