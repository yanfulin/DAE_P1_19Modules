import os
import subprocess
import time

def kill_port_8000():
    print("Finding process on port 8000...")
    try:
        # Run netstat to find PID
        cmd = "netstat -ano | findstr :8000"
        output = subprocess.check_output(cmd, shell=True).decode()
        lines = output.strip().split('\n')
        for line in lines:
            parts = line.split()
            # Proto Local Address Foreign Address State PID
            # TCP    0.0.0.0:8000   0.0.0.0:0       LISTENING   1234
            if ":8000" in parts[1] and "LISTENING" in parts[-2]:
                pid = parts[-1]
                print(f"Found server PID: {pid}. Killing...")
                os.system(f"taskkill /PID {pid} /F")
                return True
    except subprocess.CalledProcessError:
        print("No process found on port 8000.")
    except Exception as e:
        print(f"Error: {e}")
    return False

if __name__ == "__main__":
    kill_port_8000()
