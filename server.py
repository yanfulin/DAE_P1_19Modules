
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from dae_p1.core_service import OBHCoreService, CoreRuntimeConfig
from dae_p1.M20_install_verify import verify_install
from dae_p1.status_helper import calculate_simple_status
from dae_p1.M13_fp_lite import ProofCardGenerator, ProofCardGeneratorV14
from dae_p1.M00_common import iso


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
adapter = None
core = None
background_task = None
pc_generator = ProofCardGenerator()
pc_generator_v14 = ProofCardGeneratorV14()


async def run_core_loop():
    """Background task to simulate the core service tick."""
    logger.info("Starting Core Loop")
    while True:
        if core:
            try:
                core.tick_once()
                # logger.info("Tick")
            except Exception as e:
                logger.error(f"Error in tick: {e}")
        await asyncio.sleep(1) # simple 1 second tick

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global adapter, core, background_task

    
    import platform
    os_name = platform.system()
    
    if os_name == "Windows":
        try:
            from dae_p1.adapters.windows_wifi_adapter import WindowsWifiAdapter
            logger.info("Windows detected. Initializing Core Service with WindowsWifiAdapter...")
            adapter = WindowsWifiAdapter()
        except ImportError as e:
            logger.error(f"Failed to import WindowsWifiAdapter on Windows: {e}. Fallback to Demo.")
            from dae_p1.adapters.demo_adapter import DemoAdapter
            adapter = DemoAdapter()
    else:
        logger.info(f"{os_name} detected (Not Windows). Initializing Core Service with DemoAdapter...")
        from dae_p1.adapters.demo_adapter import DemoAdapter
        adapter = DemoAdapter()
    
    # Use accelerate=True so it doesn't sleep internally, we control loop with asyncio
    cfg = CoreRuntimeConfig(sample_interval_sec=1, buffer_minutes=60, accelerate=True, persistence_enabled=True)
    core = OBHCoreService(adapter, cfg)


    background_task = asyncio.create_task(run_core_loop())
    
    yield
    
    # Shutdown
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    logger.info("Core Service Shut Down")

app = FastAPI(lifespan=lifespan)

# Allow all CORS for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "running", "service": "DAE_P1 Demo Core V1.3 / V1.4"}

@app.get("/metrics")
def get_metrics():
    """Get the latest metric sample."""
    if not core:
        return {"error": "Core not initialized"}
    
    latest = core.metrics_buf.last()
    if latest:
        # If it's a dataclass, API will JSONify it, but if it's already dict?
        # M02 now returns item_class objects if configured.
        return latest
    return {"message": "No metrics collected yet"}

@app.get("/metrics/history")
def get_metrics_history(limit: int = 20):
    """Get recent metrics history."""
    if not core:
        return []
    all_metrics = core.metrics_buf.snapshot()
    return all_metrics[-limit:]

@app.get("/events")
def get_events():
    """Get recent change events."""
    if not core:
        return []
    return core.events_buf.snapshot()

@app.get("/snapshots")
def get_snapshots():
    """Get recent snapshots."""
    if not core:
        return []
    return core.snaps_buf.snapshot()

@app.get("/recognition")
def get_recognition():
    """Trigger and return recognition result."""
    if not core:
        return {"error": "Core not initialized"}
    
    try:
        rec = core.generate_recognition()
        return rec
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/install_verify")
def get_install_verify():
    """Trigger installation verification (closure readiness)."""
    if not core:
        return {"error": "Core not initialized"}
    
    # Get all available metrics from the buffer to form the window
    metrics_snapshot = core.metrics_buf.snapshot()
    
    # Get Internals for C01/C06 display
    ws, wl = core.windowing.current_refs()
    w_refs = {"Ws": ws, "Wl": wl}
    b_stats = {
        "count": len(metrics_snapshot),
        "capacity": core.metrics_buf.maxlen if hasattr(core.metrics_buf, 'maxlen') else 0
    }
    
    # Run verification (defaults to 3 minute window inside the function)
    result = verify_install(metrics_snapshot, window_refs=w_refs, buffer_stats=b_stats)
    
    return result

@app.get("/status")
def get_status():
    """Get the simple status (ok/unstable/suspected/investigation)."""
    if not core:
        return {"status": "starting"}
    
    s = calculate_simple_status(core)
    return {"status": s}

# Execution block moved to end of file

