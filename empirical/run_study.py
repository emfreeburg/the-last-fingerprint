#!/usr/bin/env python3
"""
Em Dash Frequency Study
=======================
Generates prose samples from multiple LLMs and counts em dash frequency.
Used as empirical evidence in "The Last Fingerprint" paper.

Usage:
    export ANTHROPIC_API_KEY=...
    export OPENAI_API_KEY=...
    python3 run_study.py
"""

import json
import os
import sys
import time
from pathlib import Path

# --- Configuration ---

PROMPTS = [
    "Write a 500-word essay about the experience of moving to a new city as an adult. Write in flowing prose paragraphs only. Do not use any markdown formatting, headers, bullet points, or lists.",
    "Write a 500-word essay about why some people prefer cooking at home over eating at restaurants. Write in flowing prose paragraphs only. Do not use any markdown formatting, headers, bullet points, or lists.",
    "Write a 500-word essay about the difference between how children and adults experience time. Write in flowing prose paragraphs only. Do not use any markdown formatting, headers, bullet points, or lists.",
    "Write a 500-word essay about the appeal of used bookstores in the age of digital reading. Write in flowing prose paragraphs only. Do not use any markdown formatting, headers, bullet points, or lists.",
    "Write a 500-word essay about what makes a neighborhood feel like home. Write in flowing prose paragraphs only. Do not use any markdown formatting, headers, bullet points, or lists.",
]

OUTPUT_DIR = Path(__file__).parent / "samples"
RESULTS_FILE = Path(__file__).parent / "results.json"


def count_em_dashes(text: str) -> dict:
    """Count em dashes and compute frequency per 1000 words."""
    words = text.split()
    word_count = len(words)

    # Count all em dash variants
    em_dash_unicode = text.count("\u2014")  # —
    em_dash_double = text.count("--")       # -- (sometimes used as em dash)

    # We count only the proper unicode em dash for the main metric
    total = em_dash_unicode
    per_1000 = (total / word_count * 1000) if word_count > 0 else 0

    return {
        "word_count": word_count,
        "em_dash_count": total,
        "em_dash_per_1000_words": round(per_1000, 2),
        "double_hyphen_count": em_dash_double,
    }


def call_anthropic(prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Call Anthropic API."""
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_openai(prompt: str, model: str = "gpt-4o") -> str:
    """Call OpenAI API."""
    import openai
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def run_model(name: str, call_fn, model_id: str, prompts: list[str]) -> dict:
    """Run all prompts through a model and collect results."""
    print(f"\n{'='*60}")
    print(f"  {name} ({model_id})")
    print(f"{'='*60}")

    samples = []
    total_words = 0
    total_em_dashes = 0

    model_dir = OUTPUT_DIR / name.lower().replace(" ", "_").replace("-", "_")
    model_dir.mkdir(parents=True, exist_ok=True)

    for i, prompt in enumerate(prompts):
        print(f"  Prompt {i+1}/{len(prompts)}...", end=" ", flush=True)
        try:
            text = call_fn(prompt, model_id)
            stats = count_em_dashes(text)
            total_words += stats["word_count"]
            total_em_dashes += stats["em_dash_count"]

            # Save sample
            sample_path = model_dir / f"sample_{i+1}.txt"
            sample_path.write_text(text)

            samples.append({
                "prompt_index": i + 1,
                "stats": stats,
            })
            print(f"{stats['em_dash_count']} em dashes in {stats['word_count']} words")
            time.sleep(1)  # rate limiting
        except Exception as e:
            print(f"ERROR: {e}")
            samples.append({"prompt_index": i + 1, "error": str(e)})

    aggregate_per_1000 = (
        round(total_em_dashes / total_words * 1000, 2) if total_words > 0 else 0
    )

    print(f"\n  AGGREGATE: {total_em_dashes} em dashes / {total_words} words = {aggregate_per_1000} per 1,000 words")

    return {
        "model_name": name,
        "model_id": model_id,
        "total_words": total_words,
        "total_em_dashes": total_em_dashes,
        "em_dash_per_1000_words": aggregate_per_1000,
        "samples": samples,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    # --- Anthropic Models ---
    if os.environ.get("ANTHROPIC_API_KEY"):
        results.append(run_model(
            "Claude Sonnet 4", call_anthropic, "claude-sonnet-4-20250514", PROMPTS
        ))
        results.append(run_model(
            "Claude Haiku 3.5", call_anthropic, "claude-haiku-4-5-20251001", PROMPTS
        ))
    else:
        print("SKIP: No ANTHROPIC_API_KEY set")

    # --- OpenAI Models ---
    if os.environ.get("OPENAI_API_KEY"):
        results.append(run_model(
            "GPT-4o", call_openai, "gpt-4o", PROMPTS
        ))
        results.append(run_model(
            "GPT-4o Mini", call_openai, "gpt-4o-mini", PROMPTS
        ))
    else:
        print("SKIP: No OPENAI_API_KEY set")

    # --- Save Results ---
    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    print(f"\n\nResults saved to {RESULTS_FILE}")

    # --- Summary Table ---
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Model':<25} {'Words':>8} {'Em Dashes':>10} {'Per 1K':>8}")
    print(f"  {'-'*25} {'-'*8} {'-'*10} {'-'*8}")
    for r in results:
        print(f"  {r['model_name']:<25} {r['total_words']:>8} {r['total_em_dashes']:>10} {r['em_dash_per_1000_words']:>8}")


if __name__ == "__main__":
    main()
