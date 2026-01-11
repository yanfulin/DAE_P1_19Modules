
from __future__ import annotations
from typing import List, Optional
from .M00_common import MetricSample, EpisodeRecognition, ObservabilityResult
from .M07_incident_detector import IncidentDetector
from .M08_verdict_classifier import VerdictClassifier
from .M09_episode_manager import EpisodeManager
from .M06_observability_checker import ObservabilityChecker
from .M00_common import iso

class RecognitionEngine:
    """
    Produces incident recognition: episode id, verdict, confidence, evidence refs, and observability status.
    """
    def __init__(self):
        self.detector = IncidentDetector()
        self.classifier = VerdictClassifier()
        self.episodes = EpisodeManager()
        self.obs = ObservabilityChecker()

    def recognize(self, latest_metric: MetricSample,
                  recent_change_events: List,
                  worst_window_ref: str) -> EpisodeRecognition:
        is_bad, flags = self.detector.is_bad_window(latest_metric)

        if recent_change_events:
            obs_res = self.obs.check_event(recent_change_events[-1])
            opaque = obs_res.opaque_risk
        else:
            obs_res = self.obs.check_no_change_event()
            opaque = True

        verdict, conf = self.classifier.classify(flags, opaque_risk=opaque)
        evidence_ref = f"{latest_metric.window_ref}:{','.join(flags) if flags else 'no_flags'}"
        ep = self.episodes.start_or_update(worst_window_ref=worst_window_ref, evidence_ref=evidence_ref)

        return EpisodeRecognition(
            episode_id=ep.episode_id,
            episode_start=ep.start_ts,
            worst_window_ref=ep.worst_window_ref,
            primary_verdict=verdict,
            confidence=conf,
            evidence_refs=ep.evidence_refs[-10:],  # cap
            observability=obs_res
        )
