
from __future__ import annotations
from typing import List, Dict, Any
from .M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot, iso

class TimelineBuilder:
    """
    Builds a flattened timeline for the last 60 minutes.
    """
    def build(self,
              metrics: List[MetricSample],
              events: List[ChangeEventCard],
              snapshots: List[PreChangeSnapshot]) -> Dict[str, Any]:
        return {
            "metrics_points": [
                {
                    "t": iso(m.ts),
                    "window_ref": m.window_ref,
                    "latency_p95_ms": m.latency_p95_ms,
                    "loss_pct": m.loss_pct,
                    "retry_pct": m.retry_pct,
                    "airtime_busy_pct": m.airtime_busy_pct,
                    "mesh_flap_count": m.mesh_flap_count,
                    "wan_sinr_db": m.wan_sinr_db
                } for m in metrics
            ],
            "change_events": [
                {
                    "t": iso(e.event_time),
                    "event_type": e.event_type,
                    "origin_hint": e.origin_hint,
                    "target_scope": e.target_scope,
                    "change_ref": e.change_ref,
                    "window_ref": e.window_ref
                } for e in events
            ],
            "pre_change_snapshots": [
                {
                    "t": iso(s.capture_time),
                    "snapshot_ref_id": s.snapshot_ref_id,
                    "snapshot_scope": s.snapshot_scope,
                    "snapshot_digest": s.snapshot_digest,
                    "readable_fields": s.readable_fields
                } for s in snapshots
            ]
        }
