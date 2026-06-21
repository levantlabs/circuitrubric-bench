#!/usr/bin/env python3
"""Validate CircuitRubric fixtures — structural checks for adding or editing a fixture.

Six checks per fixture:
  1. all 4 files present (meta.yaml, prompts.yaml, ratio_groups.yaml, reference.cir)
  2. meta.id matches the directory name
  3. prompts.yaml has exactly {short, verbose, spec}, with word counts short < verbose < spec
  4. verbose is architectural prose — no device IDs / terminal-wiring words / "exactly" / node names
  5. reference.cir (and any reference_alt_*.cir) parses AND grades FULL against itself
  6. the spec describes the reference's actual wiring (spec ↔ netlist audit)

Exit status is non-zero if any fixture fails, so it works as a CI / pre-PR gate.

Usage:
  python scripts/validate_fixtures.py                         # all of fixtures/
  python scripts/validate_fixtures.py fixtures/099_my_new     # one (or several) fixture dirs
  python scripts/validate_fixtures.py --fixtures-dir path/to/fixtures
"""
import sys, re, os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from circuitrubric.netlist import parse_netlist
from circuitrubric.grader import grade
from circuitrubric.task import load_task

REQUIRED = ["meta.yaml", "prompts.yaml", "ratio_groups.yaml", "reference.cir"]

def _normn(n):
    n = n.strip().lower()
    return "0" if n in ("ground", "gnd") else n

def parse_spec(spec):
    """Extract {device: (kind, terminals)} described in the spec prose (mirrors the grader's
    expectation that the spec spells out every device's connectivity)."""
    devs = {}
    for cl in re.split(r"[.;]\s+", spec):
        m = re.search(r"\b([RCL][A-Za-z]*\d*)\b\s+(?:is\s+an?\s+(?:resistor|capacitor|inductor)\s+)?"
                      r"between\s+([A-Za-z0-9_]+)\s+and\s+([A-Za-z0-9_]+)", cl)
        if m:
            devs[m.group(1)] = ("pas", frozenset({_normn(m.group(2)), _normn(m.group(3))}))
            continue
        if not re.search(r"\b(drain|gate|source|bulk)\s+(?:at|to)\b", cl):
            continue
        nm = re.search(r"\b(M\d+)\b", cl)
        if not nm:
            continue
        terms = {}
        for t in ("drain", "gate", "source", "bulk"):
            mm = re.search(rf"\b{t}\s+(?:at|to)\s+(?:the[^.,;]*?\(call it (\w+)\)|([A-Za-z0-9_]+))", cl)
            if mm:
                terms[t] = _normn(mm.group(1) or mm.group(2))
        devs[nm.group(1)] = ("mos", terms)
    return devs

