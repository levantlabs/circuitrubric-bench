# Reproducibility & run-to-run variance

*Written by Claude from the benchmark's experiment runs and the author's analysis, and reviewed by
the author.*

**TL;DR.** For hosted LLM APIs (and OpenRouter in particular), `temperature=0` does **not** give
deterministic outputs. Per-fixture grades flip on ~half of items across identical re-runs; the
*aggregate* FULL rate is stable to a few points. We therefore report design-tier scores as
**mean ± std over N≥3 repetitions** and treat single-shot numbers as point estimates, not ground
truth. True bitwise determinism is achievable only for models we can self-host with batch-invariant
kernels (which excludes every frontier model in this study), so for those it is a documented
limitation, not something we engineer away. Separately, we hold `temperature=0` for **every**
model and verified that choice against Gemini-3's vendor guidance (which recommends `temperature=1.0`):
on this benchmark temp=1.0 is, if anything, **slightly lower** (gemini-3.1-pro on `short × topology_ports`:
88.8 → 85.3) with no looping, so temp=0 stays; see [Temperature](#temperature) below.

## What we observed

All on the `short` (design) tier, `temperature=0`, max_tokens=20k, OpenRouter.

- **Same call, different backend.** With no provider pinned, repeated `temperature=0` requests to one
  model id (GLM-5.2) were routed by OpenRouter across its provider pool (z-ai, friendli, streamlake,
  atlas-cloud, novita, deepinfra), returning different completions per call. So every leaderboard entry
  for an OpenRouter model is one sample from whatever backend served it that moment.
- **Providers are not interchangeable.** Pinning the provider for the same model id changed the pass
  rate: on one fixture (5T OTA PMOS, `short`), z-ai returned 0/3 FULL and streamlake 3/3. So "the
  model" is really "the model × provider." The cause (serving stack, default reasoning settings,
  quantization) we did not pin down; we only observed that the backend matters.
- **~50 % per-fixture flip rate.** In a 4-model × 25-fixture × 3-rep study, **40–52 % of fixtures
  changed grade** (FULL↔not-FULL) across the three identical reps.
- **But aggregates are stable.** Flips partially cancel, so the aggregate FULL rate held to small
  bands: e.g. full-corpus GLM-5.1 = **62.4 ± 0.7 %** (3 reps), GLM-5.2 = **48.5 ± 2.9 %**. Reasoning
  models tend to be noisier (more tokens → more places to diverge); GLM-5.1 was unusually tight.
  Per-rep tables and the GLM-5.1-vs-5.2 comparison are in [`variance.md`](variance.md).
- **Reasoning amplifies the variance but isn't the only source.** A long thinking chain gives many
  more near-tie argmax decisions for batch-variant logits to flip, and one early flip cascades, so
  reasoning models are the noisiest. With thinking off, outputs are far more stable (byte-identical on
  our local batch=1 tier). But the underlying nondeterminism is the hosted serving stack itself
  (batch variance, provider routing), not the reasoning chain alone.

<a id="temperature"></a>

## Temperature: do we follow vendor guidance?

`temperature=0` is our default for every model: greedy decoding removes one source of variance and
is how the leaderboard is run. One model family complicates that: **Google recommends
`temperature=1.0` for all Gemini 3 models**, warning that lower temperatures can cause *looping or
degraded reasoning* on complex tasks (LiteLLM even forces 1.0 for Gemini 3+). So we tested whether
deviating from temp=0 changes anything here.

**It doesn't.** gemini-3.1-pro on `short × topology_ports`:

| setting | FULL% |
|---|---|
| temp=0 (single run, the leaderboard number) | 88.8 |
| temp=1.0 (3 reps) | 84.8, 87.2, 84.0 → **85.3 ± 1.4** |

The vendor-recommended temp=1.0 is, if anything, slightly *lower* on this benchmark, and the
warned-about failure mode never appears: across **375 temp=1 generations, 1 hit the token cap and 0
were empty**, no looping. Short, structured netlist generation simply doesn't enter the
long-reasoning regime where low temperature reportedly degrades Gemini 3.

**Decision: keep `temperature=0`.** It's marginally higher and keeps Gemini consistent with every
other model on the leaderboard (all temp=0). Temp=0 isn't bitwise-deterministic on hosted APIs
regardless (the rest of this doc), so staying with it costs no reproducibility, and we've now
*verified*, not assumed, that the vendor's temp=1.0 wouldn't help. The leaderboard's 88.8% is the
temp=0 number.

