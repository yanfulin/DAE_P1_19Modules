from __future__ import annotations
import psutil
import time
import subprocess
import re
import random
from typing import List, Tuple, Optional
from .base_adapter import DomainAdapter
from ..M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot
from ..M01_windowing import Windowing
from ..M03_metrics_collector import MetricsCollector
from ..M17_demo_simulator import DemoSimulator

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
        self.sim = DemoSimulator() # Integrated simulator
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()
        self.last_signal = None  # Track last signal for event generation
        self._last_evs = []
        self._last_snaps = []
        self.overrides = {} # For simulation injection

    def _get_signal_strength(self) -> Tuple[int, Optional[int], Optional[str], Optional[str], Optional[int], Optional[int]]:
        """
        Returns (signal_pct, channel, radio_type, band, tx_rate_mbps, rx_rate_mbps)
        """
        signal = 0
        channel = None
        radio_type = None
        band = None
        tx_rate = None
        rx_rate = None

        try:
            # Run netsh wlan show interfaces
            # Try decoding with cp950 (Traditional Chinese) first, then utf-8, then ignore errors
            raw_output = subprocess.check_output("netsh wlan show interfaces", shell=True)
            output = ""
            try:
                output = raw_output.decode("cp950")
            except:
                output = raw_output.decode("utf-8", errors="ignore")
            
            # Signal: "Signal : 88%" or "訊號 : 88%"
            match_sig = re.search(r"(?:Signal|訊號)\s*[:：]\s*(\d+)%", output)
            if match_sig:
                signal = int(match_sig.group(1))

            # Channel: "Channel : 108" or "通道 : 108"
            match_ch = re.search(r"(?:Channel|通道)\s*[:：]\s*(\d+)", output)
            if match_ch:
                channel = int(match_ch.group(1))

            # Radio Type: "Radio type : 802.11ac" or "無線電波類型 : 802.11ac"
            match_rad = re.search(r"(?:Radio type|無線電波類型)\s*[:：]\s*(.+)", output)
            if match_rad:
                radio_type = match_rad.group(1).strip()

            # Band: "Band : 5 GHz" or "頻帶 : 5 GHz"
            match_band = re.search(r"(?:Band|頻帶)\s*[:：]\s*(.+)", output)
            if match_band:
                band = match_band.group(1).strip()
            
            # Tx/Rx Rates
            # "Transmit rate (Mbps) : 1201" or "傳輸速率 (Mbps) : 400"
            match_tx = re.search(r"(?:Transmit rate|傳輸速率).*?\(Mbps\)\s*[:：]\s*(\d+)", output)
            if match_tx:
                tx_rate = int(match_tx.group(1))
            
            # "Receive rate (Mbps) : 1201" or "接收速率 (Mbps) : 162"
            match_rx = re.search(r"(?:Receive rate|接收速率).*?\(Mbps\)\s*[:：]\s*(\d+)", output)
            if match_rx:
                rx_rate = int(match_rx.group(1))

        except Exception as e:
            # print(f"Error parsing netsh: {e}")
            pass
            
        return signal, channel, radio_type, band, tx_rate, rx_rate

    def _check_dns_status(self) -> str:
        """Simple check if we can resolve google.com"""
        try:
            # nslookup is ubiquitous
            subprocess.check_call("nslookup google.com", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "OK"
        except Exception:
            return "FAIL"

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

        # 3. Signal Strength & Extended Wifi Info
        signal, channel, radio, band, tx, rx = self._get_signal_strength()
        
        # DNS Check (Do periodically? Every 1s might be heavy. Let's do it every tick for now demo)
        dns = self._check_dns_status()
        
        # 4. Latency & Jitter
        # Execute ping. Note: this blocks! In a real async server, run in executor.
        # But this is "Demo Core" ticking in a background thread, so blocking is "okay-ish" but will slow down the tick rate.
        # Tick rate is 1s, ping -n 2 takes ~20ms + timeout. Should be fine.
        lat, jit = self._get_ping_stats()

        # Check for overrides (Simulation)
        sim_metrics = {}
        if self.overrides:
            now = time.time()
            # Remove expired
            expired = [k for k, v in self.overrides.items() if v.get('until', 0) < now]
            for k in expired:
                del self.overrides[k]
                
            # Check if we have an active simulation type
            if 'simulation_type' in self.overrides:
                # Use M17 logic to generate chaos
                sim_type = self.overrides['simulation_type']['value']
                sim_metrics = self.sim.generate_metrics_only(sim_type)
            
        # Collect
        # Helper to get override or actual
        def get_val(key, default):
            # Priority: M17 generated > override > default
            if key in sim_metrics:
                return sim_metrics[key]
            
            # Fallback to old override system if needed
            if key in self.overrides:
                ov = self.overrides[key]
                return ov['value']
            return default

        ms = self.collector.collect(
            latency_p95_ms=get_val('latency_p95_ms', lat),
            retry_pct=get_val('retry_pct', 0.0),
            airtime_busy_pct=get_val('airtime_busy_pct', 0.0),
            in_rate=in_rate_mbps,
            out_rate=out_rate_mbps,
            cpu_load=cpu,
            mem_load=mem,
            signal_strength_pct=signal,
            jitter_ms=jit,
            # Extended fields
            channel=channel,
            radio_type=radio,
            band=band,
            phy_rate_mbps=tx,
            phy_rx_rate_mbps=rx,
            dns_status=dns,
            # Injected fields
            mesh_flap_count=get_val('mesh_flap_count', 0),
            wan_sinr_db=get_val('wan_sinr_db', None)
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
