# Clean design leaderboard — `short` tier, no-leak prompts

_Generated 2026-06-20 by Claude from the benchmark's experiment runs, reviewed by the author. Model-set-dependent._

No-leak system prompts only: **strict_ports** and **topology_ports** (excludes `conventions`,
which leaks topology answers, and `formatted`, which gives no output convention). FULL% is
mean±std where ≥2 reps exist. *Clean FULL* = the **least-scaffolded** no-leak prompt —
`topology_ports` if the model ran it, else `strict_ports`. This is a fixed preference, **not**
the higher of the two: several models (kimi, opus, qwen3.7-max) score higher on `strict_ports`
(shown in the last column). Empties recovered/overlaid per the reproducibility note.

| model | clean FULL% | prompt | FULL/emitted% | reps | empty | topology_ports | strict_ports |
|---|---|---|---|---|---|---|---|
| openai/gpt-5.5 | **75.2** | topology_ports | 75.2 | 1 | 0 | 75.2 | 72.0 |
| z-ai/glm-5.1 | **64.0** | topology_ports | 65.0 | 1 | 2 | 64.0 | 62.4 |
| moonshotai/kimi-k2.6 | **61.6** | topology_ports | 62.1 | 1 | 1 | 61.6 | 66.4 |
| claude-opus-4-7 | **61.6** | topology_ports | 61.6 | 1 | 0 | 61.6 | 65.6 |
| claude-opus-4-8 | **53.6** | topology_ports | 53.6 | 1 | 0 | 53.6 | 59.2 |
| qwen/qwen3.7-max | **52.0** | topology_ports | 52.0 | 1 | 0 | 52.0 | 65.6 |
| qwen/qwen3.7-plus | **48.8** | strict_ports | 49.2 | 1 | 1 | — | 48.8 |
| claude-sonnet-4-6 | **48.0** | strict_ports | 48.0 | 1 | 0 | — | 48.0 |
| minimax/minimax-m3 | **45.6** | strict_ports | 46.3 | 1 | 2 | — | 45.6 |
| z-ai/glm-5.2 | **44.8** | topology_ports | 47.1 | 1 | 6 | 44.8 | — |
| deepseek/deepseek-v4-pro | **40.0** | topology_ports | 40.3 | 1 | 1 | 40.0 | 52.0 |
| z-ai/glm-4.5 | **34.4** | strict_ports | 42.6 | 1 | 24 | — | 34.4 |
| deepseek/deepseek-v4-flash | **33.6** | strict_ports | 33.6 | 1 | 0 | — | 33.6 |
| moonshotai/kimi-k2-0905 | **20.8** | strict_ports | 20.8 | 1 | 0 | — | 20.8 |
| claude-haiku-4-5-20251001 | **19.2** | strict_ports | 19.2 | 1 | 0 | — | 19.2 |
| deepseek/deepseek-chat-v3-0324 | **13.6** | strict_ports | 14.5 | 1 | 8 | — | 13.6 |
| meta-llama/llama-4-maverick | **11.2** | strict_ports | 11.2 | 1 | 0 | — | 11.2 |
| gpt-oss:20b | **6.4** | topology_ports | 6.4 | 1 | 0 | 6.4 | 3.2 |
| qwen/qwen3-235b-a22b-2507 | **5.6** | strict_ports | 5.6 | 1 | 0 | — | 5.6 |
| qwen2.5-coder:7b | **1.6** | topology_ports | 1.6 | 1 | 0 | 1.6 | 2.4 |
| meta-llama/llama-3.3-70b-instruct | **1.6** | strict_ports | 1.6 | 1 | 0 | — | 1.6 |
| qwen3:30b-a3b-instruct-2507-q4_K_M | **0.8** | topology_ports | 0.8 | 1 | 5 | 0.8 | 0.8 |
| qwen3.5:latest | **0.8** | topology_ports | 0.8 | 1 | 2 | 0.8 | 3.2±0.0 |
| qwen2.5-coder:14b | **0.8** | topology_ports | 0.8 | 1 | 0 | 0.8 | 1.6 |
| phi4:14b | **0.8** | topology_ports | 0.8 | 1 | 0 | 0.8 | 3.2 |
| deepseek-r1:14b | **0.8** | strict_ports | 0.8 | 1 | 1 | — | 0.8 |
| qwen3:14b | **0.0** | topology_ports | 0.0 | 1 | 0 | 0.0 | 1.6±0.0 |
| llama3.1:8b | **0.0** | topology_ports | 0.0 | 1 | 0 | 0.0 | 0.0 |
| granite3.1-dense:8b | **0.0** | topology_ports | 0.0 | 1 | 0 | 0.0 | 0.0 |
| gemma3:12b | **0.0** | topology_ports | 0.0 | 1 | 0 | 0.0 | 0.8 |
| gemma2:9b | **0.0** | topology_ports | 0.0 | 1 | 1 | 0.0 | 0.8 |
| deepseek-coder-v2:16b | **0.0** | topology_ports | 0.0 | 1 | 0 | 0.0 | 0.0 |
