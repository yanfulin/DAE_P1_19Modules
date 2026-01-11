
from __future__ import annotations
from typing import List, Tuple
from .base_adapter import DomainAdapter
from .platform_access_stub import read_wifi_metric, read_wan_metric, read_docsis_metric, read_event_stream
from ..M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot, VersionRefs
from ..M01_windowing import Windowing
from ..M04_change_event_logger import ChangeEventLogger
from ..M05_snapshot_manager import SnapshotManager
from ..M03_metrics_collector import MetricsCollector

class DOCSISAdapter(DomainAdapter):
    """
    DOCSIS (Cable) adapter: maps DOCSIS PHY/MAC health + Wi-Fi symptoms into MetricSample.
    Minimal recommended inputs (open set):
      - docsis_rx_mer_db / docsis_snr_db (optional map to wan_sinr_db for generic boundary signal)
      - correctables / uncorrectables / t3_t4_counts (optional event stream)
      - wan rtt/loss to CMTS/edge
      - wifi retry/airtime for in-home symptoms
    """
    def __init__(self, version_refs: VersionRefs = VersionRefs(fw="unknown", driver="unknown", agent="dae_p1")):
        self.windowing = Windowing()
        self.collector = MetricsCollector(self.windowing)
        self.event_logger = ChangeEventLogger(self.windowing, version_refs)
        self.snap = SnapshotManager()

    def collect_metric_sample(self) -> MetricSample:
        # Map cable access metrics into existing fields without changing core schema.
        # Use wan_sinr_db as a generic "access quality" indicator if desired.
        access_q = read_docsis_metric("rx_mer_db")
        return self.collector.collect(
            latency_p95_ms=read_wan_metric("rtt_p95_ms"),
            loss_pct=read_wan_metric("loss_pct"),
            retry_pct=read_wifi_metric("retry_pct"),
            airtime_busy_pct=read_wifi_metric("airtime_busy_pct"),
            mesh_flap_count=read_wifi_metric("mesh_flap_count"),
            wan_sinr_db=access_q  # generic access quality mapping (optional)
        )

    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        events: List[ChangeEventCard] = []
        snaps: List[PreChangeSnapshot] = []
        for e in read_event_stream():
            etype = e.get("event_type", "unknown")
            origin = e.get("origin_hint", "unknown")
            scope = e.get("target_scope", "wan")
            change_ref = e.get("change_ref")
            if etype in ("cm_reset", "partial_service", "profile_change", "rf_param_change", "policy_update", "config_change"):
                snap = self.snap.create_pre_change(scope, e.get("readable_fields", {}))
                snaps.append(snap)
            events.append(self.event_logger.record(etype, origin_hint=origin, target_scope=scope, change_ref=change_ref))
        return events, snaps
