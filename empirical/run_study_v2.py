#!/usr/bin/env python3
"""
Em Dash Frequency Study v2 — Two-Condition Design
===================================================
Tests the "last fingerprint" hypothesis directly:
  Condition A: Unconstrained (no formatting instructions)
  Condition B: Prose-constrained ("no markdown formatting")

If the em dash is the artifact that survives suppression:
  - Markdown features (headers, bullets, bold) should appear in A, not B
  - Em dashes should appear in BOTH conditions

Additionally: 10 prompts × ~1000 words = ~10,000 words per model per condition.
Much more statistical power than v1.

Usage:
    export ANTHROPIC_API_KEY=...
    export OPENAI_API_KEY=...
    python3 run_study_v2.py
"""

import json
import os
import re
import sys
import time
from pathlib import Path

# --- Configuration ---

TOPICS = [
    "the experience of moving to a new city as an adult",
    "why some people prefer cooking at home over eating at restaurants",
    "the difference between how children and adults experience time",
    "the appeal of used bookstores in the age of digital reading",
    "what makes a neighborhood feel like home",
    "the strange comfort of airports and the feeling of being between places",
    "how learning a musical instrument changes the way you listen to music",
    "the relationship between walking and thinking",
    "why people are drawn to watching storms",
    "the quiet satisfaction of repairing something by hand",
]

# Condition A: Unconstrained — let the model write naturally
PROMPT_A = "Write a 1000-word essay about {topic}."

# Condition B: Prose-constrained — suppress markdown but allow prose punctuation
PROMPT_B = (
    "Write a 1000-word essay about {topic}. "
    "Write in flowing prose paragraphs only. Do not use any markdown formatting, "
    "headers, bullet points, bold text, or lists."
)

OUTPUT_DIR = Path(__file__).parent / "samples_v2"
RESULTS_FILE = Path(__file__).parent / "results_v2.json"


def count_em_dashes(text: str) -> int:
    """Count Unicode em dash characters."""
    return text.count("\u2014")


def count_markdown_features(text: str) -> dict:
    """Count overt markdown formatting artifacts."""
    lines = text.split("\n")
    headers = sum(1 for l in lines if re.match(r'^#{1,6}\s', l))
    bullets = sum(1 for l in lines if re.match(r'^\s*[-*]\s', l))
    bold = len(re.findall(r'\*\*[^*]+\*\*', text))
    italic_md = len(re.findall(r'(?<!\*)\*(?!\*)[^*]+\*(?!\*)', text))
    code = len(re.findall(r'`[^`]+`', text))
    numbered = sum(1 for l in lines if re.match(r'^\s*\d+\.\s', l))
    return {
        "headers": headers,
        "bullets": bullets,
        "bold": bold,
        "italic_md": italic_md,
        "code_spans": code,
        "numbered_items": numbered,
        "total_md_features": headers + bullets + bold + italic_md + code + numbered,
    }


def words(text: str) -> int:
    return len(text.split())


def call_anthropic(prompt: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_openai(prompt: str, model: str) -> str:
    import openai
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# Model registry
MODELS = []

def register_models():
    if os.environ.get("ANTHROPIC_API_KEY"):
        MODELS.append(("Claude Sonnet 4", "claude-sonnet-4-20250514", call_anthropic))
        MODELS.append(("Claude Haiku 3.5", "claude-haiku-4-5-20251001", call_anthropic))
    else:
        print("SKIP: No ANTHROPIC_API_KEY")

    if os.environ.get("OPENAI_API_KEY"):
        MODELS.append(("GPT-4o", "gpt-4o", call_openai))
        MODELS.append(("GPT-4o Mini", "gpt-4o-mini", call_openai))
    else:
        print("SKIP: No OPENAI_API_KEY")


def run_condition(model_name, model_id, call_fn, condition_name, prompt_template):
    """Run all topics through one model under one condition."""
    print(f"\n  [{condition_name}]")

    dir_name = model_name.lower().replace(" ", "_").replace(".", "")
    condition_dir = OUTPUT_DIR / dir_name / condition_name
    condition_dir.mkdir(parents=True, exist_ok=True)

    total_words = 0
    total_em_dashes = 0
    total_md_features = 0
    samples = []

    for i, topic in enumerate(TOPICS):
        prompt = prompt_template.format(topic=topic)
        print(f"    Topic {i+1}/{len(TOPICS)}...", end=" ", flush=True)
        try:
            text = call_fn(prompt, model_id)
            w = words(text)
            ed = count_em_dashes(text)
            md = count_markdown_features(text)

            total_words += w
            total_em_dashes += ed
            total_md_features += md["total_md_features"]

            # Save
            (condition_dir / f"sample_{i+1}.txt").write_text(text)

            samples.append({
                "topic_index": i + 1,
                "word_count": w,
                "em_dashes": ed,
                "markdown_features": md,
            })
            print(f"{w}w, {ed} em dashes, {md['total_md_features']} md features")
            time.sleep(0.5)
        except Exception as e:
            print(f"ERROR: {e}")
            samples.append({"topic_index": i + 1, "error": str(e)})
            time.sleep(2)

    per_1k = round(total_em_dashes / total_words * 1000, 2) if total_words > 0 else 0
    md_per_1k = round(total_md_features / total_words * 1000, 2) if total_words > 0 else 0

    return {
        "condition": condition_name,
        "total_words": total_words,
        "total_em_dashes": total_em_dashes,
        "em_dash_per_1000": per_1k,
        "total_md_features": total_md_features,
        "md_features_per_1000": md_per_1k,
        "samples": samples,
    }


def main():
    register_models()
    if not MODELS:
        print("No API keys set. Exiting.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    for model_name, model_id, call_fn in MODELS:
        print(f"\n{'='*60}")
        print(f"  {model_name} ({model_id})")
        print(f"{'='*60}")

        cond_a = run_condition(model_name, model_id, call_fn, "unconstrained", PROMPT_A)
        cond_b = run_condition(model_name, model_id, call_fn, "prose_constrained", PROMPT_B)

        all_results.append({
            "model_name": model_name,
            "model_id": model_id,
            "unconstrained": cond_a,
            "prose_constrained": cond_b,
        })

    # Save
    RESULTS_FILE.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to {RESULTS_FILE}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  SUMMARY: Em Dashes per 1,000 Words")
    print(f"{'='*70}")
    print(f"  {'Model':<25} {'Unconstrained':>14} {'Constrained':>14} {'Survive?':>10}")
    print(f"  {'-'*25} {'-'*14} {'-'*14} {'-'*10}")
    for r in all_results:
        a = r["unconstrained"]["em_dash_per_1000"]
        b = r["prose_constrained"]["em_dash_per_1000"]
        survive = "YES" if b > 0.5 else "low"
        print(f"  {r['model_name']:<25} {a:>14} {b:>14} {survive:>10}")

    print(f"\n  SUMMARY: Markdown Features per 1,000 Words")
    print(f"  {'-'*25} {'-'*14} {'-'*14} {'-'*10}")
    print(f"  {'Model':<25} {'Unconstrained':>14} {'Constrained':>14} {'Suppressed?':>10}")
    print(f"  {'-'*25} {'-'*14} {'-'*14} {'-'*10}")
    for r in all_results:
        a = r["unconstrained"]["md_features_per_1000"]
        b = r["prose_constrained"]["md_features_per_1000"]
        suppressed = "YES" if b < a * 0.3 else "partial"
        print(f"  {r['model_name']:<25} {a:>14} {b:>14} {suppressed:>10}")


if __name__ == "__main__":
    main()
