# Steam 2 Hour Trial

A simple Windows-only utility that watches a Steam game process and closes it when your playtime reaches 2 minutes before you are unable to refund the game.

## Requirements
- Windows 10/11
- Python 3.11+ (3.13 works)

## Install
No dependencies required. Just clone or download the repo.

## Run
From the project root:

```powershell
python src\main.py
```

You will be prompted for:
- The Steam game name (e.g., `Arc Raiders`)
- How often to print status updates (minutes)

## Notes
- The tool matches the **executable name** and ignores `.exe`, dashes, and spaces.
- It exits gracefully if the game is closed early or if you press `Ctrl+C`.
