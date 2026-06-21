# Findings

High-signal results from running the corpus across ~30 models — the cases where grading the
*structure* reveals something a pass/fail (does-it-simulate) metric can't. Each vignette links to
the doc with the full data.

*Written by Claude from the benchmark's experiment results and the author's analysis, and reviewed
by the author.*

## What structure reveals that "does it work?" can't

**One score becomes three abilities.** A pass/fail metric collapses *emission* (write valid SPICE),
*transcription* (turn a given wiring into a netlist), and *design* (choose the topology) into a single
number. The structural grader, swept across request tiers, separates them — and they dissociate
sharply: emission is essentially solved (models copy a given netlist near-perfectly), transcription is
tractable (`spec`: locals ~64–69%, frontier ~85–96%), and design is the wall (`short`: small locals
≤3%). qwen3.5 alone spans the whole range — `spec` 68.8% but `short` 3.2%. This three-way split is the
benchmark's core contribution and is invisible to a sim/pass@1 number.

**A low score can be invalid SPICE, not a wrong circuit.** Emission isn't uniformly solved — some
weak models fail the *syntax*, not the topology. granite-3.1 routinely omits the bulk terminal
(3-terminal MOSFETs), which aren't valid/simulatable SPICE: ~78 of its `spec` outputs are malformed,
so its near-zero score is a syntax failure, not a design one. qwen2.5-coder collapses the same way
(≈88% malformed) under the bare `topology` prompt and recovers with a port-order reminder. The
grader's parse step catches these as a distinct failure mode — `scripts/diagnose.py` reports the
malformed-terminal count — separating *can't write SPICE* from *drew the wrong circuit*, a
distinction a pass/fail rate hides.

**Right wiring, wrong number — and the grader can tell.** On `spec`, Opus-4.8 is 96.0% FULL but
**100% topology-correct**: it never drew a wrong circuit on any of the 125 fixtures. Its five non-FULL
results are *purely sizing* (two M-ratio mismatches, three over-scaled multipliers) — it expressed a
width ratio differently than the reference. FULL alone reads this as "5 failures"; the credit ladder
shows zero wiring errors. (Sonnet is likewise 100% topology on `spec`.) → [leaderboard.md](leaderboard.md)

**Models confidently mislabel a simpler topology as the requested one.** A model emits a subcircuit
name or comment with the *correct* topology name, but the netlist is a different (usually simpler)
circuit. On `033` wide-swing cascode mirror, gpt-5.5 named the block `NMOS_WIDE_SWING_CASCODE_MIRROR`
but gated the bottom mirror from its own diode node → an ordinary cascode mirror, one connection
short of wide-swing. On `035` it labeled the output "modified Wilson" but built a plain mirror with
misplaced feedback. The label is unreliable — only the structure tells the truth, so a
graph-isomorphism grader catches these while an LLM-judge or self-report grader would be fooled.
(Notably, Claude Opus 4-7/4-8 are the *only* models that build a correct wide-swing from the
one-line prompt — a real capability discriminator, not a reference bug.)

**Multiple models converging on a topology doesn't make it valid.** Several models independently
produced the *same* alternative for the 4-transistor Wilson mirror (`039`/`040`). It looked like
consensus — but the convergent circuit is a cascode mirror with no feedback loop, not a Wilson, so
we rejected it as a blessed reference. Agreement across models is not evidence of correctness; the
structural check is.

**Knowing a topology ≠ building it.** A two-part probe — state it in prose, then build it —
separates ignorance from a realization gap. On the folded-cascode OTA, kimi-k2.6's prose says "nine
transistors, simple mirror load" and it builds exactly that wrong 9-transistor form: a genuine
*knowledge* gap. gpt-5.5 and opus-4-8 both say "eleven, cascode mirror load" and build the correct
11T. Yet even gpt-5.5, which knows it, reverts to the wrong 9T under the terse `short` prompt — a
separate *grounding* gap. → [methodology.md](../methodology.md)

## Reasoning

**Reasoning is the single biggest lever — bigger than any prompt.** Turning kimi-k2.6's reasoning
off collapses FULL by ~60 points (strict_ports 66%→18%, conventions 68%→22%) — but eliminates the
empty outputs. Reasoning is load-bearing for topology choice, and the empties are its price.
→ [reasoning-ablation.md](reasoning-ablation.md)

**Small models run away into an indecision loop.** qwen3:14b spent ~14,000 characters of reasoning
on a *two-transistor* source follower, looping the same under-specified detail a dozen times and
never committing. At a smaller budget that loop exhausts the tokens and emits nothing — which is
the "empty." The failure is the lack of a stop condition, not reasoning ability.
→ [reasoning-ablation.md](reasoning-ablation.md)

