import argparse
import html
import json
import os
import re
import time
import datetime
import email.utils
from math import ceil
from pathlib import Path
from typing import Any, Iterable

from newsroom.paths import DATA_DIR, DOCS_DATA_DIR, PROJECT_ROOT

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - handled at runtime when API access is needed.
    genai = None
    genai_types = None


DEFAULT_MODEL = "gemini-flash-lite-latest"
DEFAULT_MAX_ITEMS = 25
DEFAULT_BATCH_SIZE = 50
DEFAULT_RANKING_POOL_SIZE = 50
DEFAULT_MAX_TOKENS = 4096
DEFAULT_REQUEST_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 4
DEFAULT_STATS_OUTPUT = str(DOCS_DATA_DIR / "news_stats.json")
TITLE_SCREEN_MAX_TOKENS = 1024
RANKING_MAX_TOKENS = 2048
TRANSLATION_MAX_TOKENS = 3072

MODEL_PRICING_USD_PER_MILLION = {
    "gemini-flash-lite-latest": {
        "input": 0.10,
        "output": 0.40,
    }
}

SYSTEM_PROMPT = """
You are a strict news triage model.

Your job is to apply the plain-text filter profile exactly as written, select only the most relevant news, and produce concise Chinese summaries.

Rules:
1. Return valid JSON only.
2. Do not invent links, dates, or facts not present in the input.
3. Use the filter profile exactly as the decision policy.
4. Keep summaries concise, technical, and mechanism-focused.
""".strip()

TITLE_SCREENING_SCHEMA = {
    "type": "object",
    "properties": {
        "selected": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "integer"},
                },
                "required": ["id", "score"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["selected"],
    "additionalProperties": False,
}

