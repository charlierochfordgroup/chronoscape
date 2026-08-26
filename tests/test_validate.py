"""Tests for site/validate.py.

The validator is the only thing standing between a malformed country file and
a broken page, since build.py runs it before rendering anything. The
error/warning split matters and is asserted directly: errors fail the build,
warnings are legitimate editorial choices that must NOT.
"""

from validate import validate


def _doc(**over):
    """A minimal country that validates cleanly."""
    doc = {
        "country": {"name": "Testland", "center_lat": 0, "center_lng": 0, "default_zoom": 5},
        # Ten eras, because validate.py requires exactly ten. The first two carry
        # the events; the filler eight only exist to satisfy the count.
        "eras": [
            {"name": "Early", "short_name": "E", "sort_order": 0, "year_start": 0,
             "year_end": 100, "date_label": "0-100", "width_pct": 50, "color": "#111111"},
            {"name": "Late", "short_name": "L", "sort_order": 1, "year_start": 100,
             "year_end": 200, "date_label": "100-200", "width_pct": 22, "color": "#222222"},
        ] + [
            {"name": f"Filler {i}", "short_name": f"F{i}", "sort_order": i,
             "year_start": 200 + i, "year_end": 300 + i, "date_label": "later",
             "width_pct": 3.5, "color": "#333333"}
            for i in range(2, 10)
        ],
        # Five events with two flagged, i.e. 40% - inside the is_major band, so
        # the fixture itself does not trip the ratio check. events[0] is the
        # major and events[1] the minor that most tests below reach for.
        "events": [
            {"era_name": "Early", "sort_year": 50, "display_date": "50", "title": "One",
             "categories": ["Military"], "source": "Testland", "lat": 1.0, "lng": 2.0,
             "is_major": True},
            {"era_name": "Late", "sort_year": 150, "display_date": "150", "title": "Two",
             "categories": [], "lat": None, "lng": None, "is_major": False},
            {"era_name": "Late", "sort_year": 160, "display_date": "160", "title": "Three",
             "categories": [], "source": "Testland_three", "lat": None, "lng": None,
             "is_major": True},
            {"era_name": "Late", "sort_year": 170, "display_date": "170", "title": "Four",
             "categories": [], "lat": None, "lng": None, "is_major": False},
            {"era_name": "Late", "sort_year": 180, "display_date": "180", "title": "Five",
             "categories": [], "lat": None, "lng": None, "is_major": False},
        ],
    }
    doc.update(over)
    # Every event needs a permanent id. Filled in here rather than written into
    # each fixture so that tests overriding "events" get them too; a test that
    # wants to check a MISSING or duplicate id sets it explicitly and this
    # leaves it alone.
    for i, ev in enumerate(doc.get("events") or []):
        ev.setdefault("id", i)
    return doc


def errs(doc):
    return validate(doc, "t")[0]


def warns(doc):
    return validate(doc, "t")[1]


def test_a_minimal_valid_country_is_clean():
    e, w = validate(_doc(), "t")
    assert e == [] and w == []


# --- structural errors -----------------------------------------------------

def test_missing_country_field_is_an_error():
    d = _doc()
    del d["country"]["center_lat"]
    assert any("center_lat" in x for x in errs(d))


def test_no_eras_or_no_events_is_an_error():
    assert any("no eras" in x for x in errs(_doc(eras=[])))
    assert any("no events" in x for x in errs(_doc(events=[])))


def test_width_pct_must_sum_to_100():
    d = _doc()
    d["eras"][0]["width_pct"] = 49
    assert any("width_pct sums to 99" in x for x in errs(d))


def test_eras_must_be_in_sort_order():
    d = _doc()
    d["eras"][0]["sort_order"], d["eras"][1]["sort_order"] = 1, 0
    assert any("not in sort_order order" in x for x in errs(d))


def test_duplicate_era_sort_order_is_an_error():
    d = _doc()
    d["eras"][1]["sort_order"] = 0
    assert any("duplicate era sort_order" in x for x in errs(d))


def test_era_start_after_end_is_an_error():
    d = _doc()
    d["eras"][0]["year_start"], d["eras"][0]["year_end"] = 100, 0
    assert any("year_start after year_end" in x for x in errs(d))


# --- event errors ----------------------------------------------------------

def test_event_era_must_match_exactly():
    # Fuzzy matching here used to hide renames and silently move events.
    d = _doc()
    d["events"][0]["era_name"] = "early"
    assert any("matches no era" in x for x in errs(d))


def test_unknown_category_is_an_error():
    d = _doc()
    d["events"][0]["categories"] = ["Sporting"]
    assert any("unknown category" in x for x in errs(d))


def test_half_a_coordinate_pair_is_an_error():
    d = _doc()
    d["events"][0]["lng"] = None
    assert any("only one of lat/lng" in x for x in errs(d))


