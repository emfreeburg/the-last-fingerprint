#!/usr/bin/env python3
"""
Em Dash Frequency Study v4 — Llama Models via Groq
====================================================
Adds Meta's Llama models (via Groq) as a third provider.
Two-condition design matching v2.

Usage:
    export GROQ_API_KEY=...
    python3 run_study_v4_llama.py
"""

import json
import os
import re
import sys
import time
from pathlib import Path

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

PROMPT_A = "Write a 1000-word essay about {topic}."
PROMPT_B = (
    "Write a 1000-word essay about {topic}. "
    "Write in flowing prose paragraphs only. Do not use any markdown formatting, "
    "headers, bullet points, bold text, or lists."
)

OUTPUT_DIR = Path(__file__).parent / "samples_v4"
RESULTS_FILE = Path(__file__).parent / "results_v4.json"


def count_em_dashes(text): return text.count("\u2014")

def count_markdown_features(text):
    lines = text.split("\n")
    h = sum(1 for l in lines if re.match(r'^#{1,6}\s', l))
    b = sum(1 for l in lines if re.match(r'^\s*[-*]\s', l))
    bo = len(re.findall(r'\*\*[^*]+\*\*', text))
    n = sum(1 for l in lines if re.match(r'^\s*\d+\.\s', l))
    return {"headers": h, "bullets": b, "bold": bo, "numbered": n, "total": h+b+bo+n}

def words(text): return len(text.split())


def call_groq(prompt, model):
    import openai
    client = openai.OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
    )
    response = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


MODELS = [
    ("Llama 3.1 8B Instruct", "llama-3.1-8b-instant", call_groq),
    ("Llama 3.3 70B Instruct", "llama-3.3-70b-versatile", call_groq),
]


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
            samples.append({"topic_index": i+1, "word_count": w, "em_dashes": ed, "markdown_features": md})
            print(f"{w}w, {ed} em dashes, {md['total']} md features")
            time.sleep(0.5)
        except Exception as e:
            print(f"ERROR: {e}")
            samples.append({"topic_index": i+1, "error": str(e)})
            time.sleep(2)

    per_1k = round(total_em_dashes / total_words * 1000, 2) if total_words > 0 else 0
    md_per_1k = round(total_md / total_words * 1000, 2) if total_words > 0 else 0
    print(f"\n    TOTAL: {total_em_dashes} em dashes / {total_words} words = {per_1k}/1K, {total_md} md features = {md_per_1k}/1K")

    return {
        "condition": condition_name,
        "total_words": total_words,
        "total_em_dashes": total_em_dashes,
        "em_dash_per_1000": per_1k,
        "total_md_features": total_md,
        "md_per_1000": md_per_1k,
        "samples": samples,
    }


def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("No GROQ_API_KEY set.")
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

    RESULTS_FILE.write_text(json.dumps(all_results, indent=2))

    print(f"\n{'='*70}")
    print(f"  LLAMA RESULTS")
    print(f"{'='*70}")
    print(f"  {'Model':<28} {'Condition':<20} {'Words':>7} {'Dashes':>7} {'Per 1K':>7} {'MD':>5}")
    print(f"  {'-'*28} {'-'*20} {'-'*7} {'-'*7} {'-'*7} {'-'*5}")
    for r in all_results:
        for ck in ["unconstrained", "prose_constrained"]:
            c = r[ck]
            print(f"  {r['model_name']:<28} {c['condition']:<20} {c['total_words']:>7} {c['total_em_dashes']:>7} {c['em_dash_per_1000']:>7} {c['total_md_features']:>5}")


if __name__ == "__main__":
    main()
