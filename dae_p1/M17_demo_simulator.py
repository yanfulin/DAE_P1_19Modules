
from __future__ import annotations
import random, time
from typing import Tuple, List, Dict
from .M01_windowing import Windowing
from .M03_metrics_collector import MetricsCollector
from .M04_change_event_logger import ChangeEventLogger
from .M05_snapshot_manager import SnapshotManager
from .M00_common import VersionRefs

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def generate_scenario(name: str, seconds: int = 900, seed: int = 7) -> List[Dict]:
    random.seed(seed + hash(name) % 1000)
    out: List[Dict] = []

    # Baselines
    retry_base = 0.06
    airtime_base = 0.35
    rssi_mean = -55.0

    for t in range(seconds):
        rate_flap = 0
        path_switch = 0

        if name == "stable":
            retry = retry_base + random.uniform(-0.01, 0.01)
            airtime = airtime_base + random.uniform(-0.05, 0.05)
            rssi_var = 2.5 + random.uniform(-0.7, 0.7)

        elif name == "oscillating":
            # oscillate around the retry redline using a square-ish wave + bursts
            phase = (t // 6) % 2  # flip every ~6s
            retry = (0.22 if phase == 0 else 0.30) + random.uniform(-0.03, 0.03)

            # control-loop flaps (rate changes) and occasional path switches
            if t % 8 == 0:
                rate_flap = 1
            if t % 90 == 0 and t > 0:
                path_switch = 1

            # airtime spikes that correlate with bad phases
            airtime = (0.55 if phase == 0 else 0.78) + random.uniform(-0.06, 0.06)
            rssi_var = (5.0 if phase == 0 else 10.0) + random.uniform(-1.0, 1.2)

        elif name == "degrading":
            # slow drift into failure (less crossing, more time above redline)
            drift = t / seconds
            retry = 0.10 + 0.25 * drift + random.uniform(-0.02, 0.02)
            airtime = 0.40 + 0.45 * drift + random.uniform(-0.05, 0.05)
            rssi_var = 3.0 + 9.0 * drift + random.uniform(-1.0, 1.0)
            if t % 120 == 0 and t > seconds * 0.6:
                rate_flap = 1
            if t % 300 == 0 and t > seconds * 0.7:
                path_switch = 1

        else:
            raise ValueError("unknown scenario: " + name)

        retry = _clamp(retry, 0.0, 1.0)
        airtime = _clamp(airtime, 0.0, 1.0)

        sample = {
            "t": t,
            "retry_ratio": retry,
            "airtime_busy": airtime,
            "rssi_var": rssi_var,
            "rate_flap": rate_flap,
            "path_switch": path_switch,
            "profile": "post-install-default"
        }
        out.append(sample)

    return out

class DemoSimulator:
    """
    Simulates incidents for quick demos (no hardware).
    """
    def __init__(self):
        self.windowing = Windowing()
        self.collector = MetricsCollector(self.windowing)
        self.events = ChangeEventLogger(self.windowing, VersionRefs(fw="fw1.0", driver="drv1.0"))
        self.snaps = SnapshotManager()
        
        # Pre-generate scenarios
        self.scenarios = {
            "stable": generate_scenario("stable"),
            "oscillating": generate_scenario("oscillating"),
            "degrading": generate_scenario("degrading")
        }

    def generate_metrics_only(self, incident_type: str = None, elapsed_time: float = 0.0) -> dict:
        """
        Generate a single dict of metrics (latency, retry, etc.) with randomization.
        incident_type: None/stable (baseline), oscillating, degrading, OR old types: 'latency', 'retry', 'airtime', 'complex'
        elapsed_time: seconds since incident start
        """
        # Default Baseline
        latency = random.uniform(20, 50)
        retry = random.uniform(0.1, 2.0)
        airtime = random.uniform(20, 40)
        flap = 0 
        sinr = random.uniform(25, 40) 
        
        # Good Wifi defaults
        signal = random.randint(85, 99)
        phy_rate = random.randint(866, 1200)
        dns = "OK"

        if incident_type:
            # New Scenarios
            if incident_type in self.scenarios:
                idx = int(elapsed_time)
                if idx >= len(self.scenarios[incident_type]):
                    idx = -1 # stay at end state
                
                point = self.scenarios[incident_type][idx]
                
                # Map back to our metrics
                retry = point["retry_ratio"] * 100.0 # ratio to pct
                airtime = point["airtime_busy"] * 100.0
                flap = point["rate_flap"] # 0 or 1
                
                # degrading/oscillating usually implies bad quality
                if incident_type != "stable":
                     signal = random.randint(50, 70)
                     latency = random.uniform(60, 100)
                     if incident_type == "degrading" and elapsed_time > 600:
                         latency += 100 # worse later
            
            # Legacy/Simple Types
            elif incident_type == 'latency' or incident_type == 'complex':
                latency = random.uniform(80, 140)
            
            elif incident_type == 'retry' or incident_type == 'complex':
                retry = random.uniform(15, 30)
                signal = random.randint(40, 60)
                
            elif incident_type == 'airtime' or incident_type == 'complex':
                airtime = random.uniform(70, 95)
                
            elif incident_type == 'complex':
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

        # Base metrics
        metrics = self.generate_metrics_only()
        
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
