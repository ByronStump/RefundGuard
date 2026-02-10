from monitor import monitor_process


def main():
    process_name = input("\nInput Steam game name to find: ").strip()
    
    if not process_name:
        print("Game name cannot be empty.")
        return
    interval_input = input("\nPrint status every how many minutes? (default 15): ").strip()
    print(f"\nAttempting to find: {process_name}")
    try:
        status_interval_minutes = int(interval_input) if interval_input else 15
    except ValueError:
        status_interval_minutes = 15

    monitor_process(process_name, status_interval_minutes=status_interval_minutes)
    
if __name__ == "__main__":
    main()