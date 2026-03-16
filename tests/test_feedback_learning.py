from pathlib import Path
from unittest.mock import patch

from newsroom import feedback_learning


def test_validate_feedback_items_normalizes_values():
    items = feedback_learning.validate_feedback_items(
        [{"date": "2026-03-14", "title": "Example Title", "result": "LIKE"}]
    )
    assert items == [{"date": "2026-03-14", "title": "Example Title", "result": "like"}]


def test_validate_feedback_items_rejects_bad_shape():
    try:
        feedback_learning.validate_feedback_items(
            [{"date": "2026-03-14", "title": "Missing result"}]
        )
    except ValueError:
        pass
    else:  # pragma: no cover - explicit failure path for readability
        raise AssertionError("Expected ValueError for malformed feedback.")


def test_extract_profile_markdown_splits_diagnosis_and_markdown():
    diagnosis, markdown = feedback_learning.extract_profile_markdown(
        "- tightened clinical noise gate\n\n```markdown\n# Updated Profile\n```"
    )
    assert "tightened" in diagnosis
    assert markdown == "# Updated Profile"


def test_main_writes_updated_profile_and_report(tmp_path, monkeypatch):
    profile_path = tmp_path / "FILTER_PROFILE.md"
    feedback_path = tmp_path / "feedback.json"
    output_path = tmp_path / "FILTER_PROFILE.updated.md"
    report_path = tmp_path / "report.md"

    profile_path.write_text("# Old Profile\n", encoding="utf-8")
    feedback_path.write_text(
        '[{"date": "2026-03-14", "title": "A Title", "result": "like"}]',
        encoding="utf-8",
    )

    fake_args = type(
        "Args",
        (),
        {
            "profile": str(profile_path),
            "feedback": str(feedback_path),
            "output": str(output_path),
            "report_output": str(report_path),
            "model": feedback_learning.DEFAULT_MODEL,
            "api_key_env": "GEMINI_API_KEY",
            "request_timeout": feedback_learning.DEFAULT_REQUEST_TIMEOUT,
            "max_retries": feedback_learning.DEFAULT_MAX_RETRIES,
        },
    )()

    monkeypatch.setenv("GEMINI_API_KEY", "from_env")
    monkeypatch.setattr(feedback_learning, "parse_args", lambda: fake_args)
    monkeypatch.setattr(feedback_learning, "load_dotenv", lambda *args, **kwargs: None)
    with patch.object(feedback_learning, "LearnFilterEngine") as mock_engine:
        instance = mock_engine.return_value
        instance.generate.return_value = (
            "- added a stricter gate\n\n```markdown\n# New Profile\n```",
            {
                "elapsed_seconds": 1.2,
                "prompt_tokens_actual": 10,
                "completion_tokens_actual": 20,
                "total_tokens_actual": 30,
                "estimated_total_cost_usd": 0.00001,
            },
        )

        feedback_learning.main()

    assert output_path.read_text(encoding="utf-8") == "# New Profile\n"
    report_text = report_path.read_text(encoding="utf-8")
    assert "added a stricter gate" in report_text
    assert '"prompt_tokens_actual": 10' in report_text