RANKING_SCHEMA = {
    "type": "object",
    "properties": {
        "selected": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "rank": {"type": "integer"},
                    "score": {"type": "integer"},
                    "reason": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["id", "rank", "score", "reason", "summary"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["selected"],
    "additionalProperties": False,
}

TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {
        "selected": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["id", "title", "summary"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["selected"],
    "additionalProperties": False,
}


def strip_html(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text or "")
    cleaned = html.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def truncate_text(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    if limit <= 3:
        return "." * limit
    return text[: limit - 3].rstrip() + "..."


def prepare_news_items(news_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared = []
    for index, item in enumerate(news_items, start=1):
        prepared.append(
            {
                "id": str(index),
                "source": item.get("source", ""),
                "title": truncate_text(strip_html(item.get("title", "")), 240),
                "link": item.get("link", ""),
                "summary": truncate_text(strip_html(item.get("summary", "")), 900),
                "published": item.get("published", ""),
                "fetched_at": item.get("fetched_at", ""),
            }
        )
    return prepared


def prepare_title_screening_items(
    news_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [{"id": item["id"], "title": item["title"]} for item in news_items]


def prepare_ranking_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prepared = []
    for item in candidates:
        prepared.append(
            {
                "id": item["id"],
                "source": item["source"],
                "title": truncate_text(item["title"], 240),
                "summary": truncate_text(strip_html(item.get("summary", "")), 320),
                "published": item.get("published", ""),
            }
        )
    return prepared


def chunked(items: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def extract_json_payload(text: str) -> Any:
    candidate = (text or "").strip()
    if not candidate:
        raise ValueError("Model response was empty.")

    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
    if fenced_match:
        candidate = fenced_match.group(1).strip()

    decoder = json.JSONDecoder()
    starts = [match.start() for match in re.finditer(r"[\{\[]", candidate)] or [0]
    for start in starts:
        try:
            payload, _ = decoder.raw_decode(candidate[start:])
            return payload
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Unable to parse JSON from model response: {text[:400]}")


def load_json_file(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array.")
    return payload


def load_dotenv(path: Path = PROJECT_ROOT / ".env") -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def align_google_genai_env(api_key: str, api_key_env: str) -> None:
    if not api_key:
        return
    os.environ["GOOGLE_API_KEY"] = api_key
    if api_key_env != "GOOGLE_API_KEY":
        os.environ.pop("GEMINI_API_KEY", None)


def save_json_file(path: Path, payload: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def save_json_object(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def build_title_screening_prompt(
    filter_profile: str, batch: list[dict[str, Any]]
) -> str:
    return f"""
Apply this plain-text filter profile exactly as written:

<filter_profile>
{filter_profile}
</filter_profile>

Now do the first-pass screening on titles only.

Return JSON with this structure:
{{
  "selected": [
    {{
      "id": "1",
      "score": 0
    }}
  ]
}}

Rules:
1. Include only titles worth keeping for the next round.
2. score must be an integer from 0 to 100.
3. If a title matches a hard block gate, do not include it.
4. Drop pure funding, PR, marketing, gossip, or generic consumer-tech news.
5. This round uses titles only. Do not summarize or rewrite titles.
6. If nothing should be kept, return {{"selected": []}}.

Title list:
{json.dumps(batch, ensure_ascii=False, indent=2)}
""".strip()


def build_ranking_prompt(
    filter_profile: str,
    candidates: list[dict[str, Any]],
    max_items: int,
) -> str:
    return f"""
Apply this plain-text filter profile exactly as written and perform the final ranking.

<filter_profile>
{filter_profile}
</filter_profile>

Choose up to the top {max_items} items from the candidate set.

Return JSON with this structure:
{{
  "selected": [
    {{
      "id": "1",
      "rank": 1,
      "score": 0,
      "reason": "one short Chinese reason",
      "summary": "one concise Chinese summary"
    }}
  ]
}}

Rules:
1. rank starts at 1 and must be unique.
2. score must be an integer from 0 to 100.
3. reason must be short Chinese text explaining why this item matters.
4. summary must be concise Chinese text and stay grounded in the provided title and summary.
5. Prefer deep technical shifts, supply-chain changes, mechanism-level discoveries, and durable engineering value.
6. Remove duplicates and weak edge cases.
7. If nothing should be selected, return {{"selected": []}}.

Candidate news:
{json.dumps(candidates, ensure_ascii=False, indent=2)}
""".strip()


def build_translation_prompt(items: list[dict[str, Any]]) -> str:
    return f"""
Translate the following selected news items into concise, natural Chinese for publishing.

Return JSON with this structure:
{{
  "selected": [
    {{
      "id": "1",
      "title": "中文标题",
      "summary": "中文摘要"
    }}
  ]
}}

Rules:
1. Translate both the title and the summary into Chinese.
2. Preserve technical meaning and do not invent new facts.
3. Keep titles compact and readable.
4. Keep summaries concise, clear, and publication-ready.
5. If an original summary is too long or noisy, compress it into a short Chinese summary grounded in the original text.
6. Return one translated item for each input item.

Selected news:
{json.dumps(items, ensure_ascii=False, indent=2)}
""".strip()


class GeminiNewsFilter:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.latest_run_stats: dict[str, Any] = {}
        self.client = client or self._build_client(api_key=api_key)

    @staticmethod
    def _build_client(api_key: str) -> Any:
        if genai is None:
            raise RuntimeError(
                "The 'google-genai' package is not installed. Run 'pip install -r requirements.txt' first."
            )
        return genai.Client(api_key=api_key)

    @staticmethod
    def _extract_usage_metrics(response: Any) -> dict[str, int | None]:
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            return {
                "prompt_tokens_actual": None,
                "completion_tokens_actual": None,
                "total_tokens_actual": None,
            }

        return {
            "prompt_tokens_actual": getattr(usage, "prompt_token_count", None),
            "completion_tokens_actual": getattr(usage, "candidates_token_count", None),
            "total_tokens_actual": getattr(usage, "total_token_count", None),
        }

    @staticmethod
    def _extract_payload(response: Any) -> Any:
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, dict):
                return parsed
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump()

        text = getattr(response, "text", "") or ""
        if not text:
            raise ValueError("Gemini returned an empty response.")
        return extract_json_payload(text)

    @staticmethod
    def _estimate_cost_usd(
        model: str,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> dict[str, float | None]:
        pricing = MODEL_PRICING_USD_PER_MILLION.get(model)
        if pricing is None:
            return {
                "input_cost_usd": None,
                "output_cost_usd": None,
                "total_cost_usd": None,
            }

        input_tokens = input_tokens or 0
        output_tokens = output_tokens or 0
        input_cost = input_tokens * pricing["input"] / 1_000_000
        output_cost = output_tokens * pricing["output"] / 1_000_000
        return {
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
        }

    def _request_json(
        self,
        prompt: str,
        phase: str,
        batch_label: str,
        max_tokens_override: int,
        response_schema: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
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
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0,
                        thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
                        response_mime_type="application/json",
                        response_json_schema=response_schema,
                        max_output_tokens=max_tokens_override,
                        http_options=genai_types.HttpOptions(
                            timeout=self.request_timeout * 1000
                        ),
                    ),
                )
                payload = self._extract_payload(response)
                elapsed_seconds = time.perf_counter() - started_at
                usage_metrics = self._extract_usage_metrics(response)
                cost_metrics = self._estimate_cost_usd(
                    self.model,
                    usage_metrics["prompt_tokens_actual"],
                    usage_metrics["completion_tokens_actual"],
                )
                return payload, {
                    "provider": "gemini",
                    "phase": phase,
                    "batch_label": batch_label,
                    "estimated_input_tokens": usage_metrics["prompt_tokens_actual"],
                    "elapsed_seconds": elapsed_seconds,
                    **usage_metrics,
                    **cost_metrics,
                }
            except (
                Exception
            ) as error:  # pragma: no cover - retries cover runtime API failures.
                last_error = error
                if attempt == self.max_retries:
                    break
                time.sleep(min(2 ** (attempt - 1), 8))

        raise RuntimeError(
            f"Gemini request failed during {phase} after {self.max_retries} attempts."
        ) from last_error

    def _screen_title_batch(
        self,
        filter_profile: str,
        batch: list[dict[str, Any]],
        batch_label: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        payload, metrics = self._request_json(
            build_title_screening_prompt(filter_profile, batch),
            phase="title_screening",
            batch_label=batch_label,
            max_tokens_override=TITLE_SCREEN_MAX_TOKENS,
            response_schema=TITLE_SCREENING_SCHEMA,
        )
        results = payload.get("selected", []) if isinstance(payload, dict) else []
        keep_count = len(results)
        metrics["items_in_batch"] = len(batch)
        metrics["kept_in_batch"] = keep_count
        print(
            f"[title {batch_label}] items={len(batch)} kept={keep_count} "
            f"input={metrics['prompt_tokens_actual'] if metrics['prompt_tokens_actual'] is not None else 'n/a'} "
            f"output={metrics['completion_tokens_actual'] if metrics['completion_tokens_actual'] is not None else 'n/a'} "
            f"elapsed={metrics['elapsed_seconds']:.2f}s "
            f"cost~=USD{metrics['total_cost_usd']:.6f}"
            if metrics["total_cost_usd"] is not None
            else f"[title {batch_label}] items={len(batch)} kept={keep_count} "
            f"input={metrics['prompt_tokens_actual'] if metrics['prompt_tokens_actual'] is not None else 'n/a'} "
            f"output={metrics['completion_tokens_actual'] if metrics['completion_tokens_actual'] is not None else 'n/a'} "
            f"elapsed={metrics['elapsed_seconds']:.2f}s"
        )
        return results, [metrics]

    def _translate_final_items(
        self,
        final_items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        translation_input = [
            {
                "id": item["id"],
                "title": truncate_text(item.get("title", ""), 240),
                "summary": truncate_text(strip_html(item.get("summary", "")), 500),
            }
            for item in final_items
        ]
        payload, metrics = self._request_json(
            build_translation_prompt(translation_input),
            phase="translation",
            batch_label="1/1",
            max_tokens_override=TRANSLATION_MAX_TOKENS,
            response_schema=TRANSLATION_SCHEMA,
        )
        translated = payload.get("selected", []) if isinstance(payload, dict) else []
        metrics["items_in_batch"] = len(final_items)
        metrics["kept_in_batch"] = len(translated)
        print(
            f"[translation] items={len(final_items)} translated={len(translated)} "
            f"input={metrics['prompt_tokens_actual'] if metrics['prompt_tokens_actual'] is not None else 'n/a'} "
            f"output={metrics['completion_tokens_actual'] if metrics['completion_tokens_actual'] is not None else 'n/a'} "
            f"elapsed={metrics['elapsed_seconds']:.2f}s "
            f"cost~=USD{metrics['total_cost_usd']:.6f}"
            if metrics["total_cost_usd"] is not None
            else f"[translation] items={len(final_items)} translated={len(translated)} "
            f"input={metrics['prompt_tokens_actual'] if metrics['prompt_tokens_actual'] is not None else 'n/a'} "
            f"output={metrics['completion_tokens_actual'] if metrics['completion_tokens_actual'] is not None else 'n/a'} "
            f"elapsed={metrics['elapsed_seconds']:.2f}s"
        )
        translated_by_id = {
            str(item.get("id", "")): item
            for item in translated
            if isinstance(item, dict) and item.get("id")
        }
        merged_items = []
        for item in final_items:
            translated_item = translated_by_id.get(item["id"], {})
            merged = dict(item)
            merged["title"] = translated_item.get("title") or item["title"]
            merged["summary"] = translated_item.get("summary") or item["summary"]
            merged_items.append(merged)
        return merged_items, metrics

    def judge(
        self,
        news_items: list[dict[str, Any]],
        filter_profile: str,
        max_items: int = DEFAULT_MAX_ITEMS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        ranking_pool_size: int = DEFAULT_RANKING_POOL_SIZE,
    ) -> list[dict[str, Any]]:
        run_started_at = time.perf_counter()
        prepared_items = prepare_news_items(news_items)
        screening_items = prepare_title_screening_items(prepared_items)
        keep_candidates: list[dict[str, Any]] = []
        request_stats: list[dict[str, Any]] = []
        total_batches = max(1, ceil(len(screening_items) / batch_size))

        print(
            f"Starting title-only screening for {len(screening_items)} items "
            f"with batch_size={batch_size} across {total_batches} batches."
        )
        original_items_by_id = {item["id"]: item for item in prepared_items}

        for batch_index, batch in enumerate(
            chunked(screening_items, batch_size), start=1
        ):
            batch_label = f"{batch_index}/{total_batches}"
            results, batch_stats = self._screen_title_batch(
                filter_profile=filter_profile,
                batch=batch,
                batch_label=batch_label,
            )
            decisions_by_id = {
                str(result.get("id", "")): result
                for result in results
                if isinstance(result, dict) and result.get("id")
            }

            for item in batch:
                decision = decisions_by_id.get(item["id"])
                if not decision:
                    continue

                original_item = original_items_by_id[item["id"]]
                keep_candidates.append(
                    {
                        "id": item["id"],
                        "source": original_item["source"],
                        "title": original_item["title"],
                        "link": original_item["link"],
                        "summary": original_item["summary"],
                        "published": original_item["published"],
                        "fetched_at": original_item["fetched_at"],
                        "score": int(decision.get("score", 0)),
                        "judgement_reason": "",
                    }
                )

            request_stats.extend(batch_stats)

        deduped_candidates = self._dedupe_candidates(keep_candidates)
        if not deduped_candidates:
            self.latest_run_stats = self._build_run_stats(
                total_items=len(prepared_items),
                batch_size=batch_size,
                keep_candidates=0,
                ranking_pool_size=0,
                request_stats=request_stats,
                duration_seconds=time.perf_counter() - run_started_at,
            )
            return []

        ranked_pool = sorted(
            deduped_candidates,
            key=lambda item: (item.get("score", 0), item.get("published", "")),
            reverse=True,
        )[: max(max_items, ranking_pool_size)]
        ranking_target_count = min(max_items, len(ranked_pool))

        payload, ranking_metrics = self._request_json(
            build_ranking_prompt(
                filter_profile,
                prepare_ranking_candidates(ranked_pool),
                ranking_target_count,
            ),
            phase="ranking",
            batch_label="1/1",
            max_tokens_override=RANKING_MAX_TOKENS,
            response_schema=RANKING_SCHEMA,
        )
        selected = payload.get("selected", []) if isinstance(payload, dict) else []
        ranking_metrics["items_in_batch"] = len(ranked_pool)
        ranking_metrics["kept_in_batch"] = len(selected)
        request_stats.append(ranking_metrics)
        print(
            f"[ranking] candidates={len(ranked_pool)} selected={len(selected)} "
            f"input={ranking_metrics['prompt_tokens_actual'] if ranking_metrics['prompt_tokens_actual'] is not None else 'n/a'} "
            f"output={ranking_metrics['completion_tokens_actual'] if ranking_metrics['completion_tokens_actual'] is not None else 'n/a'} "
            f"elapsed={ranking_metrics['elapsed_seconds']:.2f}s "
            f"cost~=USD{ranking_metrics['total_cost_usd']:.6f}"
            if ranking_metrics["total_cost_usd"] is not None
            else f"[ranking] candidates={len(ranked_pool)} selected={len(selected)} "
            f"input={ranking_metrics['prompt_tokens_actual'] if ranking_metrics['prompt_tokens_actual'] is not None else 'n/a'} "
            f"output={ranking_metrics['completion_tokens_actual'] if ranking_metrics['completion_tokens_actual'] is not None else 'n/a'} "
            f"elapsed={ranking_metrics['elapsed_seconds']:.2f}s"
        )

        ranked = self._merge_ranked_candidates(ranked_pool, selected, max_items)
        final_items = ranked if ranked else ranked_pool[:max_items]
        translated_final_items, translation_metrics = self._translate_final_items(
            final_items
        )
        request_stats.append(translation_metrics)
        self.latest_run_stats = self._build_run_stats(
            total_items=len(prepared_items),
            batch_size=batch_size,
            keep_candidates=len(deduped_candidates),
            ranking_pool_size=len(ranked_pool),
            request_stats=request_stats,
            duration_seconds=time.perf_counter() - run_started_at,
        )
        self._print_run_summary()
        return translated_final_items

    def _build_run_stats(
        self,
        total_items: int,
        batch_size: int,
        keep_candidates: int,
        ranking_pool_size: int,
        request_stats: list[dict[str, Any]],
        duration_seconds: float,
    ) -> dict[str, Any]:
        total_input_tokens = sum(
            metric["prompt_tokens_actual"] or 0 for metric in request_stats
        )
        total_output_tokens = sum(
            metric["completion_tokens_actual"] or 0 for metric in request_stats
        )
        total_tokens = sum(
            metric["total_tokens_actual"] or 0 for metric in request_stats
        )
        total_cost_usd = sum(
            metric["total_cost_usd"] or 0.0 for metric in request_stats
        )
        total_input_cost_usd = sum(
            metric["input_cost_usd"] or 0.0 for metric in request_stats
        )
        total_output_cost_usd = sum(
            metric["output_cost_usd"] or 0.0 for metric in request_stats
        )
        return {
            "model": self.model,
            "total_items": total_items,
            "screening_batch_size": batch_size,
            "kept_candidates_after_screening": keep_candidates,
            "ranking_pool_size": ranking_pool_size,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "estimated_input_tokens": total_input_tokens,
            "actual_output_tokens": total_output_tokens,
            "estimated_total_cost_usd": total_cost_usd,
            "input_cost_usd": total_input_cost_usd,
            "output_cost_usd": total_output_cost_usd,
            "duration_seconds": duration_seconds,
            "requests": request_stats,
        }

    def _print_run_summary(self) -> None:
        if not self.latest_run_stats:
            return

        stats = self.latest_run_stats
        print(
            "Run summary: "
            f"items={stats['total_items']}, "
            f"kept={stats['kept_candidates_after_screening']}, "
            f"input={stats['input_tokens']}, "
            f"output={stats['output_tokens']}, "
            f"cost~=USD{stats['estimated_total_cost_usd']:.6f}, "
            f"elapsed={stats['duration_seconds']:.2f}s"
        )

    @staticmethod
    def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            dedupe_key = candidate.get("link") or (
                f"{candidate.get('source', '')}::{candidate.get('title', '')}".lower()
            )
            existing = deduped.get(dedupe_key)
            if existing is None or candidate.get("score", 0) > existing.get("score", 0):
                deduped[dedupe_key] = candidate
        return list(deduped.values())

    @staticmethod
    def _merge_ranked_candidates(
        ranked_pool: list[dict[str, Any]],
        selections: list[dict[str, Any]],
        max_items: int,
    ) -> list[dict[str, Any]]:
        pool_by_id = {item["id"]: dict(item) for item in ranked_pool}
        merged: list[tuple[int, dict[str, Any]]] = []

        for selection in selections:
            if not isinstance(selection, dict):
                continue
            item = pool_by_id.get(str(selection.get("id", "")))
            if item is None:
                continue
            item["score"] = int(selection.get("score", item.get("score", 0)))
            item["summary"] = selection.get("summary") or item["summary"]
            item["judgement_reason"] = (
                selection.get("reason") or item.get("judgement_reason", "")
            ).strip()
            rank = int(selection.get("rank", len(merged) + 1))
            merged.append((rank, item))

        merged.sort(key=lambda pair: pair[0])
        return [item for _, item in merged[:max_items]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use Gemini Flash Lite to filter RSS news with the text filter profile."
    )
    parser.add_argument(
        "--input",
        default=str(DATA_DIR / "raw_news.json"),
        help="Input JSON file path.",
    )
    parser.add_argument(
        "--output",
        default=str(DOCS_DATA_DIR / "news.json"),
        help="Output JSON file path for the static site.",
    )
    parser.add_argument(
        "--filter-profile",
        default=str(DATA_DIR / "FILTER_PROFILE.md"),
        help="Path to the plain text filter profile.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model name.")
    parser.add_argument(
        "--api-key-env",
        default="GEMINI_API_KEY",
        help="Environment variable that stores the Gemini API key.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=DEFAULT_MAX_ITEMS,
        help="Maximum number of news items to keep.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="How many titles to send per first-pass screening batch.",
    )
    parser.add_argument(
        "--ranking-pool-size",
        type=int,
        default=DEFAULT_RANKING_POOL_SIZE,
        help="How many kept candidates to send into the final ranking pass.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum completion tokens per Gemini request.",
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
    parser.add_argument(
        "--stats-output",
        default=DEFAULT_STATS_OUTPUT,
        help="Where to save token, timing, and cost statistics as JSON.",
    )
    return parser.parse_args()


def parse_date(date_str: str) -> datetime.datetime:
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except (ValueError, TypeError):
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except (ValueError, TypeError):
            # Fallback to current time if unparseable
            return datetime.datetime.now(datetime.timezone.utc)


def is_within_days(date_str: str, days: int = 7) -> bool:
    if not date_str:
        return False
    dt = parse_date(date_str)
    now = datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return (now - dt).days <= days


def merge_and_truncate_news(
    existing_items: list[dict], new_items: list[dict], max_items: int
) -> list[dict]:
    # Filter out items older than 7 days from the existing ones
    valid_existing = [
        item for item in existing_items if is_within_days(item.get("published", ""), 7)
    ]

    # We want to dedup and merge them. The new items take precedence if there's a duplicate link.
    seen_links = set(item.get("link") for item in new_items if item.get("link"))
    for item in valid_existing:
        link = item.get("link")
        if link and link not in seen_links:
            new_items.append(item)
            seen_links.add(link)
        elif not link:
            # If no link, we just append it
            new_items.append(item)

    # Sort by published date descending
    new_items.sort(key=lambda x: parse_date(x.get("published", "")), reverse=True)

    # Truncate to max_items
    return new_items[:max_items]


def main() -> None:
    args = parse_args()
    load_dotenv()

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise RuntimeError(
            f"Missing API key. Please set the {args.api_key_env} environment variable first."
        )
    align_google_genai_env(api_key=api_key, api_key_env=args.api_key_env)

    input_path = Path(args.input)
    output_path = Path(args.output)
    filter_profile_path = Path(args.filter_profile)

    try:
        news_items = load_json_file(input_path)
    except Exception:
        news_items = []

    try:
        existing_news_items = load_json_file(output_path)
    except Exception:
        existing_news_items = []

    filter_profile = filter_profile_path.read_text(encoding="utf-8")

    judge = GeminiNewsFilter(
        api_key=api_key,
        model=args.model,
        max_tokens=args.max_tokens,
        request_timeout=args.request_timeout,
        max_retries=args.max_retries,
    )

    selected_items = []
    if news_items:
        selected_items = judge.judge(
            news_items=news_items,
            filter_profile=filter_profile,
            max_items=args.max_items,
            batch_size=args.batch_size,
            ranking_pool_size=args.ranking_pool_size,
        )
        save_json_object(Path(args.stats_output), judge.latest_run_stats)

    final_items = merge_and_truncate_news(
        existing_news_items, selected_items, args.max_items
    )

    save_json_file(output_path, final_items)
    print(f"Saved {len(final_items)} AI-filtered news items to {output_path}")
    if news_items:
        print(f"Saved run statistics to {args.stats_output}")


if __name__ == "__main__":
    main()