A bonus from that 3-rep run: it reproduces this doc's central pattern from the *other* direction. At
temp=1 the variance is **intentional** (sampling, not just batch noise), yet the aggregate still
barely moves while **~20% of fixtures flip** verdict, the same churn temp=0 batch-variance produces.
So the per-fixture instability tracks the **model's genuine uncertainty at its capability boundary**,
not merely the serving stack. Full decomposition (all@3 75% / majority 86% / pass@3 95%) in
[`variance.md`](variance.md) §3.

## Why (root cause)

Greedy sampling (`temperature=0`) fixes the *decision rule* (argmax), not the *logits*. Hosted
inference is **batch-variant**: server load sets the batch size, which changes floating-point
reduction order, which perturbs logits; at near-ties the argmax flips, and in a long reasoning chain
one early flip cascades into a different answer. See Thinking Machines Lab, *"Defeating
Nondeterminism in LLM Inference"* (2025). OpenRouter's multi-provider routing stacks additional
variance on top: different backends for the same model id return different answers, for reasons
(serving stack, quantization, defaults) we did not isolate.

## What gives determinism (and why we mostly can't use it)

- **Bitwise-deterministic inference** needs control of the server: vLLM + batch-invariant kernels
  (`batch-invariant-ops`), or simply batch size 1. Only possible for models we self-host.
- **Frontier open models are too large to self-host affordably** (GLM-5.2 ≈ 753B → ~750 GB VRAM at
  fp8, an 8×H200 node ≈ $20/hr). **Closed models** (GPT-5.x, Claude) can't be self-hosted at all.
- **Small/mid local models *are* reproducible** on our own box (Ollama with batch=1 + fixed seed),
  and we treat those as the deterministic tier.

## Empty-recovery overlay (and its budget caveat)

Heavy reasoners sometimes spend their whole token budget thinking and emit nothing (0-byte,
`finish_reason=length`). To avoid counting these reasoning-runaway *blanks* as topology failures,
empties were re-run at a higher budget (40k/64k) and the results **overlaid** onto the base run:
the aggregation step replaces any empty fixture by its recovery (where one emitted), keyed by
(model, fixture, tier, system-prompt). This is **repeatable** and surfaced
by two columns: `max_tokens` (the base budget) and `recovered` (how many fixtures were folded in
from a higher-budget run). **Caveat:** this mixes token budgets within a run (base 20k + recovered
40k/64k), so a `recovered>0` run is not single-budget; report it as such. Recovery emitted for many
heavy reasoners (kimi empties 3→1, minimax 9→4) but **not** for the pathological ones (glm-4.5 stays
~26 empty even at 64k); those remain genuine no-answers.

## What we do about it

1. **Report mean ± std over N ≥ 3 reps** for design-tier scores; flag single-run numbers as such.
2. **Disclose serving conditions:** provider routing is uncontrolled unless explicitly pinned;
   where a number depends on it, say so. (OpenRouter supports `seed` and `provider` pinning, which
   *reduce* but do not eliminate within-provider batch variance.)
3. **Trust aggregates over per-item grades:** a single fixture's FULL/NONE is not reproducible;
   the corpus-level rate is.
4. **Differences are only real if they exceed the error bars.** A single full-corpus run's FULL%
   has a std of ~±1–3 pts; comparing **two** single runs combines both spreads, so a gap needs
   roughly **6 pts** to clear the combined noise, which is why the leaderboard treats sub-~6-pt gaps
   as noise (its "±1–3 pts" is the single-run spread; the ~6-pt rule is the two-run comparison).
   Worked example: GLM-5.2's ~14-point deficit vs GLM-5.1 (48.5 ± 2.9 % vs 62.4 ± 0.7 %) is well
   outside that combined spread, so the regression is genuine, whereas a 2–4 point gap between two
   single runs is not interpretable.

## Honest limitation

For the frontier (closed + giant-open) models that anchor the leaderboard, run-to-run variance from
provider routing + batch-variant kernels is **inherent and undisclosed by the providers**. We
quantify it (above) and report error bars, but we cannot make those numbers bitwise-reproducible.
Readers reproducing the benchmark should expect per-fixture disagreement and compare at the
aggregate, error-bar level.
