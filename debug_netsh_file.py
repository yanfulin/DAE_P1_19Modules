import subprocess

def dump_netsh():
    with open("netsh_debug.txt", "wb") as f:
        try:
            raw = subprocess.check_output("netsh wlan show interfaces", shell=True)
            f.write(raw)
        except Exception as e:
            f.write(f"Error: {e}".encode("utf-8"))

if __name__ == "__main__":
    dump_netsh()
