import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from newsroom.filtering import (
    DEFAULT_MODEL,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    align_google_genai_env,
    load_dotenv,
)
from newsroom.paths import DATA_DIR

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - handled at runtime.
    genai = None
    genai_types = None


DEFAULT_OUTPUT = str(DATA_DIR / "FILTER_PROFILE.updated.md")
DEFAULT_REPORT_OUTPUT = str(DATA_DIR / "FILTER_PROFILE.learning_report.md")

MODEL_PRICING_USD_PER_MILLION = {
    "gemini-flash-lite-latest": {
        "input": 0.10,
        "output": 0.40,
    }
}

LEARN_SYSTEM_PROMPT = """
Role: Advanced algorithm tuning expert and intelligence architect.

Goal:
Use the latest user feedback to refine the current plain-text filtering protocol without changing its core persona.

Output requirements:
1. First provide concise diagnosis and rule-change logic as bullet points.
2. Then output the full updated FILTER_PROFILE.md inside one fenced markdown code block.
3. Preserve the original markdown hierarchy and append an iteration changelog section at the end.
4. Make pattern-level rule updates instead of brittle keyword-only edits.
""".strip()


def load_feedback_file(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array.")
    return payload


def validate_feedback_items(
    feedback_items: list[dict[str, Any]],
) -> list[dict[str, str]]:
    normalized = []
    for index, item in enumerate(feedback_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Feedback item #{index} must be an object.")

        date = str(item.get("date", "")).strip()
        title = str(item.get("title", "")).strip()
        result = str(item.get("result", "")).strip().lower()

        if not date or not title or result not in {"like", "dislike"}:
            raise ValueError(
                f"Feedback item #{index} must contain date, title, and result=like/dislike."
            )

        normalized.append(
            {
                "date": date,
                "title": title,
                "result": result,
            }
        )

    if not normalized:
        raise ValueError("Feedback file is empty.")

    return normalized


def build_learning_prompt(
    current_profile: str, feedback_items: list[dict[str, str]]
) -> str:
    return f"""
# Role: Advanced algorithm tuning expert and intelligence architect

## Task Objective
Your task is to iterate and tune the current content filtering profile using the latest user reading feedback.
You need to extract deep preference signals from the feedback, convert them into explicit filtering rules,
and produce a full updated markdown profile.

## Input Data
1. [CURRENT_PROFILE]
```markdown
{current_profile}
```

2. [USER_FEEDBACK]
```json
{json.dumps(feedback_items, ensure_ascii=False, indent=2)}
```

## Processing Workflow

### Step 1: Preference Diagnosis
- Analyze all result == "like" entries and extract strengthened or newly revealed interest anchors.
- Analyze all result == "dislike" entries and identify the noise patterns that slipped through.
- Compare these patterns against [CURRENT_PROFILE] and identify:
  - false positives: why disliked items passed
  - uncovered positives: where liked items are not explicitly protected

### Step 2: Rule Refactoring
- Adjust PASS_GATES and BLOCK_GATES with pattern-level rules, not brittle one-off keywords.
- Tighten rules for the disliked patterns.
- Expand or clarify protection for the liked patterns.
- Preserve the core persona: bottom-layer logic, anti-PR bias, engineering-first signal extraction.

### Step 3: Output
- Output the full updated FILTER_PROFILE.md.
- Preserve the original markdown structure, headers, and hierarchy.
- Add a final section named exactly: ## 4. Iteration Changelog
- In that section, summarize the key rule changes in cold, objective engineering language.

## Output Format Constraints
1. First output a concise diagnosis and change rationale as bullet points.
2. Then output the full updated FILTER_PROFILE.md inside one fenced markdown code block.
""".strip()


def extract_profile_markdown(response_text: str) -> tuple[str, str]:
    text = (response_text or "").strip()
    if not text:
        raise ValueError("Model response was empty.")

    match = re.search(r"```markdown\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if not match:
        raise ValueError("Model response did not contain a fenced markdown block.")

    markdown = match.group(1).strip()
    diagnosis = text[: match.start()].strip()
    return diagnosis, markdown


def estimate_cost_usd(
    model: str, input_tokens: int | None, output_tokens: int | None
) -> float | None:
    pricing = MODEL_PRICING_USD_PER_MILLION.get(model)
    if pricing is None:
        return None
    input_cost = (input_tokens or 0) * pricing["input"] / 1_000_000
    output_cost = (output_tokens or 0) * pricing["output"] / 1_000_000
    return input_cost + output_cost


class LearnFilterEngine:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        client: Any | None = None,
    ) -> None:
        if genai is None:
            raise RuntimeError(
                "The 'google-genai' package is not installed. Run 'pip install -r requirements.txt' first."
            )
        self.model = model
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.client = client or genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> tuple[str, dict[str, Any]]:
        if genai_types is None:
            raise RuntimeError(
                "The 'google-genai' package is not installed. Run 'pip install -r requirements.txt' first."
            )

        last_error = None
        started_at = time.perf_counter()
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=LEARN_SYSTEM_PROMPT,
                        temperature=0.2,
                        thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
                        http_options=genai_types.HttpOptions(
                            timeout=self.request_timeout * 1000
                        ),
                    ),
                )
                text = (getattr(response, "text", "") or "").strip()
                usage = getattr(response, "usage_metadata", None)
                prompt_tokens = getattr(usage, "prompt_token_count", None)
                completion_tokens = getattr(usage, "candidates_token_count", None)
                return text, {
                    "elapsed_seconds": time.perf_counter() - started_at,
                    "prompt_tokens_actual": prompt_tokens,
                    "completion_tokens_actual": completion_tokens,
                    "total_tokens_actual": getattr(usage, "total_token_count", None),
                    "estimated_total_cost_usd": estimate_cost_usd(
                        self.model,
                        prompt_tokens,
                        completion_tokens,
                    ),
                }
            except (
                Exception
            ) as error:  # pragma: no cover - runtime network/API behavior.
                last_error = error
                if attempt == self.max_retries:
                    break
                time.sleep(min(2 ** (attempt - 1), 8))

        raise RuntimeError(
            f"Gemini request failed during filter learning after {self.max_retries} attempts."
        ) from last_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Learn and refine FILTER_PROFILE.md from exported feedback JSON."
    )
    parser.add_argument(
        "--profile",
        default=str(DATA_DIR / "FILTER_PROFILE.md"),
        help="Path to the current filter profile markdown file.",
    )
    parser.add_argument(
        "--feedback",
        required=True,
        help="Path to the exported feedback JSON file.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Where to save the updated filter profile.",
    )
    parser.add_argument(
        "--report-output",
        default=DEFAULT_REPORT_OUTPUT,
        help="Where to save the diagnosis and raw learning report.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model name.",
    )
    parser.add_argument(
        "--api-key-env",
        default="GEMINI_API_KEY",
        help="Environment variable that stores the Gemini API key.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=DEFAULT_REQUEST_TIMEOUT,
        help="Per-request timeout in seconds for Gemini API calls.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help="How many times to retry a failed Gemini API request.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise RuntimeError(
            f"Missing API key. Please set the {args.api_key_env} environment variable first."
        )
    align_google_genai_env(api_key=api_key, api_key_env=args.api_key_env)

    profile_path = Path(args.profile)
    feedback_path = Path(args.feedback)
    output_path = Path(args.output)
    report_path = Path(args.report_output)

    current_profile = profile_path.read_text(encoding="utf-8")
    feedback_items = validate_feedback_items(load_feedback_file(feedback_path))
    prompt = build_learning_prompt(current_profile, feedback_items)

    engine = LearnFilterEngine(
        api_key=api_key,
        model=args.model,
        request_timeout=args.request_timeout,
        max_retries=args.max_retries,
    )
    response_text, metrics = engine.generate(prompt)
    diagnosis, updated_profile = extract_profile_markdown(response_text)

    output_path.write_text(updated_profile.rstrip() + "\n", encoding="utf-8")
    report_body = "\n\n".join(
        [
            "# Filter Learning Report",
            "## Diagnosis",
            diagnosis or "- No diagnosis bullets were returned.",
            "## Metrics",
            json.dumps(metrics, indent=2, ensure_ascii=False),
            "## Raw Model Output",
            response_text,
        ]
    )
    report_path.write_text(report_body.rstrip() + "\n", encoding="utf-8")

    print(f"Saved updated filter profile to {output_path}")
    print(f"Saved learning report to {report_path}")
    print(
        "Learning metrics: "
        f"input={metrics['prompt_tokens_actual'] if metrics['prompt_tokens_actual'] is not None else 'n/a'}, "
        f"output={metrics['completion_tokens_actual'] if metrics['completion_tokens_actual'] is not None else 'n/a'}, "
        f"elapsed={metrics['elapsed_seconds']:.2f}s, "
        f"cost~=USD{metrics['estimated_total_cost_usd']:.6f}"
        if metrics["estimated_total_cost_usd"] is not None
        else "Learning metrics unavailable."
    )


if __name__ == "__main__":
    main()