def test_out_of_range_coordinates_are_errors():
    d = _doc()
    d["events"][0]["lat"] = 91
    assert any("lat 91 out of range" in x for x in errs(d))
    d = _doc()
    d["events"][0]["lng"] = 181
    assert any("lng 181 out of range" in x for x in errs(d))


def test_duplicate_titles_are_an_error():
    d = _doc()
    d["events"][1]["title"] = "One"
    assert any("duplicate title" in x for x in errs(d))


def test_empty_title_is_an_error():
    d = _doc()
    d["events"][0]["title"] = "   "
    assert any("empty title" in x for x in errs(d))


# --- warnings must NOT be errors -------------------------------------------

def test_event_outside_its_era_warns_but_does_not_fail():
    """Precursor events are filed narratively on purpose - Iceland's pre-874
    voyages sit in the Settlement Age. This must never fail a build."""
    d = _doc()
    d["events"][0]["sort_year"] = -5
    e, w = validate(d, "t")
    assert e == []
    assert any("outside its era" in x for x in w)


def test_whole_year_comparison_tolerates_a_fractional_sort_year():
    # 100.4 is inside an era ending at 100 - the fraction only orders events
    # within the year and must not trip the range check.
    d = _doc()
    d["events"][0]["sort_year"] = 100.4
    d["events"][0]["era_name"] = "Early"
    e, w = validate(d, "t")
    assert e == []
    assert not any("outside its era" in x for x in w)


def test_unsorted_events_warn():
    d = _doc()
    d["events"][0]["sort_year"] = 199
    assert any("not sorted by sort_year" in x for x in warns(d))


# --- source citations -------------------------------------------------------
#
# Every one of these was checked to FAIL before the rule existed - see the
# mutation list in CLAUDE.md. A citation test that cannot go red is worthless,
# because the whole point of the field is that nobody re-reads 290 of them.

def test_major_event_without_a_source_is_an_error():
    d = _doc()
    del d["events"][0]["source"]
    assert any("is_major but has no source" in x for x in errs(d))


def test_minor_event_without_a_source_is_fine():
    d = _doc()
    d["events"][1].pop("source", None)
    assert errs(d) == []


def test_source_given_as_a_url_is_an_error():
    d = _doc()
    d["events"][0]["source"] = "https://en.wikipedia.org/wiki/Knossos"
    assert any("store the article slug only" in x for x in errs(d))


def test_source_with_a_space_is_an_error():
    # Wikipedia accepts spaces in titles but the slug must be canonical, or
    # two spellings of the same article read as two different sources.
    d = _doc()
    d["events"][0]["source"] = "Battle of Marathon"
    assert any("use underscores" in x for x in errs(d))


def test_whitespace_only_source_is_an_error():
    d = _doc()
    d["events"][0]["source"] = "   "
    assert any("empty source" in x for x in errs(d))


def test_percent_escape_in_a_source_is_an_error():
    # The renderer runs encodeURIComponent, so a pre-encoded slug would be
    # double-encoded and 404.
    d = _doc()
    d["events"][0]["source"] = "Battle_of_Marathon%20"
    assert any("not a valid article slug" in x for x in errs(d))


def test_a_slug_with_an_en_dash_or_diacritic_is_accepted():
    # The no-dash house rule does not reach this field: the article really is
    # "Egyptian-en-dash-Hittite peace treaty" and a hyphen version does not exist.
    for slug in ["Egyptian–Hittite_peace_treaty", "Jōmon_period",
                 "2013_Egyptian_coup_d'état", "Poynings'_Law"]:
        d = _doc()
        d["events"][0]["source"] = slug
        assert errs(d) == [], slug


# --- ten eras ---------------------------------------------------------------

def test_eleven_eras_is_an_error():
    d = _doc()
    extra = dict(d["eras"][-1], name="Extra", short_name="X", sort_order=10,
                 width_pct=0)
    d["eras"].append(extra)
    assert any("expected 10" in x for x in errs(d))


def test_nine_eras_is_an_error():
    # The low tail matters too: nine eras looks unfinished next to the others,
    # and the old prose rule only ever got read as "do not exceed ten".
    d = _doc()
    gone = d["eras"].pop()
    d["eras"][-1]["width_pct"] += gone["width_pct"]
    assert any("expected 10" in x for x in errs(d))


# --- no en or em dashes in rendered text ------------------------------------
#
# The house rule bans both characters anywhere a reader sees them. `source` is
# exempt: a slug has to match the Wikipedia title, and some titles contain one.

def test_en_dash_in_a_title_is_an_error():
    d = _doc()
    d["events"][0]["title"] = "One–Two"
    assert any("en or em dash" in x for x in errs(d))


