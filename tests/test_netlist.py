from circuitrubric.netlist import parse_netlist, Device, _parse_number
import pytest


def test_parse_mosfet_line():
    text = """\
M1 vout vin gnd gnd nmos W=10u L=1u
.MODEL nmos NMOS (LEVEL=1 VTO=1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    netlist = parse_netlist(text)
    assert len(netlist.devices) == 1
    d = netlist.devices[0]
    assert d.name == "M1"
    assert d.type == "nmos"
    assert d.terminals == {
        "drain": "vout",
        "gate": "vin",
        "source": "gnd",
        "bulk": "gnd",
    }
    assert d.properties["w"] == pytest.approx(10e-6)
    assert d.properties["l"] == pytest.approx(1e-6)


def test_parse_mosfet_pmos_via_model():
    text = """\
M1 vout vin vdd vdd pmos W=20u L=1u
.MODEL pmos PMOS (LEVEL=1 VTO=-1 KP=1.0e-4 LAMBDA=0.02)
.END
"""
    netlist = parse_netlist(text)
    assert netlist.devices[0].type == "pmos"


def test_parse_number_rejects_unknown_suffix():
    with pytest.raises(ValueError):
        _parse_number("1x")
    with pytest.raises(ValueError):
        _parse_number("5q")


def test_parse_number_rejects_incomplete_exponent():
    # "10e" looks like a mantissa "10" with suffix "e" — must reject because
    # "e" is not in SUFFIX. Catches typos like W=10e (missing exponent digits).
    with pytest.raises(ValueError):
        _parse_number("10e")


def test_parse_number_accepts_valid_suffixes():
    assert _parse_number("10u") == pytest.approx(10e-6)
    assert _parse_number("1k") == pytest.approx(1e3)
    assert _parse_number("1meg") == pytest.approx(1e6)
    assert _parse_number("1.0e-4") == pytest.approx(1e-4)


def test_parse_passives_and_sources():
    text = """\
R1 a b 1k
C1 b 0 10p
V1 a 0 5
I1 0 a DC 1m
.END
"""
    n = parse_netlist(text)
    types = sorted(d.type for d in n.devices)
    assert types == ["c", "i", "r", "v"]
    r1 = next(d for d in n.devices if d.name == "R1")
    assert r1.terminals == {"n1": "a", "n2": "b"}
    assert r1.properties["value"] == 1e3
    c1 = next(d for d in n.devices if d.name == "C1")
    assert c1.properties["value"] == 10e-12


from pathlib import Path

FIXTURE = Path(__file__).parent.parent / "fixtures" / "001_5t_ota_nmos"


def test_parse_fixture_reference():
    text = (FIXTURE / "reference.cir").read_text()
    n = parse_netlist(text)
    assert len(n.devices) == 5
    types = sorted(d.type for d in n.devices)
    assert types == ["nmos", "nmos", "nmos", "pmos", "pmos"]
    # nets present
    assert "voutn" in n.nets
    assert "voutp" in n.nets
    assert "ntail" in n.nets
    assert "vdd" in n.nets
    assert "vbias" in n.nets
    # M1's gate is vinp
    m1 = next(d for d in n.devices if d.name == "M1")
    assert m1.terminals["gate"] == "vinp"


def test_parse_ignores_garbage_and_comments():
    text = """\
* this is a comment
M1 vout vin 0 0 nmos W=1u L=1u
this line is garbage
.SUBCKT foo a b
foobar
.ENDS
.MODEL nmos NMOS (LEVEL=1 VTO=1)
.END
"""
    n = parse_netlist(text)
    assert len(n.devices) == 1
    assert n.devices[0].type == "nmos"


from circuitrubric.netlist import load_netlist


def test_load_netlist_from_path():
    n = load_netlist(FIXTURE / "reference.cir")
    assert len(n.devices) == 5


def test_parse_mosfet_with_non_numeric_property_is_permissive():
    """The parser docstring promises permissive handling. A non-numeric MOSFET
    instance parameter (e.g., AD=abc) should NOT cause the line to be rejected
    or the parse to fail — the property is silently dropped."""
    text = """\
M1 vout vin 0 0 nmos W=10u L=1u AD=abc M=2
.MODEL nmos NMOS (LEVEL=1 VTO=1)
.END
"""
    n = parse_netlist(text)
    assert len(n.devices) == 1
    d = n.devices[0]
    assert d.name == "M1"
    assert d.type == "nmos"
    # numeric properties present:
    assert d.properties["w"] == pytest.approx(10e-6)
    assert d.properties["l"] == pytest.approx(1e-6)
    assert d.properties["m"] == pytest.approx(2.0)
    # non-numeric AD silently skipped:
    assert "ad" not in d.properties


def test_net_names_case_insensitive():
    # SPICE node names are case-insensitive: VDD, Vdd, vdd are the same net.
    nl = parse_netlist(
        "M1 VOUT vin 0 VDD PMOS W=10u L=1u\nR1 vdd VOUT 10k\n"
        ".MODEL PMOS PMOS (LEVEL=1)\n.END"
    )
    m = next(d for d in nl.devices if d.name == "M1")
    assert m.terminals == {"drain": "vout", "gate": "vin", "source": "0", "bulk": "vdd"}
    r = next(d for d in nl.devices if d.name == "R1")
    assert set(r.terminals.values()) == {"vdd", "vout"}
    assert "VDD" not in nl.nets and "vdd" in nl.nets and "VOUT" not in nl.nets


def test_model_type_resolves_with_attached_params():
    # ".MODEL MN NMOS(VTO=...)" — params attached with NO space before "(".
    # The type must still resolve to nmos (common style; e.g. GLM/Llama emit it).
    nl = parse_netlist(
        "M1 vout vin 0 0 MN W=10u L=1u\nRL vdd vout 10k\n"
        ".MODEL MN NMOS(VTO=0.7 KP=100u)\n.END"
    )
    m = next(d for d in nl.devices if d.name == "M1")
    assert m.type == "nmos"
