
import sqlite3
import json

db_path = "data/cpe_metrics.db"

print(f"Inspecting {db_path}...")

try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, ts, data FROM metrics ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} rows.")
        for r in rows:
            rid, ts, data_str = r
            print(f"--- ID: {rid}, TS: {ts} ---")
            try:
                data = json.loads(data_str)
                # Print key metrics
                keys_to_check = ["latency_p95_ms", "rtt_ms", "phy_rate_mbps", "wifi_retry_pct"]
                for k in keys_to_check:
                    val = data.get(k, "MISSING")
                    print(f"  {k}: {val}")
            except Exception as e:
                print(f"  JSON Error: {e}")

except Exception as e:
    print(f"DB Error: {e}")
