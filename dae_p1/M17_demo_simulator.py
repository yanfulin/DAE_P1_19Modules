
from __future__ import annotations
import random, time
from typing import Tuple, List
from .M01_windowing import Windowing
from .M03_metrics_collector import MetricsCollector
from .M04_change_event_logger import ChangeEventLogger
from .M05_snapshot_manager import SnapshotManager
from .M00_common import VersionRefs

class DemoSimulator:
    """
    Simulates incidents for quick demos (no hardware).
    """
    def __init__(self):
        self.windowing = Windowing()
        self.collector = MetricsCollector(self.windowing)
        self.events = ChangeEventLogger(self.windowing, VersionRefs(fw="fw1.0", driver="drv1.0"))
        self.snaps = SnapshotManager()

    def generate_step(self, t: int) -> Tuple[dict, List, List]:
        # t=0: Emulated post-install state
        m_evs = []
        m_snaps = []
        if t == 0:
             snap = self.snaps.create_pre_change("wlan", {"channel": 36, "bandwidth": 80, "steering_enabled": True}, snapshot_type="post-install")
             m_snaps.append(snap)

        # Simulate a baseline then an incident around t in [20, 40]
        if 20 <= t <= 40:
            latency = random.uniform(80, 140)
            retry = random.uniform(15, 30)
            airtime = random.uniform(70, 95)
            flap = random.randint(1, 4)
            sinr = random.uniform(2, 8)
        else:
            latency = random.uniform(20, 50)
            retry = random.uniform(2, 10)
            airtime = random.uniform(20, 60)
            flap = random.randint(0, 1)
            sinr = random.uniform(8, 18)

        m = self.collector.collect(latency_p95_ms=latency, retry_pct=retry, airtime_busy_pct=airtime,
                                   mesh_flap_count=flap, wan_sinr_db=sinr)

        evs = []
        snaps = []
        # Occasionally emit a change event (sometimes missing refs)
        if t in (18, 22, 28, 35):
            stype = "periodic"
            if t == 18: stype = "pre-incident"
            if t == 35: stype = "post-incident"
            
            snap = self.snaps.create_pre_change("wlan", {"channel": 36, "bandwidth": 80, "steering_enabled": True}, snapshot_type=stype)
            snaps.append(snap)
            if t == 28:
                # opaque-like: missing change_ref and unknown origin
                ev = self.events.record("policy_update", origin_hint="unknown", target_scope="wlan", change_ref=None)
            else:
                ev = self.events.record("policy_update", origin_hint="cloud", target_scope="wlan", change_ref=f"pol-{t}")
            evs.append(ev)

        evs.extend(m_evs)
        snaps.extend(m_snaps)

        return m, evs, snaps
