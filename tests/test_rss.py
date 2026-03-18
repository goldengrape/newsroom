import json

from newsroom import rss


def test_fetch_rss_feeds_success(monkeypatch, tmp_path):
    class MockEntry:
        def __init__(self, link="http://example.com/test"):
            self._data = {
                "title": "Test Title",
                "link": link,
                "summary": "Test Summary",
                "published": "Thu, 26 Feb 2026 12:00:00 +0000",
                "updated": "Thu, 26 Feb 2026 12:00:00 +0000",
            }

        def get(self, key, default=None):
            return self._data.get(key, default)

    class MockFeed:
        bozo = 0
        entries = [MockEntry(), MockEntry("http://example.com/test2")]

    monkeypatch.setattr(rss.feedparser, "parse", lambda *_args, **_kwargs: MockFeed())

    # First fetch
    seen_links_file = tmp_path / "seen_links.json"
    results = rss.fetch_rss_feeds(
        {"Test Source": "http://example.com/feed"}, seen_links_file=seen_links_file
    )

    assert len(results) == 2
    assert {"http://example.com/test", "http://example.com/test2"} == set(
        json.loads(seen_links_file.read_text())
    )

    # Second fetch, should use seen_links and return empty
    results2 = rss.fetch_rss_feeds(
        {"Test Source": "http://example.com/feed"}, seen_links_file=seen_links_file
    )
    assert len(results2) == 0

    # Third fetch with a new feed entry added
    class MockFeed2:
        bozo = 0
        entries = [
            MockEntry(),
            MockEntry("http://example.com/test2"),
            MockEntry("http://example.com/test3"),
        ]

    monkeypatch.setattr(rss.feedparser, "parse", lambda *_args, **_kwargs: MockFeed2())
    results3 = rss.fetch_rss_feeds(
        {"Test Source": "http://example.com/feed"}, seen_links_file=seen_links_file
    )
    assert len(results3) == 1
    assert results3[0]["link"] == "http://example.com/test3"
    assert {
        "http://example.com/test",
        "http://example.com/test2",
        "http://example.com/test3",
    } == set(json.loads(seen_links_file.read_text()))


def test_fetch_rss_feeds_error(monkeypatch):
    def raise_error(*_args, **_kwargs):
        raise Exception("Parsing Error")

    monkeypatch.setattr(rss.feedparser, "parse", raise_error)

    results = rss.fetch_rss_feeds({"Error Source": "http://example.com/error"})

    assert results == []


def test_save_news_to_json(tmp_path):
    output_path = tmp_path / "test_output.json"
    payload = [{"source": "Test", "title": "Test"}]

    rss.save_news_to_json(payload, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == payload
