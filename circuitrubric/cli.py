"""CircuitRubric CLI. Subcommands: `show`, `grade`, `grade-all`, `run`.

  circuitrubric show      --task fixtures/001_5t_ota_nmos
  circuitrubric grade     --task fixtures/001_5t_ota_nmos --submission my.cir
  circuitrubric grade-all --fixtures fixtures --submissions out/   # evaluate a whole model run
  circuitrubric run       --backend ollama --model qwen2.5         # generate + grade end-to-end
"""

import argparse
import sys
from pathlib import Path

import yaml

from circuitrubric.grader import grade as grade_fn, Credit
from circuitrubric.task import load_task

# Repo-root system_prompts.yaml (works for the `git clone` + editable-install
# replication flow). Overridable with --system-prompts / --system-prompt.
_DEFAULT_SYSTEM_PROMPTS = Path(__file__).resolve().parent.parent / "system_prompts.yaml"

_STATUS = {
    Credit.FULL: "PASS", Credit.PARTIAL: "PARTIAL", Credit.PARTIAL_BULK: "PARTIAL_BULK",
    Credit.TOPOLOGY: "TOPOLOGY", Credit.DECORATED: "DECORATED", Credit.NONE: "FAIL",
}
_EXIT = {
    Credit.FULL: 0, Credit.PARTIAL: 3, Credit.PARTIAL_BULK: 6,
    Credit.TOPOLOGY: 4, Credit.DECORATED: 5, Credit.NONE: 1,
}


def cmd_show(args):
    tasks = load_task(Path(args.task))
    first = tasks[0]
    print(f"topology:   {first.topology_id}")
    print(f"category:   {first.meta.category}/{first.meta.family}/{first.meta.variant}")
    print(f"source:     {first.meta.source}")
    print(f"references: {[r.name for r in first.references]}")
    print("ratio groups:")
    for g in first.ratio_groups:
        print(f"  - {g.devices} W={g.ratio_W} L={g.ratio_L}")
    print("prompts:")
    for t in tasks:
        print(f"  - {t.prompt_id}: {t.prompt}")
    return 0


def _grade_one(task_dir: Path, submission_text: str, prompt_id=None):
    tasks = load_task(task_dir)
    task = tasks[0] if not prompt_id else next(
        (t for t in tasks if t.prompt_id == prompt_id), None)
    if task is None:
        raise SystemExit(f"ERROR: no prompt variant {prompt_id!r} in {task_dir}")
    return task, grade_fn(submission_text, task)


def cmd_grade(args):
    task, result = _grade_one(Path(args.task), Path(args.submission).read_text(),
                              args.prompt_id)
    print(f"{_STATUS[result.credit]} {task.id}")
    print(f"  parse_ok={result.parse_ok} iso_ok={result.iso_ok}")
    print(f"  effective_w_ratio_ok={result.effective_w_ratio_ok} "
          f"l_ratio_ok={result.l_ratio_ok} m_ratio_ok={result.m_ratio_ok} "
          f"value_ratio_ok={result.value_ratio_ok}")
    if result.matched_reference:
        print(f"  matched: {result.matched_reference}")
    if result.error:
        print(f"  error: {result.error}")
    return _EXIT[result.credit]


def cmd_grade_all(args):
    """Batch-grade a directory of model outputs against the corpus.

    Looks for `<fixture_id>.cir` (or `.txt`) under --submissions for each fixture
    dir under --fixtures, grades it, and prints a credit-level summary. This is the
    'evaluate my model across the benchmark' entry point.
    """
    fixtures_dir = Path(args.fixtures)
    subs_dir = Path(args.submissions)
    fixtures = sorted(d for d in fixtures_dir.iterdir() if (d / "meta.yaml").exists())
    tally = {c: 0 for c in Credit}
    missing = 0
    for fdir in fixtures:
        sub = next((subs_dir / f"{fdir.name}{ext}" for ext in (".cir", ".txt", ".spice")
                    if (subs_dir / f"{fdir.name}{ext}").exists()), None)
        if sub is None:
            missing += 1
            continue
        _, result = _grade_one(fdir, sub.read_text(), args.prompt_id)
        tally[result.credit] += 1
        if not args.quiet:
            print(f"{_STATUS[result.credit]:<12} {fdir.name}")
    n = len(fixtures)
    full = tally[Credit.FULL]
    print("\n=== CircuitRubric summary ===")
    print(f"fixtures: {n}   submissions found: {n - missing}   missing: {missing}")
    for c in (Credit.FULL, Credit.PARTIAL, Credit.PARTIAL_BULK, Credit.TOPOLOGY,
              Credit.DECORATED, Credit.NONE):
        print(f"  {_STATUS[c]:<12} {tally[c]:>4}")
    print(f"\nFULL (pass) rate: {full}/{n} = {100*full/n:.1f}%")
    return 0


