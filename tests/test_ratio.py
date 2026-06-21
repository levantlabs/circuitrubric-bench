import pytest

from circuitrubric.netlist import parse_netlist
from circuitrubric.ratio import check_ratio_groups, RatioCheckResult
from circuitrubric.task import RatioGroup


def _netlist(*lines):
    return parse_netlist("\n".join(lines) + "\n.MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n")


# ---- backward-compat (existing fixtures with no M) ----

def test_equality_group_passes_without_M():
    n = _netlist(
        "M1 a b c 0 nmos W=10u L=1u",
        "M2 d b c 0 nmos W=10u L=1u",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 1], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert isinstance(r, RatioCheckResult)
    assert r.effective_w_ratio_ok
    assert r.l_ratio_ok
    assert r.m_ratio_ok is None   # not declared


def test_equality_group_fails_on_unequal_W():
    n = _netlist(
        "M1 a b c 0 nmos W=10u L=1u",
        "M2 d b c 0 nmos W=20u L=1u",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 1], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert not r.effective_w_ratio_ok
    assert "W" in r.error


def test_L_checked_separately():
    n = _netlist(
        "M1 a b c 0 nmos W=10u L=1u",
        "M2 d b c 0 nmos W=10u L=2u",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 1], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert r.effective_w_ratio_ok
    assert not r.l_ratio_ok


def test_missing_device_in_netlist():
    n = _netlist("M1 a b c 0 nmos W=10u L=1u")
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 1], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert not r.effective_w_ratio_ok
    assert "M2" in r.error


# ---- effective W = W × M ----

def test_effective_w_with_M_fingers_passes_canonical():
    n = _netlist(
        "M1 iref iref 0 0 nmos W=10u L=1u",
        "M2 iout iref 0 0 nmos W=10u L=1u M=8",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 8], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert r.effective_w_ratio_ok
    assert r.l_ratio_ok
    assert r.m_ratio_ok is None


def test_effective_w_with_wide_device_passes():
    n = _netlist(
        "M1 iref iref 0 0 nmos W=10u L=1u",
        "M2 iout iref 0 0 nmos W=80u L=1u",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 8], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert r.effective_w_ratio_ok


def test_effective_w_with_mixed_W_and_M_passes():
    n = _netlist(
        "M1 iref iref 0 0 nmos W=10u L=1u",
        "M2 iout iref 0 0 nmos W=40u L=1u M=2",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 8], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert r.effective_w_ratio_ok


def test_effective_w_wrong_ratio_fails():
    n = _netlist(
        "M1 iref iref 0 0 nmos W=10u L=1u",
        "M2 iout iref 0 0 nmos W=10u L=1u M=4",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 8], ratio_L=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert not r.effective_w_ratio_ok


# ---- ratio_M (optional) ----

def test_ratio_M_passes_when_M_matches():
    n = _netlist(
        "M1 iref iref 0 0 nmos W=10u L=1u",
        "M2 iout iref 0 0 nmos W=10u L=1u M=8",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 8], ratio_L=[1, 1], ratio_M=[1, 8])]
    r = check_ratio_groups(n, groups)
    assert r.effective_w_ratio_ok
    assert r.m_ratio_ok is True


def test_ratio_M_fails_when_M_differs():
    n = _netlist(
        "M1 iref iref 0 0 nmos W=10u L=1u",
        "M2 iout iref 0 0 nmos W=80u L=1u",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 8], ratio_L=[1, 1], ratio_M=[1, 8])]
    r = check_ratio_groups(n, groups)
    assert r.effective_w_ratio_ok
    assert r.m_ratio_ok is False


def test_ratio_M_default_M_is_1():
    n = _netlist(
        "M1 iref iref 0 0 nmos W=10u L=1u",
        "M2 iout iref 0 0 nmos W=10u L=1u",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 1], ratio_L=[1, 1], ratio_M=[1, 1])]
    r = check_ratio_groups(n, groups)
    assert r.m_ratio_ok is True


# ---- fractional M is invalid ----

def test_fractional_M_raises():
    n = _netlist(
        "M1 a b c 0 nmos W=10u L=1u",
        "M2 d b c 0 nmos W=10u L=1u M=2.5",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 1], ratio_L=[1, 1])]
    with pytest.raises(ValueError, match="M must be a positive integer"):
        check_ratio_groups(n, groups)


