
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

    def generate_metrics_only(self, incident_type: str = None) -> dict:
        """
        Generate a single dict of metrics (latency, retry, etc.) with randomization.
        incident_type: None (baseline), 'latency', 'retry', 'airtime', 'complex'
        """
        # Default Baseline
        latency = random.uniform(20, 50)
        retry = random.uniform(0.1, 2.0)
        airtime = random.uniform(20, 40)
        flap = 0 # random.randint(0, 1) # Keep flaps low for baseline
        sinr = random.uniform(25, 40) # Higher is better
        
        # Good Wifi defaults
        signal = random.randint(85, 99)
        phy_rate = random.randint(866, 1200)
        dns = "OK"

        if incident_type:
            if incident_type == 'latency' or incident_type == 'complex':
                latency = random.uniform(80, 140)
            
            if incident_type == 'retry' or incident_type == 'complex':
                retry = random.uniform(15, 30)
                signal = random.randint(40, 60) # weak signal often causes retry
                
            if incident_type == 'airtime' or incident_type == 'complex':
                airtime = random.uniform(70, 95)
                
            if incident_type == 'complex':
                flap = random.randint(1, 4)
                sinr = random.uniform(2, 8)
                dns = "FAIL"

        return {
            "latency_p95_ms": latency,
            "retry_pct": retry,
            "airtime_busy_pct": airtime,
            "mesh_flap_count": flap,
            "wan_sinr_db": sinr,
            "signal_strength_pct": signal,
            "phy_rate_mbps": phy_rate,
            "dns_status": dns,
            "channel": 36,
            "band": "5GHz",
            "radio_type": "802.11ax"
        }

    def generate_step(self, t: int) -> Tuple[dict, List, List]:
        # t=0: Emulated post-install state
        m_evs = []
        m_snaps = []
        if t == 0:
             snap = self.snaps.create_pre_change("wlan", {"channel": 36, "bandwidth": 80, "steering_enabled": True}, snapshot_type="post-install")
             m_snaps.append(snap)

        # Simulate a baseline then an incident around t in [300, 320] (moved later so startup is clean)
        inc_type = None
        if 300 <= t <= 320:
            inc_type = 'complex'
            
        metrics = self.generate_metrics_only(inc_type)
        
        # Create MetricSample using the collector (which adds TS, WindowRef)
        m = self.collector.collect(
            latency_p95_ms=metrics["latency_p95_ms"],
            retry_pct=metrics["retry_pct"],
            airtime_busy_pct=metrics["airtime_busy_pct"],
            mesh_flap_count=metrics["mesh_flap_count"],
            wan_sinr_db=metrics["wan_sinr_db"],
            signal_strength_pct=metrics["signal_strength_pct"],
            # Extended
            channel=metrics["channel"],
            radio_type=metrics["radio_type"],
            band=metrics["band"],
            phy_rate_mbps=metrics["phy_rate_mbps"],
            dns_status=metrics["dns_status"]
        )

        evs = []
        snaps = []
        # Occasionally emit a change event 
        if t in (318, 500):
            stype = "periodic"
            snap = self.snaps.create_pre_change("wlan", {"channel": 36, "bandwidth": 80, "steering_enabled": True}, snapshot_type=stype)
            snaps.append(snap)
            ev = self.events.record("policy_update", origin_hint="cloud", target_scope="wlan", change_ref=f"pol-{t}")
            evs.append(ev)

        evs.extend(m_evs)
        snaps.extend(m_snaps)

        return m, evs, snaps
