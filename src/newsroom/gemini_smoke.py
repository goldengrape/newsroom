import argparse
import os

from newsroom.filtering import DEFAULT_REQUEST_TIMEOUT, align_google_genai_env, load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - handled in main for manual smoke runs.
    genai = None
    types = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the Gemini API key and model.")
    parser.add_argument(
        "--model",
        default="gemini-flash-lite-latest",
        help="Gemini model name to test.",
    )
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: GEMINI_OK",
        help="Prompt sent to the model.",
    )
    parser.add_argument(
        "--api-key-env",
        default="GEMINI_API_KEY",
        help="Environment variable that stores the Gemini API key.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_REQUEST_TIMEOUT,
        help="Per-request timeout in seconds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise RuntimeError(
            f"Missing API key. Please set {args.api_key_env} in the environment or .env."
        )
    if genai is None or types is None:
        raise RuntimeError(
            "The 'google-genai' package is not installed. Run 'uv sync --dev' first."
        )

    align_google_genai_env(api_key=api_key, api_key_env=args.api_key_env)
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=args.model,
        contents=args.prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            http_options=types.HttpOptions(timeout=args.timeout * 1000),
        ),
    )

    print("Gemini API test succeeded.")
    print(f"Model: {args.model}")
    print(f"Response: {(response.text or '').strip()}")


if __name__ == "__main__":
    main()
