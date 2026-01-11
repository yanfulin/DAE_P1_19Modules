
from __future__ import annotations
from typing import Dict, Any
from .M00_common import ensure_dir
import json
import os
import time

class BundleExporter:
    """
    Exports evidence bundles (JSON). No payload.
    """
    def export(self, out_dir: str, episode_id: str, bundle: Dict[str, Any]) -> str:
        ensure_dir(out_dir)
        fname = f"evidence_bundle_{episode_id}_{int(time.time())}.json"
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)
        return path
