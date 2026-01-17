
from __future__ import annotations
from typing import List, Tuple
from .base_adapter import DomainAdapter
from ..M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot
from ..M17_demo_simulator import DemoSimulator

class DemoAdapter(DomainAdapter):
    """
    Demo adapter to drive OBH core without hardware.
    Uses DemoSimulator to produce MetricSample / ChangeEventCard / PreChangeSnapshot.
    """
    def __init__(self):
        self.sim = DemoSimulator()
        self.t = 0
        self.overrides = {}

    def collect_metric_sample(self) -> MetricSample:
        m, evs, snaps = self.sim.generate_step(self.t, self.overrides)
        self._last_evs = evs
        self._last_snaps = snaps
        self.t += 1
        return m

    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        return getattr(self, "_last_evs", []), getattr(self, "_last_snaps", [])
