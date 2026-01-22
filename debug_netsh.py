
import subprocess

try:
    output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode("cp950", errors="ignore")
    print(output)
except Exception as e:
    print(e)
