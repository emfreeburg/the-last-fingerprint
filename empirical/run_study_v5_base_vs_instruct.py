#!/usr/bin/env python3
"""
Em Dash Frequency Study v5 — Base vs Instruct (RLHF Isolation)
================================================================
The critical experiment: same architecture, same training data,
only difference is RLHF. Tests step 4 of the genealogy directly.

Uses Together AI which hosts both base and instruct Llama models.

Base models use the completions endpoint (text completion).
Instruct models use the chat endpoint.

Usage:
    export TOGETHER_API_KEY=...
    python3 run_study_v5_base_vs_instruct.py
"""

import json
import os
import re
import sys
import time
from pathlib import Path
import urllib.request

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

OUTPUT_DIR = Path(__file__).parent / "samples_v5"
RESULTS_FILE = Path(__file__).parent / "results_v5.json"


def count_em_dashes(text): return text.count("\u2014")

def count_markdown_features(text):
    lines = text.split("\n")
    h = sum(1 for l in lines if re.match(r'^#{1,6}\s', l))
    b = sum(1 for l in lines if re.match(r'^\s*[-*]\s', l))
    bo = len(re.findall(r'\*\*[^*]+\*\*', text))
    n = sum(1 for l in lines if re.match(r'^\s*\d+\.\s', l))
    return {"headers": h, "bullets": b, "bold": bo, "numbered": n, "total": h+b+bo+n}

def words(text): return len(text.split())


def call_together_chat(prompt, model):
    """Call Together AI chat endpoint (for instruct models)."""
    api_key = os.environ["TOGETHER_API_KEY"]
    data = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.together.xyz/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["choices"][0]["message"]["content"]


def call_together_completion(prompt, model):
    """Call Together AI completions endpoint (for base models).
    Base models need a prose-style prompt prefix since they do text completion, not instruction following."""
    api_key = os.environ["TOGETHER_API_KEY"]
    data = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "prompt": prompt,
        "stop": ["\n\n\n"],  # stop on triple newline to avoid runaway generation
    }).encode()
    req = urllib.request.Request(
        "https://api.together.xyz/v1/completions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["choices"][0]["text"]


# For base models, we use a prose-style completion prompt rather than an instruction
BASE_PROMPT = """The following is a thoughtful, well-written 1000-word essay about {topic}.

"""

INSTRUCT_PROMPT = "Write a 1000-word essay about {topic}."

MODELS = [
    # (display_name, model_id, call_function, prompt_template, is_base)
    ("Llama 3.1 8B Base", "meta-llama/Meta-Llama-3.1-8B", call_together_completion, BASE_PROMPT, True),
    ("Llama 3.1 8B Instruct", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", call_together_chat, INSTRUCT_PROMPT, False),
    ("Llama 3.1 70B Base", "meta-llama/Meta-Llama-3.1-70B", call_together_completion, BASE_PROMPT, True),
    ("Llama 3.1 70B Instruct", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", call_together_chat, INSTRUCT_PROMPT, False),
]


def run_model(model_name, model_id, call_fn, prompt_template, is_base):
    print(f"\n{'='*60}")
    print(f"  {model_name} ({'BASE' if is_base else 'INSTRUCT'})")
    print(f"  {model_id}")
    print(f"{'='*60}")

    dir_name = model_name.lower().replace(" ", "_").replace(".", "")
    model_dir = OUTPUT_DIR / dir_name
    model_dir.mkdir(parents=True, exist_ok=True)

    total_words = 0
    total_em_dashes = 0
    total_md = 0
    samples = []

    for i, topic in enumerate(TOPICS):
        prompt = prompt_template.format(topic=topic)
        print(f"  Topic {i+1}/{len(TOPICS)}...", end=" ", flush=True)
        try:
            text = call_fn(prompt, model_id)
            w = words(text)
            ed = count_em_dashes(text)
            md = count_markdown_features(text)
            total_words += w
            total_em_dashes += ed
            total_md += md["total"]
            (model_dir / f"sample_{i+1}.txt").write_text(text)
            samples.append({
                "topic_index": i+1,
                "word_count": w,
                "em_dashes": ed,
                "em_dash_per_1000": round(ed / w * 1000, 2) if w > 0 else 0,
                "markdown_features": md,
            })
            print(f"{w}w, {ed} em dashes ({round(ed/w*1000,2)}/1K), {md['total']} md")
            time.sleep(1)
        except Exception as e:
            print(f"ERROR: {e}")
            samples.append({"topic_index": i+1, "error": str(e)})
            time.sleep(3)

    per_1k = round(total_em_dashes / total_words * 1000, 2) if total_words > 0 else 0
    print(f"\n  TOTAL: {total_em_dashes} em dashes / {total_words} words = {per_1k}/1K")

    return {
        "model_name": model_name,
        "model_id": model_id,
        "is_base": is_base,
        "total_words": total_words,
        "total_em_dashes": total_em_dashes,
        "em_dash_per_1000": per_1k,
        "total_md_features": total_md,
        "samples": samples,
    }


def main():
    if not os.environ.get("TOGETHER_API_KEY"):
        print("No TOGETHER_API_KEY set.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for name, mid, fn, tmpl, is_base in MODELS:
        results.append(run_model(name, mid, fn, tmpl, is_base))

    RESULTS_FILE.write_text(json.dumps(results, indent=2))

    print(f"\n{'='*70}")
    print(f"  BASE vs INSTRUCT COMPARISON")
    print(f"{'='*70}")
    print(f"  {'Model':<30} {'Type':<10} {'Words':>7} {'Dashes':>7} {'Per 1K':>7} {'MD':>5}")
    print(f"  {'-'*30} {'-'*10} {'-'*7} {'-'*7} {'-'*7} {'-'*5}")
    for r in results:
        typ = "BASE" if r["is_base"] else "INSTRUCT"
        print(f"  {r['model_name']:<30} {typ:<10} {r['total_words']:>7} {r['total_em_dashes']:>7} {r['em_dash_per_1000']:>7} {r['total_md_features']:>5}")


if __name__ == "__main__":
    main()
