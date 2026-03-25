import datetime
import email.utils
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

    now = datetime.datetime.now(datetime.timezone.utc)

    # offset-aware via email utils format
    old_date_dt = now - datetime.timedelta(days=6)
    old_date = email.utils.format_datetime(old_date_dt)

    # offset-aware via isoformat
    recent_date_dt = now - datetime.timedelta(days=2)
    recent_date = recent_date_dt.isoformat().replace("+00:00", "Z")

    # offset-naive via isoformat (should be handled properly now)
    new_date_dt = now - datetime.timedelta(days=1)
    new_date = new_date_dt.replace(tzinfo=None).isoformat()

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
