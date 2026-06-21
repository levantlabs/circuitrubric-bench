"""Convert a Netlist into a typed bipartite graph (devices × nets) and check
isomorphism with networkx's VF2 algorithm.

Graph construction:
- One node per net, labeled `kind="net"`.
- One node per device, labeled `kind="device"` and `type=<device.type>`.
- One edge per device-terminal, labeled `terminal=<terminal_name>`.

Two graphs match iff there's an isomorphism that respects:
- node kind ("net" only maps to "net", "device" to "device")
- device node `type` attribute
- edge `terminal` attribute

Terminal symmetry: two-terminal passives (R, C, L) have physically
interchangeable terminals, so n1 ↔ n2 swap is accepted as iso-equivalent.
MOSFET drain/source positions and V/I polarity are kept strict.
"""

from typing import Dict, Iterator

import networkx as nx
from networkx.algorithms import isomorphism

from circuitrubric.netlist import Netlist


# Terminal symmetry classes. Devices listed here have terminals that are
# physically interchangeable; we collapse them to a shared label so the
# graph-iso check accepts either ordering.
#
# MOSFETs are deliberately NOT included: SPICE syntax fixes position 1 as
# drain and position 3 as source, and even at level=1 the convention is
# treated as meaningful (drain ≠ source for grading purposes).
#
# Voltage and current sources are also not included: polarity (n1 = positive
# terminal) is meaningful.
_TERMINAL_CANONICAL = {
    "r": {"n1": "passive_term", "n2": "passive_term"},
    "c": {"n1": "passive_term", "n2": "passive_term"},
    "l": {"n1": "passive_term", "n2": "passive_term"},
}


def _canonical_terminal(device_type: str, terminal: str) -> str:
    return _TERMINAL_CANONICAL.get(device_type, {}).get(terminal, terminal)


def build_graph(netlist: Netlist) -> nx.Graph:
    g = nx.MultiGraph()
    for net in netlist.nets:
        g.add_node(("net", net), kind="net")
    for d in netlist.devices:
        g.add_node(("dev", d.name), kind="device", type=d.type)
        for term, net in d.terminals.items():
            label = _canonical_terminal(d.type, term)
            g.add_edge(("dev", d.name), ("net", net), terminal=label)
    return g


def _node_match(n1, n2):
    if n1["kind"] != n2["kind"]:
        return False
    if n1["kind"] == "device":
        return n1.get("type") == n2.get("type")
    return True  # nets match any net


def _edge_match(e1, e2):
    # MultiGraph edge dicts: {0: {'terminal': 'drain'}, 1: {...}}; treat
    # parallel edges as a multiset of terminal labels.
    t1 = sorted(d["terminal"] for d in e1.values())
    t2 = sorted(d["terminal"] for d in e2.values())
    return t1 == t2


def isomorphic(g1: nx.Graph, g2: nx.Graph) -> bool:
    gm = isomorphism.MultiGraphMatcher(
        g1, g2, node_match=_node_match, edge_match=_edge_match
    )
    return gm.is_isomorphic()


def subgraph_isomorphic(
    g_sub: nx.MultiGraph, g_ref: nx.MultiGraph
) -> bool:
    """True iff the reference is isomorphic to a node-induced subgraph of the
    submission. Used to detect "the model knew the topology but added extra
    devices" — distinct from strict isomorphism (which requires identical
    device sets).

    Note: device nodes carry fixed terminal arity (each MOSFET has four
    terminal edges, each passive has two), so a node-induced subgraph match
    here means the submission contains every reference device with the
    correct connectivity, embedded in some larger circuit whose extra devices
    touch the same nets via additional (non-matched) edges.
    """
    gm = isomorphism.MultiGraphMatcher(
        g_sub, g_ref, node_match=_node_match, edge_match=_edge_match
    )
    return gm.subgraph_is_isomorphic()


def count_devices(g: nx.MultiGraph) -> int:
    """Number of device nodes in a topology graph."""
    return sum(1 for n, attrs in g.nodes(data=True) if attrs.get("kind") == "device")


