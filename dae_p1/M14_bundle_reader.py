
from __future__ import annotations
from typing import Dict, Any
import json

def load_bundle(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
