#!/usr/bin/env python3
"""
Base vs Instruct — Polling Endpoint Creation
=============================================
Tries to create a Together AI dedicated endpoint for Qwen2.5-7B (base)
every 5 minutes until hardware is available. Once running, executes
the em dash frequency experiment, then tears down the endpoint.

Also runs Qwen2.5-7B-Instruct via the serverless chat API for comparison.

Usage:
    export TOGETHER_API_KEY=...
    python3 run_base_model_poll.py
"""

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

API_KEY = os.environ.get("TOGETHER_API_KEY", "")
BASE_URL = "https://api.together.xyz/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Hardware options to try, cheapest first
HARDWARE_OPTIONS = [
    "1x_nvidia_l40_48gb_pcie",      # $1.49/hr
    "1x_nvidia_l40s_48gb_pcie",     # $2.10/hr
    "1x_nvidia_a100_40gb_pcie",     # $3.00/hr
    "1x_nvidia_a100_40gb_sxm",      # $2.40/hr
    "1x_nvidia_a100_80gb_pcie",     # $2.40/hr
]

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

BASE_PROMPT = "The following is a thoughtful, well-written 1000-word essay about {topic}.\n\n"
INSTRUCT_PROMPT = "Write a 1000-word essay about {topic}."

OUTPUT_DIR = Path(__file__).parent / "samples_v8_base"
RESULTS_FILE = Path(__file__).parent / "results_v8_base.json"


