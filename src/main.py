import subprocess
def main():
    process_name = input("Input process name to find: ")
    print(f"Attempting to find: {process_name}")
    pid, cmd = find_subprocess(process_name)
    if pid:
        print(f"Found process PID: {pid}\nLaunched with CMD: {cmd}")
    else:
        print(f"No PID found for {process_name}")
def find_subprocess(process):
    pids = subprocess.run(["ps", "-e", "-o", "pid,cmd"], capture_output=True, text=True)
    for line in pids.stdout.splitlines():
        pid, cmd = line.strip().split(" ", 1)
        if process in cmd:
            return int(pid), cmd
    return None, None
    
    
if __name__ == "__main__":
    main()