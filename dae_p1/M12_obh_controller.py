
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .M00_common import EpisodeRecognition, iso
from .M10_timeline_builder import TimelineBuilder
from .M11_bundle_exporter import BundleExporter

@dataclass
class OBHResult:
    episode_id: str
    exported_path: str

class OBHController:
    """
    One-Button Help (OBH): FREEZE_BUFFER + GENERATE_TIMELINE + EXPORT_BUNDLE.
    Never changes network settings.
    """
    def __init__(self, timeline_builder: TimelineBuilder, exporter: BundleExporter):
        self.timeline_builder = timeline_builder
        self.exporter = exporter

    def run(self, out_dir: str, recognition: EpisodeRecognition,
            metrics, events, snapshots) -> OBHResult:
        timeline = self.timeline_builder.build(metrics, events, snapshots)
        bundle = {
            "spec": "DAE_P1_Free_v1",
            "episode_id": recognition.episode_id,
            "episode_start": iso(recognition.episode_start),
            "worst_window_ref": recognition.worst_window_ref,
            "primary_verdict": recognition.primary_verdict,
            "confidence": recognition.confidence,
            "evidence_refs": recognition.evidence_refs,
            "observability": {
                "observability_status": recognition.observability.observability_status,
                "opaque_risk": recognition.observability.opaque_risk,
                "missing_refs": recognition.observability.missing_refs,
                "origin_hint": recognition.observability.origin_hint
            },
            "timeline": timeline
        }
        path = self.exporter.export(out_dir, recognition.episode_id, bundle)
        return OBHResult(episode_id=recognition.episode_id, exported_path=path)
