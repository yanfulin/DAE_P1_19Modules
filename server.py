import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from dae_p1.adapters.demo_adapter import DemoAdapter
from dae_p1.adapters.windows_wifi_adapter import WindowsWifiAdapter
from dae_p1.core_service import OBHCoreService, CoreRuntimeConfig
from dae_p1.M20_install_verify import verify_install
from dae_p1.status_helper import calculate_simple_status


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
adapter = None
core = None
background_task = None

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
    logger.info("Initializing Core Service with WindowsWifiAdapter...")
    adapter = WindowsWifiAdapter()
    
    # Use accelerate=True so it doesn't sleep internally, we control loop with asyncio
    cfg = CoreRuntimeConfig(sample_interval_sec=1, buffer_minutes=60, accelerate=True)
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
    
    # Run verification (defaults to 3 minute window inside the function)
    result = verify_install(metrics_snapshot)
    
    return result

@app.get("/status")
def get_status():
    """Get the simple status (ok/unstable/suspected/investigation)."""
    if not core:
        return {"status": "starting"}
    
    s = calculate_simple_status(core)
    return {"status": s}

# Execution block moved to end of file
    
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

@app.get("/device/{device_id}/proof")
def get_device_proof(device_id: str):
    """Get the Proof Card summary."""
    # Reuse getting detail to construct the card
    detail = get_device_detail(device_id)
    
    # Construct card
    return {
        "title": f"Proof Card - {device_id}",
        "timestamp": "Now",
        "trigger_summary": detail["cohort_compare"]["message"],
        "snapshot_refs": [s["ref"] for s in detail["obh_snapshot_timeline"]],
        "feature_ledger_summary": f"{len(detail['feature_ledger'])} features tracked",
        "closure_readiness": "READY" if detail["compliance_verdict"]["result"] == "PASS" else "NOT_READY",
        "vendor_compliance_verdict": detail["compliance_verdict"]["result"]
    }

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces to allow access from Simulator/External devices
    uvicorn.run(app, host="0.0.0.0", port=8000)
