import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_incident(type_name, duration=10):
    print(f"\n--- Testing Incident: {type_name} ---")
    
    # Trigger
    resp = requests.post(f"{BASE_URL}/simulate/incident?type={type_name}&duration={duration}")
    if resp.status_code != 200:
        print(f"FAILED to trigger: {resp.text}")
        return False
    print(f"Triggered: {resp.json()}")

    # Monitor
    print("Monitoring metrics...")
    for i in range(5):
        time.sleep(1)
        m_resp = requests.get(f"{BASE_URL}/metrics")
        if m_resp.status_code == 200:
            m = m_resp.json()
            print(f"[{i}s] Retry: {m.get('retry_pct', 0):.2f}%, Airtime: {m.get('airtime_busy_pct', 0):.2f}%, Latency: {m.get('latency_p95_ms', 0):.2f}ms")
        else:
            print("Failed to get metrics")

    return True

if __name__ == "__main__":
    try:
        # Test Oscillating
        test_incident("oscillating", duration=30)
        
        # Test Degrading
        test_incident("degrading", duration=30)
        
    except Exception as e:
        print(f"Error: {e}")
