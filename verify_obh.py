import requests
import json

BASE_URL = "http://localhost:8000"

def verify_obh():
    print("Triggering OBH...", end=" ")
    try:
        r = requests.post(f"{BASE_URL}/obh/trigger")
        if r.status_code == 200:
            data = r.json()
            if "bundle" in data:
                print("OK - Bundle found in response.")
                print(f"Keys in bundle: {list(data['bundle'].keys())}")
            else:
                print("FAIL - Bundle NOT found in response.")
                print(f"Response keys: {list(data.keys())}")
        else:
            print(f"FAIL ({r.status_code})")
            print(r.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verify_obh()