def api_call(method, path, data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def try_create_endpoint():
    """Try each hardware option. Return endpoint ID on success, None on failure."""
    for hw in HARDWARE_OPTIONS:
        try:
            result = api_call("POST", "/endpoints", {
                "model": "Qwen/Qwen2.5-7B",
                "display_name": "qwen-base-emdash-test",
                "hardware": hw,
                "autoscaling": {"min_replicas": 1, "max_replicas": 1},
                "inactive_timeout": 15,
            })
            state = result.get("state", "")
            eid = result.get("id", result.get("name", ""))
            if state in ("STARTED", "PENDING", "DEPLOYING", "SCALING_UP"):
                print(f"  Endpoint created on {hw}! ID: {eid}, state: {state}")
                return eid, hw
        except Exception as e:
            msg = str(e)
            if "not available for this model" in msg:
                continue  # incompatible, try next
            elif "not available" in msg or "try again" in msg:
                continue  # out of stock, try next
            else:
                print(f"  Unexpected error on {hw}: {msg}")
    return None, None


def wait_for_endpoint(endpoint_id, max_wait=600):
    """Wait for endpoint to be STARTED. Returns True if ready."""
    print(f"  Waiting for endpoint to start...", end=" ", flush=True)
    start = time.time()
    while time.time() - start < max_wait:
        try:
            result = api_call("GET", f"/endpoints/{endpoint_id}")
            state = result.get("state", "UNKNOWN")
            if state == "STARTED":
                print(f"READY (took {int(time.time()-start)}s)")
                return True
            print(f"{state}...", end=" ", flush=True)
        except:
            pass
        time.sleep(15)
    print("TIMEOUT")
    return False


def delete_endpoint(endpoint_id):
    """Delete the endpoint to stop billing."""
    try:
        api_call("DELETE", f"/endpoints/{endpoint_id}")
        print(f"  Endpoint {endpoint_id} deleted.")
    except Exception as e:
        print(f"  WARNING: Could not delete endpoint: {e}")
        print(f"  Manually delete at: https://api.together.ai/endpoints")


def call_completion(prompt, model="Qwen/Qwen2.5-7B"):
    """Call completions endpoint for base model."""
    result = api_call("POST", "/completions", {
        "model": model,
        "max_tokens": 2048,
        "prompt": prompt,
        "stop": ["\n\n\n"],
        "temperature": 1.0,
    })
    return result["choices"][0]["text"]


def call_chat(prompt, model="Qwen/Qwen2.5-7B-Instruct-Turbo"):
    """Call chat endpoint for instruct model."""
    result = api_call("POST", "/chat/completions", {
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    })
    return result["choices"][0]["message"]["content"]


def count_em_dashes(text): return text.count("\u2014")

def count_md(text):
    lines = text.split("\n")
    return sum(1 for l in lines if re.match(r'^#{1,6}\s', l)) + \
           sum(1 for l in lines if re.match(r'^\s*[-*]\s', l)) + \
           len(re.findall(r'\*\*[^*]+\*\*', text)) + \
           sum(1 for l in lines if re.match(r'^\s*\d+\.\s', l))


def run_model(name, call_fn, prompt_template, is_base):
    print(f"\n  Running {name} ({'BASE' if is_base else 'INSTRUCT'})...")
    dir_name = name.lower().replace(" ", "_").replace(".", "")
    model_dir = OUTPUT_DIR / dir_name
    model_dir.mkdir(parents=True, exist_ok=True)

    total_words, total_ed, total_md = 0, 0, 0
    samples = []

    for i, topic in enumerate(TOPICS):
        prompt = prompt_template.format(topic=topic)
        print(f"    Topic {i+1}/{len(TOPICS)}...", end=" ", flush=True)
        try:
            text = call_fn(prompt)
            w = len(text.split())
            ed = count_em_dashes(text)
            md = count_md(text)
            total_words += w
            total_ed += ed
            total_md += md
            (model_dir / f"sample_{i+1}.txt").write_text(text)
            samples.append({"topic": i+1, "words": w, "em_dashes": ed, "md": md})
            print(f"{w}w, {ed} em, {md} md")
            time.sleep(1)
        except Exception as e:
            print(f"ERROR: {e}")
            samples.append({"topic": i+1, "error": str(e)})
            time.sleep(3)

    per_1k = round(total_ed / total_words * 1000, 2) if total_words > 0 else 0
    print(f"    TOTAL: {total_ed}/{total_words}w = {per_1k}/1K, {total_md} md")

    return {
        "model_name": name,
        "is_base": is_base,
        "total_words": total_words,
        "total_em_dashes": total_ed,
        "em_dash_per_1000": per_1k,
        "total_md": total_md,
        "samples": samples,
    }


def main():
    if not API_KEY:
        print("No TOGETHER_API_KEY set.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1: Poll for hardware
    print("=" * 60)
    print("  POLLING FOR BASE MODEL HARDWARE")
    print("=" * 60)

    endpoint_id = None
    max_attempts = 60  # 5 hours at 5min intervals
    for attempt in range(1, max_attempts + 1):
        print(f"\n  Attempt {attempt}/{max_attempts} ({time.strftime('%H:%M:%S')})...")
        eid, hw = try_create_endpoint()
        if eid:
            endpoint_id = eid
            break
        print(f"  No hardware available. Retrying in 5 minutes...")
        time.sleep(300)

    if not endpoint_id:
        print("  FAILED: Could not get hardware after all attempts.")
        sys.exit(1)

    # Phase 2: Wait for endpoint to start
    if not wait_for_endpoint(endpoint_id):
        print("  Endpoint failed to start. Deleting...")
        delete_endpoint(endpoint_id)
        sys.exit(1)

    # Phase 3: Run experiments
    print("\n" + "=" * 60)
    print("  RUNNING BASE vs INSTRUCT COMPARISON")
    print("=" * 60)

    results = []
    try:
        results.append(run_model("Qwen 2.5 7B Base", call_completion, BASE_PROMPT, True))
        results.append(run_model("Qwen 2.5 7B Instruct", call_chat, INSTRUCT_PROMPT, False))
    finally:
        # Phase 4: Always clean up
        print("\n  Cleaning up endpoint...")
        delete_endpoint(endpoint_id)

    # Save results
    RESULTS_FILE.write_text(json.dumps(results, indent=2))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  BASE vs INSTRUCT RESULTS")
    print(f"{'=' * 60}")
    for r in results:
        typ = "BASE" if r["is_base"] else "INSTRUCT"
        print(f"  {r['model_name']:<30} {typ:<10} {r['em_dash_per_1000']}/1K em, {r['total_md']} md")

    print(f"\n  Results saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
