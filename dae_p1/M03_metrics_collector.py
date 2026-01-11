
from __future__ import annotations
from typing import Optional
from .M00_common import MetricSample, now_ts
from .M01_windowing import Windowing

class MetricsCollector:
    """
    Collects metadata-only metrics. In production, replace stubs with platform adapters.
    """
    def __init__(self, windowing: Windowing):
        self.windowing = windowing

    def collect(self,
                latency_p95_ms: Optional[float]=None,
                loss_pct: Optional[float]=None,
                retry_pct: Optional[float]=None,
                airtime_busy_pct: Optional[float]=None,
                roam_count: Optional[int]=None,
                mesh_flap_count: Optional[int]=None,
                wan_sinr_db: Optional[float]=None,
                wan_rsrp_dbm: Optional[float]=None,
                wan_reattach_count: Optional[int]=None) -> MetricSample:
        ts = now_ts()
        ws = self.windowing.window_ref(ts, "Ws")
        return MetricSample(
            ts=ts, window_ref=ws,
            latency_p95_ms=latency_p95_ms, loss_pct=loss_pct,
            retry_pct=retry_pct, airtime_busy_pct=airtime_busy_pct,
            roam_count=roam_count, mesh_flap_count=mesh_flap_count,
            wan_sinr_db=wan_sinr_db, wan_rsrp_dbm=wan_rsrp_dbm,
            wan_reattach_count=wan_reattach_count
        )
