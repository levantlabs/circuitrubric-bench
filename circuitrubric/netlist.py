"""Permissive ngspice parser. Produces a Netlist of devices + nets.

Goal: extract enough structure for graph isomorphism and ratio-group checks.
Not a strict simulator-grade parser; we silently skip comments, .MODEL bodies
(we only use the type from the model name), .OP/.END/.control blocks, and
any line we don't recognize.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

import re


SUFFIX = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3,
          "k": 1e3, "meg": 1e6, "g": 1e9, "t": 1e12}


def _parse_number(s: str) -> float:
    s = s.strip().lower()
    m = re.match(r"^([-+]?\d*\.?\d+(?:e[-+]?\d+)?)([a-z]+)?$", s)
    if not m:
        raise ValueError(f"cannot parse number {s!r}")
    val = float(m.group(1))
    suf = m.group(2)
    if suf:
        if suf == "meg":
            val *= SUFFIX["meg"]
        elif suf in SUFFIX:
            val *= SUFFIX[suf]
        else:
            raise ValueError(f"unknown suffix {suf!r} in {s!r}")
    return val


@dataclass
class Device:
    name: str
    type: str                           # e.g. "nmos", "pmos", "r", "c", "v", "i"
    terminals: Dict[str, str]           # terminal name → net name
    properties: Dict[str, float] = field(default_factory=dict)


@dataclass
class Netlist:
    devices: List[Device] = field(default_factory=list)
    nets: Set[str] = field(default_factory=set)
    # True if any MOSFET type was inferred from its model NAME (e.g. "PMOS_MODEL")
    # because no .MODEL card declared it. The topology is still recognized, but the
    # grader caps such a submission at TOPOLOGY (no .MODEL cards => not a FULL answer).
    has_inferred_types: bool = False


_MOSFET_TERMINALS = ("drain", "gate", "source", "bulk")


def parse_netlist(text: str) -> Netlist:
    netlist = Netlist()
    model_type: Dict[str, str] = {}

    type_map = {"R": "r", "C": "c", "V": "v", "I": "i", "L": "l"}

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        upper = line.upper()
        if upper.startswith(".MODEL"):
            parts = line.split()
            if len(parts) >= 3:
                # type may have params attached with no space: "NMOS(VTO=...)".
                # Split on "(" so both "NMOS" and "NMOS(VTO=1)" resolve.
                name, kind = parts[1], parts[2].upper().split("(", 1)[0]
                if kind in ("NMOS", "PMOS"):
                    model_type[name.lower()] = kind.lower()
            continue
        if upper.startswith("."):
            continue
        prefix = upper[0]
        if prefix == "M":
            parts = line.split()
            if len(parts) < 6:
                continue
            name = parts[0]
            # SPICE node names are case-insensitive: normalize so e.g. VDD == vdd.
            terminals = dict(zip(_MOSFET_TERMINALS, (p.lower() for p in parts[1:5])))
            model_name = parts[5].lower()
            props: Dict[str, float] = {}
            for tok in parts[6:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        props[k.lower()] = _parse_number(v)
                    except ValueError:
                        pass
            netlist.devices.append(
                Device(name=name, type=model_name, terminals=terminals, properties=props)
            )
            for net in terminals.values():
                netlist.nets.add(net)
            continue
        if prefix in type_map:
            parts = line.split()
            if len(parts) < 3:
                continue
            name = parts[0]
            n1, n2 = parts[1].lower(), parts[2].lower()  # case-insensitive nets (see above)
            # handle "V1 a 0 DC 5" form (value in parts[4]) vs "R1 a b 1k" (value in parts[3])
            if len(parts) >= 5 and parts[3].upper() == "DC":
                raw_val = parts[4]
            elif len(parts) >= 4:
                raw_val = parts[3]
            else:
                raw_val = None
            props: Dict[str, float] = {}
            if raw_val is not None:
                try:
                    props["value"] = _parse_number(raw_val)
                except ValueError:
                    pass
            netlist.devices.append(
                Device(name=name, type=type_map[prefix],
                       terminals={"n1": n1, "n2": n2}, properties=props)
            )
            netlist.nets.add(n1)
            netlist.nets.add(n2)
            continue

    # second pass: resolve model_name → type
    _CANON = {"nmos", "pmos", "r", "c", "l", "v", "i"}
    for d in netlist.devices:
        if d.type in model_type:
            d.type = model_type[d.type]
        elif d.type not in _CANON:
            # MOSFET model never declared via a .MODEL card. If the name itself
            # unambiguously encodes polarity (e.g. "PMOS_MODEL", "nmos_dev"),
            # infer the type so the topology is still recognized, and flag it so
            # the grader caps credit at TOPOLOGY (no .MODEL cards => not FULL).
            if "pmos" in d.type:
                d.type = "pmos"; netlist.has_inferred_types = True
            elif "nmos" in d.type:
                d.type = "nmos"; netlist.has_inferred_types = True

    return netlist


def load_netlist(path) -> Netlist:
    from pathlib import Path as _P
    return parse_netlist(_P(path).read_text())
