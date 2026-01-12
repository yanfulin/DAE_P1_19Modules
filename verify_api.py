import requests
import json
import time

try:
    print("Waiting for server to collect first sample...")
    time.sleep(3) # Wait for first tick
    resp = requests.get("http://localhost:8000/metrics")
    print("Metrics Status:", resp.status_code)
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    if "jitter_ms" in data:
        print("VERIFICATION SUCCESS: jitter_ms found.")
    else:
        print("VERIFICATION FAILED: jitter_ms MISSING.")

    if "latency_p95_ms" in data and data["latency_p95_ms"] != 10.0:
         print(f"VERIFICATION SUCCESS: latency_p95_ms is real: {data['latency_p95_ms']}")
    else:
         print(f"VERIFICATION WARNING: latency_p95_ms is {data.get('latency_p95_ms')}")

except Exception as e:
    print("Error:", e)
