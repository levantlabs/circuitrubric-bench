# Reproducing the baselines

How to re-run CircuitRubric over hosted/open models and get comparable numbers. The
generation path is the shipped `circuitrubric run` / `run-all` CLI — no extra code needed.

For *what* the scores mean see [`methodology.md`](methodology.md); for run-to-run variance
see [`reproducibility.md`](results/reproducibility.md).

## 1. Install + key

```bash
pip install -e ".[openai]"          # openai SDK; add [anthropic]/[ollama] as needed
export OPENROUTER_API_KEY=sk-or-...
```

OpenRouter is **not a special backend** — it's an OpenAI-compatible endpoint, so you use the
shipped `openai` backend pointed at its base URL. The same pattern works for OpenAI, vLLM,
Together, or any `/v1/chat/completions` server (just change `base_url` / `api_key_env`).

## 2. Pick the models

Copy the OpenRouter rows from [`../models.example.yaml`](../models.example.yaml) into a
`models.openrouter.yaml`. Each row is just:

```yaml
- {backend: openai, base_url: "https://openrouter.ai/api/v1",
   api_key_env: OPENROUTER_API_KEY, model: "z-ai/glm-5.1", label: glm-5.1}
```

Use **paid** slugs (the `:free` variants are rate-capped and too slow for a full sweep).

## 3. Run the sweep

The fastest path is the example script, which runs the no-leak design prompts over a model
list and tabulates FULL% per run:

```bash
bash scripts/openrouter_sweep.sh        # reads models.openrouter.yaml, writes results/
```

Or call the CLI directly — one invocation per system prompt:

```bash
circuitrubric run-all --models models.openrouter.yaml \
    --prompt-ids short --system-prompt-id topology_ports \
    --max-tokens 20000 --temperature 0.0 --output-dir results
```

Knobs that matter (these are the choices behind the published numbers):

| flag | value | why |
|---|---|---|
| `--prompt-ids` | `short` / `verbose` / `spec` | request tier: design → architecture → full wiring. `short` is the discriminator. |
| `--system-prompt-id` | `topology_ports`, `strict_ports` | the no-leak design prompts. (`conventions` pre-resolves some named topologies; the full 8-level ladder is in [`../system_prompts.yaml`](../system_prompts.yaml).) |
| `--max-tokens` | **20000** | reasoning models exhaust a small budget on hidden reasoning and emit **empty** content; 20k is the standard budget. The CLI default (2000) is far too low for them. |
| `--temperature` | `0.0` (omit for some) | greedy. A few reasoning models reject an explicit temperature — omit the flag for those (as we do for the Claude models). |
| `--reps` | `3` for error bars | temp=0 is **not** deterministic on hosted APIs; see below. |

## 4. Read the results

Each run writes `results/<run-id>/summary.jsonl`, one row per fixture, already graded
(`grade.credit` ∈ FULL/PARTIAL/PARTIAL_BULK/TOPOLOGY/DECORATED/NONE). Tabulate FULL% + the full
credit breakdown per run with the helper:

```bash
python scripts/aggregate_runs.py results/*
```

```
| run | n | FULL% | ign_src% | func% | topo% | FULL | PARTIAL | PARTIAL_BULK | TOPOLOGY | DECORATED | NONE | xfail |
```

The three diagnostic columns each relax `FULL` along one axis (so each is ≥ FULL%):
**`ign_src%`** ignores stray V/I test-bench sources, **`func%`** allows a swapped MOSFET
drain/source, **`topo%`** = FULL+PARTIAL+PARTIAL_BULK+TOPOLOGY (right wiring, sizing aside).

**Compare against the published numbers.** Emit a CSV in the same schema as the benchmark's
[`results/all_results.csv`](results/all_results.csv) and diff it row-by-row:

```bash
python scripts/aggregate_runs.py --csv my_results.csv results/*
```

`my_results.csv` carries the identical columns, so you can line up your model's per-run metrics
against ours. (The published CSV is the raw per-run grades; the leaderboard additionally applies
the empty-recovery overlay, so a recovered model's FULL% can be a touch higher there.)

To re-grade saved outputs with the current grader without re-calling the model, use
`circuitrubric grade-all`.

## 5. Mind the variance

`temperature=0` does not give identical results across runs on hosted APIs (provider routing +
batch-variant kernels). Per-fixture grades flip on a large fraction of items; the *aggregate*
FULL% is stable to ~±1–3 percentage points on the full corpus. So:

- report **mean ± std over `--reps 3`** for any close comparison, and
- treat sub-~6-point gaps between single runs as noise.

Details and the measured spread are in [`reproducibility.md`](results/reproducibility.md) and
[`variance.md`](results/variance.md).
