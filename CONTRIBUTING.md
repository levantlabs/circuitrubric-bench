# Contributing to CircuitRubric

## Submit your model's results

1. Generate one netlist per fixture into a directory, named `<fixture_id>.cir`
   (e.g. `001_5t_ota_nmos.cir`), using each fixture's `prompts.yaml` request.
2. Run `circuitrubric grade-all --fixtures fixtures --submissions <your_dir>`.
3. Open a PR adding a row to the **Baseline results** table in `README.md` with your
   model, the FULL (pass) rate, and the prompt register you used. Include the exact prompt
   and decoding settings so the number is reproducible.

## Add a fixture

Each fixture is a self-describing directory under `fixtures/`:

```
fixtures/NNN_<slug>/
  meta.yaml           # category, family, variant, source (use "hand_authored" for new ones)
  prompts.yaml        # short / verbose / spec request variants
  reference.cir       # canonical netlist: generic ngspice, LEVEL=1 MOSFETs, house style
  ratio_groups.yaml   # equality / ratio constraints between matched devices
```

Guidelines:
- **Author the netlist fresh.** Do not paste from licensed corpora — only the *topology*
  is shared knowledge; the file must be your own expression. See `NOTICE.md`.
- Match the house style (descriptive comment header, `.MODEL` cards, `M*/R*/C*` device
  prefixes — the parser requires devices to start with their type letter).
- For topologies with multiple blessed forms, add `reference_alt_N.cir` files.
- **Validate it:** `python scripts/validate_fixtures.py fixtures/NNN_<slug>` checks the four files,
  `meta.id`, the prompt tiers and `short<verbose<spec` ordering, that `verbose` stays architectural
  (no device/terminal/node leak), the spec↔netlist wiring match, and that every reference grades
  FULL against itself. Run with no argument to validate the whole corpus.
- Run `pytest tests/` as well — the full grader test suite.

## Code

Run `pytest tests/` before a PR. The grader (`circuitrubric/grader.py`) and graph engine
(`graph.py`) are the core; keep changes covered by tests. See
[`docs/code-guide.md`](docs/code-guide.md) for a map of the package, data structures, and the
grading pipeline.
