# CircuitRubric leaderboard

_Generated 2026-06-23 by Claude from the benchmark's experiment runs, reviewed by the author. Aggregated across the current model set; model-set-dependent._

**Metrics**

| metric | meaning |
|---|---|
| `FULL` | exact iso + all sizing ratios |
| `ign_src` | FULL after stripping ideal V/I test-bench sources |
| `func_full` | FULL modulo a MOSFET drain/source swap |
| `topo` | FULL + PARTIAL + PARTIAL_BULK + TOPOLOGY (right wiring, sizing aside) |
| `recog` | topo + DECORATED (topology present in any form) |

Each diagnostic is >= FULL. `ign_src` / `func_full` are NOT nested under `topo` (an S/D-swapped or test-bench-wrapped circuit can exceed it); `topo <= recog` always.

**Reading the marks:** unmarked entries are **single runs** (temp=0, n=1) — and temp=0 is **not** deterministic on hosted APIs; full-corpus run-to-run spread is ~±1–3 percentage points, so compare at the error-bar level (see `reproducibility.md` and `variance.md`). `†` = multi-rep (mean of N reps). `*` = some empties recovered at a higher token budget (per-cell — a model may be marked in one table and not another). `‡` = a non-default reasoning/effort run (vs the model's default). `§` = a Summary-table mean over fewer than three design prompts. Default config per model: A/B variants (kimi `noreason`, local `thinktrue`) are excluded here and reported in `reasoning-ablation.md`. `—` = no run for that model×combo.

**Reasoning posture.** Per-model numbers use each model's *default* reasoning posture, which differs by vendor (opus off · gpt-5.5 medium · kimi ~full · gemini high — `thinkingLevel` default, which is also Gemini-3-Pro's *ceiling*; there is no setting above it) — so default cross-model gaps are not reasoning-equalized. The `short` per-prompt tables and both Summary tables include non-default reasoning/effort runs (marked ‡); the full effort ladder, cross-model breakdown, and cost are in `reasoning-ablation.md`.

## Contents

