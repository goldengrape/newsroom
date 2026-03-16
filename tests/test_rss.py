import json

from newsroom import rss


def test_fetch_rss_feeds_success(monkeypatch):
    class MockEntry:
        def get(self, key, default=None):
            return {
                "title": "Test Title",
                "link": "http://example.com/test",
                "summary": "Test Summary",
                "published": "Thu, 26 Feb 2026 12:00:00 +0000",
                "updated": "Thu, 26 Feb 2026 12:00:00 +0000",
            }.get(key, default)

    class MockFeed:
        bozo = 0
        entries = [MockEntry()]

    monkeypatch.setattr(rss.feedparser, "parse", lambda *_args, **_kwargs: MockFeed())

    results = rss.fetch_rss_feeds({"Test Source": "http://example.com/feed"})

    assert len(results) == 1
    item = results[0]
    assert item["source"] == "Test Source"
    assert item["title"] == "Test Title"
    assert item["link"] == "http://example.com/test"
    assert item["summary"] == "Test Summary"
    assert "fetched_at" in item


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
