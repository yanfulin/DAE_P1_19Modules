
from __future__ import annotations
from typing import List, Dict, Any, Optional
import time
import uuid
import os

class ManifestManager:
    """
    Manages the V1.3 Manifest (Index of available data).
    """
    def __init__(self, core_service=None):
        self.core = core_service 

    def get_manifest(self, device_id: str) -> Dict[str, Any]:
        """
        Generates the current Manifest.
        structure:
          manifest_ref: string
          available_day_refs: string[] (last 7 days window refs)
          available_event_refs: string[] (all event refs in buffer)
          bundle_pointer: string (location of raw data)
        """
        now = time.time()
        day_seconds = 86400
        
        # 1. Available Days (Rolling 7 days)
        # In a real system, we'd check DB for actual data presence.
        # Here we project the "validity horizon" of 7 days.
        days = []
        for i in range(7):
            d_ts = now - (i * day_seconds)
            d_str = time.strftime("DAY-%Y%m%d", time.localtime(d_ts))
            days.append(d_str)
            
        # 2. Available Events
        event_refs = []
        if self.core and hasattr(self.core, 'events_buf'):
            # Snapshot recent events
            events = self.core.events_buf.snapshot()
            # Assuming ChangeEventCard has a 'ref' or we generate one from 'ts'
            for e in events:
                # e is likely ChangeEventCard(ts=..., type=..., ...)
                ref = getattr(e, 'ref', None) # If ref exists
                if not ref and hasattr(e, 'ts'):
                    ref = f"EVT-{int(e.ts)}"
                if ref:
                    event_refs.append(str(ref))
        
        # 3. Bundle Pointer
        # Points to the SQLite DB or a downloadable endpoint
        pointer = "sqlite://data/cpe_metrics.db"
        if self.core and hasattr(self.core, 'cfg'):
            pointer = f"sqlite://{self.core.cfg.db_path}"

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
        return {"ref": ref, "content": "mock_binary_blob", "size": 1024}
