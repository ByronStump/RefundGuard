import subprocess
import time
import threading
import os


def find_subprocess(process):
    pids = subprocess.run(["ps", "-e", "-o", "pid,cmd"], capture_output=True, text=True)
    for line in pids.stdout.splitlines():
        print(line)
        try:
            pid, cmd = line.strip().split(" ", 1)
            if process in cmd:
                return int(pid), cmd
        except ValueError:
            continue
    return None, None

def monitor_process(process_name):
    while True:
        pid, cmd = find_subprocess(process_name)
        if (pid):
            print(f"Found process PID: {pid}\nLaunched with CMD: {cmd}")
            break
        time.sleep(10)
