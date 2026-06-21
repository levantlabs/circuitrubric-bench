from pathlib import Path

from circuitrubric.grader import grade, GradeResult, Credit
from circuitrubric.task import load_task

FIXTURE = Path(__file__).parent.parent / "fixtures" / "001_5t_ota_nmos"


def test_grade_correct_submission_credits_full():
    task = load_task(FIXTURE)[0]
    correct = (FIXTURE / "reference.cir").read_text()
    result = grade(correct, task)
    assert isinstance(result, GradeResult)
    assert result.credit == Credit.FULL
    assert result.passed
    assert result.parse_ok
    assert result.iso_ok
    assert result.effective_w_ratio_ok
    assert result.l_ratio_ok
    assert result.value_ratio_ok
    # m_ratio_ok is None because 001's ratio_groups.yaml has no ratio_M
    assert result.m_ratio_ok is None


def test_omitted_model_cards_capped_at_topology():
    # A submission with the CORRECT topology but no .MODEL cards — types inferable
    # only from descriptive names (NMOS_DEV/PMOS_DEV) — is recognized as correct
    # topology but capped at TOPOLOGY (not FULL): no .MODEL cards => incomplete.
    task = load_task(FIXTURE)[0]
    correct = (FIXTURE / "reference.cir").read_text()
    import re
    # rename the resolved model + strip its .MODEL card so the type is inferred
    stripped = "\n".join(
        l for l in correct.splitlines() if not l.strip().upper().startswith(".MODEL")
    )
    stripped = re.sub(r"\bNMOS\b", "NMOS_DEV", stripped)
    stripped = re.sub(r"\bPMOS\b", "PMOS_DEV", stripped)
    result = grade(stripped, task)
    assert result.credit == Credit.TOPOLOGY
    assert result.topology_recognized


def test_grade_unparseable_submission_credits_none():
    task = load_task(FIXTURE)[0]
    result = grade("this is not a netlist at all", task)
    assert result.credit == Credit.NONE
    assert not result.passed
    assert not result.iso_ok


def test_grade_wrong_topology_credits_none():
    task = load_task(FIXTURE)[0]
    wrong = """\
M1 vout vin 0 0 nmos W=10u L=1u
R1 vout vdd 1k
.MODEL nmos NMOS (LEVEL=1 VTO=1)
.END
"""
    result = grade(wrong, task)
    assert result.credit == Credit.NONE
    assert not result.passed
    assert result.parse_ok
    assert not result.iso_ok


def test_grade_wrong_sizes_credits_topology():
    """Right topology, wrong W ratio on a matched pair → TOPOLOGY (the new
    iso-passes-but-sizing-fails credit level)."""
    task = load_task(FIXTURE)[0]
    bad_sizes = """\
M1 voutn vinp ntail 0 NMOS W=10u L=1u
M2 voutp vinn ntail 0 NMOS W=10u L=1u
M3 voutn voutn vdd vdd PMOS W=40u L=1u
M4 voutp voutn vdd vdd PMOS W=20u L=1u
M5 ntail vbias 0 0 NMOS W=20u L=1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1)
.MODEL PMOS PMOS (LEVEL=1 VTO=-1)
.END
"""
    result = grade(bad_sizes, task)
    assert result.credit == Credit.TOPOLOGY
    assert not result.passed
    assert result.iso_ok
    assert not result.effective_w_ratio_ok


def test_credit_partial_when_M_ratio_fails_but_effective_w_passes(tmp_path):
    """Hand-craft a tiny task with ratio_M to exercise the partial-credit path."""
    task_dir = tmp_path / "999_mirror_1to8"
    task_dir.mkdir()
    (task_dir / "prompts.yaml").write_text(
        "prompts:\n  - id: short\n    text: 'Design a 1 to 8 NMOS current mirror.'\n"
    )
    (task_dir / "reference.cir").write_text(
        "M1 iref iref 0 0 NMOS W=10u L=1u\n"
        "M2 iout iref 0 0 NMOS W=10u L=1u M=8\n"
        ".MODEL NMOS NMOS (LEVEL=1 VTO=1)\n"
        ".END\n"
    )
    (task_dir / "ratio_groups.yaml").write_text(
        "groups:\n"
        "  - devices: [M1, M2]\n"
        "    ratio_W: [1, 8]\n"
        "    ratio_L: [1, 1]\n"
        "    ratio_M: [1, 8]\n"
    )
    (task_dir / "meta.yaml").write_text(
        'id: "999_mirror_1to8"\n'
        'category: "CurrentMirror"\n'
        'family: "simple_mirror"\n'
        'variant: "nmos_1to8"\n'
        'source: "test"\n'
        'attribution: null\n'
    )
    task = load_task(task_dir)[0]

    # Submission with correct effective W (1:8) but wide-device form (M=1)
    wide_form = (
        "M1 iref iref 0 0 NMOS W=10u L=1u\n"
        "M2 iout iref 0 0 NMOS W=80u L=1u\n"
        ".MODEL NMOS NMOS (LEVEL=1 VTO=1)\n"
        ".END\n"
    )
    result = grade(wide_form, task)
    assert result.credit == Credit.PARTIAL
    assert not result.passed   # partial is not full
    assert result.effective_w_ratio_ok
    assert result.l_ratio_ok
    assert result.m_ratio_ok is False


