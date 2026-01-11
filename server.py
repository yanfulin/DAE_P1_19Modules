import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dae_p1.adapters.demo_adapter import DemoAdapter
from dae_p1.core_service import OBHCoreService, CoreRuntimeConfig

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
    logger.info("Initializing Core Service...")
    adapter = DemoAdapter()
    
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

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces to allow access from Simulator/External devices
    uvicorn.run(app, host="0.0.0.0", port=8000)
