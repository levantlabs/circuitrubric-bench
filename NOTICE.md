# NOTICE — corpus provenance & disclosure

CircuitRubric
Copyright 2026 The CircuitRubric Authors.

## Licensing

- **Software** (the `circuitrubric` package + tooling): Apache-2.0 — see `LICENSE`.
- **Corpus** (`fixtures/`): Creative Commons Attribution 4.0 International (CC-BY-4.0) —
  see `LICENSE-CC-BY-4.0.txt`. Reuse freely with attribution (cite CircuitRubric; see `CITATION.cff`).

## Corpus construction

The 125 reference netlists in `fixtures/` were **authored fresh** for this benchmark in a
uniform house style (generic ngspice, `LEVEL=1` MOSFETs, consistent `.MODEL` cards and
naming). All fixtures are self-labeled `source: hand_authored` in their `meta.yaml`.

- Two fixtures cite **Gray & Meyer, *Analysis and Design of Analog Integrated Circuits***
  (textbook) as the topology reference.

## AI-assistance disclosure

The corpus and tooling were drafted with AI assistance and reviewed by a human analog
designer. Where a model family that assisted in authoring also appears as an evaluation
*subject*, the accompanying paper discloses that potential bias explicitly. This NOTICE
records the construction methodology transparently rather than obscuring it.
