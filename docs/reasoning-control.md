# Reasoning control per model (`--think` / `--reasoning`)

> Written and maintained with Claude; verified against the grader and run data.

Reasoning models can spend their entire token budget *thinking* and emit empty content
(`finish_reason=length`, 0-byte output) — the answer never leaves the hidden reasoning
channel. They also behave very differently with reasoning on vs off. The reference runner
exposes two flags to control this; **which one and which values depend on the model family.**

The chosen setting is recorded in each run's `config.json` (`think` / `reasoning` fields).

## ollama backend → `--think`
| value | meaning |
|---|---|
| `false` (default) | thinking OFF |
| `true` | thinking ON |
| `low` / `medium` / `high` | reasoning-effort LEVEL |
| `none` | let the model decide |

| model family | how it takes `--think` | notes |
|---|---|---|
| **qwen3 / qwen3.5 / deepseek-r1 / qwq** | **boolean** (`true`/`false`) | honors on/off cleanly |
| **gpt-oss** | **LEVEL only** (`low`/`medium`/`high`) | **IGNORES the boolean** — `false` leaves it at a runaway default; use `low` to get a concise, emitted answer (medium/high run away at small budgets) |
| phi4, qwen2.5-coder, gemma2/3, granite3.1, llama3.1, deepseek-coder-v2 | n/a | not reasoning models; flag has no effect |

## openai / OpenRouter backend → `--reasoning`
| value | sent as | meaning |
|---|---|---|
| `off` | `{"enabled": false}` | disable thinking |
| `low` / `medium` / `high` | `{"effort": "..."}` | reasoning effort ≈ a fraction of `max_tokens` (OpenRouter: low≈20%, medium≈50%, high≈80%) |
| (unset) | — | provider default (full reasoning for reasoning models) |

How OpenRouter handles `effort`: `enabled: true` runs at default **medium**. An `effort` value is
**never an error** — if a model doesn't natively support effort levels, OpenRouter maps it to the
nearest supported level (or the model's token budget) silently. Native effort support is documented
for **OpenAI o-series, Grok, Gemini-3**; **Anthropic and Qwen** are routed via a `max_tokens` budget;
**DeepSeek / Kimi / GLM** effort support is **not separately documented** (Kimi K2.6 reportedly
accepts it). So outside the natively-supported families, treat effort as best-effort.

| model family | notes |
|---|---|
| **GPT-5.x** | reasoning model — rejects `temperature != 1`, so **omit `--temperature`**. Reasons by default. |
| **GLM (z-ai/\*), Kimi (moonshotai/\*), DeepSeek, Qwen3.x** | `off` to disable; otherwise provider default. Effort levels may not map to distinct behavior (see above). |
| Claude (opus/sonnet/haiku) | run via the `anthropic` backend; reasoning not toggled here. |

(The OpenRouter leaderboard runs used **provider-default reasoning** or `off`, not effort levels — so per-family effort fidelity doesn't affect the published numbers.)

## Token-budget guidance (critical for reasoning models)
`max_tokens` must exceed the *reasoning* budget or the final answer never emits.
Observed on this benchmark (`short`/`verbose` design tier):
- **8k**: heavy reasoners (Kimi-K2.6, GLM-5.1) truncate on ~10%+ of fixtures → empty.
- **16–20k**: recovers most; our standard generous budget (≈100× a netlist's ~200 tokens).
- **>20k**: diminishing returns — a few hardest fixtures (Wilson-4T, folded/telescopic cascode)
  need 32–64k; even then they often emit a *wrong* topology. Kimi-K2.6 was seen to use 41,776
  output tokens on a single Wilson-4T fixture.

Empties are tracked as a separate `empty` count and excluded by an emitted-only score column;
latency and token totals quantify the test-time-compute cost of reasoning.

## What we ran (for reference)
- **Local leaderboard:** reasoning-capable locals ran **think=off** by default (qwen3:14b/30b,
  qwen3.5); **gpt-oss:20b** ran **think=low**. think=off was chosen *after* testing think=on on
  some of these and seeing **reasoning runaway** — the model spends the budget in the hidden
  `<think>` trace and emits empty/unparseable output (e.g. think-on qwen3.5 came back ~88% empty),
  so the leaderboard suppresses reasoning. The on/off A/B is in [`reasoning-ablation.md`](results/reasoning-ablation.md).
- **OpenRouter leaderboard:** all ran **provider-default (full) reasoning**.
- A/B experiments: kimi-k2.6 reasoning-off vs on; qwen3 think on/off; gpt-oss think low.

The measured on/off results (the ~60-pt kimi swing, the local think runaway, and worked netlist
examples) are reported in [`reasoning-ablation.md`](results/reasoning-ablation.md).
