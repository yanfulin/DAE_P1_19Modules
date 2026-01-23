
from __future__ import annotations
from dataclasses import dataclass
import time
import os
import uuid
from typing import Optional, List, Tuple, Dict, Any


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
    # API to enable persistence
    # API to enable persistence (Deprecated)
    persistence_enabled: bool = False
    # db_path is deprecated and removed


class OBHCoreService:
    """
    OBH Core runner that consumes a DomainAdapter.
    """
    def __init__(self, adapter: DomainAdapter, config: CoreRuntimeConfig = CoreRuntimeConfig()):
        self.adapter = adapter
        self.cfg = config
        
        # 7 Days @ 10s = 60480 samples.
        # But config might override buffer_minutes. 
        # The spec requires 7 days minimum for the ring buffer.
        # We enforce 7 days if persistence is enabled, or fallback to config.
        if self.cfg.persistence_enabled:
            # Deprecated path: forced to False logic effectively or just used as flag?
            # User request said "Abandon SQLite", so we force RingBuffer.
             buffer_items = int((7 * 24 * 60 * 60) / max(1, self.cfg.sample_interval_sec))
        else:
             buffer_items = int((self.cfg.buffer_minutes * 60) / max(1, self.cfg.sample_interval_sec))
             
        self.metrics_buf = RingBuffer(maxlen=buffer_items)
        self.events_buf = RingBuffer(maxlen=500)
        self.snaps_buf = RingBuffer(maxlen=500)


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

    # --- Integrated ManifestManager Logic ---

    def get_manifest(self, device_id: str) -> Dict[str, Any]:
        """
        Generates the current Manifest (V1.3 Integrated).
        """
        now = time.time()
        day_seconds = 86400
        
        # 1. Available Days (Rolling 7 days)
        days = []
        for i in range(7):
            d_ts = now - (i * day_seconds)
            d_str = time.strftime("DAY-%Y%m%d", time.localtime(d_ts))
            days.append(d_str)
            
        # 2. Available Events
        event_refs = []
        if hasattr(self, 'events_buf'):
            events = self.events_buf.snapshot()
            for e in events:
                # e is likely ChangeEventCard
                ref = getattr(e, 'ref', None) 
                if not ref and hasattr(e, 'ts'):
                    ref = f"EVT-{int(e.ts)}"
                if ref:
                    event_refs.append(str(ref))
        
        # 3. Bundle Pointer (In-Memory)
        pointer = "memory://self.metrics_buf"

        return {
            "manifest_ref": f"man-{uuid.uuid4().hex[:8]}",
            "available_day_refs": days,
            "available_event_refs": event_refs, 
            "bundle_pointer": pointer
        }

    def get_bundle(self, ref: str) -> Dict[str, Any]:
        """
        Retrieves a bundle by reference.
        """
        return {"ref": ref, "content": "mock_binary_blob_in_memory", "size": 1024}