@app.get("/modules")
def get_modules_status():
    """Get status of all 19 modules."""
    if not core:
        return {"error": "Core not initialized"}
    
    modules = []
    
    # helper
    def add_mod(id, name, status, data):
        modules.append({
            "id": id,
            "name": name,
            "status": status,
            "data": data
        })

    # M00 Common
    add_mod("M00", "Common", "Active", {"note": "Shared data structures"})

    # M01 Windowing
    ws_ref, wl_ref = core.windowing.current_refs()
    m01_data = {
        "current_refs": {"Ws": ws_ref, "Wl": wl_ref},
        "policy": {"ws_sec": core.windowing.policy.ws_sec, "wl_sec": core.windowing.policy.wl_sec}
    }
    add_mod("M01", "Windowing", "Active", m01_data)

    # M02 Ring Buffer (Metrics)
    m_buf_len = len(core.metrics_buf)
    add_mod("M02", "RingBuffer", "Active (In-Memory)", {"metrics_count": m_buf_len, "capacity": core.metrics_buf.maxlen})

    # M03 Collector
    from dataclasses import asdict, is_dataclass
    from dae_p1.M00_common import iso
    last_m = core.metrics_buf.last()
    m03_data = {}
    if last_m:
        m03_data = asdict(last_m) if is_dataclass(last_m) else last_m
        # Format TS for readability
        ts_val = m03_data.get('ts')
        if ts_val:
            m03_data['ts_iso'] = iso(ts_val)
    else:
        m03_data = {"status": "No samples yet"}
        
    add_mod("M03", "MetricsCollector", "Active", m03_data)

    # ... (Skipping M04-M12 for brevity, they remain largely same but accessing core props)
    # Re-implementing simplified status for other modules
    
    add_mod("M04", "ChangeLogger", "Active", {"events_count": len(core.events_buf)})
    add_mod("M05", "SnapshotManager", "Active", {"snapshots_count": len(core.snaps_buf)})
    
    # M13 fp_lite
    add_mod("M13", "fp_lite", "Active", {"note": "V1.3 + V1.4 ProofCard Generator Ready"})

    # M14 Bundle Reader
    add_mod("M14", "BundleReader", "Offline", {"note": "Library"})

    # M15 CLI
    add_mod("M15", "CLI_Offline_FP", "Offline", {"note": "Run via terminal"})

    # M16 Recognition Engine
    add_mod("M16", "RecognitionEngine", "Active", {"integrated": True})
    
    # M21 Manifest Manager (Integrated)
    add_mod("M21", "ManifestManager", "Integrated", {"note": "Functionality moved to Core"})


    return modules
    
# --- MOCK FLEET SERVICE ---

def _get_local_status():
    if not core:
        return "unknown"
    return calculate_simple_status(core)

def _get_mock_fleet():
    """Generate a mixed list of real and mock devices."""
    
    # Calculate real status for local device
    local_status = "unknown"
    primary_issue = "None"
    closure = "NOT_READY"
    readiness_verdict = "FAIL"
    
    if core:
        # standard simple status
        local_status = calculate_simple_status(core)
        
        # authoritative verify logic
        snaps = core.metrics_buf.snapshot()
        v_result = verify_install(snaps)
        
        closure = "READY" if v_result.closure_readiness == "ready" else "NOT_READY"
        readiness_verdict = v_result.readiness_verdict
        
        if v_result.dominant_factor != "UNKNOWN" and v_result.dominant_factor != "OPAQUE":
             primary_issue = v_result.dominant_factor + " Issue"
        elif local_status != "ok":
             primary_issue = "Stability"
    
    # Real Device
    real_device = {
        "id": "local",
        "name": "Local CPE (Real)",
        "current_state": local_status,
        "primary_issue_class": primary_issue,
        "closure_readiness": closure,
        "last_change_ref": "T-1m",
        "feature_deltas": ["BandSteering: OFF"] if local_status == "unstable" else []
    }

    # Mock Devices
    mock_devices = [
        {
            "id": "mock_1",
            "name": "Living Room Mesh",
            "current_state": "suspected",
            "primary_issue_class": "Backhaul Flapping",
            "closure_readiness": "NOT_READY",
            "last_change_ref": "T-2h",
            "feature_deltas": ["DFS: Frozen"]
        },
        {
            "id": "mock_2",
            "name": "Bedroom Extender",
            "current_state": "ok",
            "primary_issue_class": "None",
            "closure_readiness": "READY",
            "last_change_ref": "T-1d",
            "feature_deltas": []
        }
    ]
    
    return [real_device] + mock_devices

@app.get("/fleet")
def get_fleet_view():
    """Get the list of all devices in the fleet (1 real + N mock)."""
    return _get_mock_fleet()

