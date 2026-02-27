import unittest
from unittest.mock import patch, MagicMock
import fetch_rss
import json
import os

class TestFetchRSS(unittest.TestCase):

    @patch('feedparser.parse')
    def test_fetch_rss_feeds_success(self, mock_parse):
        # Create a mock feed object
        mock_feed = MagicMock()
        mock_feed.bozo = 0

        # Create a mock entry
        mock_entry = MagicMock()
        mock_entry.get.side_effect = lambda key, default=None: {
            "title": "Test Title",
            "link": "http://example.com/test",
            "summary": "Test Summary",
            "published": "Thu, 26 Feb 2026 12:00:00 +0000",
            "updated": "Thu, 26 Feb 2026 12:00:00 +0000"
        }.get(key, default)

        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        # Override the RSS_FEEDS dictionary for the test to use a dummy feed
        original_feeds = fetch_rss.RSS_FEEDS
        fetch_rss.RSS_FEEDS = {"Test Source": "http://example.com/feed"}

        try:
            results = fetch_rss.fetch_rss_feeds()

            self.assertEqual(len(results), 1)
            item = results[0]
            self.assertEqual(item['source'], "Test Source")
            self.assertEqual(item['title'], "Test Title")
            self.assertEqual(item['link'], "http://example.com/test")
            self.assertEqual(item['summary'], "Test Summary")
            self.assertIn("fetched_at", item)

        finally:
            # Restore original feeds
            fetch_rss.RSS_FEEDS = original_feeds

    @patch('feedparser.parse')
    def test_fetch_rss_feeds_error(self, mock_parse):
        # Simulate an exception during parsing
        mock_parse.side_effect = Exception("Parsing Error")

        original_feeds = fetch_rss.RSS_FEEDS
        fetch_rss.RSS_FEEDS = {"Error Source": "http://example.com/error"}

        try:
            # The function should handle the exception and continue (returning empty list for this source)
            results = fetch_rss.fetch_rss_feeds()
            self.assertEqual(len(results), 0)
        finally:
            fetch_rss.RSS_FEEDS = original_feeds

    def test_save_news_to_json(self):
        test_data = [{"source": "Test", "title": "Test"}]
        filename = "test_output.json"

        try:
            fetch_rss.save_news_to_json(test_data, filename)
            self.assertTrue(os.path.exists(filename))

            with open(filename, 'r') as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data, test_data)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == '__main__':
    unittest.main()
