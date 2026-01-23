
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

    def collect_metric_sample(self) -> MetricSample:
        # Check defaults
        sim_type = None
        elapsed = 0.0

        if hasattr(self, 'overrides') and 'simulation_type' in self.overrides:
             import time
             sim_data = self.overrides['simulation_type']
             if sim_data.get('until', 0) > time.time():
                 sim_type = sim_data['value']
                 start = sim_data.get('start', 0)
                 elapsed = time.time() - start
                 if elapsed < 0: elapsed = 0

        m, evs, snaps = self.sim.generate_step(self.t)
        
        # If simulation active, regenerate metrics part only and overwrite
        if sim_type:
            sim_metrics = self.sim.generate_metrics_only(sim_type, elapsed_time=elapsed)
            # We need to construct a new MetricSample or update 'm'. MetricSample is frozen/dataclass? 
            # M03 collector creates it.
            # Simpler: generate_step in DemoSimulator calls generate_metrics_only. 
            # We can't easily injection elapsed time into generate_step without changing signature.
            # But wait, generate_step ignores args for metrics currently.
            # Let's just create a new sample using values from sim_metrics
            m = self.sim.collector.collect(
                latency_p95_ms=sim_metrics["latency_p95_ms"],
                retry_pct=sim_metrics["retry_pct"],
                airtime_busy_pct=sim_metrics["airtime_busy_pct"],
                mesh_flap_count=sim_metrics["mesh_flap_count"],
                wan_sinr_db=sim_metrics["wan_sinr_db"],
                signal_strength_pct=sim_metrics["signal_strength_pct"],
                channel=sim_metrics["channel"],
                radio_type=sim_metrics["radio_type"],
                band=sim_metrics["band"],
                phy_rate_mbps=sim_metrics["phy_rate_mbps"],
                dns_status=sim_metrics["dns_status"]
            )
        
        self._last_evs = evs
        self._last_snaps = snaps
        self.t += 1
        return m

    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        return getattr(self, "_last_evs", []), getattr(self, "_last_snaps", [])