def test_em_dash_in_a_description_is_an_error():
    d = _doc()
    d["events"][0]["description"] = "A thing — and another."
    assert any("en or em dash" in x for x in errs(d))


def test_en_dash_in_display_date_is_an_error():
    d = _doc()
    d["events"][0]["display_date"] = "50–60"
    assert any("en or em dash" in x for x in errs(d))


def test_en_dash_in_an_era_label_is_an_error():
    d = _doc()
    d["eras"][0]["date_label"] = "0–100"
    assert any("en or em dash" in x for x in errs(d))


def test_en_dash_inside_a_source_slug_is_allowed():
    d = _doc()
    d["events"][0]["source"] = "East–West_Schism"
    assert errs(d) == []


# --- the is_major band ------------------------------------------------------

def _with_major_ratio(n_major, n_total):
    """A doc with exactly n_major of n_total events flagged."""
    d = _doc()
    d["events"] = [
        {"id": i, "era_name": "Early", "sort_year": 50, "display_date": "50",
         "title": f"Event {i}", "categories": [], "lat": None, "lng": None,
         "is_major": i < n_major,
         **({"source": f"Article_{i}"} if i < n_major else {})}
        for i in range(n_total)
    ]
    return d


def test_too_few_key_events_is_an_error():
    # Taiwan sat at 13% for months because the old check was one-tailed.
    assert any("outside 25%-55%" in x for x in errs(_with_major_ratio(13, 100)))


def test_too_many_key_events_is_an_error():
    assert any("outside 25%-55%" in x for x in errs(_with_major_ratio(80, 100)))


def test_slightly_off_target_warns_but_does_not_fail():
    d = _with_major_ratio(50, 100)
    assert errs(d) == []
    assert any("aim for 35%-45%" in x for x in warns(d))


def test_on_target_is_clean():
    d = _with_major_ratio(40, 100)
    assert errs(d) == []
    assert not any("is_major" in x for x in warns(d))


# --- truncated titles ------------------------------------------------------
#
# Taiwan had 62 of these because its titles came from splitting each description
# on "." - which cut at decimal points, so "Taiwan receives $1" stood in for
# $1.5 billion. The data was fixed 20/08/2026; these stop an import putting it back.

def test_a_title_ending_in_an_ellipsis_is_an_error():
    d = _doc()
    d["events"][0]["title"] = "Something happens and then..."
    assert any("truncated" in x for x in errs(d))


def test_a_title_ending_in_a_colon_is_an_error():
    d = _doc()
    d["events"][0]["title"] = "Dutch legacy:"
    assert any("truncated" in x for x in errs(d))


def test_a_title_stopping_mid_number_is_an_error():
    for bad in ["Aid received of $1", "Rents capped at (37", "Settlers numbering ~2"]:
        d = _doc()
        d["events"][0]["title"] = bad
        assert any("mid-number" in x for x in errs(d)), bad


def test_a_number_at_the_end_of_a_normal_title_is_fine():
    # The check must not fire on a title that legitimately ends in a figure.
    for good in ["Martial law lifted after 40 years", "Koxinga dies at age 37",
                 "Ma Ying-jeou wins the presidency with 58.5%"]:
        d = _doc()
        d["events"][0]["title"] = good
        assert errs(d) == [], good


def test_an_unbalanced_quote_in_a_title_is_an_error():
    # Taiwan had two titles cut at their closing quote mark.
    d = _doc()
    d["events"][0]["title"] = 'Described as "a state of rebellion'
    assert any("unbalanced quote" in x for x in errs(d))


def test_a_balanced_quote_in_a_title_is_fine():
    d = _doc()
    d["events"][0]["title"] = 'Described as "a state of rebellion"'
    assert errs(d) == []


# --- permanent event ids ----------------------------------------------------
#
# The id used to be the array index in build.py, so moving or inserting one
# event silently renumbered every later event and broke their
# /country/#event-N deep links. It now lives in the data and never changes.
# Each of these was checked to FAIL with the validator rule removed.

def test_missing_id_is_an_error():
    d = _doc()
    del d["events"][1]["id"]
    assert any("missing 'id'" in x for x in errs(d))


def test_duplicate_ids_are_an_error():
    d = _doc()
    d["events"][1]["id"] = d["events"][0]["id"]
    assert any("duplicate event ids" in x for x in errs(d))


def test_a_negative_id_is_an_error():
    d = _doc()
    d["events"][0]["id"] = -1
    assert any("negative id" in x for x in errs(d))


def test_a_non_integer_id_is_an_error():
    d = _doc()
    d["events"][0]["id"] = "7"
    assert any("non-integer" in x for x in errs(d))


def test_ids_need_not_match_the_array_order():
    # The whole point: an event can be moved without renumbering anything.
    d = _doc()
    d["events"][0]["id"], d["events"][1]["id"] = 99, 98
    assert errs(d) == []
