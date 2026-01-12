from __future__ import annotations
import psutil
import time
import subprocess
import re
from typing import List, Tuple
from .base_adapter import DomainAdapter
from ..M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot
from ..M01_windowing import Windowing
from ..M03_metrics_collector import MetricsCollector

class WindowsWifiAdapter(DomainAdapter):
    """
    Adapter to collect real-time metrics from Windows:
    - CPU/Mem via psutil
    - Network Rates via psutil
    - Signal Quality via netsh (subprocess)
    """
    def __init__(self):
        self.windowing = Windowing()
        self.collector = MetricsCollector(self.windowing)
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()
        self._last_evs = []
        self._last_snaps = []

    def _get_signal_strength(self) -> int:
        try:
            # Run netsh wlan show interfaces
            # Output line: "    Signal                 : 80%"
            output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode("utf-8", errors="ignore")
            match = re.search(r"Signal\s*:\s*(\d+)%", output)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 0

    def _get_ping_stats(self) -> Tuple[float, float]:
        """Returns (latency_ms, jitter_ms). Jitter is approximated as 0 for single ping or stdev for multiple."""
        try:
            # Run ping 8.8.8.8 -n 1 for speed (since we tick every 1s)
            # Or -n 2 to get some jitter. Let's do -n 2.
            output = subprocess.check_output("ping 8.8.8.8 -n 2", shell=True).decode("cp950", errors="ignore") # cp950 for TW Windows
            
            # Extract times: "時間=6ms", "time=6ms"
            times = [int(x) for x in re.findall(r"[=<](\d+)ms", output)]
            
            if not times:
                return 0.0, 0.0
            
            avg_latency = sums = sum(times) / len(times)
            
            # Simple jitter: max difference from avg? or stdev? or max-min?
            # RFC 3393 jitter is usually smoothed. Here we just take range for simplicity in a 2-ping sample.
            jitter = float(max(times) - min(times))
            
            return float(avg_latency), jitter
            
        except Exception:
            pass
        return 0.0, 0.0

    def collect_metric_sample(self) -> MetricSample:
        # 1. CPU / Mem
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent

        # 2. Network Rates
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        
        dt = current_time - self.last_time
        if dt <= 0: dt = 0.001 

        bytes_recv = current_net_io.bytes_recv - self.last_net_io.bytes_recv
        bytes_sent = current_net_io.bytes_sent - self.last_net_io.bytes_sent
        
        if bytes_recv < 0: bytes_recv = 0
        if bytes_sent < 0: bytes_sent = 0

        in_rate_mbps = (bytes_recv * 8) / (1024 * 1024) / dt
        out_rate_mbps = (bytes_sent * 8) / (1024 * 1024) / dt

        self.last_net_io = current_net_io
        self.last_time = current_time

        # 3. Signal Strength
        signal = self._get_signal_strength()
        
        # 4. Latency & Jitter
        # Execute ping. Note: this blocks! In a real async server, run in executor.
        # But this is "Demo Core" ticking in a background thread, so blocking is "okay-ish" but will slow down the tick rate.
        # Tick rate is 1s, ping -n 2 takes ~20ms + timeout. Should be fine.
        lat, jit = self._get_ping_stats()

        # Collect
        return self.collector.collect(
            latency_p95_ms=lat,
            retry_pct=0.0,
            airtime_busy_pct=0.0,
            in_rate=in_rate_mbps,
            out_rate=out_rate_mbps,
            cpu_load=cpu,
            mem_load=mem,
            signal_strength_pct=signal,
            jitter_ms=jit
        )

    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        # Currently no real event monitoring implemented
        return [], []
