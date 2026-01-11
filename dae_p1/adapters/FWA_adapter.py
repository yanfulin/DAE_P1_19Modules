
from __future__ import annotations
from typing import List, Tuple
from .base_adapter import DomainAdapter
from .platform_access_stub import read_wifi_metric, read_wan_metric, read_event_stream
from ..M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot, VersionRefs
from ..M01_windowing import Windowing
from ..M04_change_event_logger import ChangeEventLogger
from ..M05_snapshot_manager import SnapshotManager
from ..M03_metrics_collector import MetricsCollector

class FWAAdapter(DomainAdapter):
    """
    FWA (5G/4G) adapter: maps cellular + Wi-Fi symptoms into MetricSample.
    Minimal recommended inputs (open set):
      - wan_sinr_db, wan_rsrp_dbm, wan_reattach_count
      - wan_rtt_p95_ms (map to latency_p95_ms if that's your chosen RTT target)
      - wifi retry/airtime, mesh flap/roam (optional)
    """
    def __init__(self, version_refs: VersionRefs = VersionRefs(fw="unknown", driver="unknown", agent="dae_p1")):
        self.windowing = Windowing()
        self.collector = MetricsCollector(self.windowing)
        self.event_logger = ChangeEventLogger(self.windowing, version_refs)
        self.snap = SnapshotManager()

    def collect_metric_sample(self) -> MetricSample:
        # Map platform metrics to MetricSample (metadata-only).
        return self.collector.collect(
            latency_p95_ms=read_wan_metric("rtt_p95_ms"),
            loss_pct=read_wan_metric("loss_pct"),
            retry_pct=read_wifi_metric("retry_pct"),
            airtime_busy_pct=read_wifi_metric("airtime_busy_pct"),
            roam_count=None,
            mesh_flap_count=read_wifi_metric("mesh_flap_count"),
            wan_sinr_db=read_wan_metric("sinr_db"),
            wan_rsrp_dbm=read_wan_metric("rsrp_dbm"),
            wan_reattach_count=read_wan_metric("reattach_count")
        )

    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        events: List[ChangeEventCard] = []
        snaps: List[PreChangeSnapshot] = []
        for e in read_event_stream():
            # Example mapping; keep it open-set
            etype = e.get("event_type", "unknown")
            origin = e.get("origin_hint", "unknown")
            scope = e.get("target_scope", "wan")
            change_ref = e.get("change_ref")
            # Optional: attach a scoped pre-change snapshot reference for known change types
            if etype in ("policy_update", "config_change", "apn_change", "radio_param_change"):
                snap = self.snap.create_pre_change(scope, e.get("readable_fields", {}))
                snaps.append(snap)
            events.append(self.event_logger.record(etype, origin_hint=origin, target_scope=scope, change_ref=change_ref))
        return events, snaps
