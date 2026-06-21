# Speed & test-time-compute cost

_Generated 2026-06-20 by Claude from the benchmark's experiment runs, reviewed by the author. Model-set-dependent._

The cost axis beside accuracy. **short FULL%** is the design-tier accuracy on the `short` (one-line) fixture prompt, pooled over the `topology_ports`, `strict_ports`, and `conventions` system prompts (same as the leaderboard Summary); **out-tok/call** is output tokens generated per call (mean / median — reasoning models are right-skewed); **s/call** is mean wall-clock latency; **tok/s** is throughput. Timing is from freshly-called rows only.

Reading it: latency is driven by **how much a model generates** (reasoning volume), not provider speed — and token volume is **uncorrelated with accuracy** (a terse model can beat a verbose one). Dollar cost scales with out-tok/call × the provider's per-token price.

`calls` = live-timed calls the speed figures average over. **`—`** in the speed columns means speed/token data was **not captured** for that model — its runs were resumed from cached responses, and latency/tokens are recorded only on a live call. Accuracy is unaffected (it's measured over all runs).

| model | short FULL% | out-tok/call (mean/med) | s/call | tok/s | calls |
|---|---|---|---|---|---|
| openai/gpt-5.5 | 77.6 | 1326 / 798 | 28 | 47 | 507 |
| moonshotai/kimi-k2.6 | 65.3 | 8698 / 7220 | 249 | 35 | 321 |
| claude-opus-4-7 | 65.1 | 305 / 258 | 6 | 52 | 375 |
| z-ai/glm-5.1 | 63.5 | 5313 / 2870 | 111 | 48 | 280 |
| claude-opus-4-8 | 60.5 | 289 / 243 | 5 | 59 | 750 |
| qwen/qwen3.7-max | 60.0 | 4126 / 2145 | 77 | 53 | 487 |
| qwen/qwen3.7-plus | 50.4 | 5094 / 2225 | 95 | 53 | 371 |
| deepseek/deepseek-v4-pro | 48.0 | 2110 / 1348 | 46 | 46 | 378 |
| claude-sonnet-4-6 | 46.0 | 549 / 463 | 11 | 52 | 875 |
| minimax/minimax-m3 | 46.0 | 11249 / 10236 | 199 | 57 | 71 |
| z-ai/glm-5.2 | 44.8 | 3951 / 1640 | 66 | 60 | 250 |
| deepseek/deepseek-v4-flash | 33.2 | 1275 / 918 | 17 | 75 | 214 |
| z-ai/glm-4.5 | 31.2 | 14315 / 20000 | 403 | 36 | 149 |
| moonshotai/kimi-k2-0905 | 20.0 | — | — | — | 1 |
| claude-haiku-4-5-20251001 | 18.8 | 450 / 425 | 5 | 93 | 836 |
| deepseek/deepseek-chat-v3-0324 | 15.2 | 240 / 233 | 11 | 23 | 179 |
| qwen/qwen3-235b-a22b-2507 | 6.4 | 215 / 139 | 7 | 33 | 500 |
| gpt-oss:20b | 4.5 | 425 / 306 | 14 | 31 | 1126 |
| qwen3.5:latest | 2.0 | 449 / 180 | 6 | 77 | 1625 |
| qwen3:14b | 1.6 | 201 / 164 | 4 | 56 | 1375 |
| phi4:14b | 1.3 | 218 / 196 | 3 | 63 | 1500 |
| qwen2.5-coder:7b | 1.3 | 276 / 105 | 2 | 116 | 1500 |
| qwen3:30b-a3b-instruct-2507-q4_K_M | 1.3 | 328 / 204 | 9 | 36 | 1884 |
| qwen2.5-coder:14b | 0.8 | 202 / 175 | 3 | 61 | 1250 |
| deepseek-r1:14b | 0.8 | 525 / 289 | 9 | 61 | 125 |
| gemma2:9b | 0.3 | 133 / 92 | 2 | 87 | 1500 |
| gemma3:12b | 0.3 | 267 / 231 | 4 | 61 | 1250 |
| deepseek-coder-v2:16b | 0.0 | 217 / 162 | 2 | 143 | 1250 |
| llama3.1:8b | 0.0 | 212 / 174 | 2 | 111 | 1500 |
| granite3.1-dense:8b | 0.0 | 360 / 316 | 3 | 103 | 1500 |
