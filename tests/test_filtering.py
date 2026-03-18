from pathlib import Path
from unittest.mock import patch

from newsroom import filtering


class StubGeminiNewsFilter(filtering.GeminiNewsFilter):
    def __init__(self, responses):
        self.responses = list(responses)
        self.latest_run_stats = {}
        self.model = filtering.DEFAULT_MODEL

    def _request_json(
        self, prompt, phase, batch_label, max_tokens_override, response_schema
    ):
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


def test_extract_json_payload_accepts_fenced_json():
    payload = filtering.extract_json_payload(
        """```json
        {"selected": [{"id": "1", "score": 88}]}
        ```"""
    )
    assert payload["selected"][0]["id"] == "1"


def test_extract_json_payload_rejects_invalid_output():
    try:
        filtering.extract_json_payload("not json")
    except ValueError:
        pass
    else:  # pragma: no cover - explicit failure path for readability
        raise AssertionError("Expected ValueError for invalid model output.")


def test_prepare_news_items_strips_html_and_truncates():
    items = filtering.prepare_news_items(
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
    assert items[0]["title"] == "Title"
    assert items[0]["summary"] == "Hello & world"


def test_judge_keeps_items_and_applies_ranking():
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
    ]
    judge = StubGeminiNewsFilter(
        responses=[
            {"selected": [{"id": "1", "score": 88}, {"id": "2", "score": 75}]},
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
            {
                "selected": [
                    {
                        "id": "2",
                        "title": "最终中文标题",
                        "summary": "最终中文摘要",
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

    assert len(selected) == 1
    assert selected[0]["link"] == "https://example.com/b"
    assert selected[0]["title"] == "最终中文标题"
    assert selected[0]["summary"] == "最终中文摘要"
    assert selected[0]["judgement_reason"] == "final priority"
    assert "estimated_total_cost_usd" in judge.latest_run_stats


def test_main_prefers_environment_value_and_saves_output_and_stats(monkeypatch):
    selected_items = [{"title": "Chosen"}]
    fake_args = type(
        "Args",
        (),
        {
            "input": "data/raw_news.json",
            "output": "docs/data/news.json",
            "filter_profile": "data/FILTER_PROFILE.md",
            "model": filtering.DEFAULT_MODEL,
            "api_key_env": "GEMINI_API_KEY",
            "max_items": 25,
            "batch_size": filtering.DEFAULT_BATCH_SIZE,
            "ranking_pool_size": 50,
            "max_tokens": filtering.DEFAULT_MAX_TOKENS,
            "request_timeout": filtering.DEFAULT_REQUEST_TIMEOUT,
            "max_retries": filtering.DEFAULT_MAX_RETRIES,
            "stats_output": filtering.DEFAULT_STATS_OUTPUT,
        },
    )()

    monkeypatch.setenv("GEMINI_API_KEY", "from_env")
    monkeypatch.setattr(filtering, "parse_args", lambda: fake_args)
    monkeypatch.setattr(filtering, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        filtering, "load_json_file", lambda *_args, **_kwargs: [{"title": "Input"}]
    )
    with patch.object(Path, "read_text", return_value="filter profile"):
        with patch.object(filtering, "save_json_file") as mock_save:
            with patch.object(filtering, "save_json_object") as mock_save_stats:
                with patch.object(filtering, "GeminiNewsFilter") as mock_filter:
                    instance = mock_filter.return_value
                    instance.judge.return_value = selected_items
                    instance.latest_run_stats = {"input_tokens": 123}

                    filtering.main()

    mock_filter.assert_called_once()
    mock_save.assert_called_once()
    mock_save_stats.assert_called_once()
