import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dae_p1.core_service import OBHCoreService, CoreRuntimeConfig
from dae_p1.M20_install_verify import verify_install
from dae_p1.status_helper import calculate_simple_status
from dae_p1.rgap import RGAPController, OutcomeFacet, ProofCard, asdict as dataclass_asdict


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
adapter = None
core = None
background_task = None
rgap_ctrl = None

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
    global adapter, core, background_task, rgap_ctrl
    
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
    cfg = CoreRuntimeConfig(sample_interval_sec=1, buffer_minutes=60, accelerate=True)
    core = OBHCoreService(adapter, cfg)
    
    # Initialize RGAP Controller
    # rgap_ctrl = RGAPController() # Deprecated global
    # logger.info(f"LIFESPAN: RGAP Controller Initialized: {rgap_ctrl}")
    
    app.state.rgap_ctrl = RGAPController()
    logger.info(f"LIFESPAN: RGAP Controller Initialized in app.state: {app.state.rgap_ctrl}")
    
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
    return {"status": "running", "service": "DAE_P1 Demo Core"}

@app.get("/metrics")
def get_metrics():
    """Get the latest metric sample."""
    if not core:
        return {"error": "Core not initialized"}
    
    latest = core.metrics_buf.last()
    if latest:
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
        "capacity": core.metrics_buf._dq.maxlen
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
    m_buf_len = len(core.metrics_buf.snapshot())
    add_mod("M02", "RingBuffer", "Active", {"metrics_count": m_buf_len, "capacity": core.metrics_buf._dq.maxlen})

    # M03 Collector
    from dataclasses import asdict
    from dae_p1.M00_common import iso
    last_m = core.metrics_buf.last()
    m03_data = {}
    if last_m:
        m03_data = asdict(last_m)
        # Format TS for readability
        m03_data['ts_iso'] = iso(last_m.ts)
    else:
        m03_data = {"status": "No samples yet"}
        
    add_mod("M03", "MetricsCollector", "Active", m03_data)

    # M04 Change Logger
    e_buf_len = len(core.events_buf.snapshot())
    add_mod("M04", "ChangeLogger", "Active", {"events_count": e_buf_len})

    # M05 Snapshot Manager
    s_buf_len = len(core.snaps_buf.snapshot())
    add_mod("M05", "SnapshotManager", "Active", {"snapshots_count": s_buf_len})

    # M06 Observability
    # Just dry-run a check
    obs_res = core.recognition.obs.check_no_change_event()
    add_mod("M06", "ObservabilityChecker", "Active", {"opaque_risk": obs_res.opaque_risk})

    # M07 Incident Detector
    # Run on latest
    if last_m:
        is_bad, flags = core.recognition.detector.is_bad_window(last_m)
        add_mod("M07", "IncidentDetector", "Active", {"is_bad_window": is_bad, "flags": flags})
    else:
        add_mod("M07", "IncidentDetector", "Waiting", {"msg": "No metrics"})

    # M08 Verdict Classifier
    add_mod("M08", "VerdictClassifier", "Ready", {"mode": "Heuristic"})

    # M09 Episode Manager
    ep_count = 1 if core.recognition.episodes.current else 0
    add_mod("M09", "EpisodeManager", "Active", {"episodes_tracked": ep_count})

    # M10 Timeline
    add_mod("M10", "TimelineBuilder", "Ready", {"ready_for_export": True})

    # M11 Exporter
    add_mod("M11", "BundleExporter", "Ready", {"format": "JSON spec 1.0"})

    # M12 OBH Controller
    m12_data = {"status": "Idle"}
    if core.obh.last_result:
        m12_data = {
            "status": "Has Result",
            "last_episode": core.obh.last_result.episode_id,
            "path": core.obh.last_result.exported_path,
            "bundle": core.obh.last_result.bundle_content
        }
    add_mod("M12", "OBHController", "Ready", m12_data)

    # M13 fp_lite
    add_mod("M13", "fp_lite", "Offline", {"note": "Use M15 CLI"})

    # M14 Bundle Reader
    add_mod("M14", "BundleReader", "Offline", {"note": "Library"})

    # M15 CLI
    add_mod("M15", "CLI_Offline_FP", "Offline", {"note": "Run via terminal"})

    # M16 Recognition Engine
    add_mod("M16", "RecognitionEngine", "Active", {"integrated": True})

    # M17 Demo
    add_mod("M17", "DemoSimulator", "Active", {"running": True})

    # M18 Notes
    add_mod("M18", "AppIntegration", "Info", {"doc": "See M18_app_integration_notes.md"})

    # M19 Readme
    add_mod("M19", "Readme", "Info", {"doc": "See M19_readme.md"})

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
        },
         {
            "id": "mock_3",
            "name": "Guest Router",
            "current_state": "investigating",
            "primary_issue_class": "WAN Latency",
            "closure_readiness": "NOT_READY",
            "last_change_ref": "T-15m",
            "feature_deltas": ["QoS: Downgraded"]
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
                formatted_snaps.append({
                    "ref": f"S-{s.ts}",
                    "type": s.trigger,
                    "time": s.ts
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

from fastapi import Request

@app.get("/device/{device_id}/proof")
def get_device_proof(request: Request, device_id: str):
    """Get the Proof Card (RGAP v1.3)."""
    rgap_ctrl = getattr(request.app.state, "rgap_ctrl", None)
    logger.info(f"ENDPOINT: Accessing RGAP Controller from state: {rgap_ctrl}")
    if not rgap_ctrl:
        return {"error": "RGAP Controller not initialized"}

    # 1. Gather Data (similar to detail view)
    if device_id == "local" and core:
        # Calculate Verdicts
        m_snaps = core.metrics_buf.snapshot()
        v_result = verify_install(m_snaps)
        
        # Map to RGAP fields
        verdict = "READY" if v_result.closure_readiness == "ready" else "NOT_READY"
        if v_result.readiness_verdict == "FAIL":
            verdict = "NOT_READY" # stricter mapping
        
        reasons = []
        if v_result.dominant_factor != "UNKNOWN":
            reasons.append(v_result.dominant_factor)
        if not reasons and verdict == "NOT_READY":
            reasons.append("generic_failure")
            
        # Create Facets (Example mapping from metrics)
        facets = []
        last = core.metrics_buf.last()
        if last:
            # We can map some real metrics if available in last sample
            # This is a simplification; ideally we aggregate over the window
            facets.append(OutcomeFacet("fwa_rsrp_p50_dbm", getattr(last, 'rsrp', -100), "dBm"))
            facets.append(OutcomeFacet("fwa_sinr_p50_db", getattr(last, 'sinr', 0), "dB"))
        
        card = rgap_ctrl.generate_proof_card(
            verdict=verdict,
            reason_codes=reasons,
            facets=facets,
            sample_count=len(m_snaps)
        )
        return dataclass_asdict(card)

    # Mock fallback for other devices or if core missing
    return {
        "proof_card_ref": "PC-MOCK-001",
        "verdict": "NOT_READY",
        "reason_code": ["mock_device_no_data"],
        "outcome_facet": []
    }

@app.get("/manifest/{device_id}")
def get_manifest(device_id: str):
    """Get the RGAP Manifest."""
    if not rgap_ctrl:
        return {"error": "RGAP Controller not initialized"}
    
    # For local device, return the real manifest
    if device_id == "local":
        return dataclass_asdict(rgap_ctrl.manifest)
    
    return {"manifest_ref": "man-mock", "available_day_refs": []}

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
    
    if type in ["latency", "retry", "airtime", "complex"]:
        # New simplified logic: Delegate to M17 via adapter
        core.adapter.overrides['simulation_type'] = {"value": type, "until": until}
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

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces to allow access from Simulator/External devices
    uvicorn.run(app, host="0.0.0.0", port=8000)
