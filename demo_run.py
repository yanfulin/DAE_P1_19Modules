
import os, time
from dae_p1.M01_windowing import Windowing
from dae_p1.M02_ring_buffer import RingBuffer
from dae_p1.M10_timeline_builder import TimelineBuilder
from dae_p1.M11_bundle_exporter import BundleExporter
from dae_p1.M12_obh_controller import OBHController
from dae_p1.M16_recognition_engine import RecognitionEngine
from dae_p1.M17_demo_simulator import DemoSimulator

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    sim = DemoSimulator()
    rec = RecognitionEngine()

    metrics_buf = RingBuffer(maxlen=360)  # 60 min @ 10s would be 360; demo uses quicker loop
    events_buf = RingBuffer(maxlen=200)
    snaps_buf  = RingBuffer(maxlen=200)

    # Simulate 60 "ticks" (not real time); each tick represents a sample
    worst_window_ref = "Wl:0"
    for t in range(60):
        m, evs, snaps = sim.generate_step(t)
        metrics_buf.append(m)
        for e in evs: events_buf.append(e)
        for s in snaps: snaps_buf.append(s)
        worst_window_ref = "Wl:{}".format(int(m.ts//60)*60)

        time.sleep(0.02)

    recognition = rec.recognize(metrics_buf.last(), events_buf.snapshot(), worst_window_ref=worst_window_ref)

    obh = OBHController(TimelineBuilder(), BundleExporter())
    res = obh.run(
        out_dir=OUT_DIR,
        recognition=recognition,
        metrics=metrics_buf.snapshot(),
        events=events_buf.snapshot(),
        snapshots=snaps_buf.snapshot()
    )
    print("Exported:", res.exported_path)

if __name__ == "__main__":
    main()
