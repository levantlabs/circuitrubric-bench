# CircuitRubric

**A structural benchmark for evaluating LLM-generated analog circuit netlists.**

CircuitRubric tests whether a language model, given a designer-style request
(*"Design a 5T OTA with NMOS inputs"*), produces a netlist whose **connectivity and
relative device sizing** match the canonical topology, graded by **graph isomorphism**,
with no SPICE simulation required.

It targets the failure mode that functional metrics miss: LLMs write netlists that *parse
and simulate* but are **wired wrong**. The usual functional check — *Pass@1* (sample one
netlist, simulate it, see if it works) — needs a working testbench and only gives pass/fail.
CircuitRubric grades the **structure directly** and tells you *how* it's wrong.

This benchmark contains:

- **125 iso-verified fixtures** across amplifiers, current mirrors, OTAs, oscillators, and more (multiple valid topology forms are accepted)
- **Two extensible prompt axes** — per-fixture request tiers (`short` / `verbose` / `spec`) that separate *design* from *transcription*, plus an 8-level system-prompt set (both extensible) for experimenting with model context
- **6-level credit ladder** that localizes failures (right topology? right sizing ratios? over-elaborated?)
- **Simulation-free** with pure, name-agnostic graph matching (net/device names don't matter), no PDK required
- **Runnable grader + CLI** that is pip-installable and can grade one netlist or a whole model run

## How to Install

Requires Python 3.10+.

```bash
git clone https://github.com/levantlabs/circuitrubric-bench
cd circuitrubric-bench
pip install -e .
```

## Quickstart — grade one netlist

```bash
circuitrubric grade --task fixtures/001_5t_ota_nmos --submission my_netlist.cir
```

Or in Python:

```python
from circuitrubric import grade, load_task

task = load_task("fixtures/001_5t_ota_nmos")[0]
result = grade(open("my_netlist.cir").read(), task)
print(result.credit)   # Credit.FULL / PARTIAL / PARTIAL_BULK / TOPOLOGY / DECORATED / NONE
```

## Evaluate a whole model run

Generate a netlist per fixture into a directory (named `<fixture_id>.cir`), then:

```bash
circuitrubric grade-all --fixtures fixtures --submissions my_model_outputs/
```

…which prints the credit-level distribution and the FULL (pass) rate.

To see what evaluated runs look like, [`examples/`](examples/) ships three sample runs — a closed
frontier (gpt-5.5), an open frontier (kimi-k2.6), and a local model (qwen3.5) — each with
per-fixture netlists and grades, inspectable without an API key.

## Run it through a model (generate + grade)

To reproduce results end-to-end, prompt a model for every fixture, and then grade the results, 
use `circuitrubric run`. It loops fixtures × prompt variants (`short`/`verbose`/`spec`)
× reps, calls the chosen backend, extracts the netlist, grades it, and writes a
per-run directory (`config.json`, `raw/*.txt`, `summary.jsonl`) plus a credit-ladder
tally. The grader core needs no extra packages; install only the backend you use:

```bash
pip install -e ".[ollama]"      # or: ".[anthropic]", ".[openai]", ".[run]" (all)

# Local model via ollama (no API key):
circuitrubric run --backend ollama --model qwen3.5:latest --prompt-ids spec

# Anthropic API (export ANTHROPIC_API_KEY first):
circuitrubric run --backend anthropic --model claude-opus-4-8

# Any OpenAI-compatible endpoint (OpenAI, vLLM, Together, ollama's /v1, …):
circuitrubric run --backend openai --model gpt-4o            # OPENAI_API_KEY
circuitrubric run --backend openai --model qwen3.5:latest \
    --base-url http://localhost:11434/v1 --api-key-env OLLAMA_KEY
```

The system-prompt scaffolding level is chosen with `--system-prompt-id`
(`minimal`/`formatted`/`topology`/`topology_ports`/`topology_oneshot`/`strict`/`strict_ports`/`conventions`,
default `topology`; see [`system_prompts.yaml`](system_prompts.yaml)). Add `--dry-run` to preview the plan
without calling a model. Runs resume: re-invoking with the same `--run-id` reuses
already-saved responses instead of re-calling.

### Sweep several models → a leaderboard

To reproduce a full leaderboard, list the models in a config and sweep them in one
command. Copy [`models.example.yaml`](models.example.yaml) to `models.yaml`, edit it,
then:

```bash
circuitrubric run-all                  # uses models.yaml; add --dry-run to preview
```

Each row is `{backend, model, [base_url], [api_key_env], [label]}`. The sweep runs
every model over the corpus, writes a per-model results directory, and prints a
combined credit-ladder table (sorted by FULL rate) you can paste into the leaderboard.

To reproduce the **open-model baselines through OpenRouter** (one key for the glm / kimi /
deepseek / qwen families), see the step-by-step recipe in
[`docs/reproducing.md`](docs/reproducing.md) and the example sweep in
[`scripts/openrouter_sweep.sh`](scripts/openrouter_sweep.sh).

## The 6-level credit ladder

| Credit | Meaning |
|---|---|
| **FULL** | isomorphic match + all sizing ratios correct |
| **PARTIAL** | correct topology + W/L/value ratios, but device-multiplicity (M) ratio wrong |
| **PARTIAL_BULK** | matches except MOSFET bulk convention (bulk-tied-to-source idiom) |
| **TOPOLOGY** | right wiring, wrong/missing sizing |
| **DECORATED** | reference topology present as a subgraph + extra bolted-on devices (over-elaboration) |
| **NONE** | wrong topology |

Beyond `FULL`, runs also report two roll-ups: **topology-correct%**
(`FULL+PARTIAL+PARTIAL_BULK+TOPOLOGY` — right wiring, any sizing) and **functional%**
(correct except for a swapped source/drain orientation).

## Corpus

125 fixtures, each a self-describing directory:

```
fixtures/001_5t_ota_nmos/
  prompts.yaml        # short / verbose / spec request variants
  reference.cir       # canonical netlist (generic ngspice, level=1 MOSFETs)
  ratio_groups.yaml   # equality / ratio constraints between matched devices
  meta.yaml           # category, family, variant, source
```

Categories: Amplifier (64), CurrentMirror (28), OTA (7), Oscillator (6), Digital (6),
SampledData (5), Feedback (4), Memory (2), Bias (2), Mixer (1).
See [`docs/CATALOG.md`](docs/CATALOG.md) for the full list and [`docs/methodology.md`](docs/methodology.md)
for how grading works. For a single-page read-through of every fixture (metadata,
prompts, reference netlist, ratio groups), see [`docs/full_corpus.md`](docs/full_corpus.md),
regenerated with `python scripts/full_corpus.py`.

## Baseline results

Local models via `circuitrubric run` (ollama, temp 0, single run — ~±2% run-to-run spread,
`n=125`), all under one fixed system prompt (`strict_ports`), **as of 2026-06-19**. Values are
FULL%. **`short`** gives
only the topology name (measures *design*); **`verbose`** describes the circuit without wiring;
**`spec`** gives the full device wiring (measures *transcription*).

Small local models stall on design (`short` ≤3.2%); even handed the full wiring (`spec`), the best
clears only ~69%.

| Model | size | `short` | `verbose` | `spec` |
|---|---|---|---|---|
| qwen3.5 | 6.6 GB | 3.2% | 4.0% | **68.8%** |
| phi4:14b | 9.1 GB | 3.2% | 2.4% | 68.0% |
| qwen3:30b-a3b-instruct | 18 GB | 0.8% | 3.2% | 64.0% |
| qwen2.5-coder:7b | 4.7 GB | 2.4% | 4.0% | 63.2% |
| llama3.1:8b | 4.9 GB | 0.0% | 0.0% | 27.2% |
| gemma2:9b | 5.4 GB | 0.8% | 0.8% | 19.2% |
| granite3.1-dense:8b | 5.0 GB | 0.0% | 0.0% | 16.0% |

### Stronger models (frontier + large open, via API / OpenRouter)

FULL% under the same fixed system prompt (`strict_ports`), single run, sorted by `short` (the
design tier), **as of 2026-06-19**. ✓ = open-weight.

| Model | open | `short` | `verbose` | `spec` |
|---|---|---|---|---|
| gpt-5.5 | | 72.0% | 84.8% | 95.2% |
| kimi-k2.6 | ✓ | 66.4% | 76.8% | 94.4% |
| qwen3.7-max | ✓ | 65.6% | 79.2% | 92.0% |
| claude-opus-4-7 | | 65.6% | — | — ‡ |
| glm-5.1 | ✓ | 62.4% | 72.0% | 91.2% |
| claude-opus-4-8 | | 59.2% | 75.2% | 96.0% † |
| deepseek-v4-pro | ✓ | 52.0% | 58.4% | 92.0% |
| claude-sonnet-4-6 | | 48.0% | 64.8% | 91.2% |
| minimax-m3 | ✓ | 45.6% | 55.2% | 89.6% |
| deepseek-v4-flash | ✓ | 33.6% | 41.6% | 85.6% |
| claude-haiku-4-5 | | 19.2% | 30.4% | 88.0% |

† opus-4.8 `spec` ran `conventions` only (no `strict_ports`); 96.0% is that value.
‡ opus-4.7 ran the `short` tier only — notably **higher on design than opus-4.8** (65.6 vs 59.2).

These two tables are a summary; the full per-model leaderboard is in
[`docs/results/leaderboard.md`](docs/results/leaderboard.md), and per-model speed / test-time-compute
cost (tokens and latency per call, beside accuracy) in [`docs/results/cost.md`](docs/results/cost.md).

## Results Overview

What the structural grader reveals that pass/fail can't:
- **Design ability tracks capability, not openness.** Transcription is broadly tractable (`spec`
  up to 96%). On `short` (design), the **small local models score ≤3.2%** while stronger models —
  open and closed alike — reach ~72% (GPT-5.5 72%, Kimi-K2.6 66%, Qwen3.7-max 66%, GLM-5.1 62%,
  Opus 59%). Designing a topology from a one-line ask is a capability threshold: small models hit
  the wall, frontier-scale models (open or closed) clear it.
- **Among the small local models, size doesn't predict skill.** A 7B *code* model ties 14–30B
  general models (SPICE is code-like; emission/syntax affinity matters more than parameters).
- **Large prompt sensitivity** — an explicit SPICE port-order reminder swings some models
  from ~0–3% to ~66% on `spec`; the `strict` (no-decoration) variant helps the models that
  over-elaborate. See [`system_prompts.yaml`](system_prompts.yaml).

## Limitations

- **Single run, no error bars (yet).** Results are one sample per cell at temperature 0; even then,
  cloud endpoints aren't bit-deterministic and local runs carry ~±2% spread. 
- **Structural only.** Grading checks topology and relative sizing, not that the circuit *works* —
  bias point, gain, stability, and absolute values are out of scope. A `FULL` netlist is structurally
  correct, not a verified design (functional/simulation grading is a complementary axis).
- **Contamination over time.** Like any static public benchmark, a fixture's value erodes once its
  reference leaks into training data — a model may recall an answer instead of designing it. Because
  topology is shared knowledge and only the *expression* is ours, the durable contribution is the
  **method** — the grader plus the fixture style — which can regenerate fresh, held-out, or perturbed
  fixtures; treat published scores as a snapshot, not a permanent ranking.

## Contribution

To add your model: run `circuitrubric run` / `grade-all` and open a PR with your numbers and exact
prompt + decoding settings (see [CONTRIBUTING](CONTRIBUTING.md)).

## Documentation

Full index: [`docs/`](docs/README.md). Highlights:

- **How grading works** — [`docs/methodology.md`](docs/methodology.md)
- **Results & analysis** — [`docs/results/findings.md`](docs/results/findings.md) (highlights), [`docs/results/leaderboard.md`](docs/results/leaderboard.md)
- **Reproduce it** — [`docs/reproducing.md`](docs/reproducing.md)
- **Code internals** — [`docs/code-guide.md`](docs/code-guide.md)

## Provenance & honesty

Netlists were authored fresh for this benchmark.  Two fixtures cite Gray & Meyer (textbook). The corpus was partly drafted with AI assistance
and reviewed by a human analog designer; see [`NOTICE.md`](NOTICE.md).

## License & citation

- **Code** (the `circuitrubric` package + tooling): Apache-2.0 — see [`LICENSE`](LICENSE).
- **Corpus** (`fixtures/`): CC-BY-4.0 — see [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt). Reuse with attribution.

To cite, see [`CITATION.cff`](CITATION.cff) (will point to the CircuitRubric paper once posted).