def test_credit_full_when_canonical_M_ratio_used(tmp_path):
    task_dir = tmp_path / "999_mirror_1to8"
    task_dir.mkdir()
    (task_dir / "prompts.yaml").write_text(
        "prompts:\n  - id: short\n    text: 'Design a 1 to 8 NMOS current mirror.'\n"
    )
    (task_dir / "reference.cir").write_text(
        "M1 iref iref 0 0 NMOS W=10u L=1u\n"
        "M2 iout iref 0 0 NMOS W=10u L=1u M=8\n"
        ".MODEL NMOS NMOS (LEVEL=1 VTO=1)\n"
        ".END\n"
    )
    (task_dir / "ratio_groups.yaml").write_text(
        "groups:\n"
        "  - devices: [M1, M2]\n"
        "    ratio_W: [1, 8]\n"
        "    ratio_L: [1, 1]\n"
        "    ratio_M: [1, 8]\n"
    )
    (task_dir / "meta.yaml").write_text(
        'id: "999_mirror_1to8"\n'
        'category: "CurrentMirror"\n'
        'family: "simple_mirror"\n'
        'variant: "nmos_1to8"\n'
        'source: "test"\n'
        'attribution: null\n'
    )
    task = load_task(task_dir)[0]

    canonical = (task_dir / "reference.cir").read_text()
    result = grade(canonical, task)
    assert result.credit == Credit.FULL
    assert result.passed
    assert result.m_ratio_ok is True


