
import sys
import os

# Improve import path handling
sys.path.append(os.getcwd())

from dae_p1.adapters.windows_wifi_adapter import WindowsWifiAdapter

try:
    print("Initializing Adapter...")
    adapter = WindowsWifiAdapter()
    print("Getting Signal Strength...")
    res = adapter._get_signal_strength()
    print(f"Result: {res}")
    
    if res[0] == 0 and res[4] is None:
        print("FAIL: Signal is 0 and Rate is None")
    else:
        print("PASS: Got valid signal/rate")

except Exception as e:
    print(f"Error: {e}")
