
from __future__ import annotations
from typing import List, Dict, Any, Optional
import time
import uuid
import os

class ManifestManager:
    """
    Manages the V1.3 Manifest (Index of available data).
    DEPRECATED: Functionality has been moved to OBHCoreService. This class remains for backward compatibility.
    """
    def __init__(self, core_service=None):
        import warnings
        warnings.warn("ManifestManager is deprecated. Use core_service.get_manifest() instead.", DeprecationWarning, stacklevel=2)
        self.core = core_service 

    def get_manifest(self, device_id: str) -> Dict[str, Any]:
        """
        Generates the current Manifest.
        Delegates to core_service if available.
        """
        if self.core and hasattr(self.core, 'get_manifest'):
            return self.core.get_manifest(device_id)

        # Fallback implementation if core not available (or old core)
        now = time.time()
        days = [time.strftime("DAY-%Y%m%d", time.localtime(now - (i * 86400))) for i in range(7)]
        
        return {
            "manifest_ref": f"man-{uuid.uuid4().hex[:8]}",
            "available_day_refs": days,
            "available_event_refs": [], 
            "bundle_pointer": "memory://deprecated_fallback"
        }

    def get_bundle(self, ref: str) -> Dict[str, Any]:
        """
        Retrieves a bundle by reference. 
        """
        return {"ref": ref, "content": "mock_binary_blob", "size": 1024}
