# CircuitRubric: Topology Catalog

> Hand-maintained coverage map; cleaned up, verified against the fixtures, and formatted with Claude.

The named analog topologies the benchmark covers, grouped by circuit function/family.

For the full
read-through of every shipped fixture (metadata, prompts, reference netlist, and ratio
groups), see [`full_corpus.md`](full_corpus.md) (regenerate with `python scripts/full_corpus.py`).

Scope: MOS-native (Layer 1 = generic `level=1` MOSFETs, no PDK). BJT-only topologies are excluded; those with clean MOS analogs (e.g., Wilson, Sooch wide-swing) are listed under their MOS form.

`✓ NNN` marks the fixture that covers a topology. A blank/`—` cell means that polarity or
variant is not in the corpus.

**125 fixtures**, contiguously numbered `001`–`125`.
Distribution by category: Amplifier 64, CurrentMirror 28, OTA 7, Oscillator 6, Digital 6,
SampledData 5, Feedback 4, Memory 2, Bias 2, Mixer 1. See the
[aggregated counts](#aggregated-counts) below.

---

## Single-transistor / single-stage amplifiers

| Topology                                                 | NMOS  | PMOS  | Notes                                              |
| -------------------------------------------------------- | ----- | ----- | -------------------------------------------------- |
| CS amp + R load                                          | ✓ 008 | ✓ 011 |                                                    |
| CS amp + diode-connected load (same-type)                | ✓ 067 | ✓ 069 | NMOS-in/NMOS-diode (067), PMOS-in/PMOS-diode (069) |
| CS amp + diode-connected load (opposite-type)            | ✓ 068 | ✓ 070 | NMOS-in/PMOS-diode (068), PMOS-in/NMOS-diode (070) |
| CS amp + current-source load (active load)               | ✓ 021 | ✓ 022 |                                                    |
| CS amp + cascode current-source load                     | ✓ 083 | ✓ 084 |                                                    |
| Cascode CS amp + R load                                  | ✓ 081 | ✓ 082 | Two transistors stacked, gain at top               |
| Cascode CS amp + current-source load                     | ✓ 057 | ✓ 058 |                                                    |
| Source-degenerated CS (resistor degen)                   | ✓ 071 | ✓ 072 |                                                    |
| Common-gate amp + R load                                 | ✓ 019 | ✓ 020 |                                                    |
| Common-gate amp + current-source load                    | ✓ 055 | ✓ 056 |                                                    |
| Common-gate amp + AC-coupled current-source bias         | ✓ 079 | ✓ 080 | Input AC-coupled to a CS bias                      |
| Source follower (CD) + R load                            | ✓ 023 | ✓ 024 |                                                    |
| Source follower + current-source load                    | ✓ 009 | ✓ 012 |                                                    |
| Source follower (current-source biased) driving R load   | ✓ 073 | ✓ 074 |                                                    |
| Source follower (current-source biased) driving cap load | ✓ 075 | ✓ 076 |                                                    |
| Super source follower                                    | ✓ 122 | ✓ 121 | Feedback-boosted low-Zout follower                 |
| Two-stage cascaded CS (single-ended) + R loads           | ✓ 017 | ✓ 018 |                                                    |
| CS → SF cascade (single-ended)                           | ✓ 077 | ✓ 078 | Gain stage then buffer                             |

## Differential pairs and operational transconductance amplifiers (OTAs)

| Topology                                               | NMOS-input | PMOS-input | Notes                                 |
| ------------------------------------------------------ | ---------- | ---------- | ------------------------------------- |
| Diff pair + matched R loads                            | ✓ 013      | ✓ 014      |                                       |
| Diff pair + diode-connected loads (low gain)           | ✓ 043      | ✓ 044      |                                       |
| Diff pair + simple current-mirror load = 5T OTA        | ✓ 001      | ✓ 002      |                                       |
| Diff pair + cascode current-mirror load                | ✓ 045      | ✓ 046      |                                       |
| Source-degenerated diff pair                           | ✓ 047      | ✓ 048      |                                       |
| Diff amp + current-source loads                        | ✓ 087      | ✓ 088      | Fully-differential, no mirror         |
| Diff amp + current-source + diode loads                | ✓ 091      | ✓ 092      |                                       |
| Diff amp + current-mirror bias, resistor loads         | ✓ 093      | ✓ 094      | Tail set by a current mirror          |
| Cascaded diff amp + R loads                            | ✓ 085      | ✓ 086      | Two diff stages cascaded              |
| Diff amp + resistive CMFB (fully differential)         | ✓ 103      | ✓ 104      | Resistor-network common-mode feedback |
| Telescopic cascode OTA (single-ended)                  | ✓ 049      | ✓ 050      | Classic high-gain OTA                 |
| Telescopic cascode OTA (differential output)           | ✓ 089      | ✓ 090      |                                       |
| Telescopic cascode OTA, wide-swing load (single-ended) | ✓ 117      | —          |                                       |
| Triple-cascode op-amp (differential output, no CMFB)   | ✓ 118      | —          |                                       |
| Triple-cascode op-amp (single-ended)                   | ✓ 119      | —          |                                       |
| Folded-cascode OTA (single-ended)                      | ✓ 051      | ✓ 052      | Input pair folds into cascode         |
| Two-stage Miller-compensated op-amp                    | ✓ 053      | ✓ 054      | Diff stage + CS + Miller Cc           |
| Two-stage diff amp (no CMFB, no compensation)          | ✓ 101      | ✓ 102      | Diff stage + CS, uncompensated        |

## Current mirrors and current sources

| Topology                                              | NMOS  | PMOS  | Notes                                         |
| ----------------------------------------------------- | ----- | ----- | --------------------------------------------- |
| Simple 1:1                                            | ✓ 003 | ✓ 005 |                                               |
| Simple 1:2                                            | ✓ 025 | ✓ 026 |                                               |
| Simple 1:4                                            | ✓ 027 | ✓ 028 |                                               |
| Simple 1:8                                            | ✓ 004 | ✓ 006 |                                               |
| Cascode 1:1                                           | ✓ 007 | ✓ 010 |                                               |
| Cascode 1:2                                           | ✓ 029 | ✓ 030 |                                               |
| Cascode 1:4                                           | ✓ 031 | ✓ 032 |                                               |
| Cascode 1:8                                           | ✓ 041 | ✓ 042 |                                               |
| Wide-swing (high-swing) cascode 1:1, multi-reference | ✓ 033 | ✓ 034 | Both 5-T Sooch and 4-T external-bias accepted |
| Wilson (generic, multi-reference)                     | ✓ 035 | ✓ 036 | 3-T or 4-T accepted                           |
| 3-T Wilson (strict)                                   | ✓ 037 | ✓ 038 |                                               |
| 4-T improved Wilson (strict)                          | ✓ 039 | ✓ 040 |                                               |
| Source-degenerated mirror 1:1                         | ✓ 114 | ✓ 115 | Resistor degeneration in both legs            |
| Widlar current source                                 | ✓ 123 | ✓ 124 | Single degeneration resistor in output leg    |

## Bias / reference generators

| Topology                                   | NMOS-flavor | PMOS-flavor | Notes |
| ------------------------------------------ | ----------- | ----------- | ----- |
| Diode-connected + current-setting resistor | ✓ 015       | ✓ 016       |       |

## Comparators and latches

| Topology                     | Fixture | Notes                |
| ---------------------------- | ------- | -------------------- |
| Cross-coupled inverter latch | ✓ 063   | 4-T memory cell core |

## Oscillators

*Functional grouping (8 fixtures). `064`/`065` are `Digital`-category in `meta.yaml`, so the
**Oscillator** category count is 6 (`110`–`113`, `120`, `125`); see the category-table note below.*

| Topology                                           | Fixture     | Notes                                             |
| -------------------------------------------------- | ----------- | ------------------------------------------------- |
| Ring oscillator, 3-stage (CMOS inverter chain)     | ✓ 064       | Inverter chain                                    |
| Ring oscillator, 5-stage                           | ✓ 065       |                                                   |
| Ring oscillator, 3-stage (CS-amp stages + R loads) | ✓ 110 / 111 | NMOS (110) / PMOS (111)                           |
| Differential ring oscillator, 3-stage (+ R loads)  | ✓ 112 / 113 | NMOS (112) / PMOS (113)                           |
| LC VCO, cross-coupled NMOS pair (center-tapped)    | ✓ 120       | Tank + cross-coupled NMOS, center-tapped inductor |
| LC VCO, cross-coupled NMOS pair (no tail)          | ✓ 125       |                                                   |

## Switched-capacitor / sample-and-hold

| Topology                                             | Fixture | Notes                                  |
| ---------------------------------------------------- | ------- | -------------------------------------- |
| Basic S/H: NMOS switch + hold cap                   | ✓ 105   |                                        |
| Basic S/H: PMOS switch + hold cap                   | ✓ 106   |                                        |
| Basic S/H: CMOS transmission-gate switch + hold cap | ✓ 107   |                                        |
| Bottom-plate / dummy-switch S/H: NMOS               | ✓ 108   | Dummy switch cancels clock feedthrough |
| Bottom-plate / dummy-switch S/H: PMOS               | ✓ 109   |                                        |


## Digital primitives / mixed-signal building blocks

| Topology          | Fixture | Notes                            |
| ----------------- | ------- | -------------------------------- |
| CMOS inverter     | ✓ 059   | Canonical 2-T                    |
| NAND2 (CMOS)      | ✓ 060   | 4-T                              |
| NOR2 (CMOS)       | ✓ 061   | 4-T                              |
| Transmission gate | ✓ 062   | NMOS ∥ PMOS, gates complementary |
| SRAM cell (6T)    | ✓ 066   |                                  |


## Feedback / closed-loop configurations

| Topology                                      | NMOS-input | PMOS-input | Notes                                 |
| --------------------------------------------- | ---------- | ---------- | ------------------------------------- |
| Unity-gain buffer (5T OTA in feedback)        | ✓ 097      | ✓ 098      |                                       |
| Non-inverting amp (5T OTA + resistor divider) | ✓ 099      | ✓ 100      |                                       |
| Shunt-shunt CS amp + resistor feedback        | ✓ 095      | ✓ 096      | R load + R feedback around a CS stage |

## Mixers

| Topology                                       | Fixture | Notes                              |
| ---------------------------------------------- | ------- | ---------------------------------- |
| Gilbert cell (double-balanced), resistor loads | ✓ 116   | NMOS switching/transconductor core |

---

## Aggregated counts

Shipped fixtures by category (from each fixture's `meta.yaml`; authoritative, sums to 125):

| Category      | Fixtures |
| ------------- | -------- |
| Amplifier     | 64       |
| CurrentMirror | 28       |
| OTA           | 7        |
| Oscillator    | 6        |
| Digital       | 6        |
| SampledData   | 5        |
| Feedback      | 4        |
| Memory        | 2        |
| Bias          | 2        |
| Mixer         | 1        |
| **Total**     | **125**  |

Note: the functional grouping above is a topology coverage map and does not line up
one-to-one with the `meta.yaml` `category` field. For example: folded-/telescopic-cascode OTAs are
filed under `Amplifier` while the 5T OTA is `OTA`; feedback configs span both `Feedback` and
`Amplifier`; the **Oscillators** section lists 8 but `064`/`065` (inverter-chain ring oscillators) are
`Digital`, so the **Oscillator category is 6**; and the two **Memory** fixtures (`063` latch, `066`
SRAM) appear in the *Comparators and latches* and *Digital primitives* sections. The category table
here is the authoritative shipped count; the section tables list the named topologies the corpus covers.

---

## Future tasks

- **Optional-device annotation**: beyond multi-reference (`reference_alt_N.cir`), support "device
  may or may not be present" (e.g. an optional decoupling cap); needs new graph-iso logic.
- **PDK layers** (sky130, etc.): "Layer 2," deferred.

