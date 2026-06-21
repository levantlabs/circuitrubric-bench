from pathlib import Path

from circuitrubric.graph import build_graph, isomorphic
from circuitrubric.netlist import load_netlist

FIXTURE = Path(__file__).parent.parent / "fixtures" / "001_5t_ota_nmos"


def test_self_isomorphic():
    n = load_netlist(FIXTURE / "reference.cir")
    g = build_graph(n)
    assert isomorphic(g, g)


def test_renamed_nets_still_isomorphic():
    text = (FIXTURE / "reference.cir").read_text()
    renamed = (text
               .replace("voutn", "outA")
               .replace("voutp", "outB")
               .replace("ntail", "tailX")
               .replace("vbias", "biasZ"))
    n1 = load_netlist(FIXTURE / "reference.cir")
    from circuitrubric.netlist import parse_netlist
    n2 = parse_netlist(renamed)
    assert isomorphic(build_graph(n1), build_graph(n2))


def test_different_topology_not_isomorphic():
    n1 = load_netlist(FIXTURE / "reference.cir")
    # swap M1 and M3 terminals to break the topology
    different = """\
M1 vout vin 0 0 nmos W=1u L=1u
.MODEL nmos NMOS (LEVEL=1 VTO=1)
.END
"""
    from circuitrubric.netlist import parse_netlist
    n2 = parse_netlist(different)
    assert not isomorphic(build_graph(n1), build_graph(n2))


def test_nmos_input_vs_pmos_input_not_isomorphic():
    """The same 5T-OTA wiring but with NMOS input devices swapped for PMOS
    should NOT be considered isomorphic, since failure mode B includes
    'right shape, wrong polarity'."""
    nmos_text = (FIXTURE / "reference.cir").read_text()
    pmos_text = """\
* 5T OTA, PMOS-input pair, NMOS current-mirror load, PMOS tail
M1 voutn vinp ntail vdd PMOS W=10u L=1u
M2 voutp vinn ntail vdd PMOS W=10u L=1u
M3 voutn voutn 0 0 NMOS W=20u L=1u
M4 voutp voutn 0 0 NMOS W=20u L=1u
M5 ntail vbias vdd vdd PMOS W=20u L=1u
.MODEL NMOS NMOS (LEVEL=1 VTO=1)
.MODEL PMOS PMOS (LEVEL=1 VTO=-1)
.END
"""
    from circuitrubric.netlist import parse_netlist
    g_nmos = build_graph(parse_netlist(nmos_text))
    g_pmos = build_graph(parse_netlist(pmos_text))
    assert not isomorphic(g_nmos, g_pmos)


def test_resistor_terminal_swap_is_isomorphic():
    """A resistor's two terminals are physically symmetric — the grader should
    accept either ordering."""
    canonical_text = "R1 a b 1k\n.END\n"
    swapped_text = "R1 b a 1k\n.END\n"
    from circuitrubric.netlist import parse_netlist
    g1 = build_graph(parse_netlist(canonical_text))
    g2 = build_graph(parse_netlist(swapped_text))
    assert isomorphic(g1, g2)


def test_capacitor_terminal_swap_is_isomorphic():
    from circuitrubric.netlist import parse_netlist
    canonical_text = "C1 a b 10p\n.END\n"
    swapped_text = "C1 b a 10p\n.END\n"
    g1 = build_graph(parse_netlist(canonical_text))
    g2 = build_graph(parse_netlist(swapped_text))
    assert isomorphic(g1, g2)


def test_inductor_terminal_swap_is_isomorphic():
    from circuitrubric.netlist import parse_netlist
    canonical_text = "L1 a b 1n\n.END\n"
    swapped_text = "L1 b a 1n\n.END\n"
    g1 = build_graph(parse_netlist(canonical_text))
    g2 = build_graph(parse_netlist(swapped_text))
    assert isomorphic(g1, g2)


def test_voltage_source_polarity_with_anchor_is_NOT_isomorphic():
    """V source polarity matters. With a MOSFET as an anchor (its terminals
    are distinguishable), a polarity flip on V1 produces a graph-iso-distinct
    netlist — VF2 cannot relabel the nets in a way that preserves both
    M1.source=0 and V1.n1=vdd simultaneously."""
    from circuitrubric.netlist import parse_netlist
    canonical = (
        "V1 vdd 0 5\n"
        "M1 vout vin 0 0 nmos W=10u L=1u\n"
        ".MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n"
    )
    swapped = (
        "V1 0 vdd 5\n"
        "M1 vout vin 0 0 nmos W=10u L=1u\n"
        ".MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n"
    )
    g1 = build_graph(parse_netlist(canonical))
    g2 = build_graph(parse_netlist(swapped))
    assert not isomorphic(g1, g2)


def test_voltage_source_alone_is_topologically_symmetric():
    """A V1 between two unconstrained nets has no asymmetry the graph can see,
    so graph-iso accepts a polarity flip. Polarity is only detectable when
    other devices anchor the nets. This documents the limitation."""
    from circuitrubric.netlist import parse_netlist
    canonical_text = "V1 a 0 5\n.END\n"
    swapped_text = "V1 0 a 5\n.END\n"
    g1 = build_graph(parse_netlist(canonical_text))
    g2 = build_graph(parse_netlist(swapped_text))
    assert isomorphic(g1, g2)


def test_mosfet_drain_source_swap_STILL_NOT_isomorphic():
    """SPICE position 1 is drain by language convention. Even though level=1
    is electrically symmetric, the syntactic distinction is enforced."""
    from circuitrubric.netlist import parse_netlist
    canonical_text = (
        "M1 vout vin 0 0 nmos W=10u L=1u\n"
        ".MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n"
    )
    swapped_text = (
        "M1 0 vin vout 0 nmos W=10u L=1u\n"
        ".MODEL nmos NMOS (LEVEL=1 VTO=1)\n.END\n"
    )
    g1 = build_graph(parse_netlist(canonical_text))
    g2 = build_graph(parse_netlist(swapped_text))
    assert not isomorphic(g1, g2)
