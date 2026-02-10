import subprocess
import time
import os
import csv
import io
import re
from datetime import datetime, timezone

def _make_process_regex(process):
    tokens = []
    for t in process.strip().split():
        t = re.sub(r"[^a-zA-Z0-9]+", "", t)
        if t:
            tokens.append(re.escape(t))
    if not tokens:
        tokens = [re.escape(process.strip())]
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

def monitor_process(process_name, limit_minutes=115, status_interval_minutes=15, use_steam_playtime=False):
    try:
        while True:
            pid, cmd = find_subprocess(process_name)
            if pid:
                print(f"\nFound process PID: {pid}\nExecutable: {cmd}")
                break
            time.sleep(10)

        remaining_seconds = limit_minutes * 60
        steam_used = False

        if os.name == "nt":
            if use_steam_playtime:
                playtime_minutes = _get_steam_playtime_minutes_windows(process_name)
                if playtime_minutes is not None:
                    remaining_seconds = max(0, (limit_minutes * 60) - int(playtime_minutes * 60))
                    print(f"\nSteam playtime (local): {playtime_minutes:.2f} minutes")
                    steam_used = True

                    if remaining_seconds <= 0:
                        print("\nTime limit already exceeded. Exiting without closing the game.")
                        return

            # Only adjust by process start time if Steam playtime was NOT used
            if not steam_used:
                start_time = _get_process_start_time_windows(pid)
                if start_time:
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    remaining_seconds = max(0, remaining_seconds - int(elapsed))

                    if remaining_seconds <= 0:
                        print("\nTime limit already exceeded. Exiting without closing the game.")
                        return

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

def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())

def _find_steam_root_windows() -> str | None:
    env_path = os.environ.get("STEAM_PATH")
    if env_path and os.path.isdir(env_path):
        return env_path
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    default_path = os.path.join(program_files_x86, "Steam")
    return default_path if os.path.isdir(default_path) else None

def _get_steam_library_paths_windows(steam_root: str) -> list[str]:
    paths = []
    if not steam_root:
        return paths

    steamapps = os.path.join(steam_root, "steamapps")
    if os.path.isdir(steamapps):
        paths.append(steamapps)

    library_vdf = os.path.join(steamapps, "libraryfolders.vdf")
    if not os.path.isfile(library_vdf):
        return paths

    try:
        with open(library_vdf, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for match in re.finditer(r'"path"\s*"([^"]+)"', content, re.IGNORECASE):
            raw = match.group(1)
            path = raw.replace("\\\\", "\\")
            steamapps_path = os.path.join(path, "steamapps")
            if os.path.isdir(steamapps_path):
                paths.append(steamapps_path)
    except Exception:
        return paths

    # Deduplicate while preserving order
    seen = set()
    unique_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)
    return unique_paths

def _parse_appmanifest(path: str) -> dict:
    data = {}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for key in ("appid", "name", "LastPlayed", "HoursPlayed"):
            match = re.search(rf'"{key}"\s*"([^"]+)"', content, re.IGNORECASE)
            if match:
                data[key.lower()] = match.group(1)
    except Exception:
        return {}
    return data

def _find_steam_app_by_process_name_windows(process_name: str, steam_root: str | None = None) -> dict | None:
    steam_root = steam_root or _find_steam_root_windows()
    if not steam_root:
        return None

    target = _normalize_name(process_name)
    if not target:
        return None

    for steamapps_path in _get_steam_library_paths_windows(steam_root):
        try:
            for filename in os.listdir(steamapps_path):
                if not filename.startswith("appmanifest_") or not filename.endswith(".acf"):
                    continue
                manifest_path = os.path.join(steamapps_path, filename)
                data = _parse_appmanifest(manifest_path)
                name = data.get("name", "")
                if not name:
                    continue
                name_norm = _normalize_name(name)
                if name_norm and (name_norm in target or target in name_norm):
                    return data
        except Exception:
            continue
    return None

def _get_steam_playtime_minutes_windows(process_name: str, steam_root: str | None = None) -> float | None:
    steam_root = steam_root or _find_steam_root_windows()
    if not steam_root:
        return None

    data = _find_steam_app_by_process_name_windows(process_name, steam_root)
    if not data:
        return None

    appid = data.get("appid")
    if appid:
        playtime_local = _get_playtime_from_localconfig(appid, steam_root)
        if playtime_local is not None:
            return playtime_local

    hours_str = data.get("hoursplayed")
    if not hours_str:
        return None
    try:
        return float(hours_str) * 60.0
    except ValueError:
        return None
    
def _get_steam_user_config_paths_windows(steam_root: str) -> list[str]:
    paths = []
    if not steam_root:
        return paths
    userdata = os.path.join(steam_root, "userdata")
    if not os.path.isdir(userdata):
        return paths
    try:
        for user_id in os.listdir(userdata):
            config_path = os.path.join(userdata, user_id, "config", "localconfig.vdf")
            if os.path.isfile(config_path):
                paths.append(config_path)
    except Exception:
        return paths
    return paths

def _get_playtime_from_localconfig(appid: str, steam_root: str) -> float | None:
    if not appid:
        return None
    appid_pattern = re.escape(appid)
    playtime_re = re.compile(rf'"{appid_pattern}"\s*{{[^}}]*?"Playtime"\s*"(\d+)"', re.IGNORECASE | re.DOTALL)

    for config_path in _get_steam_user_config_paths_windows(steam_root):
        try:
            with open(config_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            match = playtime_re.search(content)
            if match:
                return float(match.group(1))  # already minutes
        except Exception:
            continue
    return None