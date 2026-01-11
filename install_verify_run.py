
import json
from dae_p1.M14_bundle_reader import load_bundle
from dae_p1.M20_install_verify import verify_install
from types import SimpleNamespace

def main(bundle_path: str):
    b = load_bundle(bundle_path)
    pts = b["timeline"]["metrics_points"]
    samples = []
    # Free v1 export points may not include epoch ts; we treat as sequential 10s samples.
    for idx, p in enumerate(pts):
        ts = idx * 10
        samples.append(SimpleNamespace(
            ts=ts,
            latency_p95_ms=p.get("latency_p95_ms"),
            loss_pct=p.get("loss_pct"),
            retry_pct=p.get("retry_pct"),
            airtime_busy_pct=p.get("airtime_busy_pct"),
            mesh_flap_count=p.get("mesh_flap_count"),
            wan_sinr_db=p.get("wan_sinr_db")
        ))
    res = verify_install(samples)
    print(json.dumps(res.__dict__, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python install_verify_run.py <evidence_bundle.json>")
        raise SystemExit(2)
    main(sys.argv[1])