@app.get("/device/{device_id}")
def get_device_detail(device_id: str):
    """Get detailed drilldown info for a device."""
    
    # Local Device (Real-ish Data)
    if device_id == "local":
        local_status = "unknown"
        if core:
            local_status = calculate_simple_status(core)
        
        # We can pull real snapshots if available, or mock them if empty
        snapshots = []
        v_result = None
        
        if core:
            snaps = core.snaps_buf.snapshot()
            # Convert to simplified format for UI
            formatted_snaps = []
            for s in snaps[-5:]: # Last 5
                ts_val = getattr(s, 'ts', 0)
                trig_val = getattr(s, 'trigger', 'unknown')
                formatted_snaps.append({
                    "ref": f"S-{ts_val}",
                    "type": trig_val,
                    "time": ts_val
                })
            snapshots = formatted_snaps
            
            # Run verification for detail
            m_snaps = core.metrics_buf.snapshot()
            v_result = verify_install(m_snaps)
        
        if not snapshots:
            snapshots = [
                {"ref": "S-100", "type": "post-install", "time": 1000},
                {"ref": "S-105", "type": "periodic", "time": 1050}
            ]

        # Use verification result if available
        pass_fail = "FAIL"
        if v_result:
             pass_fail = v_result.readiness_verdict
        elif local_status == "ok":
             # fallback if core matches but no metrics (unlikely with core) or no core
             pass_fail = "PASS"

        return {
            "id": "local",
            "obh_snapshot_timeline": snapshots,
            "cohort_compare": {
                "status": "normal", # normal / outlier
                "message": "Behaving as expected for Model X v2.1"
            },
            "feature_ledger": [
                {"feature": "BandSteering", "state": "ON", "reason": "Default", "ttl": None},
                {"feature": "DFS", "state": "ON", "reason": "Default", "ttl": None}
            ],
            "compliance_verdict": {
                "result": pass_fail,
                "evidence_missing": [] if pass_fail == "PASS" else ["Stability Check"]
            }
        }

    # Mock Device 1 (Suspected)
    elif device_id == "mock_1":
        return {
            "id": "mock_1",
            "obh_snapshot_timeline": [
                {"ref": "S-800", "type": "post-install", "time": 800},
                {"ref": "S-1200", "type": "pre-incident", "time": 1200},
                {"ref": "S-1210", "type": "post-incident", "time": 1210}
            ],
            "cohort_compare": {
                "status": "outlier",
                "message": "High flap rate compared to cohort (Top 5%)"
            },
            "feature_ledger": [
                 {"feature": "BandSteering", "state": "OFF", "reason": "Stability logic", "ttl": "2h remaining"},
                 {"feature": "DFS", "state": "FROZEN", "reason": "Radar detected", "ttl": "30m remaining"}
            ],
            "compliance_verdict": {
                "result": "FAIL",
                "evidence_missing": ["Pcap dump for recent flap"]
            }
        }
        
    # Default Mock
    return {
         "id": device_id,
         "obh_snapshot_timeline": [],
         "cohort_compare": {"status": "normal", "message": "No data"},
         "feature_ledger": [],
         "compliance_verdict": {"result": "PASS", "evidence_missing": []}
    }

# --- NEW V1.3 API ---

@app.get("/device/{device_id}/proof")
def get_device_proof(device_id: str, profile: str = "WIFI78_INSTALL_ACCEPT"):
    """
    Get the Proof Card V1.3 for this device.
    Defaults to WIFI78_INSTALL_ACCEPT profile.
    """
    if device_id != "local":
        return {"error": "Only local device implemented for V1.3 ProofCard"}
    
    if not core:
        return {"error": "Core not initialized"}
        
    # Get current Window (last N minutes or samples)
    # For sim, we take the last 100 samples
    metrics = core.metrics_buf.snapshot()[-100:] 
    
    # Convert dataclasses to dicts for M13 processing
    from dataclasses import asdict, is_dataclass
    metrics_dicts = [asdict(m) if is_dataclass(m) else m for m in metrics]

    # Get Manifest Ref
    manifest = core.get_manifest(device_id)
    manifest_ref = manifest["manifest_ref"]


    # Generate
    try:
        card = pc_generator.generate(metrics_dicts, profile, window_ref_str="W-LATEST-100", manifest_ref_str=manifest_ref)
        return card
    except Exception as e:
        return {"error": f"Proof Generation Failed: {e}"}

