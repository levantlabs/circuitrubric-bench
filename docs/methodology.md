# CircuitRubric — Methodology

> Written and maintained with Claude; verified against the grader and run data.

How the benchmark is built and how grading works.

## What it measures

Whether an LLM, given a designer-style request, produces a netlist whose
**connectivity** and **relative device sizing** match a canonical reference topology —
decided by **graph isomorphism**, with no SPICE simulation.

This is "Layer 1": generic ngspice, `level=1` MOSFETs, hand-set `KP`/`VTO`, **no PDK**. The
references carry no supply or test-bench — only the devices, their connectivity, and *relative*
sizing (the `ratio_groups`); there are no absolute voltages or currents. It tests **structure
only** — topology and ratio'd device sizes — not absolute values, bias points, or
dynamic/functional behavior. (Functional correctness via simulation is a complementary axis,
not what this measures.)

It targets the failure mode that functional metrics miss: netlists that parse and simulate
but are **wired wrong**, and **over-elaborated** answers (right topology with extra devices
bolted on).

## Task shape

Each fixture is a self-describing directory `fixtures/NNN_<slug>/`:

- `prompts.yaml` — three request tiers: **short** (the topology name), **verbose**
  (architectural prose), **spec** (device-by-device wiring).
- `reference.cir` — the canonical netlist (generic ngspice, `level=1`). Topologies with
  more than one acceptable form add `reference_alt_N.cir`; a submission passes if it
  matches **any** blessed reference.
- `ratio_groups.yaml` — equality/ratio constraints between matched devices (W / L / M / value).
- `meta.yaml` — category, family, variant, source.

## Submission / netlist format

A plain SPICE netlist: each device line starts with its type letter — `M` (MOSFET),
`R`/`C`/`L` (passives) — with MOSFET terminal order `M<name> <drain> <gate> <source> <bulk> <model>`,
plus the `.MODEL` cards the devices reference. **Net and device names are free** — grading
is name-agnostic (see below).

## Grading

The submission is parsed, then graded in three steps:

1. **Graph isomorphism (connectivity).** The netlist is turned into a graph: one node per
   net, one node per device (labeled by device type), and one edge per device terminal
   (labeled by terminal role). A submission matches a reference iff the two graphs are
   isomorphic under matching device types and terminal roles.
   - Net names and device names are relabeled freely — only structure matters.
   - Passive (R/C/L) terminals are interchangeable (`n1 ↔ n2`); **MOSFET drain/source are
     strict** (drain ≠ source), as is source polarity — so for the credit ladder a drain/source
     swap is a real error, not a relabeling. (A MOSFET's drain/source are physically symmetric at
     `level=1`, so a swapped-but-otherwise-correct circuit is recognized separately as
     *functionally* equivalent — see **`functional`** below — without relaxing `FULL`.)
   - Pass = isomorphic to at least one blessed reference.

2. **Ratio groups (relative sizing).** For each group declared in `ratio_groups.yaml`, the
   matched devices must hold the declared W / L / M / value ratios (equality is the 1:1
   case), within **±1%**.

3. **Subgraph check (over-elaboration).** If the submission is not a clean match but the
   reference appears as a node-induced subgraph with extra devices added around it, it is
   graded `DECORATED`.

### The 6-level credit ladder

| Credit | Meaning |
|---|---|
| **FULL** | isomorphic match + all sizing ratios correct |
| **PARTIAL** | correct topology + W/L/value ratios, but device-multiplicity (M) ratio wrong |
| **PARTIAL_BULK** | matches except the MOSFET bulk convention (bulk-tied-to-source idiom) |
| **TOPOLOGY** | right wiring, wrong/missing sizing |
| **DECORATED** | reference topology present as a subgraph + extra bolted-on devices |
| **NONE** | wrong topology |

`DECORATED` is the diagnostic a pass/fail metric cannot produce: it catches "the model knew
the topology but added bias networks / coupling caps / extra devices around it."

### Reported aggregates

Alongside the per-submission credit, runs report:

