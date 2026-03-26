#!/usr/bin/env python3
"""
DeepSeek V3 two-condition rerun for Table 1 data.
Matches v7 methodology exactly.
"""

import json
import os
import re
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

OUTPUT_DIR = Path(__file__).parent / "samples_deepseek_rerun"
RESULTS_FILE = Path(__file__).parent / "results_deepseek_rerun.json"


def count_em_dashes(text): return text.count("\u2014")

def count_markdown_features(text):
    lines = text.split("\n")
    h = sum(1 for l in lines if re.match(r'^#{1,6}\s', l))
    b = sum(1 for l in lines if re.match(r'^\s*[-*]\s', l))
    bo = len(re.findall(r'\*\*[^*]+\*\*', text))
    n = sum(1 for l in lines if re.match(r'^\s*\d+\.\s', l))
    return {"headers": h, "bullets": b, "bold": bo, "numbered": n, "total": h+b+bo+n}

def words(text): return len(text.split())


def call_deepseek(prompt, model):
    import openai
    client = openai.OpenAI(
        base_url="https://api.deepseek.com",
        api_key=os.environ["DEEPSEEK_API_KEY"],
    )
    response = client.chat.completions.create(
        model=model, max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def run_condition(condition_name, prompt_template):
    print(f"\n  [{condition_name}]")
    condition_dir = OUTPUT_DIR / "deepseek_v3" / condition_name
    condition_dir.mkdir(parents=True, exist_ok=True)

    total_words = 0
    total_em_dashes = 0
    total_md = 0
    samples = []

    for i, topic in enumerate(TOPICS):
        prompt = prompt_template.format(topic=topic)
        print(f"    Topic {i+1}/{len(TOPICS)}...", end=" ", flush=True)
        try:
            text = call_deepseek(prompt, "deepseek-chat")
            w = words(text)
            ed = count_em_dashes(text)
            md = count_markdown_features(text)
            total_words += w
            total_em_dashes += ed
            total_md += md["total"]
            (condition_dir / f"sample_{i+1}.txt").write_text(text)
            samples.append({"topic_index": i+1, "word_count": w, "em_dashes": ed, "markdown_features": md})
            print(f"{w}w, {ed} em dashes, {md['total']} md features")
            time.sleep(1)
        except Exception as e:
            print(f"ERROR: {e}")
            samples.append({"topic_index": i+1, "error": str(e)})
            time.sleep(3)

    per_1k = round(total_em_dashes / total_words * 1000, 2) if total_words > 0 else 0
    md_per_1k = round(total_md / total_words * 1000, 2) if total_words > 0 else 0
    print(f"\n    TOTAL: {total_em_dashes}/{total_words}w = {per_1k}/1K, {total_md} md = {md_per_1k}/1K")

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
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("ERROR: DEEPSEEK_API_KEY not set")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  DeepSeek V3 — Two-Condition Rerun")
    print("=" * 60)

    cond_a = run_condition("unconstrained", PROMPT_A)
    cond_b = run_condition("prose_constrained", PROMPT_B)

    result = {
        "model_name": "DeepSeek V3",
        "model_id": "deepseek-chat",
        "unconstrained": cond_a,
        "prose_constrained": cond_b,
    }

    RESULTS_FILE.write_text(json.dumps(result, indent=2))
    print(f"\nResults written to {RESULTS_FILE}")
    print(f"\nSUMMARY:")
    print(f"  Unconstrained: {cond_a['em_dash_per_1000']}/1K em dashes, {cond_a['md_per_1000']}/1K md features")
    print(f"  Constrained:   {cond_b['em_dash_per_1000']}/1K em dashes, {cond_b['md_per_1000']}/1K md features")


if __name__ == "__main__":
    main()
