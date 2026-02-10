import time
import subprocess
import threading
from monitor import monitor_process


def main():
    process_name = input("Input Steam game name to find: ").strip()
    print(f"Attempting to find: {process_name}")
    if not process_name:
        print("Game name cannot be empty.")
        return
    monitor_process(process_name)
    
if __name__ == "__main__":
    main()