
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from .M00_common import now_ts

@dataclass
class WindowPolicy:
    ws_sec: int = 10
    wl_sec: int = 60

class Windowing:
    """
    Generates window_ref identifiers for 10s (Ws) and 60s (Wl) windows.
    """
    def __init__(self, policy: WindowPolicy = WindowPolicy()):
        self.policy = policy

    def window_ref(self, ts: float, kind: str = "Ws") -> str:
        step = self.policy.ws_sec if kind == "Ws" else self.policy.wl_sec
        bucket = int(ts // step) * step
        return f"{kind}:{bucket}"

    def current_refs(self) -> Tuple[str, str]:
        ts = now_ts()
        return self.window_ref(ts, "Ws"), self.window_ref(ts, "Wl")
