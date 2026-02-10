from monitor import monitor_process


def main():
    print("\nSteam 2‑Hour Trial Helper")
    print("Tip: Enter the game’s name as it appears in Steam.\n")

    process_name = input("Game name: ").strip()
    if not process_name:
        print("Game name cannot be empty.")
        return

    interval_input = input("Status update interval in minutes (default 15): ").strip()
    try:
        status_interval_minutes = int(interval_input) if interval_input else 15
    except ValueError:
        status_interval_minutes = 15

    use_steam_playtime_input = input("Use Steam’s saved playtime? (recommended) [Y/n]: ").strip().lower()
    use_steam_playtime = use_steam_playtime_input in ("", "y", "yes")

    print(f"\nLooking for: {process_name}")

    monitor_process(
        process_name,
        status_interval_minutes=status_interval_minutes,
        use_steam_playtime=use_steam_playtime,
    )

    
if __name__ == "__main__":
    main()