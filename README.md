# Steam 2 Hour Trial

A simple Windows-only utility that watches a Steam game process and closes it when your playtime reaches approximately 5 minutes before you are unable to refund the game.

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
- Total allowed minutes (default 115)
- How often to print status updates (minutes)
- Whether to use Steam’s saved playtime (recommended)

## Notes
- The tool matches the **executable name** and ignores `.exe`, dashes, spaces, and punctuation.
- If Steam playtime is enabled, it uses local Steam files to estimate remaining time, then uses the timer for the current session.
- If total playtime is already over the limit, the tool exits without closing the game.
- It exits gracefully if the game is closed early or if you press `Ctrl+C`.