# Sentinel net names used by build_bulk_canonical_graph; chosen so they cannot
# collide with any net name a user-written netlist would produce.
_NMOS_BULK_NET = "__nmos_bulk__"
_PMOS_BULK_NET = "__pmos_bulk__"


def build_bulk_canonical_graph(netlist: Netlist) -> nx.MultiGraph:
    """Like build_graph but every MOSFET's bulk terminal is redirected to a
    single canonical sentinel net (one for NMOS, one for PMOS).

    This lets the grader check "iso modulo bulk convention": two netlists are
    canonical-iso iff they would be iso under any consistent renaming of bulk
    nets. Used to detect the case where the topology is correct except for a
    bulk-convention violation (typically bulk-tied-to-source for body-effect
    cancellation), so we can grade those as PARTIAL_BULK rather than NONE.
    """
    g = nx.MultiGraph()
    canonical_bulk_used = {"nmos": False, "pmos": False}
    for net in netlist.nets:
        g.add_node(("net", net), kind="net")
    for d in netlist.devices:
        g.add_node(("dev", d.name), kind="device", type=d.type)
        for term, net in d.terminals.items():
            if d.type in ("nmos", "pmos") and term == "bulk":
                canonical = _NMOS_BULK_NET if d.type == "nmos" else _PMOS_BULK_NET
                if not canonical_bulk_used[d.type]:
                    g.add_node(("net", canonical), kind="net")
                    canonical_bulk_used[d.type] = True
                net = canonical
            label = _canonical_terminal(d.type, term)
            g.add_edge(("dev", d.name), ("net", net), terminal=label)
    return g


# Shared label used by build_sd_canonical_graph for a MOSFET's drain/source.
_MOS_DS_TERMINAL = "mos_ds"


def build_sd_canonical_graph(netlist: Netlist) -> nx.MultiGraph:
    """Like build_graph but every MOSFET's drain and source terminals share a
    single canonical edge label, so the iso check treats drain/source as
    interchangeable. Gate and bulk stay strict.

    A 4-terminal MOSFET's drain and source are physically symmetric (at this
    device level, swapping them yields the identical device), so a submission
    that writes a transistor's drain/source in the opposite order is
    electrically equivalent. This builder lets the grader report "iso modulo
    source/drain orientation" as a diagnostic WITHOUT relaxing the strict-iso
    credit ladder — FULL still requires the idiomatic drain/source order.
    """
    g = nx.MultiGraph()
    for net in netlist.nets:
        g.add_node(("net", net), kind="net")
    for d in netlist.devices:
        g.add_node(("dev", d.name), kind="device", type=d.type)
        for term, net in d.terminals.items():
            if d.type in ("nmos", "pmos") and term in ("drain", "source"):
                label = _MOS_DS_TERMINAL
            else:
                label = _canonical_terminal(d.type, term)
            g.add_edge(("dev", d.name), ("net", net), terminal=label)
    return g


def iso_device_mappings(
    g_ref: nx.MultiGraph, g_sub: nx.MultiGraph
) -> Iterator[Dict[str, str]]:
    """Yield {ref_device_name -> sub_device_name} for each valid isomorphism.

    If the graphs are not isomorphic, yields nothing. Net nodes are present in
    the underlying VF2 mapping but stripped here — callers only need the
    device-name correspondence for ratio-group translation.

    Most fixtures yield a unique mapping; symmetric topologies (matched diff
    pair, cascode left/right swap) yield 2-4 equivalent mappings.
    """
    gm = isomorphism.MultiGraphMatcher(
        g_ref, g_sub, node_match=_node_match, edge_match=_edge_match
    )
    if not gm.is_isomorphic():
        return
    for mapping in gm.isomorphisms_iter():
        yield {
            ref_node[1]: sub_node[1]
            for ref_node, sub_node in mapping.items()
            if ref_node[0] == "dev"
        }
