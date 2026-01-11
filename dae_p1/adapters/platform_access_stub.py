
"""
Platform Access Stub

Replace these functions with platform-specific integrations:
- TR-369/USP
- TR-069
- local agents / CLI / SDK
- syslog/telemetry collectors

The adapters in this folder call these stubs to illustrate mapping only.
"""
from __future__ import annotations
from typing import Any, Dict, Optional

def read_wifi_metric(name: str) -> Optional[float]:
    return None

def read_wan_metric(name: str) -> Optional[float]:
    return None

def read_docsis_metric(name: str) -> Optional[float]:
    return None

def read_pon_metric(name: str) -> Optional[float]:
    return None

def read_event_stream() -> list[Dict[str, Any]]:
    # Return a list of event dicts from platform telemetry/log bridge
    return []