@app.get("/device/{device_id}/proof/v1.4")
def get_device_proof_v14(
    device_id: str,
    profile: str = "WIFI78_INSTALL_ACCEPT",
    byuse_context: str = "",
    export_mode: str = "min_only",
):
    """
    Get ProofCard V1.4 with privacy/admissibility framework.

    Parameters:
      - profile: Profile ref (e.g. WIFI78_INSTALL_ACCEPT, PROFILE_OPENRAN_RIC)
      - byuse_context: BYUSE context (e.g. SUPPORT_CLOSURE, COMPLIANCE_DEFENSE). Empty = none.
      - export_mode: 'min_only' (default) or 'full_with_auth'
    """
    if device_id != "local":
        return {"error": "Only local device implemented for V1.4 ProofCard"}

    if not core:
        return {"error": "Core not initialized"}

    metrics = core.metrics_buf.snapshot()[-100:]

    from dataclasses import asdict, is_dataclass
    metrics_dicts = [asdict(m) if is_dataclass(m) else m for m in metrics]

    manifest = core.get_manifest(device_id)
    manifest_ref = manifest["manifest_ref"]

    try:
        ctx_overrides = {}
        if byuse_context:
            ctx_overrides["byuse_context_ref"] = byuse_context
        if export_mode:
            ctx_overrides["proposed_egress"] = export_mode

        card = pc_generator_v14.generate(
            metrics_dicts,
            profile,
            window_ref_str="W-LATEST-100",
            manifest_ref_str=manifest_ref,
            ctx_overrides=ctx_overrides or None,
        )

        # Apply egress gate to filter output
        from dae_p1.M13A_privacy_framework import AttemptCtx
        egress_result = pc_generator_v14.apply_egress_gate(card)

        response = {
            "proof_card": card,
            "egress": {
                "mode": egress_result.mode,
                "allowed": egress_result.allowed,
                "egress_receipt_ref": egress_result.egress_receipt_ref,
                "reason_code": egress_result.reason_code,
            },
        }

        # If egress is MIN_ONLY, strip priv section from the returned card
        if egress_result.mode == "MIN_ONLY" and "priv" in card:
            card_copy = dict(card)
            card_copy.pop("priv", None)
            response["proof_card"] = card_copy

        return response
    except Exception as e:
        return {"error": f"V1.4 Proof Generation Failed: {e}"}


@app.get("/proof/versions")
def get_proof_versions():
    """List available ProofCard versions."""
    return {
        "versions": [
            {
                "version": "V1.3",
                "endpoint": "/device/{device_id}/proof",
                "description": "Core ProofCard with verdict, p50/p95, outcome_facet",
            },
            {
                "version": "V1.4",
                "endpoint": "/device/{device_id}/proof/v1.4",
                "description": "V1.3 + Privacy/Admissibility framework (PC-Min/PC-Priv, egress gate, BYUSE)",
            },
        ]
    }


@app.get("/device/{device_id}/manifest")
def get_device_manifest(device_id: str):
    """
    Get the Manifest V1.3.
    """
    if not core:
         return {"error": "Core not initialized"}
    
    return core.get_manifest(device_id)


@app.post("/simulate/incident")
def simulate_incident(type: str = "latency", duration: int = 30):
    """
    Simulate an incident by injecting bad metrics into the adapter.
    Type can be: latency, retry, airtime, complex.
    """
    if not core:
        return {"error": "Core not initialized"}
    
    import time
    until = time.time() + duration
    
    if type in ["latency", "retry", "airtime", "complex", "stable", "oscillating", "degrading"]:
        # New simplified logic: Delegate to M17 via adapter
        core.adapter.overrides['simulation_type'] = {"value": type, "until": until, "start": time.time()}
    else:
        return {"error": "Unknown incident type"}
        
    return {"status": "Simulating", "type": type, "duration": duration, "mode": "M17_Integrated"}

@app.post("/obh/trigger")
def trigger_obh():
    """
    Trigger One-Button Help export manually.
    """
    if not core:
        return {"error": "Core not initialized"}
    
    try:
        # Export to current directory or a 'bundles' subdir
        import os
        os.makedirs("bundles", exist_ok=True)
        res = core.obh_export("bundles")
        return {
            "status": "Exported",
            "episode_id": res.episode_id,
            "path": res.exported_path,
            "bundle": res.bundle_content
        }
    except Exception as e:
        return {"error": str(e)}

# --- STATIC FILE SERVING (Expo Web Build) ---
_frontend_dist = os.path.join(os.path.dirname(__file__), "dae-mobile-app", "dist")

if os.path.isdir(_frontend_dist):
    # Serve _expo static assets
    _expo_dir = os.path.join(_frontend_dist, "_expo")
    if os.path.isdir(_expo_dir):
        app.mount("/_expo", StaticFiles(directory=_expo_dir), name="expo_static")

    # Serve other static files (favicon, etc.)
    @app.get("/favicon.ico")
    def favicon():
        return FileResponse(os.path.join(_frontend_dist, "favicon.ico"))

    # SPA fallback: serve index.html for any non-API route
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # If the file exists in dist, serve it
        file_path = os.path.join(_frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise serve index.html (SPA routing)
        return FileResponse(os.path.join(_frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces to allow access from Simulator/External devices
    uvicorn.run(app, host="0.0.0.0", port=8000)
