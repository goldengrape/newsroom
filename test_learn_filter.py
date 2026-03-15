import argparse
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import learn_filter


class TestLearnFilterHelpers(unittest.TestCase):
    def test_validate_feedback_items_normalizes_values(self):
        items = learn_filter.validate_feedback_items(
            [
                {
                    "date": "2026-03-14",
                    "title": "Example Title",
                    "result": "LIKE",
                }
            ]
        )
        self.assertEqual(
            items,
            [
                {
                    "date": "2026-03-14",
                    "title": "Example Title",
                    "result": "like",
                }
            ],
        )

    def test_validate_feedback_items_rejects_bad_shape(self):
        with self.assertRaises(ValueError):
            learn_filter.validate_feedback_items(
                [{"date": "2026-03-14", "title": "Missing result"}]
            )

    def test_extract_profile_markdown_splits_diagnosis_and_markdown(self):
        diagnosis, markdown = learn_filter.extract_profile_markdown(
            "- tightened clinical noise gate\n\n```markdown\n# Updated Profile\n```"
        )
        self.assertIn("tightened", diagnosis)
        self.assertEqual(markdown, "# Updated Profile")

    def test_build_learning_prompt_contains_profile_and_feedback(self):
        prompt = learn_filter.build_learning_prompt(
            "# Current Profile",
            [{"date": "2026-03-14", "title": "A Title", "result": "like"}],
        )
        self.assertIn("# Current Profile", prompt)
        self.assertIn('"result": "like"', prompt)


class TestLearnFilterMain(unittest.TestCase):
    def test_main_writes_updated_profile_and_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            profile_path = temp_path / "FILTER_PROFILE.md"
            feedback_path = temp_path / "feedback.json"
            output_path = temp_path / "FILTER_PROFILE.updated.md"
            report_path = temp_path / "report.md"

            profile_path.write_text("# Old Profile\n", encoding="utf-8")
            feedback_path.write_text(
                '[{"date": "2026-03-14", "title": "A Title", "result": "like"}]',
                encoding="utf-8",
            )

            fake_args = argparse.Namespace(
                profile=str(profile_path),
                feedback=str(feedback_path),
                output=str(output_path),
                report_output=str(report_path),
                model=learn_filter.DEFAULT_MODEL,
                api_key_env="GEMINI_API_KEY",
                request_timeout=learn_filter.DEFAULT_REQUEST_TIMEOUT,
                max_retries=learn_filter.DEFAULT_MAX_RETRIES,
            )

            with patch.dict(os.environ, {"GEMINI_API_KEY": "from_env"}, clear=False):
                with patch("learn_filter.parse_args", return_value=fake_args):
                    with patch("learn_filter.load_dotenv"):
                        with patch("learn_filter.LearnFilterEngine") as mock_engine:
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

                            learn_filter.main()

            self.assertEqual(output_path.read_text(encoding="utf-8"), "# New Profile\n")
            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("added a stricter gate", report_text)
            self.assertIn('"prompt_tokens_actual": 10', report_text)


if __name__ == "__main__":
    unittest.main()
