"""Verify ratio groups declared in a task against a parsed netlist.

A ratio group is homogeneous in device type:
- MOSFET groups (nmos/pmos): declare `ratio_W` (required), `ratio_L`
  (required), `ratio_M` (optional). Effective W = W × M (default M=1);
  fractional/non-positive M raises ValueError.
- Passive groups (r/c/l): declare `ratio_value` (required). Matches the
  `value` property captured by the parser.

Tolerance: ±1% per ratio.
"""

from dataclasses import dataclass
from typing import List, Optional

from circuitrubric.netlist import Netlist
from circuitrubric.task import RatioGroup


TOLERANCE = 0.01  # ±1%

_MOSFET_TYPES = {"nmos", "pmos"}
_PASSIVE_TYPES = {"r", "c", "l"}


@dataclass
class RatioCheckResult:
    effective_w_ratio_ok: bool
    l_ratio_ok: bool
    m_ratio_ok: Optional[bool]
    value_ratio_ok: bool
    error: str

    @property
    def all_ok(self) -> bool:
        return (
            self.effective_w_ratio_ok
            and self.l_ratio_ok
            and self.value_ratio_ok
            and self.m_ratio_ok is not False
        )


def _device_by_name(netlist: Netlist, name: str):
    for d in netlist.devices:
        if d.name.lower() == name.lower():
            return d
    return None


def _validated_m(device) -> int:
    raw = device.properties.get("m", 1)
    if raw != int(raw) or raw <= 0:
        raise ValueError(
            f"M must be a positive integer for device {device.name}, got {raw}"
        )
    return int(raw)


def _ratio_matches(values: List[float], ratios: List[float]) -> bool:
    v0, r0 = values[0], ratios[0]
    if v0 == 0:
        return all(v == 0 for v in values)
    for v, r in zip(values[1:], ratios[1:]):
        expected = v0 * (r / r0)
        if expected == 0:
            if v != 0:
                return False
            continue
        err = abs(v - expected) / abs(expected)
        if err > TOLERANCE:
            return False
    return True


def check_ratio_groups(
    netlist: Netlist, groups: List[RatioGroup]
) -> RatioCheckResult:
    effective_w_ok = True
    l_ok = True
    m_ok: Optional[bool] = None
    value_ok = True
    error = ""

    for group in groups:
        devices = [_device_by_name(netlist, n) for n in group.devices]
        for name, dev in zip(group.devices, devices):
            if dev is None:
                effective_w_ok = False
                value_ok = False
                if not error:
                    error = f"ratio group references missing device {name!r}"

        if any(d is None for d in devices):
            continue

        device_types = {d.type for d in devices}
        is_mos = device_types <= _MOSFET_TYPES
        is_passive = device_types <= _PASSIVE_TYPES

        if not is_mos and not is_passive:
            value_ok = False
            effective_w_ok = False
            if not error:
                error = (
                    f"ratio group {group.devices} has incompatible device "
                    f"types: {sorted(device_types)}"
                )
            continue

        if is_mos:
            if group.ratio_W is None or group.ratio_L is None:
                effective_w_ok = False
                if not error:
                    error = (
                        f"MOSFET group {group.devices} missing ratio_W/ratio_L"
                    )
                continue
            m_values = [_validated_m(d) for d in devices]
            ws = [d.properties.get("w") for d in devices]
            ls = [d.properties.get("l") for d in devices]
            for name, w, l in zip(group.devices, ws, ls):
                if w is None:
                    effective_w_ok = False
                    if not error:
                        error = f"device {name} missing W"
                if l is None:
                    l_ok = False
                    if not error:
                        error = f"device {name} missing L"
            if all(w is not None for w in ws):
                effective_ws = [w * m for w, m in zip(ws, m_values)]
                if not _ratio_matches(effective_ws, group.ratio_W):
                    effective_w_ok = False
                    if not error:
                        error = f"W (effective W*M) ratio mismatch in group {group.devices}"
            if all(l is not None for l in ls):
                if not _ratio_matches(ls, group.ratio_L):
                    l_ok = False
                    if not error:
                        error = f"L ratio mismatch in group {group.devices}"
            if group.ratio_M is not None:
                this_m_ok = _ratio_matches(
                    [float(m) for m in m_values], group.ratio_M
                )
                m_ok = (m_ok is None or m_ok) and this_m_ok
                if not this_m_ok and not error:
                    error = f"M ratio mismatch in group {group.devices}"
        elif is_passive:
            if group.ratio_value is None:
                value_ok = False
                if not error:
                    error = (
                        f"passive group {group.devices} missing ratio_value"
                    )
                continue
            values = [d.properties.get("value") for d in devices]
            for name, v in zip(group.devices, values):
                if v is None:
                    value_ok = False
                    if not error:
                        error = f"device {name} missing value"
            if all(v is not None for v in values):
                if not _ratio_matches(values, group.ratio_value):
                    value_ok = False
                    if not error:
                        error = f"value ratio mismatch in group {group.devices}"

    return RatioCheckResult(
        effective_w_ratio_ok=effective_w_ok,
        l_ratio_ok=l_ok,
        m_ratio_ok=m_ok,
        value_ratio_ok=value_ok,
        error=error,
    )
