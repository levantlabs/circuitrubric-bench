"""S/D-equivalence diagnostics: a transistor written with drain/source swapped
is electrically identical at this device level. The grader keeps FULL strict
(idiomatic orientation required) but reports `sd_equiv` / `functional_full` so
the functionally-correct-but-non-idiomatic case is visible.
"""
from pathlib import Path

from circuitrubric.grader import grade, Credit
from circuitrubric.task import load_task

FIX = Path(__file__).parent.parent / "fixtures"
SF = FIX / "009_source_follower_nmos"          # M1 drain=vdd source=vout, M2 drain=vout source=0
OTA = FIX / "001_5t_ota_nmos"


def _swap_ds(line: str) -> str:
    """Swap the drain (pos 1) and source (pos 3) fields of a MOSFET card."""
    p = line.split()
    p[1], p[3] = p[3], p[1]
    return " ".join(p)


def test_reference_is_sd_equiv_and_functional_full():
    task = load_task(SF)[0]
    res = grade((SF / "reference.cir").read_text(), task)
    assert res.credit == Credit.FULL
    assert res.sd_equiv            # strict iso implies sd-canonical iso
    assert res.functional_full


def test_sd_swapped_follower_stays_none_but_flags_functional():
    """Swap drain/source on the follower devices: FULL stays NONE (non-idiomatic
    orientation), but sd_equiv + functional_full fire — the circuit is correct."""
    task = load_task(SF)[0]
    lines = []
    for l in (SF / "reference.cir").read_text().splitlines():
        s = l.strip()
        lines.append(_swap_ds(l) if s[:1] in "Mm" else l)
    swapped = "\n".join(lines)
    res = grade(swapped, task)
    assert res.credit == Credit.NONE      # FULL unchanged: idiom still required
    assert not res.iso_ok
    assert res.sd_equiv                   # but recognized modulo S/D
    assert res.functional_full            # ratios pass + .MODEL present


def test_genuinely_wrong_topology_is_not_sd_equiv():
    task = load_task(OTA)[0]
    wrong = (
        "M1 vout vin 0 0 nmos W=10u L=1u\n"
        "R1 vout vdd 1k\n"
        ".MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n"
    )
    res = grade(wrong, task)
    assert res.credit == Credit.NONE
    assert not res.sd_equiv
    assert not res.functional_full


def test_sd_swap_without_model_cards_is_sd_equiv_but_not_functional_full():
    """S/D-swapped AND no .MODEL cards (inferred types): sd_equiv still True, but
    functional_full requires declared types (mirrors FULL), so it stays False."""
    import re
    task = load_task(SF)[0]
    txt = (SF / "reference.cir").read_text()
    txt = "\n".join(l for l in txt.splitlines() if not l.strip().upper().startswith(".MODEL"))
    txt = re.sub(r"\bNMOS\b", "NMOS_DEV", txt)
    lines = [_swap_ds(l) if l.strip()[:1] in "Mm" else l for l in txt.splitlines()]
    res = grade("\n".join(lines), task)
    assert res.credit == Credit.NONE
    assert res.sd_equiv
    assert not res.functional_full


def test_all_references_are_functional_full():
    """Every shipped reference grades FULL and therefore functional_full=True."""
    for fdir in sorted(FIX.iterdir()):
        if not fdir.is_dir() or not (fdir / "reference.cir").exists():
            continue
        for task in load_task(fdir):
            res = grade((fdir / "reference.cir").read_text(), task)
            assert res.credit == Credit.FULL, fdir.name
            assert res.sd_equiv and res.functional_full, fdir.name
