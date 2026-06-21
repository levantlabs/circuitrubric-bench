# Example runs

Three **complete** run directories (all 125 fixtures) so you can see *what models actually produce*
and how the grader scores it — without an API key or re-running anything. The full raw outputs for
*every* model aren't shipped in the repo (large; archived separately) — these three are
representative complete runs.

Three runs, all on the **same task** — the `short` (one-line design) request with the
`strict_ports` system prompt — spanning the capability range:

| dir | model | kind | FULL |
|---|---|---|---|
| `or-gpt-5.5-closed-short-strict_ports/` | gpt-5.5 | closed frontier | 90/125 (72%) |
| `or-kimi-k2.6-2026-short-strict_ports/` | kimi-k2.6 | open frontier | 83/125 (66%) |
| `lb-qwen3.5-short-strict_ports/` | qwen3.5 | local (6.6 GB, ollama) | 4/125 (3%) |

Same prompt, three tiers of capability — the design wall in miniature: frontier models clear it,
a small local model emits valid SPICE but the wrong topology. (The dir names match rows in
[`../docs/results/all_results.csv`](../docs/results/all_results.csv).)

## What's in each directory

- **`config.json`** — the exact run settings (backend, model, temperature, max_tokens, system prompt).
- **`summary.jsonl`** — one row per fixture (all 125): the `extracted_netlist`, the `grade`
  (`credit` + the ratio/iso flags), token usage, latency. This is the per-run data.
- **`raw/`** — the model's *full response* for **all 125 fixtures** (`<fixture>--short--rep1.txt`).

Three good fixtures to compare across the runs:
- `008_cs_amp_nmos_resistor_load` — an easy single-stage amp (most models FULL),
- `051_folded_cascode_ota_nmos` — a hard multi-stage OTA (frontier sometimes, local no),
- `074_source_follower_pmos_driving_resistor_load` — the fixture *every* model gets wrong the same
  way (load to ground instead of VDD).

## Reproduce / re-grade

These are a **snapshot** — `temperature=0` is not deterministic on hosted APIs (see
[`../docs/results/reproducibility.md`](../docs/results/reproducibility.md)), so re-running won't
reproduce them byte-for-byte. The grade is already in each `summary.jsonl` row; to re-score a
netlist yourself, paste the fenced `spice` block from a `raw/` file into a `.cir` and run
`circuitrubric grade --task fixtures/<id> --submission <that.cir>`.

To run your own models and compare against the published numbers, see
[`../docs/reproducing.md`](../docs/reproducing.md).
