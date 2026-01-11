
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import statistics

def _window_slice(metrics_points: List[Dict[str, Any]], start_idx: int, end_idx: int) -> List[Dict[str, Any]]:
    return metrics_points[max(0,start_idx):max(0,end_idx)]

def _vec(slice_pts: List[Dict[str, Any]]) -> Dict[str, float]:
    def vals(key):
        v = [p[key] for p in slice_pts if p.get(key) is not None]
        return v
    out = {}
    for k in ["latency_p95_ms","retry_pct","airtime_busy_pct","mesh_flap_count","wan_sinr_db","loss_pct"]:
        v = vals(k)
        if v:
            out[k] = float(statistics.mean(v))
    return out

def _delta(a: Dict[str,float], b: Dict[str,float]) -> Dict[str,float]:
    keys = set(a.keys()) | set(b.keys())
    return {k: b.get(k,0.0) - a.get(k,0.0) for k in keys}

def _label(delta: Dict[str,float]) -> Tuple[str,float]:
    # Heuristic: pick dominant pattern
    score = {"drift":0.0,"stability":0.0,"boundary":0.0,"oscillation":0.0}
    if delta.get("wan_sinr_db",0.0) < -2.0:
        score["boundary"] += 1.0
    if delta.get("mesh_flap_count",0.0) > 1.0:
        score["oscillation"] += 1.0
    if delta.get("retry_pct",0.0) > 5.0 or delta.get("airtime_busy_pct",0.0) > 10.0:
        score["stability"] += 1.0
    if delta.get("latency_p95_ms",0.0) > 20.0:
        score["drift"] += 1.0
    label = max(score, key=score.get)
    conf = min(0.9, 0.4 + 0.2*score[label])
    return label, conf

def fp_lite_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    pts = bundle["timeline"]["metrics_points"]
    n = len(pts)
    if n < 6:
        return {"error":"insufficient_points"}
    # Split into thirds: before/during/after
    a = _window_slice(pts, 0, n//3)
    d = _window_slice(pts, n//3, 2*n//3)
    z = _window_slice(pts, 2*n//3, n)
    fp_before = _vec(a)
    fp_during = _vec(d)
    fp_after  = _vec(z)
    delta_db = _delta(fp_before, fp_during)
    delta_ab = _delta(fp_before, fp_after)
    label, conf = _label(delta_db)
    return {
        "fp_before": fp_before,
        "fp_during": fp_during,
        "fp_after": fp_after,
        "delta_during_minus_before": delta_db,
        "delta_after_minus_before": delta_ab,
        "pattern_label": label,
        "confidence": conf
    }
