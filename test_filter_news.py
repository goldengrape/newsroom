import argparse
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import filter_news


class StubGeminiNewsFilter(filter_news.GeminiNewsFilter):
    def __init__(self, responses):
        self.responses = list(responses)
        self.latest_run_stats = {}
        self.model = filter_news.DEFAULT_MODEL

    def _request_json(self, prompt, phase, batch_label, max_tokens_override, response_schema):
        if not self.responses:
            raise AssertionError("No stubbed response left for prompt.")
        payload = self.responses.pop(0)
        return payload, {
            "provider": "gemini",
            "phase": phase,
            "batch_label": batch_label,
            "estimated_input_tokens": 100,
            "elapsed_seconds": 1.0,
            "prompt_tokens_actual": 100,
            "completion_tokens_actual": 20,
            "total_tokens_actual": 120,
            "input_cost_usd": 0.00001,
            "output_cost_usd": 0.000008,
            "total_cost_usd": 0.000018,
        }


class TestFilterNewsHelpers(unittest.TestCase):
    def test_extract_json_payload_accepts_fenced_json(self):
        payload = filter_news.extract_json_payload(
            """```json
            {"selected": [{"id": "1", "score": 88}]}
            ```"""
        )
        self.assertEqual(payload["selected"][0]["id"], "1")

    def test_extract_json_payload_rejects_invalid_output(self):
        with self.assertRaises(ValueError):
            filter_news.extract_json_payload("not json")

    def test_prepare_news_items_strips_html_and_truncates(self):
        items = filter_news.prepare_news_items(
            [
                {
                    "source": "Test",
                    "title": "<b>Title</b>",
                    "link": "https://example.com",
                    "summary": "<p>Hello &amp; world</p>",
                    "published": "2026-03-13",
                }
            ]
        )
        self.assertEqual(items[0]["title"], "Title")
        self.assertEqual(items[0]["summary"], "Hello & world")

    def test_load_dotenv_reads_file_without_overriding_existing_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "FROM_DOTENV=loaded\nEXISTING=from_file\n# comment line\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"EXISTING": "from_env"}, clear=False):
                os.environ.pop("FROM_DOTENV", None)
                filter_news.load_dotenv(env_path)

                self.assertEqual(os.environ["FROM_DOTENV"], "loaded")
                self.assertEqual(os.environ["EXISTING"], "from_env")

    def test_align_google_genai_env_prefers_google_api_key_only(self):
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "gemini-key", "GOOGLE_API_KEY": "other-key"},
            clear=False,
        ):
            filter_news.align_google_genai_env(
                api_key="gemini-key",
                api_key_env="GEMINI_API_KEY",
            )
            self.assertEqual(os.environ["GOOGLE_API_KEY"], "gemini-key")
            self.assertNotIn("GEMINI_API_KEY", os.environ)

    def test_estimate_cost_usd_uses_gemini_pricing(self):
        costs = filter_news.GeminiNewsFilter._estimate_cost_usd(
            filter_news.DEFAULT_MODEL,
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        self.assertEqual(costs["input_cost_usd"], 0.10)
        self.assertEqual(costs["output_cost_usd"], 0.40)
        self.assertEqual(costs["total_cost_usd"], 0.50)


class TestFilterNewsWorkflow(unittest.TestCase):
    def test_judge_keeps_items_and_applies_ranking(self):
        news_items = [
            {
                "source": "Source A",
                "title": "Article A",
                "link": "https://example.com/a",
                "summary": "Summary A",
                "published": "2026-03-13",
                "fetched_at": "2026-03-13T10:00:00",
            },
            {
                "source": "Source B",
                "title": "Article B",
                "link": "https://example.com/b",
                "summary": "Summary B",
                "published": "2026-03-12",
                "fetched_at": "2026-03-13T10:00:00",
            },
            {
                "source": "Source C",
                "title": "Article C",
                "link": "https://example.com/c",
                "summary": "Summary C",
                "published": "2026-03-11",
                "fetched_at": "2026-03-13T10:00:00",
            },
        ]
        judge = StubGeminiNewsFilter(
            responses=[
                {
                    "selected": [
                        {"id": "1", "score": 88},
                        {"id": "2", "score": 75},
                    ]
                },
                {
                    "selected": [
                        {
                            "id": "2",
                            "rank": 1,
                            "score": 91,
                            "reason": "final priority",
                            "summary": "Final B summary",
                        }
                    ]
                },
            ]
        )

        selected = judge.judge(
            news_items=news_items,
            filter_profile="text filter",
            max_items=1,
            batch_size=10,
            ranking_pool_size=10,
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["link"], "https://example.com/b")
        self.assertEqual(selected[0]["summary"], "Final B summary")
        self.assertEqual(selected[0]["judgement_reason"], "final priority")
        self.assertIn("estimated_total_cost_usd", judge.latest_run_stats)

    def test_judge_falls_back_to_screening_order_when_ranking_returns_empty(self):
        news_items = [
            {
                "source": "Source A",
                "title": "Article A",
                "link": "https://example.com/a",
                "summary": "Summary A",
                "published": "2026-03-13",
                "fetched_at": "2026-03-13T10:00:00",
            }
        ]
        judge = StubGeminiNewsFilter(
            responses=[
                {"selected": [{"id": "1", "score": 83}]},
                {"selected": []},
            ]
        )

        selected = judge.judge(
            news_items=news_items,
            filter_profile="text filter",
            max_items=5,
            batch_size=10,
            ranking_pool_size=10,
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["title"], "Article A")
        self.assertEqual(selected[0]["score"], 83)

    def test_main_prefers_environment_value_and_saves_output_and_stats(self):
        selected_items = [{"title": "Chosen"}]
        fake_args = argparse.Namespace(
            input="raw_news.json",
            output="docs/data/news.json",
            filter_profile="FILTER_PROFILE.md",
            model=filter_news.DEFAULT_MODEL,
            api_key_env="GEMINI_API_KEY",
            max_items=25,
            batch_size=filter_news.DEFAULT_BATCH_SIZE,
            ranking_pool_size=50,
            max_tokens=filter_news.DEFAULT_MAX_TOKENS,
            request_timeout=filter_news.DEFAULT_REQUEST_TIMEOUT,
            max_retries=filter_news.DEFAULT_MAX_RETRIES,
            stats_output=filter_news.DEFAULT_STATS_OUTPUT,
        )

        with patch.dict(os.environ, {"GEMINI_API_KEY": "from_env"}, clear=False):
            with patch("filter_news.parse_args", return_value=fake_args):
                with patch("filter_news.load_dotenv") as mock_load_dotenv:
                    with patch("filter_news.load_json_file", return_value=[{"title": "Input"}]):
                        with patch("pathlib.Path.read_text", return_value="filter profile"):
                            with patch("filter_news.save_json_file") as mock_save:
                                with patch("filter_news.save_json_object") as mock_save_stats:
                                    with patch("filter_news.GeminiNewsFilter") as mock_filter:
                                        instance = mock_filter.return_value
                                        instance.judge.return_value = selected_items
                                        instance.latest_run_stats = {"input_tokens": 123}

                                        filter_news.main()

        mock_load_dotenv.assert_called_once()
        mock_filter.assert_called_once_with(
            api_key="from_env",
            model=filter_news.DEFAULT_MODEL,
            max_tokens=filter_news.DEFAULT_MAX_TOKENS,
            request_timeout=filter_news.DEFAULT_REQUEST_TIMEOUT,
            max_retries=filter_news.DEFAULT_MAX_RETRIES,
        )
        instance.judge.assert_called_once()
        mock_save.assert_called_once()
        mock_save_stats.assert_called_once()
        self.assertEqual(mock_save.call_args.args[1], selected_items)


if __name__ == "__main__":
    unittest.main()