def check_fixture(fdir):
    """Return a list of (ok: bool, message: str) for one fixture directory."""
    out = []
    def chk(ok, msg): out.append((bool(ok), msg))
    fid = fdir.name

    # 1. required files
    missing = [f for f in REQUIRED if not (fdir / f).exists()]
    chk(not missing, "4 required files present" + (f" — missing {missing}" if missing else ""))
    if missing:
        return out  # nothing else can run

    meta = yaml.safe_load((fdir / "meta.yaml").read_text()) or {}
    prompts = {e["id"]: e["text"] for e in yaml.safe_load((fdir / "prompts.yaml").read_text())["prompts"]}

    # 2. meta.id == dirname
    chk(meta.get("id") == fid, f"meta.id == dirname (meta.id={meta.get('id')!r})")

    # 3. prompt tiers + word-count ordering
    if set(prompts) != {"short", "verbose", "spec"}:
        chk(False, f"prompts are exactly short/verbose/spec (got {sorted(prompts)})")
        return out
    ws, wv, wsp = (len(prompts[k].split()) for k in ("short", "verbose", "spec"))
    chk(ws < wv < wsp, f"word counts short<verbose<spec ({ws}/{wv}/{wsp})")

    # 4. verbose is architectural prose (no answer leak)
    v = prompts["verbose"]
    leaks = []
    if re.search(r"\bM\d", v): leaks.append("device IDs (M#)")
    if re.search(r"\bbulk\b", v, re.I): leaks.append("'bulk'")
    if re.search(r"\b(drain|gate)\s+(at|to)\b", v, re.I): leaks.append("terminal wiring (drain/gate at/to)")
    if re.search(r"\bexactly\b", v, re.I): leaks.append("'exactly'")
    if re.search(r"\b(vinp|vinn|voutp|voutn|ntail|iref|iout|vbias|vdd|vss|clkb)\b", v): leaks.append("explicit node names")
    chk(not leaks, "verbose is architectural prose" + (f" — leaks: {', '.join(leaks)}" if leaks else ""))

    # 5. reference(s) parse + grade FULL against itself
    try:
        task = load_task(fdir)[0]
    except Exception as e:
        chk(False, f"load_task — ERROR {e}")
        return out
    for ref in sorted(fdir.glob("reference.cir")) + sorted(fdir.glob("reference_alt_*.cir")):
        try:
            parse_netlist(ref.read_text())
            cr = grade(ref.read_text(), task).credit.value
            chk(cr == "full", f"{ref.name} grades FULL against itself (got {cr})")
        except Exception as e:
            chk(False, f"{ref.name} parses + grades — ERROR {e}")

    # 6. spec <-> reference wiring audit
    try:
        nl = parse_netlist((fdir / "reference.cir").read_text())
        net = {}
        for d in nl.devices:
            if d.type in ("nmos", "pmos"):
                net[d.name.lower()] = ("mos", {k: _normn(x) for k, x in d.terminals.items()})
            elif d.type in ("r", "c", "l"):
                net[d.name.lower()] = ("pas", frozenset(_normn(x) for x in d.terminals.values()))
        sd = {n.lower(): val for n, val in parse_spec(prompts["spec"]).items()}
        problems = []
        if set(sd) != set(net):
            problems.append(f"device set spec={sorted(sd)} vs netlist={sorted(net)}")
        else:
            for name in sd:
                sk, sv = sd[name]; nk, nv = net[name]
                if sk != nk:
                    problems.append(f"{name}: kind"); continue
                if sk == "mos":
                    for t in ("drain", "gate", "source", "bulk"):
                        if t in sv and sv[t] != nv.get(t):
                            problems.append(f"{name}.{t} spec={sv[t]} netlist={nv.get(t)}")
                elif sv != nv:
                    problems.append(f"{name}: nodes")
        chk(not problems, "spec matches reference wiring" + (f" — {problems[:4]}" if problems else ""))
    except Exception as e:
        chk(False, f"spec<->netlist audit — ERROR {e}")

    return out

def main(argv):
    fdarg = next((argv[i + 1] for i, a in enumerate(argv) if a == "--fixtures-dir" and i + 1 < len(argv)), None)
    pos = [a for a in argv if not a.startswith("-") and a != fdarg]
    if pos:
        targets = [Path(a) for a in pos]
    else:
        base = Path(fdarg) if fdarg else (ROOT / "fixtures")
        targets = sorted(d for d in base.iterdir() if (d / "meta.yaml").exists())
    if not targets:
        print("no fixtures found"); return 1
    n_fail = 0
    for fdir in targets:
        results = check_fixture(fdir)
        fails = [m for ok, m in results if not ok]
        if fails:
            n_fail += 1
            print(f"FAIL {fdir.name}")
            for m in fails:
                print(f"     ✗ {m}")
        else:
            print(f"ok   {fdir.name}  ({len(results)} checks)")
    print(f"\n{len(targets) - n_fail}/{len(targets)} fixtures pass"
          + (f"  ({n_fail} FAILED)" if n_fail else "  — ALL PASS"))
    return 1 if n_fail else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
