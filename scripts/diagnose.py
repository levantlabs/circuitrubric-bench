#!/usr/bin/env python3
"""Categorize WHY a run's fixtures failed, from its saved summary.jsonl (no model calls).

After a run (`circuitrubric run` / `run-all`), point this at the run directory to see *why* the
non-FULL fixtures missed. It buckets each non-FULL result into:
  no_netlist                 — nothing parseable was emitted
  unparseable                — emitted text didn't parse as SPICE
  decorated(extra devices)   — reference topology present + extra devices bolted on
  near:<credit>              — right wiring, wrong/missing sizing (TOPOLOGY/PARTIAL/PARTIAL_BULK)
  wrong_device_set           — different set of device types than the reference
  right_devices_wrong_wiring — same devices, connected differently
…prints a histogram, then a few reference-vs-model netlist examples per bucket so you can eyeball
the actual mistakes.

It also reports a separate **malformed-SPICE** signal — responses that emit a MOSFET with the
wrong number of terminals (a valid `M` line needs exactly 4 nodes: drain/gate/source/bulk). This
cuts across the failure buckets — it tells you how much of the loss is bad SPICE *syntax* rather
than wrong topology.

Usage:  python scripts/diagnose.py results/<run-id>
"""
import sys, os, json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from circuitrubric.netlist import parse_netlist

def hist(text):
    try: return Counter(d.type for d in parse_netlist(text).devices)
    except Exception: return Counter()

def _ref(fid):
    return (ROOT / "fixtures" / fid / "reference.cir").read_text()

def _model_names(nl):
    names = set()
    for line in nl.splitlines():
        s = line.strip()
        if s.upper().startswith(".MODEL"):
            p = s.split()
            if len(p) >= 3:
                names.add(p[1].lower())
    return names

def malformed_mosfet_terminals(nl):
    """Terminal-counts of MOSFET lines whose node count != 4 (model token resolvable).

    A valid SPICE M element is `M<name> <drain> <gate> <source> <bulk> <model> [params]`.
    Counts a line only when its model token resolves (a declared .MODEL name or a literal
    NMOS/PMOS), so repetition-loop / prose garbage doesn't inflate the count.
    """
    names = _model_names(nl)
    bad = []
    for raw in nl.splitlines():
        s = raw.strip()
        if not s or s[0].upper() != "M":
            continue
        pos = [t for t in s.split()[1:] if "=" not in t]   # nodes + model (params have '=')
        midx = None
        for i, t in enumerate(pos):
            if t.lower() in names or t.upper() in ("NMOS", "PMOS"):
                midx = i                                    # last resolvable model token
        if midx is None:
            continue                                        # not a clean device line
        if midx != 4:                                       # terminals = pos[:midx]
            bad.append(midx)
    return bad

def main(run_dir):
    rows = [json.loads(l) for l in open(os.path.join(run_dir, "summary.jsonl")) if l.strip()]
    cats = Counter(); ex = {}
    n_malformed = 0; term_dist = Counter()   # malformed-SPICE signal (cuts across buckets)
    for r in rows:
        nl = r.get("extracted_netlist")
        if nl:
            bad = malformed_mosfet_terminals(nl)
            if bad:
                n_malformed += 1
                for t in bad:
                    term_dist[t] += 1
        g = r.get("grade") or {}
        cr = g.get("credit")
        if cr == "full":
            continue
        fid = r["topology_id"]
        if not r.get("extraction_ok"):
            cat = "no_netlist"
        elif not g.get("parse_ok", True):
            cat = "unparseable"
        elif cr == "decorated":
            cat = "decorated(extra devices)"
        elif cr in ("topology", "partial", "partial_bulk"):
            cat = f"near:{cr}(right wiring, wrong sizing)"
        else:  # none
            refh = hist(_ref(fid))
            modh = hist(nl or "")
            cat = "wrong_device_set" if modh != refh else "right_devices_wrong_wiring"
        key = cat.split("(")[0].split(":")[0] if cat.startswith("near") else cat
        cats[key] += 1
        ex.setdefault(key, []).append((fid, nl))
    print(f"=== {os.path.basename(os.path.normpath(run_dir))}: {sum(cats.values())} non-FULL ===")
    for k, v in cats.most_common():
        print(f"  {k:34} {v}")
    if n_malformed:
        parts = []
        if term_dist.get(3): parts.append(f"{term_dist[3]} three-terminal (missing bulk)")
        if term_dist.get(5): parts.append(f"{term_dist[5]} five-terminal (extra node)")
        other = sum(v for t, v in term_dist.items() if t not in (3, 5))
        if other: parts.append(f"{other} other")
        print(f"\nmalformed SPICE — MOSFET with ≠4 terminals: {n_malformed} responses"
              + (f"  [{'; '.join(parts)}]" if parts else ""))
    for k in ("wrong_device_set", "right_devices_wrong_wiring", "decorated(extra devices)"):
        if k in ex:
            print(f"\n--- examples: {k} ---")
            for fid, nl in ex[k][:3]:
                ref = " | ".join(l for l in _ref(fid).splitlines() if l and l[0] in "MRCL")
                mod = " | ".join(l for l in (nl or "").splitlines() if l and l[:1] in "MRCLmrcl")
                print(f"  {fid}\n    REF: {ref}\n    MOD: {mod}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