- [short x topology_ports](#short-x-topology_ports)
- [short x strict_ports](#short-x-strict_ports)
- [short x conventions](#short-x-conventions)
- [verbose x strict_ports](#verbose-x-strict_ports)
- [verbose x conventions](#verbose-x-conventions)
- [spec x topology](#spec-x-topology)
- [spec x topology_ports](#spec-x-topology_ports)
- [spec x strict_ports](#spec-x-strict_ports)
- [spec x conventions](#spec-x-conventions)
- [System-prompt impact on the short tier](#system-prompt-impact-on-the-short-tier)
- [Summary: best design prompt per tier](#summary-best-design-prompt-per-tier)
- [Summary: mean across the design prompts per tier](#summary-mean-across-the-design-prompts-per-tier)
- [Run coverage](#run-coverage)

## short x topology_ports

This cell includes the **reasoning/effort experiment runs** (non-default `config` marked); all other tables are default-only. **Single-run.** Full effort ladder, cross-model breakdown, and cost in `reasoning-ablation.md`.

| model                              | config          | FULL% | ign_src% | func_full% | topo% | recog% |
| ---------------------------------- | --------------- | ----- | -------- | ---------- | ----- | ------ |
| gemini-3.1-pro                     | default         | 88.8  | 88.8     | 89.6       | 88.8  | 90.4   |
| gemini-3.1-pro                     | low             | 84.8  | 84.8     | 85.6       | 88.0  | 91.2   |
| claude-opus-4-8                    | max + think     | 84.0  | 84.0     | 84.8       | 84.0  | 91.2   |
| claude-opus-4-8                    | xhigh + think   | 82.4  | 82.4     | 82.4       | 82.4  | 89.6   |
| openai/gpt-5.5                     | xhigh           | 77.6  | 77.6     | 77.6       | 78.4  | 85.6   |
| claude-opus-4-8                    | high + think    | 75.2  | 75.2     | 75.2       | 75.2  | 84.8   |
| openai/gpt-5.5                     | default         | 75.2  | 75.2     | 76.8       | 76.0  | 82.4   |
| claude-opus-4-7                    | high + think    | 71.2  | 71.2     | 72.0       | 71.2  | 84.8   |
| z-ai/glm-5.1 *                     | default         | 64.0  | 64.0     | 64.8       | 64.0  | 70.4   |
| claude-opus-4-8                    | xhigh, no think | 62.4  | 62.4     | 62.4       | 62.4  | 71.2   |
| claude-opus-4-7                    | default         | 61.6  | 61.6     | 62.4       | 61.6  | 72.8   |
| moonshotai/kimi-k2.6 *             | default         | 61.6  | 61.6     | 62.4       | 63.2  | 72.8   |
| gemini-3.5-flash                   | default         | 58.4  | 58.4     | 58.4       | 59.2  | 86.4   |
| claude-opus-4-8                    | default         | 53.6  | 53.6     | 54.4       | 53.6  | 64.8   |
| qwen/qwen3.7-max                   | default         | 52.0  | 52.0     | 53.6       | 52.0  | 71.2   |
| z-ai/glm-5.2                       | default         | 44.8  | 44.8     | 45.6       | 44.8  | 62.4   |
| deepseek/deepseek-v4-pro           | default         | 40.0  | 40.0     | 41.6       | 40.0  | 52.0   |
| gemma-4-31b                        | default         | 12.8  | 12.8     | 12.8       | 14.4  | 18.4   |
| gpt-oss:20b                        | default         | 6.4   | 6.4      | 7.2        | 7.2   | 9.6    |
| qwen2.5-coder:7b                   | default         | 1.6   | 1.6      | 3.2        | 1.6   | 1.6    |
| phi4:14b                           | default         | 0.8   | 1.6      | 0.8        | 0.8   | 4.0    |
| qwen2.5-coder:14b                  | default         | 0.8   | 2.4      | 0.8        | 0.8   | 2.4    |
| qwen3.5:latest                     | default         | 0.8   | 2.4      | 1.6        | 0.8   | 2.4    |
| qwen3:30b-a3b-instruct-2507-q4_K_M | default         | 0.8   | 4.8      | 0.8        | 0.8   | 6.4    |
| deepseek-coder-v2:16b              | default         | 0.0   | 0.0      | 0.8        | 0.8   | 1.6    |
| gemma2:9b                          | default         | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| gemma3:12b                         | default         | 0.0   | 0.0      | 0.0        | 0.0   | 1.6    |
| granite3.1-dense:8b                | default         | 0.0   | 0.0      | 0.0        | 0.0   | 1.6    |
| llama3.1:8b                        | default         | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| qwen3:14b                          | default         | 0.0   | 0.0      | 0.8        | 0.0   | 3.2    |

## short x strict_ports

| model                              | FULL% | ign_src% | func_full% | topo% | recog% |
| ---------------------------------- | ----- | -------- | ---------- | ----- | ------ |
| gemini-3.1-pro                     | 84.8  | 84.8     | 85.6       | 84.8  | 84.8   |
| claude-opus-4-8 (xhigh + think) ‡  | 77.6  | 77.6     | 77.6       | 78.4  | 78.4   |
| openai/gpt-5.5                     | 72.0  | 72.0     | 72.0       | 72.0  | 74.4   |
| moonshotai/kimi-k2.6 *             | 66.4  | 66.4     | 68.8       | 66.4  | 66.4   |
| claude-opus-4-7                    | 65.6  | 65.6     | 65.6       | 66.4  | 68.0   |
| qwen/qwen3.7-max                   | 65.6  | 65.6     | 67.2       | 66.4  | 69.6   |
| z-ai/glm-5.1                       | 62.4  | 62.4     | 64.0       | 62.4  | 63.2   |
| claude-opus-4-8                    | 59.2  | 59.2     | 60.0       | 60.0  | 60.8   |
| deepseek/deepseek-v4-pro           | 52.0  | 52.0     | 53.6       | 52.0  | 53.6   |
| qwen/qwen3.7-plus                  | 48.8  | 48.8     | 50.4       | 50.4  | 55.2   |
| claude-sonnet-4-6                  | 48.0  | 48.0     | 49.6       | 48.8  | 53.6   |
| minimax/minimax-m3 *               | 45.6  | 45.6     | 48.0       | 45.6  | 50.4   |
| z-ai/glm-4.5 *                     | 34.4  | 34.4     | 34.4       | 36.0  | 37.6   |
| deepseek/deepseek-v4-flash         | 33.6  | 33.6     | 34.4       | 33.6  | 36.8   |
| moonshotai/kimi-k2-0905            | 20.8  | 20.8     | 21.6       | 24.0  | 27.2   |
| claude-haiku-4-5-20251001          | 19.2  | 20.0     | 20.0       | 20.8  | 26.4   |
| deepseek/deepseek-chat-v3-0324     | 13.6  | 13.6     | 13.6       | 13.6  | 13.6   |
| meta-llama/llama-4-maverick        | 11.2  | 11.2     | 11.2       | 12.0  | 12.8   |
| qwen/qwen3-235b-a22b-2507          | 5.6   | 7.2      | 6.4        | 5.6   | 8.0    |
| gpt-oss:20b                        | 3.2   | 5.6      | 4.8        | 4.0   | 6.4    |
| phi4:14b                           | 3.2   | 4.0      | 3.2        | 3.2   | 4.8    |
| qwen3.5:latest †                   | 3.2   | 3.2      | 3.2        | 4.0   | 4.0    |
| qwen2.5-coder:7b                   | 2.4   | 2.4      | 2.4        | 2.4   | 2.4    |
| meta-llama/llama-3.3-70b-instruct  | 1.6   | 1.6      | 1.6        | 1.6   | 1.6    |
| qwen2.5-coder:14b                  | 1.6   | 2.4      | 1.6        | 1.6   | 2.4    |
| qwen3:14b †                        | 1.6   | 2.0      | 1.6        | 1.6   | 2.0    |
| deepseek-r1:14b                    | 0.8   | 0.8      | 0.8        | 1.6   | 1.6    |
| gemma2:9b                          | 0.8   | 0.8      | 0.8        | 0.8   | 0.8    |
| gemma3:12b                         | 0.8   | 0.8      | 0.8        | 0.8   | 0.8    |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 0.8   | 2.4      | 0.8        | 1.6   | 3.2    |
| deepseek-coder-v2:16b              | 0.0   | 0.8      | 0.0        | 0.0   | 1.6    |
| granite3.1-dense:8b                | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| llama3.1:8b                        | 0.0   | 0.0      | 0.0        | 0.0   | 0.8    |

## short x conventions

| model                              | FULL% | ign_src% | func_full% | topo% | recog% |
| ---------------------------------- | ----- | -------- | ---------- | ----- | ------ |
| claude-opus-4-8 (xhigh + think) ‡  | 92.8  | 92.8     | 93.6       | 93.6  | 93.6   |
| gemini-3.1-pro                     | 89.6  | 89.6     | 91.2       | 89.6  | 89.6   |
| openai/gpt-5.5                     | 85.6  | 85.6     | 85.6       | 85.6  | 86.4   |
| claude-opus-4-8                    | 68.8  | 68.8     | 69.6       | 72.8  | 72.8   |
| claude-opus-4-7                    | 68.0  | 68.0     | 68.0       | 69.6  | 69.6   |
| moonshotai/kimi-k2.6 *             | 68.0  | 68.0     | 70.4       | 68.8  | 69.6   |
| z-ai/glm-5.1                       | 64.0  | 64.0     | 64.0       | 64.0  | 68.0   |
| qwen/qwen3.7-max                   | 62.4  | 62.4     | 64.8       | 64.0  | 72.0   |
| deepseek/deepseek-v4-pro           | 52.0  | 52.0     | 55.2       | 53.6  | 55.2   |
| qwen/qwen3.7-plus                  | 52.0  | 52.0     | 54.4       | 52.0  | 58.4   |
| minimax/minimax-m3 *               | 46.4  | 46.4     | 48.0       | 48.0  | 57.6   |
| claude-sonnet-4-6                  | 44.0  | 44.0     | 44.8       | 47.2  | 53.6   |
| deepseek/deepseek-v4-flash         | 32.8  | 32.8     | 35.2       | 36.8  | 39.2   |
| z-ai/glm-4.5 *                     | 28.0  | 28.0     | 28.0       | 35.2  | 38.4   |
| moonshotai/kimi-k2-0905            | 19.2  | 19.2     | 19.2       | 20.8  | 24.0   |
| claude-haiku-4-5-20251001          | 18.4  | 18.4     | 18.4       | 20.0  | 22.4   |
| deepseek/deepseek-chat-v3-0324     | 16.8  | 17.6     | 16.8       | 21.6  | 28.0   |
| meta-llama/llama-4-maverick        | 12.0  | 12.0     | 12.0       | 14.4  | 16.0   |
| gemma-4-31b                        | 7.2   | 7.2      | 8.0        | 7.2   | 8.0    |
| qwen/qwen3-235b-a22b-2507          | 7.2   | 9.6      | 7.2        | 8.8   | 11.2   |
| gpt-oss:20b                        | 4.0   | 7.2      | 4.0        | 4.0   | 8.0    |
| meta-llama/llama-3.3-70b-instruct  | 4.0   | 4.0      | 4.0        | 4.0   | 5.6    |
| qwen3:14b                          | 3.2   | 4.0      | 3.2        | 3.2   | 4.0    |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 2.4   | 2.4      | 2.4        | 2.4   | 5.6    |
| qwen3.5:latest                     | 0.8   | 0.8      | 0.8        | 0.8   | 0.8    |
| deepseek-coder-v2:16b              | 0.0   | 0.8      | 0.0        | 0.0   | 0.8    |
| gemma2:9b                          | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| gemma3:12b                         | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| granite3.1-dense:8b                | 0.0   | 0.0      | 0.0        | 0.0   | 0.8    |
| llama3.1:8b                        | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| phi4:14b                           | 0.0   | 0.0      | 0.8        | 0.0   | 0.0    |
| qwen2.5-coder:14b                  | 0.0   | 0.8      | 0.0        | 0.0   | 1.6    |
| qwen2.5-coder:7b                   | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |

## verbose x strict_ports

| model                              | FULL% | ign_src% | func_full% | topo% | recog% |
| ---------------------------------- | ----- | -------- | ---------- | ----- | ------ |
| openai/gpt-5.5                     | 84.8  | 84.8     | 85.6       | 85.6  | 85.6   |
| qwen/qwen3.7-max                   | 79.2  | 79.2     | 81.6       | 84.0  | 84.0   |
| moonshotai/kimi-k2.6 *             | 76.8  | 76.8     | 79.2       | 80.0  | 80.0   |
| claude-opus-4-8                    | 75.2  | 75.2     | 76.0       | 76.0  | 76.0   |
| z-ai/glm-5.1                       | 72.0  | 72.0     | 74.4       | 75.2  | 75.2   |
| claude-sonnet-4-6                  | 64.8  | 64.8     | 64.8       | 68.8  | 69.6   |
| qwen/qwen3.7-plus                  | 61.6  | 61.6     | 64.0       | 66.4  | 66.4   |
| deepseek/deepseek-v4-pro           | 58.4  | 58.4     | 64.0       | 63.2  | 64.0   |
| minimax/minimax-m3 *               | 55.2  | 55.2     | 56.8       | 60.8  | 60.8   |
| z-ai/glm-4.5 *                     | 52.8  | 52.8     | 55.2       | 58.4  | 58.4   |
| deepseek/deepseek-v4-flash         | 41.6  | 41.6     | 43.2       | 44.0  | 44.0   |
| claude-haiku-4-5-20251001          | 30.4  | 31.2     | 30.4       | 33.6  | 35.2   |
| moonshotai/kimi-k2-0905            | 25.6  | 25.6     | 25.6       | 29.6  | 29.6   |
| deepseek/deepseek-chat-v3-0324     | 18.4  | 20.0     | 18.4       | 19.2  | 20.8   |
| meta-llama/llama-4-maverick        | 13.6  | 14.4     | 13.6       | 15.2  | 16.0   |
| gpt-oss:20b                        | 9.6   | 12.0     | 10.4       | 13.6  | 16.0   |
| qwen/qwen3-235b-a22b-2507          | 8.8   | 12.0     | 10.4       | 12.0  | 15.2   |
| meta-llama/llama-3.3-70b-instruct  | 6.4   | 6.4      | 7.2        | 6.4   | 6.4    |
| qwen2.5-coder:7b                   | 4.0   | 4.0      | 4.0        | 4.0   | 4.0    |
| qwen3.5:latest                     | 4.0   | 4.0      | 4.0        | 4.0   | 4.8    |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 3.2   | 4.0      | 3.2        | 7.2   | 8.0    |
| phi4:14b                           | 2.4   | 2.4      | 2.4        | 2.4   | 2.4    |
| gemma2:9b                          | 0.8   | 0.8      | 0.8        | 0.8   | 0.8    |
| gemma3:12b                         | 0.8   | 0.8      | 1.6        | 0.8   | 0.8    |
| qwen3:14b                          | 0.8   | 2.4      | 1.6        | 0.8   | 3.2    |
| deepseek-coder-v2:16b              | 0.0   | 0.8      | 0.0        | 0.0   | 0.8    |
| granite3.1-dense:8b                | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| llama3.1:8b                        | 0.0   | 0.0      | 0.8        | 0.0   | 0.0    |
| qwen2.5-coder:14b                  | 0.0   | 2.4      | 0.8        | 1.6   | 4.0    |

## verbose x conventions

| model                              | FULL% | ign_src% | func_full% | topo% | recog% |
| ---------------------------------- | ----- | -------- | ---------- | ----- | ------ |
| claude-opus-4-8                    | 75.2  | 75.2     | 76.0       | 78.4  | 78.4   |
| claude-sonnet-4-6                  | 65.6  | 65.6     | 66.4       | 71.2  | 71.2   |
| claude-haiku-4-5-20251001          | 26.4  | 28.0     | 27.2       | 31.2  | 32.8   |
| gpt-oss:20b                        | 4.8   | 8.8      | 4.8        | 7.2   | 12.0   |
| qwen3:14b                          | 4.8   | 4.8      | 4.8        | 4.8   | 5.6    |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 3.2   | 4.0      | 3.2        | 4.0   | 4.8    |
| phi4:14b                           | 1.6   | 1.6      | 1.6        | 1.6   | 1.6    |
| qwen2.5-coder:7b                   | 0.8   | 0.8      | 0.8        | 0.8   | 0.8    |
| qwen3.5:latest                     | 0.8   | 0.8      | 0.8        | 1.6   | 1.6    |
| deepseek-coder-v2:16b              | 0.0   | 0.8      | 0.0        | 0.0   | 0.8    |
| gemma2:9b                          | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| gemma3:12b                         | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| granite3.1-dense:8b                | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| llama3.1:8b                        | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| qwen2.5-coder:14b                  | 0.0   | 0.0      | 0.0        | 0.0   | 0.8    |

## spec x topology

| model                                | FULL% | ign_src% | func_full% | topo% | recog% |
| ------------------------------------ | ----- | -------- | ---------- | ----- | ------ |
| phi4:14b                             | 56.8  | 60.8     | 59.2       | 63.2  | 67.2   |
| qwen3:30b-a3b-instruct-2507-q4_K_M † | 55.6  | 56.8     | 60.8       | 60.8  | 62.0   |
| qwen3:14b                            | 54.4  | 55.2     | 56.0       | 54.4  | 67.2   |
| gpt-oss:20b                          | 41.6  | 43.2     | 45.6       | 60.0  | 61.6   |
| qwen2.5-coder:14b                    | 32.0  | 33.6     | 32.0       | 36.8  | 38.4   |
| deepseek-coder-v2:16b                | 27.2  | 27.2     | 29.6       | 31.2  | 31.2   |
| qwen3.5:latest                       | 15.2  | 15.2     | 16.8       | 16.0  | 16.8   |
| granite3.1-dense:8b                  | 5.6   | 6.4      | 5.6        | 5.6   | 9.6    |
| qwen2.5-coder:7b                     | 3.2   | 3.2      | 3.2        | 5.6   | 5.6    |
| gemma3:12b                           | 0.8   | 4.0      | 0.8        | 0.8   | 4.0    |
| gemma2:9b                            | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |
| llama3.1:8b                          | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |

## spec x topology_ports

| model                                | FULL% | ign_src% | func_full% | topo% | recog% |
| ------------------------------------ | ----- | -------- | ---------- | ----- | ------ |
| gpt-oss:20b                          | 75.2  | 75.2     | 78.4       | 86.4  | 87.2   |
| phi4:14b †                           | 65.6  | 70.0     | 68.0       | 75.6  | 85.6   |
| qwen2.5-coder:7b †                   | 65.6  | 65.6     | 65.6       | 74.4  | 78.0   |
| qwen3:30b-a3b-instruct-2507-q4_K_M † | 60.8  | 60.8     | 64.0       | 68.4  | 76.4   |
| qwen3.5:latest †                     | 55.2  | 55.2     | 56.0       | 64.0  | 78.4   |
| deepseek-coder-v2:16b                | 38.4  | 38.4     | 38.4       | 47.2  | 52.8   |
| qwen2.5-coder:14b                    | 30.4  | 30.4     | 30.4       | 60.8  | 60.8   |
| qwen3:14b                            | 30.4  | 31.2     | 32.8       | 72.0  | 77.6   |
| gemma3:12b                           | 24.0  | 29.6     | 24.0       | 27.2  | 46.4   |
| gemma2:9b †                          | 23.2  | 23.2     | 24.0       | 52.4  | 58.8   |
| granite3.1-dense:8b †                | 7.6   | 7.6      | 8.0        | 10.8  | 32.4   |
| llama3.1:8b †                        | 6.0   | 6.0      | 8.4        | 7.6   | 21.2   |

## spec x strict_ports

| model                                | FULL% | ign_src% | func_full% | topo% | recog% |
| ------------------------------------ | ----- | -------- | ---------- | ----- | ------ |
| openai/gpt-5.5                       | 95.2  | 95.2     | 95.2       | 100.0 | 100.0  |
| qwen/qwen3.7-plus                    | 95.2  | 95.2     | 95.2       | 100.0 | 100.0  |
| moonshotai/kimi-k2.6                 | 94.4  | 94.4     | 94.4       | 99.2  | 99.2   |
| deepseek/deepseek-v4-pro             | 92.0  | 92.0     | 93.6       | 98.4  | 98.4   |
| qwen/qwen3.7-max                     | 92.0  | 92.0     | 92.0       | 100.0 | 100.0  |
| claude-sonnet-4-6                    | 91.2  | 91.2     | 91.2       | 99.2  | 99.2   |
| z-ai/glm-5.1                         | 91.2  | 91.2     | 91.2       | 93.6  | 93.6   |
| minimax/minimax-m3                   | 89.6  | 89.6     | 90.4       | 98.4  | 98.4   |
| claude-haiku-4-5-20251001            | 88.0  | 88.0     | 88.0       | 98.4  | 98.4   |
| z-ai/glm-4.5 *                       | 87.2  | 87.2     | 88.8       | 97.6  | 97.6   |
| deepseek/deepseek-v4-flash           | 85.6  | 85.6     | 89.6       | 94.4  | 94.4   |
| meta-llama/llama-4-maverick          | 85.6  | 85.6     | 87.2       | 94.4  | 94.4   |
| meta-llama/llama-3.3-70b-instruct    | 84.8  | 84.8     | 84.8       | 92.0  | 92.0   |
| moonshotai/kimi-k2-0905              | 82.4  | 82.4     | 85.6       | 93.6  | 93.6   |
| gpt-oss:20b                          | 78.4  | 78.4     | 82.4       | 92.8  | 92.8   |
| deepseek/deepseek-chat-v3-0324       | 76.8  | 76.8     | 77.6       | 89.6  | 89.6   |
| qwen3.5:latest †                     | 68.8  | 68.8     | 68.8       | 80.0  | 80.8   |
| phi4:14b †                           | 66.0  | 66.0     | 66.8       | 74.8  | 74.8   |
| qwen3:30b-a3b-instruct-2507-q4_K_M † | 64.0  | 64.8     | 66.8       | 76.4  | 78.4   |
| qwen2.5-coder:7b †                   | 62.4  | 62.4     | 62.8       | 71.6  | 71.6   |
| qwen/qwen3-235b-a22b-2507            | 59.2  | 61.6     | 62.4       | 67.2  | 69.6   |
| qwen3:14b                            | 52.0  | 56.8     | 53.6       | 89.6  | 96.0   |
| deepseek-coder-v2:16b                | 45.6  | 45.6     | 48.0       | 52.8  | 54.4   |
| qwen2.5-coder:14b                    | 42.4  | 46.4     | 42.4       | 61.6  | 65.6   |
| gemma3:12b                           | 34.4  | 38.4     | 35.2       | 39.2  | 44.0   |
| llama3.1:8b †                        | 24.8  | 24.8     | 24.8       | 41.6  | 42.0   |
| gemma2:9b †                          | 18.4  | 18.4     | 19.2       | 50.0  | 50.8   |
| granite3.1-dense:8b †                | 16.0  | 16.4     | 16.8       | 24.4  | 27.2   |

## spec x conventions

| model                              | FULL% | ign_src% | func_full% | topo% | recog% |
| ---------------------------------- | ----- | -------- | ---------- | ----- | ------ |
| claude-opus-4-8                    | 96.0  | 96.0     | 96.0       | 100.0 | 100.0  |
| claude-sonnet-4-6                  | 92.8  | 92.8     | 92.8       | 100.0 | 100.0  |
| claude-haiku-4-5-20251001          | 84.8  | 86.4     | 84.8       | 95.2  | 96.8   |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 49.6  | 52.8     | 51.2       | 58.4  | 61.6   |
| qwen3:14b                          | 48.8  | 51.2     | 48.8       | 52.8  | 56.8   |
| phi4:14b                           | 40.0  | 42.4     | 43.2       | 44.0  | 46.4   |
| qwen2.5-coder:14b                  | 40.0  | 42.4     | 40.8       | 46.4  | 48.8   |
| gpt-oss:20b                        | 32.0  | 36.0     | 32.8       | 60.0  | 64.0   |
| deepseek-coder-v2:16b              | 18.4  | 20.0     | 19.2       | 28.0  | 30.4   |
| qwen3.5:latest                     | 18.4  | 18.4     | 19.2       | 22.4  | 22.4   |
| qwen2.5-coder:7b                   | 6.4   | 6.4      | 6.4        | 8.8   | 8.8    |
| granite3.1-dense:8b                | 5.6   | 5.6      | 5.6        | 5.6   | 7.2    |
| gemma2:9b                          | 1.6   | 1.6      | 1.6        | 2.4   | 2.4    |
| gemma3:12b                         | 0.0   | 0.8      | 0.0        | 0.0   | 0.8    |
| llama3.1:8b                        | 0.0   | 0.0      | 0.0        | 0.0   | 0.0    |

## System-prompt impact on the short tier

FULL% across system prompts for models run on 3 or more of them, plus the reasoning/effort experiment runs (‡). How each model's design (short) FULL% shifts across system prompts — from `formatted` (no output convention) through `conventions` (pre-resolves topology defaults). ‡ = non-default reasoning/effort config (most ran only `topology_ports`); single-run, see `reasoning-ablation.md`.

| model                               | topology | topology_ports | strict_ports | conventions | formatted |
| ----------------------------------- | -------- | -------------- | ------------ | ----------- | --------- |
| claude-opus-4-8 (xhigh + think) ‡   | —        | 82.4           | 77.6         | 92.8        | —         |
| gemini-3.1-pro                      | —        | 88.8           | 84.8         | 89.6        | —         |
| openai/gpt-5.5                      | —        | 75.2           | 72.0         | 85.6        | 1.6       |
| gemini-3.1-pro (low) ‡              | —        | 84.8           | —            | —           | —         |
| claude-opus-4-8 (max + think) ‡     | —        | 84.0           | —            | —           | —         |
| openai/gpt-5.5 (xhigh) ‡            | —        | 77.6           | —            | —           | —         |
| claude-opus-4-8 (high + think) ‡    | —        | 75.2           | —            | —           | —         |
| claude-opus-4-7 (high + think) ‡    | —        | 71.2           | —            | —           | —         |
| claude-opus-4-8                     | —        | 53.6           | 59.2         | 68.8        | —         |
| claude-opus-4-7                     | —        | 61.6           | 65.6         | 68.0        | —         |
| moonshotai/kimi-k2.6                | —        | 61.6           | 66.4         | 68.0        | 0.0       |
| qwen/qwen3.7-max                    | —        | 52.0           | 65.6         | 62.4        | —         |
| z-ai/glm-5.1                        | —        | 64.0           | 62.4         | 64.0        | 0.0       |
| claude-opus-4-8 (xhigh, no think) ‡ | —        | 62.4           | —            | —           | —         |
| deepseek/deepseek-v4-pro            | —        | 40.0           | 52.0         | 52.0        | 0.0       |
| claude-sonnet-4-6                   | 12.0     | —              | 48.0         | 44.0        | —         |
| claude-haiku-4-5-20251001           | 3.2      | —              | 19.2         | 18.4        | —         |
| gpt-oss:20b                         | 0.0      | 6.4            | 3.2          | 4.0         | —         |
| phi4:14b                            | 0.8      | 0.8            | 3.2          | 0.0         | —         |
| qwen3.5:latest                      | 0.0      | 0.8            | 3.2          | 0.8         | —         |
| qwen3:14b                           | 0.8      | 0.0            | 1.6          | 3.2         | —         |
| qwen3:30b-a3b-instruct-2507-q4_K_M  | 2.8      | 0.8            | 0.8          | 2.4         | —         |
| qwen2.5-coder:7b                    | 0.0      | 1.6            | 2.4          | 0.0         | —         |
| qwen2.5-coder:14b                   | 0.0      | 0.8            | 1.6          | 0.0         | —         |
| gemma2:9b                           | 0.0      | 0.0            | 0.8          | 0.0         | —         |
| gemma3:12b                          | 0.0      | 0.0            | 0.8          | 0.0         | —         |
| deepseek-coder-v2:16b               | 0.0      | 0.0            | 0.0          | 0.0         | —         |
| granite3.1-dense:8b                 | 0.0      | 0.0            | 0.0          | 0.0         | —         |
| llama3.1:8b                         | 0.0      | 0.0            | 0.0          | 0.0         | —         |

## Summary: best design prompt per tier

Each cell = the model's **best** FULL% / topo% / recog% across the design prompts it ran, with the winning prompt in parens (tp=`topology_ports`, sp=`strict_ports`, cv=`conventions`). This is the peak — a best-of-N upper bound; for an apples-to-apples comparison use a single fixed system prompt (the per-prompt tables above, or the README's `strict_ports` view). Sorted by best `short`.

| model                              | short F/t/r (p)         | verbose F/t/r (p)       | spec F/t/r (p)            |
| ---------------------------------- | ----------------------- | ----------------------- | ------------------------- |
| claude-opus-4-8 (xhigh + think) ‡  | 92.8 / 93.6 / 93.6 (cv) | —                       | —                         |
| gemini-3.1-pro                     | 89.6 / 89.6 / 89.6 (cv) | —                       | —                         |
| openai/gpt-5.5                     | 85.6 / 85.6 / 86.4 (cv) | 84.8 / 85.6 / 85.6 (sp) | 95.2 / 100.0 / 100.0 (sp) |
| claude-opus-4-8                    | 68.8 / 72.8 / 72.8 (cv) | 75.2 / 76.0 / 76.0 (sp) | 96.0 / 100.0 / 100.0 (cv) |
| claude-opus-4-7                    | 68.0 / 69.6 / 69.6 (cv) | —                       | —                         |
| moonshotai/kimi-k2.6               | 68.0 / 68.8 / 69.6 (cv) | 76.8 / 80.0 / 80.0 (sp) | 94.4 / 99.2 / 99.2 (sp)   |
| qwen/qwen3.7-max                   | 65.6 / 66.4 / 69.6 (sp) | 79.2 / 84.0 / 84.0 (sp) | 92.0 / 100.0 / 100.0 (sp) |
| z-ai/glm-5.1                       | 64.0 / 64.0 / 70.4 (tp) | 72.0 / 75.2 / 75.2 (sp) | 91.2 / 93.6 / 93.6 (sp)   |
| gemini-3.5-flash                   | 58.4 / 59.2 / 86.4 (tp) | —                       | —                         |
| deepseek/deepseek-v4-pro           | 52.0 / 52.0 / 53.6 (sp) | 58.4 / 63.2 / 64.0 (sp) | 92.0 / 98.4 / 98.4 (sp)   |
| qwen/qwen3.7-plus                  | 52.0 / 52.0 / 58.4 (cv) | 61.6 / 66.4 / 66.4 (sp) | 95.2 / 100.0 / 100.0 (sp) |
| claude-sonnet-4-6                  | 48.0 / 48.8 / 53.6 (sp) | 65.6 / 71.2 / 71.2 (cv) | 92.8 / 100.0 / 100.0 (cv) |
| minimax/minimax-m3                 | 46.4 / 48.0 / 57.6 (cv) | 55.2 / 60.8 / 60.8 (sp) | 89.6 / 98.4 / 98.4 (sp)   |
| z-ai/glm-5.2                       | 44.8 / 44.8 / 62.4 (tp) | —                       | —                         |
| z-ai/glm-4.5                       | 34.4 / 36.0 / 37.6 (sp) | 52.8 / 58.4 / 58.4 (sp) | 87.2 / 97.6 / 97.6 (sp)   |
| deepseek/deepseek-v4-flash         | 33.6 / 33.6 / 36.8 (sp) | 41.6 / 44.0 / 44.0 (sp) | 85.6 / 94.4 / 94.4 (sp)   |
| moonshotai/kimi-k2-0905            | 20.8 / 24.0 / 27.2 (sp) | 25.6 / 29.6 / 29.6 (sp) | 82.4 / 93.6 / 93.6 (sp)   |
| claude-haiku-4-5-20251001          | 19.2 / 20.8 / 26.4 (sp) | 30.4 / 33.6 / 35.2 (sp) | 88.0 / 98.4 / 98.4 (sp)   |
| deepseek/deepseek-chat-v3-0324     | 16.8 / 21.6 / 28.0 (cv) | 18.4 / 19.2 / 20.8 (sp) | 76.8 / 89.6 / 89.6 (sp)   |
| gemma-4-31b                        | 12.8 / 14.4 / 18.4 (tp) | —                       | —                         |
| meta-llama/llama-4-maverick        | 12.0 / 14.4 / 16.0 (cv) | 13.6 / 15.2 / 16.0 (sp) | 85.6 / 94.4 / 94.4 (sp)   |
| qwen/qwen3-235b-a22b-2507          | 7.2 / 8.8 / 11.2 (cv)   | 8.8 / 12.0 / 15.2 (sp)  | 59.2 / 67.2 / 69.6 (sp)   |
| gpt-oss:20b                        | 6.4 / 7.2 / 9.6 (tp)    | 9.6 / 13.6 / 16.0 (sp)  | 78.4 / 92.8 / 92.8 (sp)   |
| meta-llama/llama-3.3-70b-instruct  | 4.0 / 4.0 / 5.6 (cv)    | 6.4 / 6.4 / 6.4 (sp)    | 84.8 / 92.0 / 92.0 (sp)   |
| phi4:14b                           | 3.2 / 3.2 / 4.8 (sp)    | 2.4 / 2.4 / 2.4 (sp)    | 66.0 / 74.8 / 74.8 (sp)   |
| qwen3.5:latest                     | 3.2 / 4.0 / 4.0 (sp)    | 4.0 / 4.0 / 4.8 (sp)    | 68.8 / 80.0 / 80.8 (sp)   |
| qwen3:14b                          | 3.2 / 3.2 / 4.0 (cv)    | 4.8 / 4.8 / 5.6 (cv)    | 52.0 / 89.6 / 96.0 (sp)   |
| qwen2.5-coder:7b                   | 2.4 / 2.4 / 2.4 (sp)    | 4.0 / 4.0 / 4.0 (sp)    | 65.6 / 74.4 / 78.0 (tp)   |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 2.4 / 2.4 / 5.6 (cv)    | 3.2 / 7.2 / 8.0 (sp)    | 64.0 / 76.4 / 78.4 (sp)   |
| qwen2.5-coder:14b                  | 1.6 / 1.6 / 2.4 (sp)    | 0.0 / 1.6 / 4.0 (sp)    | 42.4 / 61.6 / 65.6 (sp)   |
| deepseek-r1:14b                    | 0.8 / 1.6 / 1.6 (sp)    | —                       | —                         |
| gemma2:9b                          | 0.8 / 0.8 / 0.8 (sp)    | 0.8 / 0.8 / 0.8 (sp)    | 23.2 / 52.4 / 58.8 (tp)   |
| gemma3:12b                         | 0.8 / 0.8 / 0.8 (sp)    | 0.8 / 0.8 / 0.8 (sp)    | 34.4 / 39.2 / 44.0 (sp)   |
| deepseek-coder-v2:16b              | 0.0 / 0.8 / 1.6 (tp)    | 0.0 / 0.0 / 0.8 (sp)    | 45.6 / 52.8 / 54.4 (sp)   |
| granite3.1-dense:8b                | 0.0 / 0.0 / 1.6 (tp)    | 0.0 / 0.0 / 0.0 (sp)    | 16.0 / 24.4 / 27.2 (sp)   |
| llama3.1:8b                        | 0.0 / 0.0 / 0.0 (tp)    | 0.0 / 0.0 / 0.0 (sp)    | 24.8 / 41.6 / 42.0 (sp)   |

## Summary: mean across the design prompts per tier

Each cell = model's FULL% / topo% / recog% **averaged** over `topology_ports`, `strict_ports`, and `conventions` — an average-case view across prompt choice. It can **understate a model's best** (see best-per-tier above), and the denominator varies with how many of the three prompts a model ran. Excludes the `minimal` / `formatted` controls and the bare `topology` / `strict` variants.

| model                              | short F/t/r        | verbose F/t/r      | spec F/t/r           |
| ---------------------------------- | ------------------ | ------------------ | -------------------- |
| gemini-3.1-pro                     | 87.7 / 87.7 / 88.3 | —                  | —                    |
| claude-opus-4-8 (xhigh+think) ‡    | 84.3 / 84.8 / 87.2 | —                  | —                    |
| openai/gpt-5.5                     | 77.6 / 77.9 / 81.1 | 84.8 / 85.6 / 85.6 | 95.2 / 100.0 / 100.0 |
| moonshotai/kimi-k2.6               | 65.3 / 66.1 / 69.6 | 76.8 / 80.0 / 80.0 | 94.4 / 99.2 / 99.2   |
| claude-opus-4-7                    | 65.1 / 65.9 / 70.1 | —                  | —                    |
| z-ai/glm-5.1                       | 63.5 / 63.5 / 67.2 | 72.0 / 75.2 / 75.2 | 91.2 / 93.6 / 93.6   |
| claude-opus-4-8                    | 60.5 / 62.1 / 66.1 | 75.2 / 77.2 / 77.2 | 96.0 / 100.0 / 100.0 |
| qwen/qwen3.7-max                   | 60.0 / 60.8 / 70.9 | 79.2 / 84.0 / 84.0 | 92.0 / 100.0 / 100.0 |
| gemini-3.5-flash §                 | 58.4 / 59.2 / 86.4 | —                  | —                    |
| qwen/qwen3.7-plus                  | 50.4 / 51.2 / 56.8 | 61.6 / 66.4 / 66.4 | 95.2 / 100.0 / 100.0 |
| deepseek/deepseek-v4-pro           | 48.0 / 48.5 / 53.6 | 58.4 / 63.2 / 64.0 | 92.0 / 98.4 / 98.4   |
| claude-sonnet-4-6                  | 46.0 / 48.0 / 53.6 | 65.2 / 70.0 / 70.4 | 92.0 / 99.6 / 99.6   |
| minimax/minimax-m3                 | 46.0 / 46.8 / 54.0 | 55.2 / 60.8 / 60.8 | 89.6 / 98.4 / 98.4   |
| z-ai/glm-5.2                       | 44.8 / 44.8 / 62.4 | —                  | —                    |
| deepseek/deepseek-v4-flash         | 33.2 / 35.2 / 38.0 | 41.6 / 44.0 / 44.0 | 85.6 / 94.4 / 94.4   |
| z-ai/glm-4.5                       | 31.2 / 35.6 / 38.0 | 52.8 / 58.4 / 58.4 | 87.2 / 97.6 / 97.6   |
| moonshotai/kimi-k2-0905            | 20.0 / 22.4 / 25.6 | 25.6 / 29.6 / 29.6 | 82.4 / 93.6 / 93.6   |
| claude-haiku-4-5-20251001          | 18.8 / 20.4 / 24.4 | 28.4 / 32.4 / 34.0 | 86.4 / 96.8 / 97.6   |
| deepseek/deepseek-chat-v3-0324     | 15.2 / 17.6 / 20.8 | 18.4 / 19.2 / 20.8 | 76.8 / 89.6 / 89.6   |
| meta-llama/llama-4-maverick        | 11.6 / 13.2 / 14.4 | 13.6 / 15.2 / 16.0 | 85.6 / 94.4 / 94.4   |
| gemma-4-31b §                      | 10.0 / 10.8 / 13.2 | —                  | —                    |
| qwen/qwen3-235b-a22b-2507          | 6.4 / 7.2 / 9.6    | 8.8 / 12.0 / 15.2  | 59.2 / 67.2 / 69.6   |
| gpt-oss:20b                        | 4.5 / 5.1 / 8.0    | 7.2 / 10.4 / 14.0  | 61.9 / 79.7 / 81.3   |
| meta-llama/llama-3.3-70b-instruct  | 2.8 / 2.8 / 3.6    | 6.4 / 6.4 / 6.4    | 84.8 / 92.0 / 92.0   |
| qwen3.5:latest                     | 2.0 / 2.4 / 2.8    | 2.4 / 2.8 / 3.2    | 53.3 / 62.1 / 68.2   |
| qwen3:14b                          | 1.6 / 1.6 / 2.8    | 2.8 / 2.8 / 4.4    | 43.7 / 71.5 / 76.8   |
| phi4:14b                           | 1.3 / 1.3 / 2.9    | 2.0 / 2.0 / 2.0    | 60.6 / 69.0 / 73.4   |
| qwen2.5-coder:7b                   | 1.3 / 1.3 / 1.3    | 2.4 / 2.4 / 2.4    | 52.5 / 60.2 / 61.6   |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 1.3 / 1.6 / 5.1    | 3.2 / 5.6 / 6.4    | 59.8 / 69.6 / 74.2   |
| deepseek-r1:14b                    | 0.8 / 1.6 / 1.6    | —                  | —                    |
| qwen2.5-coder:14b                  | 0.8 / 0.8 / 2.1    | 0.0 / 0.8 / 2.4    | 37.6 / 56.3 / 58.4   |
| gemma2:9b                          | 0.3 / 0.3 / 0.3    | 0.4 / 0.4 / 0.4    | 17.0 / 41.4 / 44.3   |
| gemma3:12b                         | 0.3 / 0.3 / 0.8    | 0.4 / 0.4 / 0.4    | 19.5 / 22.1 / 30.4   |
| deepseek-coder-v2:16b              | 0.0 / 0.3 / 1.3    | 0.0 / 0.0 / 0.8    | 34.1 / 42.7 / 45.9   |
| granite3.1-dense:8b                | 0.0 / 0.0 / 0.8    | 0.0 / 0.0 / 0.0    | 10.6 / 15.2 / 25.3   |
| llama3.1:8b                        | 0.0 / 0.0 / 0.3    | 0.0 / 0.0 / 0.0    | 12.3 / 19.7 / 25.3   |

‡ reasoning-on variant — xhigh + adaptive thinking, pooled over the three design prompts (the only variant run across all three). Single-run; full effort ladder + cross-model detail in `reasoning-ablation.md`.

§ mean over **fewer than three** design prompts (gemini-3.5-flash: `topology_ports` only; gemma-4-31b: `topology_ports` + `conventions`) — not directly comparable to the full-ladder means above.

## Run coverage

Which (tier × system-prompt) combos each model was run on. **✓** = full 125-fixture run; a number = partial (n fixtures); blank = not run. Tiers: **S**=short, **V**=verbose, **X**=spec.

| model                              | S·topo | S·topo_p | S·strict_p | S·conv | S·fmt | V·topo | V·strict_p | V·conv | X·topo | X·topo_p | X·strict | X·strict_p | X·conv |
| ---------------------------------- | ------ | -------- | ---------- | ------ | ----- | ------ | ---------- | ------ | ------ | -------- | -------- | ---------- | ------ |
| gemini-3.1-pro                     |        | ✓        | ✓          | ✓      |       |        |            |        |        |          |          |            |        |
| openai/gpt-5.5                     |        | ✓        | ✓          | ✓      | ✓     |        | ✓          |        |        |          |          | ✓          |        |
| moonshotai/kimi-k2.6               |        | ✓        | ✓          | ✓      | ✓     |        | ✓          |        |        |          |          | ✓          |        |
| claude-opus-4-7                    |        | ✓        | ✓          | ✓      |       |        |            |        |        |          |          |            |        |
| z-ai/glm-5.1                       |        | ✓        | ✓          | ✓      | ✓     |        | ✓          |        |        |          |          | ✓          |        |
| claude-opus-4-8                    |        | ✓        | ✓          | ✓      |       |        | ✓          | ✓      |        |          |          |            | ✓      |
| qwen/qwen3.7-max                   |        | ✓        | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| gemini-3.5-flash                   |        | ✓        |            |        |       |        |            |        |        |          |          |            |        |
| qwen/qwen3.7-plus                  |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| deepseek/deepseek-v4-pro           |        | ✓        | ✓          | ✓      | ✓     |        | ✓          |        |        |          |          | ✓          |        |
| claude-sonnet-4-6                  | ✓      |          | ✓          | ✓      |       |        | ✓          | ✓      |        |          |          | ✓          | ✓      |
| minimax/minimax-m3                 |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| z-ai/glm-5.2                       |        | ✓        |            |        | ✓     |        |            |        |        |          |          |            |        |
| deepseek/deepseek-v4-flash         |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| z-ai/glm-4.5                       |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| moonshotai/kimi-k2-0905            |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| claude-haiku-4-5-20251001          | ✓      |          | ✓          | ✓      |       |        | ✓          | ✓      |        |          |          | ✓          | ✓      |
| deepseek/deepseek-chat-v3-0324     |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| meta-llama/llama-4-maverick        |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| gemma-4-31b                        |        | ✓        |            | ✓      |       |        |            |        |        |          |          |            |        |
| qwen/qwen3-235b-a22b-2507          |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| gpt-oss:20b                        | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| meta-llama/llama-3.3-70b-instruct  |        |          | ✓          | ✓      |       |        | ✓          |        |        |          |          | ✓          |        |
| qwen3.5:latest                     | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| qwen3:14b                          | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| phi4:14b                           | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| qwen2.5-coder:7b                   | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| qwen3:30b-a3b-instruct-2507-q4_K_M | ✓      | ✓        | ✓          | ✓      |       | ✓      | ✓          | ✓      | ✓      | ✓        | ✓        | ✓          | ✓      |
| deepseek-r1:14b                    |        |          | ✓          |        |       |        |            |        |        |          |          |            |        |
| qwen2.5-coder:14b                  | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| gemma2:9b                          | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| gemma3:12b                         | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| deepseek-coder-v2:16b              | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| granite3.1-dense:8b                | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |
| llama3.1:8b                        | ✓      | ✓        | ✓          | ✓      |       |        | ✓          | ✓      | ✓      | ✓        |          | ✓          | ✓      |

---
### Notes & caveats

- **Single runs (unmarked):** temp=0, n=1, and temp=0 is **not deterministic** on hosted APIs; full-corpus run-to-run spread is ~±1–3 percentage points, so compare at the error-bar level rather than on small gaps. See `reproducibility.md` and `variance.md`.
- **`†` multi-rep:** value is the mean over N reps (several local models were re-run across reps). The glm-5.1/5.2 3-rep comparison is reported separately in `variance.md`, not here.
- **`*` recovered:** some empties were re-run at a higher token budget (40k/64k vs 20k base) and overlaid, so the run mixes budgets (per-fixture counts and token budgets are recorded per run).
- **Coverage:** the single default-config runs. Reported separately: the glm-5.1/5.2 3-rep comparison + run-to-run variance (`variance.md`), the reasoning on/off A/B (`reasoning-ablation.md`), and qualitative probes.
- **Per-fixture × model view:** which specific models design each fixture (FULL / topology-correct), per system prompt and combined, is in [`fixture_success_matrix.md`](fixture_success_matrix.md) — the inverse of this aggregate leaderboard.