def test_cli_grade_full_prints_PASS(tmp_path, capsys):
    from circuitrubric.cli import main
    sub = tmp_path / "predicted.cir"
    sub.write_text((FIXTURE / "reference.cir").read_text())
    rc = main(["grade", "--task", str(FIXTURE), "--submission", str(sub)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.startswith("PASS 001_5t_ota_nmos.short")
    assert "effective_w_ratio_ok=True" in captured.out
    assert "l_ratio_ok=True" in captured.out
    assert "value_ratio_ok=True" in captured.out


def test_cli_grade_fail_prints_FAIL_with_exit_1(tmp_path, capsys):
    from circuitrubric.cli import main
    sub = tmp_path / "bad.cir"
    sub.write_text("M1 vout vin 0 0 nmos W=1u L=1u\n.MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n")
    rc = main(["grade", "--task", str(FIXTURE), "--submission", str(sub)])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out.startswith("FAIL")


def test_cli_grade_partial_prints_PARTIAL_with_exit_3(tmp_path, capsys):
    """Build a task with ratio_M and submit a wide-device-form netlist."""
    task_dir = tmp_path / "999_mirror_1to8"
    task_dir.mkdir()
    (task_dir / "prompts.yaml").write_text(
        "prompts:\n  - id: short\n    text: 'Design a 1 to 8 NMOS current mirror.'\n"
    )
    (task_dir / "reference.cir").write_text(
        "M1 iref iref 0 0 NMOS W=10u L=1u\n"
        "M2 iout iref 0 0 NMOS W=10u L=1u M=8\n"
        ".MODEL NMOS NMOS (LEVEL=1 VTO=1)\n"
        ".END\n"
    )
    (task_dir / "ratio_groups.yaml").write_text(
        "groups:\n"
        "  - devices: [M1, M2]\n"
        "    ratio_W: [1, 8]\n"
        "    ratio_L: [1, 1]\n"
        "    ratio_M: [1, 8]\n"
    )
    (task_dir / "meta.yaml").write_text(
        'id: "999_mirror_1to8"\n'
        'category: "CurrentMirror"\n'
        'family: "simple_mirror"\n'
        'variant: "nmos_1to8"\n'
        'source: "test"\n'
        'attribution: null\n'
    )

    sub = tmp_path / "wide.cir"
    sub.write_text(
        "M1 iref iref 0 0 NMOS W=10u L=1u\n"
        "M2 iout iref 0 0 NMOS W=80u L=1u\n"
        ".MODEL NMOS NMOS (LEVEL=1 VTO=1)\n"
        ".END\n"
    )

    from circuitrubric.cli import main
    rc = main(["grade", "--task", str(task_dir), "--submission", str(sub)])
    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out.startswith("PARTIAL")
    assert "effective_w_ratio_ok=True" in captured.out
    assert "m_ratio_ok=False" in captured.out


def test_cli_grade_with_explicit_prompt_id(tmp_path, capsys):
    from circuitrubric.cli import main
    sub = tmp_path / "predicted.cir"
    sub.write_text((FIXTURE / "reference.cir").read_text())
    rc = main(["grade", "--task", str(FIXTURE),
               "--submission", str(sub), "--prompt-id", "verbose"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "001_5t_ota_nmos.verbose" in captured.out


# ---------- Device-name independence ----------

DIFF_PAIR_FIXTURE = (
    Path(__file__).parent.parent / "fixtures"
    / "013_diff_pair_nmos_resistor_loads"
)


def test_grade_accepts_renamed_resistors():
    """Model output that uses RD1/RD2 instead of R1/R2 should still grade
    FULL: graph-iso gives the correspondence, and the ratio check uses
    that mapping rather than literal device names from ratio_groups.yaml."""
    task = load_task(DIFF_PAIR_FIXTURE)[0]
    submission = """\
* NMOS diff pair, renamed loads.
M1 voutn vinp ntail 0 NMOS W=20u L=1u
M2 voutp vinn ntail 0 NMOS W=20u L=1u
RD1 vdd voutn 10k
RD2 vdd voutp 10k
M3 ntail vbias 0 0 NMOS W=40u L=1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    result = grade(submission, task)
    assert result.iso_ok
    assert result.credit == Credit.FULL, (
        f"expected FULL credit despite renamed resistors, got "
        f"credit={result.credit} error={result.error!r}"
    )


def test_grade_renamed_mosfets_in_5t_ota():
    """Same idea but for MOSFET groups: model labels the input pair MNL/MNR
    instead of M1/M2."""
    task = load_task(FIXTURE)[0]
    submission = """\
* 5T OTA with non-standard device names.
MNL voutn vinp ntail 0 NMOS W=10u L=1u
MNR voutp vinn ntail 0 NMOS W=10u L=1u
MPL voutn voutn vdd vdd PMOS W=20u L=1u
MPR voutp voutn vdd vdd PMOS W=20u L=1u
MTAIL ntail vbias 0 0 NMOS W=20u L=1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1 KP=1.0e-4 LAMBDA=0.02)
.MODEL PMOS PMOS (LEVEL=1 VTO=-1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    result = grade(submission, task)
    assert result.iso_ok
    assert result.credit == Credit.FULL, (
        f"expected FULL credit despite renamed MOSFETs, got "
        f"credit={result.credit} error={result.error!r}"
    )


def test_grade_renamed_resistors_but_mismatched_values_credits_topology():
    """Sanity check the inverse: if the renamed devices have unmatched
    values, the grader detects the real ratio mismatch — credit is
    TOPOLOGY (iso passes, sizing/value ratio fails)."""
    task = load_task(DIFF_PAIR_FIXTURE)[0]
    submission = """\
* Diff pair with renamed BUT unequal load resistors.
M1 voutn vinp ntail 0 NMOS W=20u L=1u
M2 voutp vinn ntail 0 NMOS W=20u L=1u
RD1 vdd voutn 10k
RD2 vdd voutp 20k
M3 ntail vbias 0 0 NMOS W=40u L=1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    result = grade(submission, task)
    assert result.iso_ok
    assert result.credit == Credit.TOPOLOGY
    assert not result.value_ratio_ok


# ---------- topology_recognized / extra_devices ----------

CS_AMP_FIXTURE = (
    Path(__file__).parent.parent / "fixtures"
    / "008_cs_amp_nmos_resistor_load"
)


def test_topology_recognized_when_iso_passes():
    """Exact iso match: topology_recognized=True, extra_devices=0."""
    task = load_task(CS_AMP_FIXTURE)[0]
    correct = (CS_AMP_FIXTURE / "reference.cir").read_text()
    result = grade(correct, task)
    assert result.iso_ok
    assert result.topology_recognized is True
    assert result.extra_devices == 0


def test_topology_recognized_with_extra_devices():
    """Reference topology embedded in a circuit with extra devices.
    Iso fails (different device set), but subgraph match succeeds, so
    topology_recognized=True and extra_devices counts the extras."""
    task = load_task(CS_AMP_FIXTURE)[0]
    # 008's reference is M1 + R1. Embed those exactly + add a gate bias
    # divider (2 extra Rs) + an input coupling cap (1 extra C). 5 devices total,
    # vs reference's 2 -> extras = 3.
    submission = """\
* Mock model output: correct topology + 3 extra devices.
M1 vout vin 0 0 NMOS W=10u L=1u
R1 vout vdd 10k
RG1 vdd vbias_node 1Meg
RG2 vbias_node 0 1Meg
Cin vin_ext vin 1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    result = grade(submission, task)
    assert result.iso_ok is False
    assert result.credit == Credit.DECORATED
    assert result.topology_recognized is True, (
        "expected the reference topology to be detected as a subgraph"
    )
    assert result.extra_devices == 3


def test_grade_body_tied_input_pair_credits_partial_bulk():
    """5T OTA where the input pair has bulk tied to source (TAIL) instead of
    ground. Iso fails because the bulk net differs from the reference; bulk-
    canonicalized iso passes; the only violation is bulk=source → PARTIAL_BULK.
    """
    task = load_task(FIXTURE)[0]
    submission = """\
* 5T OTA with body-tied input pair (NMOS bulks at TAIL instead of 0).
M1 voutn vinp ntail ntail NMOS W=10u L=1u
M2 voutp vinn ntail ntail NMOS W=10u L=1u
M3 voutn voutn vdd vdd PMOS W=20u L=1u
M4 voutp voutn vdd vdd PMOS W=20u L=1u
M5 ntail vbias 0 0 NMOS W=20u L=1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1 KP=1.0e-4 LAMBDA=0.02)
.MODEL PMOS PMOS (LEVEL=1 VTO=-1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    result = grade(submission, task)
    assert result.credit == Credit.PARTIAL_BULK, (
        f"expected PARTIAL_BULK, got {result.credit}: {result.error!r}"
    )
    assert not result.iso_ok
    assert result.topology_recognized
    assert "tied bulk to source" in result.error


def test_grade_wild_bulk_does_not_credit_partial_bulk():
    """If a MOSFET's bulk is at some unexpected non-source net, that's a wild
    bulk violation and PARTIAL_BULK should not be granted — fall through to
    DECORATED (if subgraph matches) or NONE.
    """
    task = load_task(FIXTURE)[0]
    submission = """\
* 5T OTA with one input device's bulk at a stray node (not source, not gnd).
M1 voutn vinp ntail stray_bias_node NMOS W=10u L=1u
M2 voutp vinn ntail 0 NMOS W=10u L=1u
M3 voutn voutn vdd vdd PMOS W=20u L=1u
M4 voutp voutn vdd vdd PMOS W=20u L=1u
M5 ntail vbias 0 0 NMOS W=20u L=1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1 KP=1.0e-4 LAMBDA=0.02)
.MODEL PMOS PMOS (LEVEL=1 VTO=-1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    result = grade(submission, task)
    assert result.credit != Credit.PARTIAL_BULK
    assert not result.iso_ok


def test_grade_canonical_bulks_still_credits_full():
    """Sanity check: a submission with all-canonical bulks goes through the
    normal iso path and still grades FULL — the bulk fallback should not steal
    submissions that already match strictly."""
    task = load_task(FIXTURE)[0]
    correct = (FIXTURE / "reference.cir").read_text()
    result = grade(correct, task)
    assert result.credit == Credit.FULL
    assert result.iso_ok


def test_topology_not_recognized_when_wrong():
    """Submission with entirely different topology: subgraph match also fails.
    topology_recognized=False, extra_devices=None."""
    task = load_task(CS_AMP_FIXTURE)[0]
    # A PMOS CS amp with R load — wrong polarity. Different graph structure
    # because M1 is PMOS where the reference expects NMOS.
    submission = """\
* PMOS CS amp — wrong topology for an NMOS CS fixture.
M1 vout vin vdd vdd PMOS W=20u L=1u
R1 vout 0 10k
.MODEL PMOS PMOS (LEVEL=1 VTO=-1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    result = grade(submission, task)
    assert result.iso_ok is False
    assert result.topology_recognized is False
    assert result.extra_devices is None
