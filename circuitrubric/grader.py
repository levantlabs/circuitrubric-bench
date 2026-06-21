"""Top-level grade() function: combines parse, graph-iso, and ratio checks
into a GradeResult with Credit (FULL/PARTIAL/NONE).

The ratio check uses the device-name correspondence established by graph
isomorphism, so a submission that renames devices (e.g. RD1/RD2 instead of
R1/R2) is still graded correctly as long as the topology matches.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from circuitrubric.graph import (
    build_bulk_canonical_graph,
    build_graph,
    build_sd_canonical_graph,
    count_devices,
    iso_device_mappings,
    isomorphic,
    subgraph_isomorphic,
)
from circuitrubric.netlist import Netlist, parse_netlist, load_netlist
from circuitrubric.ratio import RatioCheckResult, check_ratio_groups
from circuitrubric.task import RatioGroup, Task


class Credit(Enum):
    """Six-level credit ladder (best to worst):

    - FULL:         iso match + every ratio passes.
    - PARTIAL:      iso match + W/L/value ratios pass, but M ratio fails
                    (the Plan-03 case: model used W=N*W_unit instead of M=N).
    - PARTIAL_BULK: would have been iso match except MOSFET bulks are tied to
                    source (body-effect cancellation convention) instead of
                    the canonical NMOS→ground, PMOS→VDD. Iso passes after
                    bulk-canonicalization and every bulk violation is a
                    bulk=source tie (no "wild" bulk nodes).
    - TOPOLOGY:     iso match but a sizing ratio (W, L, or value) fails or is
                    unspecified. Right wiring, wrong/missing sizing.
    - DECORATED:    no iso match, but the reference topology appears as a
                    node-induced subgraph of the submission. Model knew the
                    topology but added extra devices around it.
    - NONE:         no subgraph match at all. Wrong topology.
    """

    FULL = "full"
    PARTIAL = "partial"
    PARTIAL_BULK = "partial_bulk"
    TOPOLOGY = "topology"
    DECORATED = "decorated"
    NONE = "none"


@dataclass
class GradeResult:
    credit: Credit
    parse_ok: bool
    iso_ok: bool
    effective_w_ratio_ok: bool
    l_ratio_ok: bool
    m_ratio_ok: Optional[bool]      # None when ratio_M not declared in any group
    value_ratio_ok: bool
    matched_reference: Optional[str]
    error: str
    # Diagnostic-only fields (do not affect credit). Capture whether the
    # submission contains the reference topology as a subgraph even when
    # strict iso fails ("model knew the topology but added extras").
    topology_recognized: bool = False
    extra_devices: Optional[int] = None       # devices beyond the reference; None if no match
    # S/D-equivalence diagnostics (do not affect credit; FULL stays strict).
    # sd_equiv: iso to a reference modulo MOSFET drain/source orientation
    #   (gate & bulk strict) — i.e. right wiring, drain/source maybe swapped.
    # functional_full: sd_equiv AND every ratio passes AND .MODEL types declared
    #   — would be FULL but for the non-idiomatic source/drain order.
    sd_equiv: bool = False
    functional_full: bool = False

    @property
    def passed(self) -> bool:
        return self.credit == Credit.FULL

    @property
    def ratio_ok(self) -> bool:
        """Convenience: True iff all declared ratio dimensions pass."""
        return (
            self.effective_w_ratio_ok
            and self.l_ratio_ok
            and self.value_ratio_ok
            and self.m_ratio_ok is not False
        )


_CREDIT_RANK = {
    Credit.NONE: 0,
    Credit.DECORATED: 1,
    Credit.TOPOLOGY: 2,
    Credit.PARTIAL_BULK: 3,
    Credit.PARTIAL: 4,
    Credit.FULL: 5,
}


# Net names recognized as "canonical ground" for NMOS bulk.
_GROUND_NETS = frozenset({"0", "gnd", "vss", "ground"})
# Net names recognized as "canonical VDD" for PMOS bulk.
_VDD_NETS = frozenset({"vdd"})


def _classify_bulk_violations(netlist: Netlist) -> Dict[str, str]:
    """Return {device_name: 'body_tied' | 'wild'} for each MOSFET whose bulk
    doesn't follow the canonical convention (NMOS→ground, PMOS→VDD).

    A MOSFET is 'body_tied' if its bulk == its source (the textbook
    body-effect-cancellation trick: tying bulk to source forces V_BS=0).
    Otherwise it's 'wild' (some other unexpected bulk node).
    """
    out: Dict[str, str] = {}
    for d in netlist.devices:
        if d.type not in ("nmos", "pmos"):
            continue
        bulk = d.terminals.get("bulk", "").lower()
        if d.type == "nmos" and bulk in _GROUND_NETS:
            continue
        if d.type == "pmos" and bulk in _VDD_NETS:
            continue
        source = d.terminals.get("source", "").lower()
        out[d.name] = "body_tied" if bulk == source else "wild"
    return out


def _translate_groups(
    groups: List[RatioGroup], device_map: Dict[str, str]
) -> List[RatioGroup]:
    """Rewrite each group's device list with submission-side names.

    Devices that don't appear in the mapping fall through unchanged — that
    lets the underlying ratio checker still emit a 'missing device' error
    for a genuinely-absent device rather than silently passing.
    """
    return [
        RatioGroup(
            devices=[device_map.get(d, d) for d in g.devices],
            ratio_W=g.ratio_W,
            ratio_L=g.ratio_L,
            ratio_M=g.ratio_M,
            ratio_value=g.ratio_value,
        )
        for g in groups
    ]


def _credit_from_rc(rc: RatioCheckResult) -> Credit:
    """Called when iso has matched. Derive the credit level from the ratio
    check. FULL = all ratios pass; PARTIAL = only M ratio fails; TOPOLOGY =
    any other ratio fails (W/L/value), meaning the topology is right but the
    sizing isn't (or wasn't specified).
    """
    if rc.effective_w_ratio_ok and rc.l_ratio_ok and rc.value_ratio_ok:
        return Credit.PARTIAL if rc.m_ratio_ok is False else Credit.FULL
    return Credit.TOPOLOGY


def _sd_equivalence(predicted: Netlist, task: Task) -> tuple[bool, bool]:
    """Diagnostic only: is the submission isomorphic to a reference modulo
    MOSFET source/drain orientation (gate & bulk kept strict)?

    Returns (sd_equiv, functional_full):
      - sd_equiv:        an S/D-canonical iso exists — the wiring matches with
                         drain/source possibly swapped on any device (a swap is
                         electrically null at this device level).
      - functional_full: sd_equiv AND every ratio passes AND .MODEL types were
                         declared — i.e. would be FULL but for the source/drain
                         orientation idiom.

    Never affects `credit`. Strict iso implies sd-canonical iso, so any strict
    FULL is also functional_full (sizing/types are S/D-independent).
    """
    pred_sd_g = build_sd_canonical_graph(predicted)
    sd_equiv = False
    functional_full = False
    for ref_path in task.references:
        ref_sd_g = build_sd_canonical_graph(load_netlist(ref_path))
        for device_map in iso_device_mappings(ref_sd_g, pred_sd_g):
            sd_equiv = True
            translated = _translate_groups(task.ratio_groups, device_map)
            try:
                rc = check_ratio_groups(predicted, translated)
            except ValueError:
                continue
            if rc.all_ok and not predicted.has_inferred_types:
                functional_full = True
                break
        if functional_full:
            break
    return sd_equiv, functional_full


def grade(submission_text: str, task: Task) -> GradeResult:
    # 1. Parse
    try:
        predicted = parse_netlist(submission_text)
    except Exception as e:
        return GradeResult(
            credit=Credit.NONE,
            parse_ok=False, iso_ok=False,
            effective_w_ratio_ok=False, l_ratio_ok=False, m_ratio_ok=None,
            value_ratio_ok=False,
            matched_reference=None,
            error=f"parse failed: {e}",
        )

    pred_g = build_graph(predicted)
    n_pred_devices = count_devices(pred_g)

    # Additive S/D-equivalence diagnostics — computed once, never affect credit.
    sd_equiv, functional_full = _sd_equivalence(predicted, task)

    # Pre-load each reference's graph; we use it for both iso checks and
    # the diagnostic-only subgraph check.
    ref_graphs = [
        (ref_path, build_graph(load_netlist(ref_path)))
        for ref_path in task.references
    ]

    # 2-3. For each reference whose graph is isomorphic, iterate over all
    # valid device-name mappings and run the ratio check under each.
    # Accept the best credit any mapping achieves; pick a representative
    # mapping for the error message if none reach FULL.
    best: Optional[tuple[int, RatioCheckResult, str, int]] = None
    matched_any_iso = False
    for ref_path, ref_g in ref_graphs:
        any_mapping = False
        for device_map in iso_device_mappings(ref_g, pred_g):
            any_mapping = True
            matched_any_iso = True
            translated = _translate_groups(task.ratio_groups, device_map)
            try:
                rc = check_ratio_groups(predicted, translated)
            except ValueError as e:
                # Fractional M (or similar structural error) — same for every
                # mapping; surface immediately.
                return GradeResult(
                    credit=Credit.NONE,
                    parse_ok=True, iso_ok=True,
                    effective_w_ratio_ok=False, l_ratio_ok=False,
                    m_ratio_ok=None, value_ratio_ok=False,
                    matched_reference=ref_path.name,
                    error=str(e),
                    topology_recognized=True,
                    extra_devices=0,
                    sd_equiv=sd_equiv,
                    functional_full=functional_full,
                )
            credit = _credit_from_rc(rc)
            rank = _CREDIT_RANK[credit]
            extras = n_pred_devices - count_devices(ref_g)
            if best is None or rank > best[0]:
                best = (rank, rc, ref_path.name, extras)
            if credit == Credit.FULL:
                break
        if best is not None and best[0] == _CREDIT_RANK[Credit.FULL]:
            break
        # If this reference matched no mappings, try the next reference.
        if not any_mapping:
            continue

    if not matched_any_iso:
        # Strict iso failed. Before falling back to subgraph (DECORATED/NONE),
        # try bulk-canonicalized iso: if the only obstacle to a match is the
        # bulk-node convention, and every bulk violation is a bulk=source tie
        # (a recognized body-effect-cancellation idiom), grade as PARTIAL_BULK.
        pred_bulk_g = build_bulk_canonical_graph(predicted)
        for ref_path, _ in ref_graphs:
            ref_nl = load_netlist(ref_path)
            ref_bulk_g = build_bulk_canonical_graph(ref_nl)
            if not isomorphic(pred_bulk_g, ref_bulk_g):
                continue
            violations = _classify_bulk_violations(predicted)
            # iso-modulo-bulk passed with no violations would imply normal iso
            # already passed, so we expect violations to be non-empty here.
            if violations and all(v == "body_tied" for v in violations.values()):
                return GradeResult(
                    # cap at TOPOLOGY if types were inferred (no .MODEL cards)
                    credit=Credit.TOPOLOGY if predicted.has_inferred_types else Credit.PARTIAL_BULK,
                    parse_ok=True, iso_ok=False,
                    effective_w_ratio_ok=False, l_ratio_ok=False,
                    m_ratio_ok=None, value_ratio_ok=False,
                    matched_reference=ref_path.name,
                    error=(f"topology matches modulo bulk; "
                           f"{len(violations)} device(s) tied bulk to source"),
                    topology_recognized=True,
                    extra_devices=0,
                    sd_equiv=sd_equiv,
                    functional_full=functional_full,
                )
            # Any wild bulk → no PARTIAL_BULK; fall through to subgraph.
            break

        # Subgraph check: does the reference topology appear as a node-induced
        # subgraph of the submission ("model knew the topology but added extras")?
        topology_recognized = False
        extra_devices: Optional[int] = None
        subgraph_matched_ref: Optional[str] = None
        for ref_path, ref_g in ref_graphs:
            if subgraph_isomorphic(pred_g, ref_g):
                topology_recognized = True
                extra_devices = n_pred_devices - count_devices(ref_g)
                subgraph_matched_ref = ref_path.name
                break
        return GradeResult(
            credit=Credit.DECORATED if topology_recognized else Credit.NONE,
            parse_ok=True, iso_ok=False,
            effective_w_ratio_ok=False, l_ratio_ok=False, m_ratio_ok=None,
            value_ratio_ok=False,
            matched_reference=subgraph_matched_ref,
            error=("reference appears as subgraph of submission with "
                   f"{extra_devices} extra device(s); strict iso failed")
                   if topology_recognized
                   else "no blessed reference is graph-isomorphic to submission",
            topology_recognized=topology_recognized,
            extra_devices=extra_devices,
            sd_equiv=sd_equiv,
            functional_full=functional_full,
        )

    rank, rc, matched_ref, extras = best
    credit = _credit_from_rc(rc)
    # A submission that omitted .MODEL cards (types inferred from device names) is
    # structurally recognizable but not a complete/FULL answer: cap at TOPOLOGY.
    if predicted.has_inferred_types and _CREDIT_RANK[credit] > _CREDIT_RANK[Credit.TOPOLOGY]:
        credit = Credit.TOPOLOGY
    return GradeResult(
        credit=credit,
        parse_ok=True, iso_ok=True,
        effective_w_ratio_ok=rc.effective_w_ratio_ok,
        l_ratio_ok=rc.l_ratio_ok,
        m_ratio_ok=rc.m_ratio_ok,
        value_ratio_ok=rc.value_ratio_ok,
        matched_reference=matched_ref,
        error=rc.error,
        topology_recognized=True,
        extra_devices=extras,
        sd_equiv=sd_equiv,
        functional_full=functional_full,
    )
