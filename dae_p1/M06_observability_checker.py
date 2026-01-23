
from __future__ import annotations
from typing import List, Optional
from .M00_common import ChangeEventCard, ObservabilityResult

class ObservabilityChecker:
    """
    Determines if minimum referenceable artifacts exist for a change/event.
    """
    MIN_REFS = ["origin_hint", "change_ref", "version_refs"]

    def check_event(self, ev: ChangeEventCard) -> ObservabilityResult:
        missing: List[str] = []
        if not ev.origin_hint or ev.origin_hint == "unknown":
            missing.append("origin_hint")
        if not ev.change_ref:
            missing.append("change_ref")
        # Safe access helper
        def get_ver(vrefs, attr):
            if isinstance(vrefs, dict):
                return vrefs.get(attr, "unknown")
            return getattr(vrefs, attr, "unknown")

        v_fw = get_ver(ev.version_refs, "fw")
        v_driver = get_ver(ev.version_refs, "driver")

        if not ev.version_refs or (v_fw == "unknown" and v_driver == "unknown"):
            missing.append("version_refs")

        insufficient = len(missing) > 0
        return ObservabilityResult(
            observability_status="INSUFFICIENT" if insufficient else "SUFFICIENT",
            opaque_risk=insufficient,
            missing_refs=missing,
            origin_hint=ev.origin_hint or "unknown"
        )

    def check_no_change_event(self) -> ObservabilityResult:
        return ObservabilityResult(
            observability_status="INSUFFICIENT",
            opaque_risk=True,
            missing_refs=["no_change_event_detected"],
            origin_hint="unknown"
        )
