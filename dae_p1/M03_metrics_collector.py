
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
                wan_reattach_count: Optional[int]=None,
                jitter_ms: Optional[float]=None,
                in_rate: Optional[float]=None,
                out_rate: Optional[float]=None,
                cpu_load: Optional[float]=None,
                mem_load: Optional[float]=None,
                signal_strength_pct: Optional[int]=None,
                # Extended
                channel: Optional[int]=None,
                bssid: Optional[str]=None,
                radio_type: Optional[str]=None,
                band: Optional[str]=None,
                phy_rate_mbps: Optional[int]=None,
                phy_rx_rate_mbps: Optional[int]=None,
                dns_status: Optional[str]=None) -> MetricSample:
        ts = now_ts()
        ws = self.windowing.window_ref(ts, "Ws")
        return MetricSample(
            ts=ts, window_ref=ws,
            latency_p95_ms=latency_p95_ms, loss_pct=loss_pct,
            retry_pct=retry_pct, airtime_busy_pct=airtime_busy_pct,
            roam_count=roam_count, mesh_flap_count=mesh_flap_count,
            wan_sinr_db=wan_sinr_db, wan_rsrp_dbm=wan_rsrp_dbm,
            wan_reattach_count=wan_reattach_count,
            jitter_ms=jitter_ms,
            in_rate=in_rate, out_rate=out_rate,
            cpu_load=cpu_load, mem_load=mem_load,
            signal_strength_pct=signal_strength_pct,
            # Extended
            channel=channel, bssid=bssid, radio_type=radio_type, band=band,
            phy_rate_mbps=phy_rate_mbps, phy_rx_rate_mbps=phy_rx_rate_mbps,
            dns_status=dns_status
        )