- **FULL%** — the idiom-strict pass rate (the headline).
- **topology-correct%** = `FULL + PARTIAL + PARTIAL_BULK + TOPOLOGY` — got the wiring right,
  regardless of sizing.

Two **near-FULL diagnostics** each relax `FULL` along one axis — both say "the circuit is
essentially right," isolating one reason it isn't idiom-strict FULL. They are reported *alongside*
the credit ladder, not folded into it (they are orthogonal axes, not rungs):

- **`functional`** — would be `FULL` but for a non-idiomatic source/drain orientation (isomorphic
  *modulo* MOSFET drain/source, with gate/bulk strict and all ratios satisfied). At `level=1` a
  MOSFET's drain/source are symmetric, so this is an electrically-equivalent answer drawn in the
  other orientation.
- **`ign_src`** — would be `FULL` after ignoring an ideal-source test-bench wrapper: re-grade with
  the independent `V*`/`I*` source lines stripped from the submission. Catches a correct topology
  that was only marked `DECORATED` because the model added a `VDD` rail / `IREF` source / output
  sweep around it. Conservative — if a source was load-bearing, removing it leaves a device missing,
  so it stays non-FULL.

Each is **≥ `FULL`** (it relaxes one FULL criterion), but they are *not* nested under
`topology-correct`: an S/D-swapped or test-bench-wrapped circuit can count as `functional` /
`ign_src` while strict isomorphism places it below `TOPOLOGY` (so `functional` or `ign_src` can
exceed `topology-correct`). Read `FULL` (idiom-strict), `functional` / `ign_src` (essentially
right), and `topology-correct` (wiring) as separate views. `scripts/aggregate_runs.py` prints
these columns per run.

## Prompt axes

Two independent knobs let you probe *where* a model fails:

- **Fixture prompt** (per request, in `prompts.yaml`): `short` / `verbose` / `spec` —
  escalating information, from the bare name to the full wiring.
- **System prompt** (global scaffolding, in [`system_prompts.yaml`](../system_prompts.yaml)):
  an 8-level ladder from `minimal` to `conventions` (including the `topology` default,
  `topology_ports`, `strict`, and `strict_ports`). These change how the request is framed,
  not the fixtures themselves.

The system prompt is itself a variable, not just a wrapper: its wording can shift the FULL
rate on individual fixtures — a level that spells out a topology's conventions may under- or
over-specify it and nudge the model toward a particular form. The effect is usually small in
aggregate but real per-fixture, so report scores **with the system-prompt level**, and read
differences across levels as part of the measurement, not noise.

**Worked example — debugging the `conventions` prompt** (fixture 051, NMOS folded cascode;
gpt-5.5, `short` request). Changing one thing at a time in the system prompt, graded normally:

| system-prompt change | model builds | grade |
|---|---|---|
| baseline (`conventions`) | 9-transistor | NONE |
| − the "minimum set of devices" line | 9T | NONE |
| + reasoning scaffold ("describe it, then build") | 9T | NONE |
| + "use the canonical textbook implementation" | 9T | NONE |
| − the folded-cascode convention bullet | **11T** | **FULL** |
| that bullet *completed* ("…feeding a cascoded mirror load") | **11T** | **FULL** |

The `conventions` bullet describes the folding stage but never says the load mirror must also be
cascoded — so it effectively specifies the 9-transistor form, and the model follows it faithfully
and is graded NONE. The point is **prompt-dependence**: on this fixture gpt-5.5 reaches the
canonical 11-transistor form (FULL) only under `strict_ports`; under both `conventions` *and*
`topology_ports` it builds the same 9-transistor circuit — a simple, un-cascoded NMOS mirror load
instead of a cascoded one — and is graded NONE. So *which* scaffolding you use can move a capable
model between FULL and NONE on a given fixture. (Single sample per row; the contrast is sharp and
consistent.)

---

Provenance & sourcing: [`NOTICE.md`](../NOTICE.md). Topology coverage: [`CATALOG.md`](CATALOG.md).
Full read-through of every fixture: [`full_corpus.md`](full_corpus.md).
