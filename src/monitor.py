import subprocess
import time
import os
import csv
import io
import re
from datetime import datetime, timezone

def _make_process_regex(process):
    tokens = [re.escape(t) for t in process.strip().split()]
    pattern = r"[ \-._]*".join(tokens) + r"(?:\.exe)?"
    return re.compile(pattern, re.IGNORECASE)

def _run_tasklist(args):
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return None

def _find_subprocess_windows(process):
    result = _run_tasklist(["tasklist", "/v", "/fo", "csv"])
    if result is None or not result.stdout:
        result = _run_tasklist(["tasklist", "/fo", "csv"])
        if result is None or not result.stdout:
            return None, None

    matcher = _make_process_regex(process)
    reader = csv.reader(io.StringIO(result.stdout))
    headers = next(reader, None)
    for row in reader:
        # Columns: Image Name, PID, Session Name, Session#, Mem Usage, Status, User Name, CPU Time, Window Title
        if len(row) < 2:
            continue
        image_name = row[0]
        pid_str = row[1]
        if not image_name.lower().endswith(".exe"):
            continue
        if matcher.search(image_name):
            try:
                return int(pid_str), image_name
            except ValueError:
                continue
    return None, None

def find_subprocess(process):
    if os.name == "nt":
        return _find_subprocess_windows(process)
    matcher = _make_process_regex(process)
    pids = subprocess.run(["ps", "-e", "-o", "pid,cmd"], capture_output=True, text=True)
    for line in pids.stdout.splitlines():
        try:
            pid, cmd = line.strip().split(" ", 1)
            if matcher.search(cmd):
                return int(pid), cmd
        except ValueError:
            continue
    return None, None

def _is_process_running_windows(pid: int) -> bool:
    result = _run_tasklist(["tasklist", "/fi", f"PID eq {pid}", "/fo", "csv"])
    if result is None or not result.stdout:
        return False
    return str(pid) in result.stdout

def monitor_process(process_name, limit_minutes=1, status_interval_minutes=15):
    try:
        while True:
            pid, cmd = find_subprocess(process_name)
            if pid:
                print(f"\nFound process PID: {pid}\nExecutable: {cmd}")
                break
            time.sleep(10)

        remaining_seconds = limit_minutes * 60
        if os.name == "nt":
            start_time = _get_process_start_time_windows(pid)
            if start_time:
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                remaining_seconds = max(0, remaining_seconds - int(elapsed))

        interval = max(60, int(status_interval_minutes * 60))
        while remaining_seconds > 0:
            if os.name == "nt" and not _is_process_running_windows(pid):
                print("\nProcess ended early. Exiting.")
                return
            print(f"\nTime remaining: {remaining_seconds // 60} minutes")
            sleep_for = min(interval, remaining_seconds)
            time.sleep(sleep_for)
            remaining_seconds -= sleep_for

        if os.name == "nt":
            _terminate_process_windows(pid)
        print("\nTime limit reached. Process closed.")
    except KeyboardInterrupt:
        print("\nCancelled by user. Exiting gracefully.")
        
def _get_process_start_time_windows(pid: int):
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-Process -Id {pid}).StartTime.ToUniversalTime().ToString('o')",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        value = result.stdout.strip()
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None

def _terminate_process_windows(pid: int):
    subprocess.run(
        ["taskkill", "/PID", str(pid), "/F"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
