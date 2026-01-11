
from __future__ import annotations
from typing import Optional
from .M00_common import ChangeEventCard, VersionRefs, now_ts
from .M01_windowing import Windowing

class ChangeEventLogger:
    """
    Records command/change stubs (metadata-only).
    Does NOT capture payload, only event facts.
    """
    def __init__(self, windowing: Windowing, version_refs: VersionRefs):
        self.windowing = windowing
        self.version_refs = version_refs

    def record(self, event_type: str, origin_hint: str="unknown", trigger: str="unknown",
               target_scope: str="unknown", change_ref: Optional[str]=None) -> ChangeEventCard:
        ts = now_ts()
        ws = self.windowing.window_ref(ts, "Ws")
        return ChangeEventCard(
            event_time=ts, event_type=event_type, origin_hint=origin_hint, trigger=trigger,
            target_scope=target_scope, change_ref=change_ref, version_refs=self.version_refs,
            window_ref=ws
        )
