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
        self.last_signal = None  # Track last signal for event generation
        self._last_evs = []
        self._last_snaps = []
        self.overrides = {} # For simulation injection

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

        # Check for overrides (Simulation)
        if self.overrides:
            now = time.time()
            # Remove expired
            expired = [k for k, v in self.overrides.items() if v.get('until', 0) < now]
            for k in expired:
                del self.overrides[k]
                
            # Apply active
            if 'latency' in self.overrides: lat = self.overrides['latency']['value']
            if 'jitter' in self.overrides: jit = self.overrides['jitter']['value']
            # Only override collected values or inject new ones?
            # We inject new ones into collector below.
            
        # Collect
        # Helper to get override or actual
        def get_val(key, default):
            if key in self.overrides: return self.overrides[key]['value']
            return default

        ms = self.collector.collect(
            latency_p95_ms=lat, # Already handled above or can be re-handled
            retry_pct=get_val('retry_pct', 0.0), # Default 0
            airtime_busy_pct=get_val('airtime_busy_pct', 0.0), # Default 0
            in_rate=in_rate_mbps,
            out_rate=out_rate_mbps,
            cpu_load=cpu,
            mem_load=mem,
            signal_strength_pct=signal,
            jitter_ms=jit
        )
        
        # Store for event generation in next call (or same tick if we want strict sync, but adapter pattern separates them)
        # Actually proper place is to update last_signal after checking events, but here we only have local state.
        # Let's do it in collect_change_events_and_snapshots using the value cached or passed?
        # The interface separates collect_metric_sample and collect_change_events.
        # So we should probably store 'current_signal' in self to access it in collect_change_events.
        # For simplicity, we can rely on what we just collected.
        self._current_signal = signal
        return ms

    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        events = []
        
        current_sig = getattr(self, '_current_signal', 0)
        
        # Initialize if first run
        if self.last_signal is None:
            self.last_signal = current_sig
            # Optionally record a "startup" event?
            # events.append(self.event_logger.record("adapter_startup", origin_hint="windows", target_scope="wifi"))
        
        diff = current_sig - self.last_signal
        
        # Threshold: report if signal changes by more than 5%
        if abs(diff) > 5:
            # It's a change!
            direction = "improved" if diff > 0 else "degraded"
            
            # We don't have self.event_logger here (it was in DOCSIS adapter but not initialized here)
            # Let's add it or construct ChangeEventCard manually.
            # BaseAdapter doesn't enforce event_logger, but it's good practice.
            # M00Common imports are available.
            
            # Helper to make card
            card = ChangeEventCard(
                event_time=time.time(),
                event_type=f"signal_{direction}",
                origin_hint="windows_wifi",
                trigger="signal_threshold",
                target_scope="wifi",
                change_ref=f"sig:{self.last_signal}->{current_sig}",
                window_ref=self.windowing.window_ref(time.time(), "Wl") # simple current window
            )
            events.append(card)
            
            # Update last
            self.last_signal = current_sig
            
        return events, []
