#!/usr/bin/env python3
"""Tabulate benchmark runs — a markdown credit table (default) or a full CSV (`--csv FILE`).

Point it at run directories (each a `<output-dir>/<run-id>/` from `circuitrubric run` / `run-all`,
holding `config.json` + `summary.jsonl`). The default prints a per-run credit table; `--csv FILE`
writes one row per run with the **full metric set** — the same schema as the benchmark's published
`docs/results/all_results.csv`, so you can run it on your own runs and diff against ours.

Per-run metrics:
  full_pct        exact FULL (iso + all sizing ratios)
  full_ign_src    FULL after stripping ideal V/I test-bench sources (re-grade)
  sd_equiv        iso modulo MOSFET drain/source orientation
  functional_full FULL modulo drain/source orientation (sd_equiv + ratios + .MODEL)
  full_emitted    FULL among non-empty responses
  topo_ok         FULL+PARTIAL+PARTIAL_BULK+TOPOLOGY (right wiring, sizing aside)
  recognized      topo_ok + DECORATED
  + the 6 credit counts, xfail, empty, malformed-MOSFET count, latency, tokens.

`full_ign_src` re-grades (strip V*/I*, grade again), so it needs the `circuitrubric` grader +
`fixtures/`; if unavailable it falls back to FULL and the rest still works.

Usage:
  python scripts/aggregate_runs.py results/*                  # markdown table
  python scripts/aggregate_runs.py --csv my_results.csv results/*
"""
import sys, json, glob, os, csv, statistics
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
ORDER = ("full", "partial", "partial_bulk", "topology", "decorated", "none")
TOPO = ("full", "partial", "partial_bulk", "topology")
RECOG = TOPO + ("decorated",)

# Optional re-grade for full_ign_src (needs grader + fixtures); degrade gracefully if absent.
try:
    sys.path.insert(0, str(ROOT))
    import yaml
    from circuitrubric.task import load_task
    from circuitrubric.grader import grade
    SPMAP = {e["text"]: e["id"] for e in yaml.safe_load(open(ROOT / "system_prompts.yaml"))["prompts"]}
    _RG = True
except Exception:
    _RG = False; SPMAP = {}

_TASKS = {}
def _task(tid):
    if tid not in _TASKS:
        try: _TASKS[tid] = load_task(ROOT / "fixtures" / tid)[0]
        except Exception: _TASKS[tid] = None
    return _TASKS[tid]

def _strip_vi(text):
    return "\n".join(l for l in text.splitlines()
                     if not (l.strip() and not l.strip().startswith(("*", ".")) and l.strip()[0].upper() in ("V", "I")))

def _malformed_mosfet(nl):
    """1 if the netlist has a MOSFET line with != 4 terminals (model token resolvable)."""
    names = set()
    for line in nl.splitlines():
        s = line.strip()
        if s.upper().startswith(".MODEL") and len(s.split()) >= 3:
            names.add(s.split()[1].lower())
    for raw in nl.splitlines():
        s = raw.strip()
        if not s or s[0].upper() != "M":
            continue
        pos = [t for t in s.split()[1:] if "=" not in t]
        midx = next((i for i, t in reversed(list(enumerate(pos)))
                     if t.lower() in names or t.upper() in ("NMOS", "PMOS")), None)
        if midx is not None and midx != 4:
            return 1
    return 0

