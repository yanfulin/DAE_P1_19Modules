import subprocess
import sys

def debug_netsh():
    print("Running netsh wlan show interfaces...")
    try:
        # maximize potential for capturing output
        raw = subprocess.check_output("netsh wlan show interfaces", shell=True)
        print(f"Raw len: {len(raw)}")
        print(f"Raw hex: {raw[:100].hex()}...") 
        
        encodings = ['cp950', 'utf-8', 'mbcs', 'big5']
        decoded = None
        for enc in encodings:
            try:
                decoded = raw.decode(enc)
                print(f"Successfully decoded with {enc}")
                print("-" * 20)
                print(decoded)
                print("-" * 20)
                break
            except Exception as e:
                print(f"Failed with {enc}: {e}")
        
        if decoded:
            import re
            # Test regexes from adapter
            patterns = {
                "Signal": [r"Signal\s*:\s*(\d+)%", r"信號\s*:\s*(\d+)%", r"信号\s*:\s*(\d+)%"],
                "TxRate": [r"Transmit rate \(Mbps\)\s*:\s*(\d+)", r"傳輸速率 \(Mbps\)\s*:\s*(\d+)", r"传输速率 \(Mbps\)\s*:\s*(\d+)"]
            }
            
            for name, pats in patterns.items():
                found = None
                for p in pats:
                    m = re.search(p, decoded)
                    if m:
                        found = m.group(1)
                        print(f"Matched {name} with pattern '{p}': {found}")
                        break
                if found is None:
                    print(f"FAILED to match {name}")

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    debug_netsh()