def test_zero_or_negative_M_raises():
    n = _netlist(
        "M1 a b c 0 nmos W=10u L=1u",
        "M2 d b c 0 nmos W=10u L=1u M=0",
    )
    groups = [RatioGroup(devices=["M1", "M2"], ratio_W=[1, 1], ratio_L=[1, 1])]
    with pytest.raises(ValueError, match="M must be a positive integer"):
        check_ratio_groups(n, groups)


# ---- ratio_M length validation (pydantic) ----

def test_ratio_M_length_must_match_devices():
    with pytest.raises(Exception):
        RatioGroup(devices=["M1", "M2", "M3"], ratio_W=[1, 1, 1], ratio_L=[1, 1, 1], ratio_M=[1, 1])


# ---- resistor matching via ratio_value ----

def test_resistor_pair_matched_passes():
    """Two equal resistors with ratio_value [1,1] should pass."""
    netlist = parse_netlist("R1 a b 10k\nR2 c d 10k\n.END\n")
    groups = [RatioGroup(devices=["R1", "R2"], ratio_value=[1, 1])]
    r = check_ratio_groups(netlist, groups)
    assert r.value_ratio_ok
    assert r.error == ""


def test_resistor_pair_mismatched_fails():
    netlist = parse_netlist("R1 a b 10k\nR2 c d 20k\n.END\n")
    groups = [RatioGroup(devices=["R1", "R2"], ratio_value=[1, 1])]
    r = check_ratio_groups(netlist, groups)
    assert not r.value_ratio_ok
    assert "value" in r.error.lower()


def test_resistor_pair_ratio_2to1_passes():
    netlist = parse_netlist("R1 a b 10k\nR2 c d 20k\n.END\n")
    groups = [RatioGroup(devices=["R1", "R2"], ratio_value=[1, 2])]
    r = check_ratio_groups(netlist, groups)
    assert r.value_ratio_ok


def test_capacitor_pair_matched_passes():
    netlist = parse_netlist("C1 a b 10p\nC2 c d 10p\n.END\n")
    groups = [RatioGroup(devices=["C1", "C2"], ratio_value=[1, 1])]
    r = check_ratio_groups(netlist, groups)
    assert r.value_ratio_ok


def test_passive_missing_value_fails():
    """Synthetic case: a passive device whose value didn't parse cleanly."""
    # Construct a netlist whose R line lacks a numeric value (will be unparseable
    # and silently dropped by _parse_number's try/except, so value property absent).
    netlist = parse_netlist("R1 a b abc\nR2 c d 10k\n.END\n")
    groups = [RatioGroup(devices=["R1", "R2"], ratio_value=[1, 1])]
    r = check_ratio_groups(netlist, groups)
    assert not r.value_ratio_ok


# ---- schema validation ----

def test_ratio_group_requires_at_least_one_ratio_kind():
    """A RatioGroup with no ratio fields must fail validation."""
    with pytest.raises(Exception):
        RatioGroup(devices=["X1", "X2"])


def test_ratio_group_cannot_mix_mos_and_passive_ratios():
    """ratio_W and ratio_value together is a schema error (group must be
    homogeneous)."""
    with pytest.raises(Exception):
        RatioGroup(
            devices=["M1", "R1"],
            ratio_W=[1, 1], ratio_L=[1, 1],
            ratio_value=[1, 1],
        )


def test_ratio_value_length_must_match_devices():
    with pytest.raises(Exception):
        RatioGroup(devices=["R1", "R2", "R3"], ratio_value=[1, 1])


# ---- mixed device types in a group at check time ----

def test_check_rejects_group_with_mixed_device_types():
    """If a group's devices in the netlist span MOSFET and passive types,
    that's a structural problem the checker should flag."""
    netlist = parse_netlist(
        "R1 a b 10k\n"
        "M1 c d 0 0 nmos W=1u L=1u\n"
        ".MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n"
    )
    # Group declares ratio_value (passive-style) but the second device M1 is a MOSFET.
    groups = [RatioGroup(devices=["R1", "M1"], ratio_value=[1, 1])]
    r = check_ratio_groups(netlist, groups)
    assert not r.value_ratio_ok
    assert "incompatible" in r.error.lower() or "mismatch" in r.error.lower() or "type" in r.error.lower()
