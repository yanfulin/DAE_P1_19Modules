import requests
import time

BASE_URL = "http://localhost:8000"

def check(name, method, url):
    print(f"Checking {name}...", end=" ")
    try:
        if method == "GET":
            r = requests.get(url)
        else:
            r = requests.post(url)
        
        if r.status_code == 200:
            print("OK")
            print(r.json())
        else:
            print(f"FAIL ({r.status_code})")
            print(r.text)
    except Exception as e:
        print(f"ERROR: {e}")

check("Install Verify", "GET", f"{BASE_URL}/install_verify")
check("Simulate Incident", "POST", f"{BASE_URL}/simulate/incident?type=latency&duration=1")
check("OBH Trigger", "POST", f"{BASE_URL}/obh/trigger")
