
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple
import time

from .M02_ring_buffer import RingBuffer
from .M10_timeline_builder import TimelineBuilder
from .M11_bundle_exporter import BundleExporter
from .M12_obh_controller import OBHController, OBHResult
from .M16_recognition_engine import RecognitionEngine
from .M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot, EpisodeRecognition
from .adapters.base_adapter import DomainAdapter
from .M01_windowing import Windowing

@dataclass
class CoreRuntimeConfig:
    sample_interval_sec: int = 10
    buffer_minutes: int = 60
    # For demos/tests we can accelerate time with a smaller interval
    accelerate: bool = False

class OBHCoreService:
    """
    OBH Core runner that consumes a DomainAdapter.
    Core semantics are unchanged. This only standardizes the data ingress path.

    - Collects MetricSample every sample_interval_sec (or faster if accelerate=True)
    - Collects ChangeEventCard and PreChangeSnapshot on each cycle (best-effort)
    - Maintains rolling buffers
    - On-demand: generates EpisodeRecognition and exports an evidence bundle via OBHController
    """
    def __init__(self, adapter: DomainAdapter, config: CoreRuntimeConfig = CoreRuntimeConfig()):
        self.adapter = adapter
        self.cfg = config
        # 60 min @ 10s = 360 samples; scale with interval
        max_metrics = int((config.buffer_minutes * 60) / max(1, config.sample_interval_sec))
        self.metrics_buf: RingBuffer[MetricSample] = RingBuffer(maxlen=max_metrics)
        self.events_buf: RingBuffer[ChangeEventCard] = RingBuffer(maxlen=500)
        self.snaps_buf: RingBuffer[PreChangeSnapshot] = RingBuffer(maxlen=500)

        self.windowing = Windowing()
        self.recognition = RecognitionEngine()
        self.obh = OBHController(TimelineBuilder(), BundleExporter())

    def tick_once(self) -> None:
        m = self.adapter.collect_metric_sample()
        self.metrics_buf.append(m)

        evs, snaps = self.adapter.collect_change_events_and_snapshots()
        for e in evs:
            self.events_buf.append(e)
        for s in snaps:
            self.snaps_buf.append(s)

        if not self.cfg.accelerate:
            time.sleep(self.cfg.sample_interval_sec)

    def run_for(self, seconds: int) -> None:
        """
        Run collection loop for a duration (best for demos).
        """
        end = time.time() + seconds
        while time.time() < end:
            self.tick_once()

    def generate_recognition(self) -> EpisodeRecognition:
        """
        Generate recognition from latest buffered data.
        """
        latest = self.metrics_buf.last()
        if latest is None:
            # create a minimal dummy MetricSample-like; but normally you'd collect first
            raise RuntimeError("No metrics collected")
        worst_window_ref = self.windowing.window_ref(latest.ts, "Wl")
        return self.recognition.recognize(
            latest_metric=latest,
            recent_change_events=self.events_buf.snapshot(),
            worst_window_ref=worst_window_ref
        )

    def obh_export(self, out_dir: str) -> OBHResult:
        """
        Perform OBH export using current buffers.
        """
        rec = self.generate_recognition()
        return self.obh.run(
            out_dir=out_dir,
            recognition=rec,
            metrics=self.metrics_buf.snapshot(),
            events=self.events_buf.snapshot(),
            snapshots=self.snaps_buf.snapshot()
        )