**Reasoning has a steep cost, and more of it doesn't mean better.** Test-time compute spans ~80× across
the model set — kimi-k2.6 averages ~8,700 output tokens/call (~250 s) versus Opus's ~290 tokens (~5 s),
making the top open reasoners 10–50× slower per call than the non-reasoning frontier. Crucially, token
volume is **uncorrelated with accuracy**: Opus (≈290 tok) beats kimi (≈8,700) on design. So "thinks more"
is a cost, not a quality signal. → [cost.md](cost.md)

## Sensitivity & robustness

**System-prompt wording can flip a correct answer to wrong.** The `conventions` prompt's
folded-cascode description spells out the folding stage but never says the load mirror must also be
cascoded — so it specifies the wrong 9T form, and a capable model follows it faithfully into a NONE.
Removing *or* completing that one bullet flips gpt-5.5 from 9T/NONE to 11T/FULL.
→ [methodology.md](../methodology.md)

**Every model gets `074` wrong the same way — and only some can be talked out of it.** On the `074`
PMOS source follower with a resistive load, every model defaults to a ground-referenced load
resistor; the correct reference ties it to VDD. It's a robust shared *prior*, not a prompt artifact.
Whether a neutral challenge ("are you sure?") recovers it is model-dependent: Claude self-corrects,
gpt-5.5 defends the wrong default (2/2 trials). → [fixture_difficulty.md](fixture_difficulty.md)

**A "convention" prompt can backfire, and the best prompt is model-dependent.** The richest system
prompt, `conventions`, lifts Opus's design score (~57→67) but *hurts* weaker models and *hurts* `spec`
across the board; `strict` alone (43%) scores below the plainer `topology` (56%) on local `spec`. There
is no single best system prompt — report scores with the prompt, and treat prompt choice as part of the
measurement. A second case (`076` PMOS source follower): a polarity rule written for common-source amps
("PMOS amp → NMOS-to-ground load") misfires on followers and flips gpt-5.5 from the correct VDD-sourced
bias to a wrong one — though glm-5.1/deepseek build it wrong even without the rule, so it is part prompt,
part genuine gap. → [leaderboard.md](leaderboard.md)

**A newer model can be worse — twice.** glm-5.2 scores *below* glm-5.1 on clean structural design —
48.5±2.9% vs 62.4±0.7% over three full-corpus reps, a ~14-point regression well outside the run-to-run
spread. The same pattern shows in Anthropic: on the design (`short`) tier Opus-4.8 lands at or below
Opus-4.7 (topology_ports 61.6→53.6, strict_ports 65.6→59.2, conventions tied at ~68) — design plateaued,
not improved, across the version bump (single run, so read alongside the ±2% caveat below).
→ [variance.md](variance.md)

**temp=0 is not deterministic on hosted APIs.** ~40–52% of fixtures flip grade between identical
re-runs while the aggregate FULL% holds to a few points — so compare at the error-bar level, not on
single runs. → [reproducibility.md](reproducibility.md)

**"The model id" isn't one backend.** OpenRouter routes an unpinned `temperature=0` request across a
model's provider pool, and the backend matters: for the same model id (GLM-5.2) on one fixture (5T OTA
PMOS, `short`), **pinning z-ai returned 0/3 FULL while streamlake returned 3/3**. So an OpenRouter
leaderboard entry is really *model × provider*, sampled from whatever backend served that moment. (Why
providers diverge — serving stack, default reasoning settings, quantization — we did not isolate.) Pin
the provider, and disclose it, for any number you want to compare. → [reproducibility.md](reproducibility.md)

## Difficulty

**Design is a capability threshold, and the residual is idiom-specific.** Given the full wiring
(`spec`) the top models reach ~85–96%; asked to *design* from a one-line name (`short`) the spread is
enormous — small local models ≤3%, frontier-scale models (open or closed) up to ~86%. So design is a
threshold, not a universal wall. But a residual set of idioms stays hard *even for the best*:
super-source-follower, triple-cascode op-amp, wide-swing and folded cascode, and the 4-transistor
Wilson all sit near 0% on `short` across the strong models. Many *other* cascode idioms are already
tractable (cascode CS amps, telescopic diff-out), so the grader localizes exactly which topologies
remain out of reach.
→ [fixture_difficulty.md](fixture_difficulty.md), [baseline results](../../README.md#baseline-results)