def _resolve_system_prompt(args) -> str:
    """Resolve the system prompt text from --system-prompt (literal),
    else --system-prompt-id looked up in the --system-prompts YAML."""
    if args.system_prompt is not None:
        return args.system_prompt
    sp_path = Path(args.system_prompts)
    if not sp_path.is_file():
        raise SystemExit(
            f"ERROR: system prompts file not found: {sp_path}\n"
            f"  pass --system-prompts <file> or --system-prompt \"<text>\"."
        )
    doc = yaml.safe_load(sp_path.read_text()) or {}
    prompts = {e["id"]: e["text"] for e in doc.get("prompts", [])}
    pid = args.system_prompt_id or doc.get("default_id")
    if pid not in prompts:
        raise SystemExit(
            f"ERROR: system-prompt-id {pid!r} not in {sp_path} "
            f"(have: {', '.join(prompts)})"
        )
    return prompts[pid]


def _parse_think(val):
    """Map the --think CLI string to the backend's think value.

    qwen3-style reasoning models take a bool; gpt-oss IGNORES the bool and needs
    a level string ("low"/"medium"/"high"). Default (None) -> False (thinking off).
    """
    if val is None or val == "false":
        return False
    if val == "true":
        return True
    if val == "none":
        return None
    return val  # "low" / "medium" / "high"


def _parse_reasoning(val):
    """Map --reasoning to OpenRouter's unified `reasoning` object.
    off -> disable thinking entirely; low/medium/high -> effort level; None -> provider default."""
    if val is None:
        return None
    if val == "off":
        return {"enabled": False}
    return {"effort": val}   # low / medium / high


def cmd_run(args):
    """Generate a netlist per (fixture, prompt) with an LLM backend, then grade
    it — the end-to-end 'run the benchmark through a model' entry point."""
    from datetime import datetime, timezone
    from circuitrubric.runner import RunConfig, run_benchmark, tally_credits, format_tally

    fixtures_dir = Path(args.fixtures_dir)
    if args.topology_ids:
        topology_ids = [s.strip() for s in args.topology_ids.split(",") if s.strip()]
    else:
        topology_ids = sorted(d.name for d in fixtures_dir.iterdir()
                              if (d / "meta.yaml").exists())
    prompt_ids = sorted(s.strip() for s in args.prompt_ids.split(",") if s.strip())
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    config = RunConfig(
        fixtures_dir=fixtures_dir,
        topology_ids=topology_ids,
        prompt_ids=prompt_ids,
        reps=args.reps,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        system_prompt=_resolve_system_prompt(args),
        output_dir=Path(args.output_dir),
        run_id=run_id,
        backend_id=args.backend,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        think=_parse_think(args.think),
        reasoning=_parse_reasoning(args.reasoning),
        dry_run=args.dry_run,
    )
    summary_path = run_benchmark(config)
    if config.dry_run:
        return 0
    print(f"\nWrote {summary_path}")
    print(format_tally(tally_credits(summary_path)))
    return 0


