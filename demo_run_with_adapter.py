
import os
from dae_p1.core_service import OBHCoreService, CoreRuntimeConfig
from dae_p1.adapters.demo_adapter import DemoAdapter

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    adapter = DemoAdapter()
    cfg = CoreRuntimeConfig(sample_interval_sec=1, buffer_minutes=60, accelerate=True)
    core = OBHCoreService(adapter, cfg)
    # Run 60 ticks quickly
    for _ in range(60):
        core.tick_once()
    res = core.obh_export(OUT_DIR)
    print("Exported:", res.exported_path)

if __name__ == "__main__":
    main()
