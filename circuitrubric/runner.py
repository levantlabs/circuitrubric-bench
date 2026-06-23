"""Reference runner: run the corpus through an LLM and grade the results.

Loops over (topology, prompt_variant, rep) triples, calls the configured LLM
backend, extracts a fenced SPICE netlist from the response, grades it with the
CircuitRubric grader, and writes both the raw response and a summary row per
triple. The backend is pluggable (see ``circuitrubric.backends``); the runner
itself is vendor-agnostic and only sees the normalized response dict.

Outputs land under ``<output_dir>/<run_id>/``:
  - ``config.json``    the run configuration (+ git rev), for reproducibility
  - ``raw/*.txt``      the raw model responses
  - ``summary.jsonl``  one JSON row per triple (extraction + grade result)

Runs resume: a triple whose raw response already exists is reused, not
re-called, so an interrupted run can be restarted cheaply.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import traceback
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Optional

from circuitrubric.backends import Backend, make_backend
from circuitrubric.grader import grade, GradeResult
from circuitrubric.netlist import parse_netlist
from circuitrubric.task import load_task

CONFIG_FILENAME = "config.json"
SUMMARY_FILENAME = "summary.jsonl"

_TYPED_FENCE_RE = re.compile(r"```(?:spice|ngspice)\s*\n(.*?)\n?```", re.DOTALL)
_BARE_FENCE_RE = re.compile(r"```\s*\n(.*?)\n?```", re.DOTALL)
# Match a SPICE device declaration line: optional leading indent, a device-letter
# prefix, an identifier, and at least two more whitespace-separated tokens on
# the SAME line. Using [ \t] (not \s) keeps the regex from crossing newlines.
_SPICE_DEVICE_LINE = re.compile(
    r"^[ \t]*[MRCLVIQDXKEFGHJSWBTU]\w+[ \t]+\S+[ \t]+\S+",
    re.IGNORECASE | re.MULTILINE,
)


def _looks_like_spice(block: str) -> bool:
    """True if the block contains at least one SPICE device declaration line.
    Fallback heuristic for bare ``` ``` fences whose language tag the model
    omitted (common with Qwen / Llama / Mistral)."""
    return bool(_SPICE_DEVICE_LINE.search(block))


# Fields whose change between runs is treated as drift and aborts a resume,
# so resuming with a different vendor/endpoint/model errors out instead of
# silently mixing responses in one run dir.
_CONFIG_DRIFT_FIELDS = (
    "backend_id",
    "base_url",
    "model",
    "temperature",
    "max_tokens",
    "fixtures_dir",
    "system_prompt",
    "effort",
)


@dataclass
class RunConfig:
    fixtures_dir: Path
    topology_ids: list[str]
    prompt_ids: list[str]
    reps: int
    model: str
    temperature: Optional[float]
    max_tokens: int
    system_prompt: str
    output_dir: Path
    run_id: str
    backend_id: str = "anthropic"
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    think: Any = False   # ollama: bool (qwen3-style) or level str "low"/"medium"/"high" (gpt-oss)
    reasoning: Any = None  # openai/OpenRouter reasoning control, e.g. {"enabled": False} / {"effort": "low"}
    effort: Optional[str] = None  # anthropic output_config.effort: low/medium/high/xhigh/max (None = API default high)
    dry_run: bool = False


def extract_netlist(raw_text: str) -> tuple[Optional[str], Optional[str]]:
    """Pull the LAST fenced SPICE netlist out of ``raw_text``.

    When the model self-corrects ("wait, let me fix that…") it emits multiple
    fenced blocks; the last one is the intended answer, so we grade that.

    Preference order:
      1. Last ```spice or ```ngspice fence (typed)
      2. Last bare ``` ``` fence whose content looks like a SPICE netlist

    Returns (extracted, None) on success or (None, error_str) on failure.
    """
    typed = list(_TYPED_FENCE_RE.finditer(raw_text))
    if typed:
        return typed[-1].group(1).strip(), None
    bare = [m for m in _BARE_FENCE_RE.finditer(raw_text)
            if _looks_like_spice(m.group(1))]
    if bare:
        return bare[-1].group(1).strip(), None
    # 3. No fences at all: some models (e.g. Qwen on OpenRouter) emit the netlist
    #    raw, sometimes prefixed with a bare ``spice``/``ngspice`` tag line. Gate on
    #    the real parser (>=2 parsed devices) rather than the loose line heuristic, so
    #    prose can't slip through. Only reached when both fence branches miss, so this
    #    can never change a fenced result.
    body = re.sub(r"^[ \t]*(?:spice|ngspice)[ \t]*\n", "", raw_text, count=1, flags=re.IGNORECASE)
    if len(parse_netlist(body).devices) >= 2:
        return body.strip(), None
    return None, "no fenced spice or ngspice block"


def _write_raw_atomic(raw_path: Path, text: str) -> None:
    """Write via tmp file + os.replace so a Ctrl-C between open and write
    cannot leave a zero-byte file at the final path."""
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = raw_path.with_suffix(raw_path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, raw_path)


def _grade_to_dict(g: GradeResult) -> dict:
    return {
        "credit": g.credit.value,
        "parse_ok": g.parse_ok,
        "iso_ok": g.iso_ok,
        "effective_w_ratio_ok": g.effective_w_ratio_ok,
        "l_ratio_ok": g.l_ratio_ok,
        "m_ratio_ok": g.m_ratio_ok,
        "value_ratio_ok": g.value_ratio_ok,
        "matched_reference": g.matched_reference,
        "error": g.error,
        "topology_recognized": g.topology_recognized,
        "extra_devices": g.extra_devices,
        "sd_equiv": g.sd_equiv,
        "functional_full": g.functional_full,
    }


def run_one(
    topology_id: str,
    task: Any,
    prompt_id: str,
    prompt_text: str,
    rep: int,
    config: RunConfig,
    output_dir: Path,
    backend: Backend,
) -> dict:
    """Execute one (topology, prompt, rep) triple.

    - If the raw file already exists and is non-empty, reuse it (no API call).
    - If the raw file exists but is empty, delete it and re-call.
    - Otherwise call the backend, save the raw response atomically, then
      extract and grade.

    Returns the summary row dict. The raw file is written as a side effect.
    """
    raw_path = output_dir / "raw" / f"{topology_id}--{prompt_id}--rep{rep}.txt"

    # Resume handling: clean up zero-byte raws so they get refetched.
    if raw_path.exists() and raw_path.stat().st_size == 0:
        raw_path.unlink()

    call_error: Optional[str] = None
    if raw_path.exists():
        raw_text = raw_path.read_text()
        stop_reason = None
        usage = None
        latency_ms = None
    else:
        # Retry transient API failures (malformed/truncated JSON, timeouts) a few
        # times; if they persist, record the error and continue so one bad response
        # can't abort the whole run. No raw is written on failure, so a later resume
        # retries this fixture.
        result = None
        for attempt in range(3):
            try:
                result = backend.call(
                    model=config.model,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    system_prompt=config.system_prompt,
                    user_prompt=prompt_text,
                )
                break
            except Exception:
                call_error = traceback.format_exc()
                time.sleep(2 * (attempt + 1))
        if result is None:
            raw_text = ""
            stop_reason = "call_error"
            usage = None
            latency_ms = None
        else:
            call_error = None
            raw_text = result["raw_text"]
            stop_reason = result["stop_reason"]
            usage = result["usage"]
            latency_ms = result["latency_ms"]
            _write_raw_atomic(raw_path, raw_text)

    extracted, extract_err = extract_netlist(raw_text)

    grade_dict: Optional[dict] = None
    grade_err: Optional[str] = None
    grade_err_type: Optional[str] = None
    if extracted is not None:
        try:
            g = grade(extracted, task)
            grade_dict = _grade_to_dict(g)
        except Exception as e:
            grade_err = traceback.format_exc()
            grade_err_type = type(e).__name__

    return {
        "run_id": config.run_id,
        "topology_id": topology_id,
        "prompt_id": prompt_id,
        "rep": rep,
        "backend_id": config.backend_id,
        "base_url": config.base_url,
        "model": config.model,
        "temperature": config.temperature,
        "prompt_text": prompt_text,
        "raw_path": str(raw_path.relative_to(output_dir)),
        "stop_reason": stop_reason,
        "extraction_ok": extracted is not None,
        "extracted_netlist": extracted,
        "extraction_error": extract_err,
        "grade": grade_dict,
        "grade_error": grade_err,
        "grade_error_type": grade_err_type,
        "call_error": call_error,
        "latency_ms": latency_ms,
        "usage": usage,
    }


def _git_rev() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _load_or_check_config(config_path: Path, config: RunConfig) -> dict:
    """If config.json exists, verify no drift on key fields and return the
    on-disk dict. Otherwise write a fresh config.json and return its dict."""
    cli_dict = {
        "run_id": config.run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "git_rev": _git_rev(),
        "backend_id": config.backend_id,
        "base_url": config.base_url,
        "api_key_env": config.api_key_env,
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "think": config.think,            # ollama reasoning control (bool / level str)
        "reasoning": config.reasoning,    # openai/OpenRouter reasoning control (dict)
        "effort": config.effort,          # anthropic output_config.effort (level str / None)
        "system_prompt": config.system_prompt,
        "fixtures_dir": str(config.fixtures_dir),
        "topology_ids": list(config.topology_ids),
        "prompt_ids": list(config.prompt_ids),
        "reps": config.reps,
    }
    if config_path.exists():
        on_disk = json.loads(config_path.read_text())
        drift = []
        for f in _CONFIG_DRIFT_FIELDS:
            if on_disk.get(f) != cli_dict.get(f):
                drift.append(
                    f"  {f}: on-disk={on_disk.get(f)!r}, cli={cli_dict.get(f)!r}"
                )
        if drift:
            raise RuntimeError(
                "Config drift detected on resume; aborting:\n" + "\n".join(drift)
            )
        return on_disk
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(cli_dict, indent=2))
    return cli_dict


def _build_plan(config: RunConfig) -> list[tuple[str, str, str, int, Any]]:
    """Build the ordered list of (topology_id, prompt_id, prompt_text, rep,
    task) tuples that drive the loop: the grid
    ``product(sorted(topology_ids), sorted(prompt_ids), 1..reps)`` with the
    per-fixture prompt resolved through ``load_task``. A (topology, prompt)
    pair with no matching variant is recorded with task=None and skipped."""
    plan: list[tuple[str, str, str, int, Any]] = []
    for topology_id, prompt_id, rep in product(
        sorted(config.topology_ids),
        sorted(config.prompt_ids),
        range(1, config.reps + 1),
    ):
        tasks = load_task(config.fixtures_dir / topology_id)
        task = next((t for t in tasks if t.prompt_id == prompt_id), None)
        if task is None:
            plan.append((topology_id, prompt_id, "", rep, None))
            continue
        plan.append((topology_id, prompt_id, task.prompt, rep, task))
    return plan


def run_benchmark(config: RunConfig, backend: Optional[Backend] = None) -> Path:
    """Orchestrate the full grid. Writes config.json, raw/*.txt, and
    summary.jsonl under config.output_dir/config.run_id/. Returns the
    summary.jsonl path. In dry-run mode prints the plan and returns Path("").

    ``backend`` may be injected (e.g. a mock) for testing; otherwise it is
    constructed from the config's backend_id/base_url/api_key_env."""
    plan = _build_plan(config)

    if config.dry_run:
        print(f"DRY RUN [{config.run_id}]")
        print(f"  backend: {config.backend_id}"
              + (f" (base_url={config.base_url})" if config.base_url else ""))
        print(f"  model: {config.model}")
        print(f"  system: {config.system_prompt}")
        for topology_id, prompt_id, prompt_text, rep, task in plan:
            if task is None:
                print(f"  SKIP {topology_id}/{prompt_id}/rep{rep} (no such variant)")
                continue
            print(f"  CALL {topology_id}/{prompt_id}/rep{rep}")
            print(f"    user: {prompt_text}")
        return Path("")

    output_dir = config.output_dir / config.run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    config_path = output_dir / CONFIG_FILENAME
    _load_or_check_config(config_path, config)

    summary_path = output_dir / SUMMARY_FILENAME
    if summary_path.exists():
        summary_path.unlink()

    if backend is None:
        backend = make_backend(
            backend_id=config.backend_id,
            base_url=config.base_url,
            api_key_env=config.api_key_env,
            think=config.think,
            reasoning=config.reasoning,
            effort=config.effort,
        )

    with summary_path.open("a") as summary_f:
        for topology_id, prompt_id, prompt_text, rep, task in plan:
            if task is None:
                continue
            row = run_one(
                topology_id=topology_id,
                task=task,
                prompt_id=prompt_id,
                prompt_text=prompt_text,
                rep=rep,
                config=config,
                output_dir=output_dir,
                backend=backend,
            )
            summary_f.write(json.dumps(row) + "\n")
    return summary_path


# Credit enum .value strings, best-to-worst (see circuitrubric.grader.Credit).
_CREDIT_ORDER = ("full", "partial", "partial_bulk", "topology", "decorated", "none")


def tally_credits(summary_path: Path) -> dict:
    """Read a summary.jsonl and return the credit-level tally:
    ``{"total", "graded", "counts": {level: n}, "full_rate"}``, where level is
    the ``Credit`` enum value (e.g. "full", "decorated"). Rows that failed
    extraction or grading count toward total but not graded."""
    counts: Counter = Counter()
    total = graded = 0
    for line in Path(summary_path).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        total += 1
        g = row.get("grade")
        if g and g.get("credit"):
            graded += 1
            counts[g["credit"]] += 1
    full = counts.get("full", 0)
    return {
        "total": total,
        "graded": graded,
        "counts": dict(counts),
        "full_rate": (full / total) if total else 0.0,
    }


def format_tally(t: dict) -> str:
    lines = [f"Results: {t['graded']}/{t['total']} graded; "
             f"FULL (pass) rate {t['full_rate']:.1%}"]
    ordered = list(_CREDIT_ORDER) + [c for c in t["counts"] if c not in _CREDIT_ORDER]
    for level in ordered:
        n = t["counts"].get(level, 0)
        if n:
            lines.append(f"  {level.upper():<13} {n}")
    return "\n".join(lines)


def _slug(s: str) -> str:
    """Filesystem-safe label for run-id dirs (e.g. 'gpt-4o' -> 'gpt-4o',
    'qwen2.5:latest' -> 'qwen2.5-latest')."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-") or "model"


def run_sweep(
    models: list[dict],
    *,
    fixtures_dir: Path,
    topology_ids: list[str],
    prompt_ids: list[str],
    reps: int,
    max_tokens: int,
    system_prompt: str,
    output_dir: Path,
    timestamp: str,
    temperature: Optional[float] = None,
    think: Any = False,
    reasoning: Any = None,
    effort: Optional[str] = None,
    backend_factory=make_backend,
) -> list[dict]:
    """Run the corpus through each model in ``models`` and grade.

    Each row is a dict: ``{"backend", "model", ["base_url"], ["api_key_env"],
    ["label"]}``. Per-model results land in ``<output_dir>/<timestamp>-<label>/``;
    one shared timestamp groups the sweep. ``backend_factory(backend_id,
    base_url, api_key_env)`` is injectable for testing.

    Returns a list of ``{"label", "model", "backend", "summary_path", "tally"}``.
    """
    results = []
    for row in models:
        backend_id = row["backend"]
        model = row["model"]
        label = row.get("label") or model
        run_id = f"{timestamp}-{_slug(label)}"
        # reasoning posture: per-row override (think/reasoning/effort keys) else the sweep default
        row_think = row.get("think", think)
        row_reasoning = row.get("reasoning", reasoning)
        row_effort = row.get("effort", effort)
        config = RunConfig(
            fixtures_dir=fixtures_dir,
            topology_ids=topology_ids,
            prompt_ids=prompt_ids,
            reps=reps,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            output_dir=output_dir,
            run_id=run_id,
            backend_id=backend_id,
            base_url=row.get("base_url"),
            api_key_env=row.get("api_key_env"),
            think=row_think,
            reasoning=row_reasoning,
            effort=row_effort,
        )
        # forward reasoning kwargs only when set, so a 3-arg test factory still works
        fkw = {}
        if row_think is not False: fkw["think"] = row_think
        if row_reasoning is not None: fkw["reasoning"] = row_reasoning
        if row_effort is not None: fkw["effort"] = row_effort
        backend = backend_factory(backend_id, config.base_url, config.api_key_env, **fkw)
        summary_path = run_benchmark(config, backend=backend)
        results.append({
            "label": label, "model": model, "backend": backend_id,
            "summary_path": summary_path, "tally": tally_credits(summary_path),
        })
    return results


def format_combined_table(results: list[dict]) -> str:
    """Markdown leaderboard table across models, sorted by FULL rate desc."""
    rows = sorted(results, key=lambda r: r["tally"]["full_rate"], reverse=True)
    cols = [c.upper() for c in _CREDIT_ORDER]
    header = "| model | FULL% | " + " | ".join(cols) + " | graded |"
    sep = "|" + "---|" * (len(cols) + 3)
    out = [header, sep]
    for r in rows:
        t = r["tally"]
        cells = [str(t["counts"].get(c, 0)) for c in _CREDIT_ORDER]
        out.append(
            f"| {r['label']} | {t['full_rate']:.1%} | "
            + " | ".join(cells)
            + f" | {t['graded']}/{t['total']} |"
        )
    return "\n".join(out)
