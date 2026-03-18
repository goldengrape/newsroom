import datetime
from newsroom.filtering import merge_and_truncate_news


def test_merge_and_truncate_news():
    now = datetime.datetime.now(datetime.timezone.utc)

    old_date = (now - datetime.timedelta(days=8)).isoformat()
    recent_date = (now - datetime.timedelta(days=2)).isoformat()
    new_date = now.isoformat()

    existing = [
        {"title": "Old", "published": old_date, "link": "http://old"},
        {"title": "Recent", "published": recent_date, "link": "http://recent"},
        {"title": "Dup", "published": recent_date, "link": "http://dup"},
    ]

    new_items = [
        {"title": "New", "published": new_date, "link": "http://new"},
        {"title": "Dup New", "published": new_date, "link": "http://dup"},
    ]

    merged = merge_and_truncate_news(existing, new_items, 2)
    assert len(merged) == 2
    assert merged[0]["title"] == "New"
    assert (
        merged[1]["title"] == "Dup New"
    )  # It replaces existing Dup because new items take precedence and are sorted

    merged = merge_and_truncate_news(existing, new_items, 5)
    assert len(merged) == 3  # Old is filtered out (8 days old), and Dup is deduplicated


def test_merge_and_truncate_news_with_mixed_date_formats():

    # offset-aware via email utils format
    old_date = "Mon, 16 Mar 2026 20:30:00 GMT"

    # offset-aware via isoformat
    recent_date = "2026-03-20T20:30:00Z"

    # offset-naive via isoformat (should be handled properly now)
    new_date = "2026-03-24T20:30:00"

    existing = [
        {"title": "Old", "published": old_date, "link": "http://old"},
        {"title": "Recent", "published": recent_date, "link": "http://recent"},
    ]

    new_items = [
        {"title": "New", "published": new_date, "link": "http://new"},
    ]

    # It shouldn't crash, because parsing dates should normalize timezone info
    merged = merge_and_truncate_news(existing, new_items, 3)

    # After merging, they should be sorted by date descending
    assert len(merged) == 3
    assert merged[0]["title"] == "New"
    assert merged[1]["title"] == "Recent"
    assert merged[2]["title"] == "Old"