def metrics(run_dir):
    d = Path(run_dir)
    cfg = json.load(open(d / "config.json")) if (d / "config.json").exists() else {}
    sj = d / "summary.jsonl"
    rows = [json.loads(l) for l in open(sj) if l.strip()] if sj.exists() else []
    if not rows:
        return None
    n = len(rows)
    c = Counter((r.get("grade") or {}).get("credit") for r in rows)
    full = c.get("full", 0)
    empty = sum(1 for r in rows if not r.get("extracted_netlist"))
    xfail = sum(1 for r in rows if not r.get("extraction_ok", True)
                or (r.get("extraction_ok", True) and (r.get("grade") or {}).get("credit") is None))
    n_ign = n_sd = n_func = n_mal = 0
    for r in rows:
        nl = r.get("extracted_netlist"); g = r.get("grade") or {}
        if not nl:
            continue
        n_mal += _malformed_mosfet(nl)
        n_sd += int(g.get("sd_equiv") or False)
        n_func += int(g.get("functional_full") or False)
        if _RG and (t := _task(r.get("topology_id", ""))) is not None:
            try: n_ign += int(grade(_strip_vi(nl), t).credit.value == "full")
            except Exception: n_ign += int(g.get("credit") == "full")
        else:
            n_ign += int(g.get("credit") == "full")
    emitted = n - empty
    lat = [r["latency_ms"] for r in rows if r.get("latency_ms")]
    tps = [(r.get("usage") or {}).get("output_tokens", 0) / (r["latency_ms"] / 1000)
           for r in rows if r.get("latency_ms") and (r.get("usage") or {}).get("output_tokens")]
    pids = cfg.get("prompt_ids") or sorted({r.get("prompt_id") for r in rows})
    # reasoning config: anthropic uses `effort`; openai/OpenRouter uses a `reasoning` object.
    # Flatten the latter to a short string (effort level / "off" / "").
    rz = cfg.get("reasoning")
    reasoning_str = ("" if rz is None
                     else "off" if isinstance(rz, dict) and rz.get("enabled") is False
                     else rz.get("effort", "") if isinstance(rz, dict) else str(rz))
    return {
        "id": d.name, "model": cfg.get("model"), "backend": cfg.get("backend_id"),
        "fixture_prompt": ",".join(p for p in pids if p) if pids else "?",
        "system_prompt": SPMAP.get(cfg.get("system_prompt", ""), cfg.get("system_prompt", "?")),
        "temperature": cfg.get("temperature"), "max_tokens": cfg.get("max_tokens"),
        "effort": cfg.get("effort") or "", "reasoning": reasoning_str, "n": n,
        **{k: c.get(k, 0) for k in ORDER}, "xfail": xfail, "empty": empty,
        "full_pct": round(100 * full / n, 1),
        "full_ign_src_pct": round(100 * n_ign / n, 1),
        "sd_equiv_pct": round(100 * n_sd / n, 1),
        "functional_full_pct": round(100 * n_func / n, 1),
        "full_emitted_pct": round(100 * full / emitted, 1) if emitted else 0.0,
        "topo_ok_pct": round(100 * sum(c.get(k, 0) for k in TOPO) / n, 1),
        "recognized_pct": round(100 * sum(c.get(k, 0) for k in RECOG) / n, 1),
        "malformed_term": n_mal,
        "mean_latency_s": round(statistics.mean(lat) / 1000, 1) if lat else "",
        "out_tok_per_s": round(statistics.mean(tps), 1) if tps else "",
        "in_tokens": sum((r.get("usage") or {}).get("input_tokens", 0) for r in rows if r.get("usage")),
        "out_tokens": sum((r.get("usage") or {}).get("output_tokens", 0) for r in rows if r.get("usage")),
    }

CSV_COLS = ["id", "model", "backend", "fixture_prompt", "system_prompt", "temperature", "max_tokens",
            "effort", "reasoning",
            "n", *ORDER, "xfail", "empty", "full_pct", "full_ign_src_pct", "sd_equiv_pct",
            "functional_full_pct", "full_emitted_pct", "topo_ok_pct", "recognized_pct",
            "malformed_term", "mean_latency_s", "out_tok_per_s", "in_tokens", "out_tokens"]

def main(argv):
    csv_out = None
    if "--csv" in argv:
        i = argv.index("--csv"); csv_out = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if not argv:
        print(__doc__); return 1
    dirs = []
    for a in argv:
        if (Path(a) / "summary.jsonl").exists():
            dirs.append(a)
        else:
            dirs += [os.path.dirname(p) for p in
                     sorted(glob.glob(os.path.join(a, "summary.jsonl")))
                     or sorted(glob.glob(os.path.join(a, "*", "summary.jsonl")))]
    recs = [m for d in sorted(set(dirs)) if (m := metrics(d))]
    if not recs:
        print("no runs found under:", argv); return 1
    recs.sort(key=lambda r: (r["model"] or "", r["fixture_prompt"], r["system_prompt"]))
    if csv_out:
        with open(csv_out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CSV_COLS); w.writeheader()
            for r in recs: w.writerow(r)
        print(f"wrote {csv_out} ({len(recs)} runs)")
        return 0
    head = ["run", "n", "FULL%", "ign_src%", "func%", "topo%", *[c.upper() for c in ORDER], "xfail"]
    print("| " + " | ".join(head) + " |"); print("|" + "---|" * len(head))
    for r in recs:
        print(f"| {r['id']} | {r['n']} | {r['full_pct']} | {r['full_ign_src_pct']} | "
              f"{r['functional_full_pct']} | {r['topo_ok_pct']} | "
              + " | ".join(str(r[k]) for k in ORDER) + f" | {r['xfail']} |")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
