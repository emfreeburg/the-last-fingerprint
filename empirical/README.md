# Empirical Studies

Index of all experiments conducted for "The Last Fingerprint."

## Studies Used in the Paper

| Study | Script | Results | Paper Table | Description |
|-------|--------|---------|-------------|-------------|
| v2 | `run_study_v2.py` | `results_v2.json` | Table 1 | Two-condition suppression: Claude Sonnet 4, Claude Haiku 3.5, GPT-4o, GPT-4o Mini |
| v4 | `run_study_v4_llama.py` | `results_v4.json` | Table 1 | Two-condition suppression: Llama 3.1 8B, Llama 3.3 70B (via Groq) |
| v6 | `run_study_v6_frontier.py` | `results_v6.json` | Table 1 | Two-condition suppression: Claude Opus 4.6, GPT-4.1 |
| v6+ | (standalone) | `results_v6_gpt54.json` | Table 1 | Two-condition suppression: GPT-5.4 (parameter fix) |
| v7 | `run_study_v7_gemini_deepseek.py` | `results_v7.json`, `results_v7_gemini_pro.json` | Table 1 | Two-condition suppression: Gemini 2.5 Flash, Gemini 2.5 Pro |
| ds | `run_deepseek_rerun.py` | `results_deepseek_rerun.json` | Table 1 | Two-condition suppression: DeepSeek V3 (rerun with verified data) |
| v9 | (inline) | `results_v9_suppression.json`, `results_v9_gpt54.json` | Table 2 | Three-condition suppression gradient: GPT-4.1, Claude Opus 4.6, DeepSeek V3, GPT-5.4 |
| v10 | (inline) | `results_v10_longform_suppression.json` | Text (§5.5) | Long-form (5000w) three-condition: Claude Opus, GPT-4.1, GPT-5.4, DeepSeek V3 |
| v11 | (inline) | `results_v11_local_base.json` | Table 3 | Base vs instruct: Llama 3.1 8B via Ollama (local) |

## Other Files

| File | Description |
|------|-------------|
| `run_study.py` | Initial v1 study (superseded by v2) |
| `run_study_v3_longform.py` | Early long-form study (two conditions, superseded by v10) |
| `run_study_v5_base_vs_instruct.py` | Together AI base model attempt (failed — hardware unavailable) |
| `run_base_model_poll.py` | Together AI hardware polling script (replaced by local Ollama) |
| `human_baseline.json` | Em dash frequency in 8 published human essays (57,232 words) |
| `results_v3.json`, `results_v5.json` | Intermediate/superseded results |
| `samples_*/` | Generated text samples for each study |
