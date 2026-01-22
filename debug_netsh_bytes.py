
import subprocess

try:
    output = subprocess.check_output("netsh wlan show interfaces", shell=True)
    with open("netsh_output.txt", "wb") as f:
        f.write(output)
    print("Dumped to netsh_output.txt")
except Exception as e:
    print(e)
