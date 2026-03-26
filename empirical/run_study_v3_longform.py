#!/usr/bin/env python3
"""
Em Dash Frequency Study v3 — Long-Form Test
=============================================
Tests whether em dash frequency increases with output length.
Hypothesis: longer outputs require more structural articulation,
producing more structural joints where the em dash leaks through.

3 essays × ~5000 words × 4 models = ~60,000 words per condition.
Two conditions: unconstrained vs. prose-constrained.

Usage:
    export ANTHROPIC_API_KEY=...
    export OPENAI_API_KEY=...
    python3 run_study_v3_longform.py
"""

import json
import os
import re
import sys
import time
from pathlib import Path

TOPICS = [
    "the ways that cities shape the personalities of the people who live in them, drawing on the differences between growing up in a small town versus a large metropolis, and how the rhythms of urban life create habits of mind that persist even after someone leaves",
    "the history and future of libraries as public institutions, exploring how they have evolved from simple book repositories into community centers, digital hubs, and refuges, and what their continued survival says about what people actually need from shared spaces",
    "the psychology of collecting things, from stamps and vinyl records to bookmarks and restaurant menus, examining what drives the impulse to accumulate and organize objects, how collections become extensions of identity, and why some people find deep satisfaction in completeness while others find it suffocating",
]

PROMPT_UNCONSTRAINED = "Write a 5000-word essay about {topic}."

PROMPT_CONSTRAINED = (
    "Write a 5000-word essay about {topic}. "
    "Write in flowing prose paragraphs only. Do not use any markdown formatting, "
    "headers, bullet points, bold text, or lists."
)

OUTPUT_DIR = Path(__file__).parent / "samples_v3"
RESULTS_FILE = Path(__file__).parent / "results_v3.json"


def count_em_dashes(text: str) -> int:
    return text.count("\u2014")


def count_markdown_features(text: str) -> dict:
    lines = text.split("\n")
    headers = sum(1 for l in lines if re.match(r'^#{1,6}\s', l))
    bullets = sum(1 for l in lines if re.match(r'^\s*[-*]\s', l))
    bold = len(re.findall(r'\*\*[^*]+\*\*', text))
    numbered = sum(1 for l in lines if re.match(r'^\s*\d+\.\s', l))
    return {
        "headers": headers,
        "bullets": bullets,
        "bold": bold,
        "numbered_items": numbered,
        "total": headers + bullets + bold + numbered,
    }


def words(text: str) -> int:
    return len(text.split())


def call_anthropic(prompt: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_openai(prompt: str, model: str) -> str:
    import openai
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


MODELS = []

def register_models():
    if os.environ.get("ANTHROPIC_API_KEY"):
        MODELS.append(("Claude Sonnet 4", "claude-sonnet-4-20250514", call_anthropic))
        MODELS.append(("Claude Haiku 3.5", "claude-haiku-4-5-20251001", call_anthropic))
    if os.environ.get("OPENAI_API_KEY"):
        MODELS.append(("GPT-4o", "gpt-4o", call_openai))
        MODELS.append(("GPT-4o Mini", "gpt-4o-mini", call_openai))


def run_condition(model_name, model_id, call_fn, condition_name, prompt_template):
    print(f"\n  [{condition_name}]")

    dir_name = model_name.lower().replace(" ", "_").replace(".", "")
    condition_dir = OUTPUT_DIR / dir_name / condition_name
    condition_dir.mkdir(parents=True, exist_ok=True)

    total_words = 0
    total_em_dashes = 0
    total_md = 0
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
            total_md += md["total"]

            (condition_dir / f"sample_{i+1}.txt").write_text(text)

            samples.append({
                "topic_index": i + 1,
                "word_count": w,
                "em_dashes": ed,
                "em_dash_per_1000": round(ed / w * 1000, 2) if w > 0 else 0,
                "markdown_features": md,
            })
            print(f"{w}w, {ed} em dashes ({round(ed/w*1000, 2)}/1K), {md['total']} md")
            time.sleep(1)
        except Exception as e:
            print(f"ERROR: {e}")
            samples.append({"topic_index": i + 1, "error": str(e)})
            time.sleep(3)

    per_1k = round(total_em_dashes / total_words * 1000, 2) if total_words > 0 else 0

    print(f"\n    TOTAL: {total_em_dashes} em dashes / {total_words} words = {per_1k}/1K")

    return {
        "condition": condition_name,
        "total_words": total_words,
        "total_em_dashes": total_em_dashes,
        "em_dash_per_1000": per_1k,
        "total_md_features": total_md,
        "md_per_1000": round(total_md / total_words * 1000, 2) if total_words > 0 else 0,
        "samples": samples,
    }


def main():
    register_models()
    if not MODELS:
        print("No API keys set.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    for model_name, model_id, call_fn in MODELS:
        print(f"\n{'='*60}")
        print(f"  {model_name} ({model_id})")
        print(f"{'='*60}")

        cond_a = run_condition(model_name, model_id, call_fn, "unconstrained", PROMPT_UNCONSTRAINED)
        cond_b = run_condition(model_name, model_id, call_fn, "prose_constrained", PROMPT_CONSTRAINED)

        all_results.append({
            "model_name": model_name,
            "model_id": model_id,
            "unconstrained": cond_a,
            "prose_constrained": cond_b,
        })

    RESULTS_FILE.write_text(json.dumps(all_results, indent=2))

    # Summary
    print(f"\n{'='*70}")
    print(f"  LONG-FORM RESULTS (5000-word essays)")
    print(f"{'='*70}")
    print(f"  {'Model':<25} {'Condition':<20} {'Words':>7} {'Dashes':>7} {'Per 1K':>7} {'MD feat':>7}")
    print(f"  {'-'*25} {'-'*20} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for r in all_results:
        for cond_key in ["unconstrained", "prose_constrained"]:
            c = r[cond_key]
            print(f"  {r['model_name']:<25} {c['condition']:<20} {c['total_words']:>7} {c['total_em_dashes']:>7} {c['em_dash_per_1000']:>7} {c['total_md_features']:>7}")


if __name__ == "__main__":
    main()
