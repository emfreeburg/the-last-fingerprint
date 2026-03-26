# The Last Fingerprint: How Markdown Training Shapes LLM Prose

**E. M. Freeburg**
Independent Researcher

---

## Abstract

Large language models produce em dashes at varying rates, and the observation that some models "overuse" them has become one of the most widely discussed markers of AI-generated text. Yet no mechanistic account of this pattern exists, and the parallel observation that LLMs default to markdown-formatted output has never been connected to it. We propose that the em dash is *markdown leaking into prose* — the smallest surviving unit of the structural orientation that LLMs acquire from markdown-saturated training corpora. We present a five-step genealogy connecting training data composition, structural internalization, the dual-register status of the em dash, and post-training amplification. We test this with a two-condition suppression experiment across twelve models from five providers (Anthropic, OpenAI, Meta, Google, DeepSeek): when models are instructed to avoid markdown formatting, overt features (headers, bullets, bold) are eliminated or nearly eliminated, but em dashes persist — except in Meta's Llama models, which produce none at all. Em dash frequency and suppression resistance vary from 0.0 per 1,000 words (Llama) to 9.1 (GPT-4.1 under suppression), functioning as a signature of the specific fine-tuning procedure applied. A three-condition suppression gradient shows that even explicit em dash prohibition fails to eliminate the artifact in some models, and a base-vs-instruct comparison confirms that the latent tendency exists pre-RLHF. These findings connect two previously isolated online discourses and reframe em dash frequency as a diagnostic of fine-tuning methodology rather than a stylistic defect.

## Read the Paper

**[Read the full paper in markdown](PAPER.md)** — readable directly on GitHub.

The authoritative version is a self-contained LaTeX project in the [`paper/`](paper/) directory.

### Building

Requires a TeX distribution (TeX Live, MacTeX, or TinyTeX).

```bash
cd paper
make
```

This produces `paper/main.pdf`.

### Submission Archive

To generate a flattened `.tar.gz` for arXiv submission:

```bash
cd paper
make submission
```

## Repository Structure

```
.
├── README.md
├── PAPER.md              # Full paper readable on GitHub
├── LICENSE
├── paper/                # Self-contained LaTeX project
│   ├── main.tex
│   ├── references.bib
│   ├── Makefile
│   └── sections/
│       ├── abstract.tex
│       ├── introduction.tex
│       ├── background.tex
│       ├── genealogy.tex         # Core contribution: five-step genealogy
│       ├── two-discourses.tex
│       ├── empirical.tex         # Suppression test results
│       ├── discussion.tex        # Includes future work and limitations
│       └── conclusion.tex
├── empirical/            # Experiment code and data
│   ├── run_study_v2.py           # Two-condition suppression test
│   ├── run_study_v3_longform.py  # 5,000-word length study
│   ├── run_study_v4_llama.py     # Llama models via Groq
│   ├── run_study_v6_frontier.py  # Frontier models (Opus 4.6, GPT-4.1, GPT-5.4)
│   ├── run_deepseek_rerun.py     # DeepSeek V3 two-condition (verified data)
│   ├── human_baseline.json       # Em dash frequency in published essays
│   ├── results_*.json            # All study results
│   └── samples_*/                # Generated text samples
└── scripts/
    └── publish.sh        # Export clean copy for public release
```

## Key Findings

| Model | Provider | Em Dashes/1K (free) | Em Dashes/1K (suppressed) | MD (suppressed) |
|---|---|---|---|---|
| GPT-4.1 | OpenAI | 10.62 | **9.10** | 0.0 |
| Claude Opus 4.6 | Anthropic | 9.09 | **0.19** | 0.0 |
| Claude Sonnet 4 | Anthropic | 8.29 | **1.31** | 0.0 |
| Claude Haiku 3.5 | Anthropic | 7.51 | **0.18** | 0.9 |
| DeepSeek V3 | DeepSeek | 6.95 | **5.41** | 0.0 |
| GPT-4o Mini | OpenAI | 4.16 | **4.23** | 0.0 |
| GPT-4o | OpenAI | 4.12 | **2.68** | 0.0 |
| Gemini 2.5 Pro | Google | 3.53 | **0.00** | 0.0 |
| GPT-5.4 | OpenAI | 1.43 | **0.29** | 0.0 |
| Gemini 2.5 Flash | Google | 1.28 | **1.48** | 0.0 |
| Llama 3.1 8B | Meta | 0.00 | **0.00** | 0.0 |
| Llama 3.3 70B | Meta | 0.00 | **0.00** | 0.0 |
| Human baseline | — | — | **3.23** (mean) | — |

Markdown features are eliminated or nearly eliminated. Em dashes persist — at rates determined by the fine-tuning procedure.

### Suppression Gradient (three conditions)

| Model | Unconstrained | "No markdown" | "No em dashes" |
|---|---|---|---|
| GPT-4.1 | 11.51 | 8.20 | **3.86** |
| DeepSeek V3 | 8.66 | 4.75 | **1.57** |
| Claude Opus 4.6 | 8.46 | 0.19 | **0.00** |
| GPT-5.4 | 0.75 | 0.15 | **0.00** |

Even explicit em dash prohibition fails to eliminate the artifact in GPT-4.1 and DeepSeek.

### Base vs Instruct (Llama 3.1 8B, local)

| Type | Em Dashes/1K | MD Features |
|---|---|---|
| Base (pre-RLHF) | **0.49** | 28 |
| Instruct (post-RLHF) | **0.00** | 5 |

Latent tendency exists pre-RLHF. The direction of amplification is provider-dependent.

## Citation

```bibtex
@article{freeburg2026lastfingerprint,
  author = {Freeburg, E. M.},
  title = {The Last Fingerprint: How Markdown Training Shapes {LLM} Prose},
  year = {2026},
  note = {arXiv preprint}
}
```

## License

This work is licensed under [CC BY 4.0](LICENSE).