def cmd_run_all(args):
    """Config-driven multi-model sweep: run every model in --models over the
    corpus, then print a combined leaderboard table."""
    from datetime import datetime, timezone
    from circuitrubric.runner import run_sweep, format_combined_table

    models_path = Path(args.models)
    if not models_path.is_file():
        raise SystemExit(
            f"ERROR: models file not found: {models_path}\n"
            f"  copy models.example.yaml to {models_path} and edit it."
        )
    models = yaml.safe_load(models_path.read_text()) or []
    if not isinstance(models, list) or not models:
        raise SystemExit(f"ERROR: {models_path} must be a non-empty YAML list of models")
    for i, row in enumerate(models):
        if not (isinstance(row, dict) and row.get("backend") and row.get("model")):
            raise SystemExit(f"ERROR: {models_path} row {i} needs at least 'backend' and 'model'")

    fixtures_dir = Path(args.fixtures_dir)
    if args.topology_ids:
        topology_ids = [s.strip() for s in args.topology_ids.split(",") if s.strip()]
    else:
        topology_ids = sorted(d.name for d in fixtures_dir.iterdir()
                              if (d / "meta.yaml").exists())
    prompt_ids = sorted(s.strip() for s in args.prompt_ids.split(",") if s.strip())

    if args.dry_run:
        per = len(topology_ids) * len(prompt_ids) * args.reps
        print(f"DRY RUN sweep: {len(models)} models x {per} calls each "
              f"({len(topology_ids)} fixtures x {len(prompt_ids)} prompts x {args.reps} reps)")
        for row in models:
            label = row.get("label") or row["model"]
            print(f"  {label}  [backend={row['backend']}"
                  + (f", base_url={row['base_url']}" if row.get("base_url") else "") + "]")
        return 0

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    results = run_sweep(
        models,
        fixtures_dir=fixtures_dir,
        topology_ids=topology_ids,
        prompt_ids=prompt_ids,
        reps=args.reps,
        max_tokens=args.max_tokens,
        system_prompt=_resolve_system_prompt(args),
        output_dir=Path(args.output_dir),
        timestamp=timestamp,
        temperature=args.temperature,
    )
    print("\n=== CircuitRubric leaderboard ===")
    print(format_combined_table(results))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="circuitrubric", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("show", help="show a fixture and its prompt variants")
    ps.add_argument("--task", required=True)
    ps.set_defaults(func=cmd_show)

    pg = sub.add_parser("grade", help="grade one submitted netlist against a fixture")
    pg.add_argument("--task", required=True)
    pg.add_argument("--submission", required=True)
    pg.add_argument("--prompt-id", default=None)
    pg.set_defaults(func=cmd_grade)

    pa = sub.add_parser("grade-all", help="batch-grade a model's outputs over the corpus")
    pa.add_argument("--fixtures", default="fixtures")
    pa.add_argument("--submissions", required=True,
                    help="dir of <fixture_id>.cir model outputs")
    pa.add_argument("--prompt-id", default=None)
    pa.add_argument("--quiet", action="store_true")
    pa.set_defaults(func=cmd_grade_all)

    pr = sub.add_parser("run", help="generate netlists with an LLM backend and grade them")
    pr.add_argument("--fixtures-dir", default="fixtures")
    pr.add_argument("--topology-ids", default=None,
                    help="comma-separated fixture ids (default: all under --fixtures-dir)")
    pr.add_argument("--prompt-ids", default="short,verbose,spec",
                    help="comma-separated prompt variants to run (default: short,verbose,spec)")
    pr.add_argument("--reps", type=int, default=1,
                    help="repetitions per (fixture, prompt) pair")
    pr.add_argument("--backend", default="anthropic",
                    choices=("anthropic", "openai", "ollama"))
    pr.add_argument("--model", required=True,
                    help="model id for the backend (e.g. claude-opus-4-8, gpt-4o, qwen2.5)")
    pr.add_argument("--base-url", default=None,
                    help="endpoint for openai-compatible servers, e.g. "
                         "http://localhost:11434/v1 for ollama; or the ollama host")
    pr.add_argument("--api-key-env", default=None,
                    help="env var holding the API key (openai backend; default OPENAI_API_KEY)")
    pr.add_argument("--temperature", type=float, default=None)
    pr.add_argument("--max-tokens", type=int, default=2000)
    pr.add_argument("--think", default=None,
                    choices=("true", "false", "none", "low", "medium", "high"),
                    help="ollama reasoning control: true/false (qwen3-style) or a level "
                         "low/medium/high (REQUIRED for gpt-oss — it ignores the bool). "
                         "Default: thinking off.")
    pr.add_argument("--reasoning", default=None,
                    choices=("off", "low", "medium", "high"),
                    help="openai/OpenRouter reasoning control: off disables thinking, "
                         "low/medium/high sets effort. Default: provider default.")
    pr.add_argument("--system-prompt-id", default=None,
                    help="which system prompt to use (default: the file's default_id)")
    pr.add_argument("--system-prompts", default=str(_DEFAULT_SYSTEM_PROMPTS),
                    help="path to system_prompts.yaml")
    pr.add_argument("--system-prompt", default=None,
                    help="literal system prompt text (overrides --system-prompt-id)")
    pr.add_argument("--output-dir", default="results")
    pr.add_argument("--run-id", default=None, help="default: UTC timestamp")
    pr.add_argument("--dry-run", action="store_true",
                    help="print the plan without calling any model")
    pr.set_defaults(func=cmd_run)

    pall = sub.add_parser("run-all",
                          help="sweep multiple models from a config and print a leaderboard")
    pall.add_argument("--models", default="models.yaml",
                      help="YAML list of {backend, model, [base_url], [api_key_env], [label]} "
                           "(copy models.example.yaml). Default: models.yaml")
    pall.add_argument("--fixtures-dir", default="fixtures")
    pall.add_argument("--topology-ids", default=None,
                      help="comma-separated fixture ids (default: all)")
    pall.add_argument("--prompt-ids", default="short,verbose,spec")
    pall.add_argument("--reps", type=int, default=1)
    pall.add_argument("--temperature", type=float, default=None)
    pall.add_argument("--max-tokens", type=int, default=2000)
    pall.add_argument("--system-prompt-id", default=None)
    pall.add_argument("--system-prompts", default=str(_DEFAULT_SYSTEM_PROMPTS))
    pall.add_argument("--system-prompt", default=None)
    pall.add_argument("--output-dir", default="results")
    pall.add_argument("--dry-run", action="store_true")
    pall.set_defaults(func=cmd_run_all)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
