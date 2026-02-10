# RefundGuard

RefundGuard is a Windows-only helper that watches a Steam game and closes it shortly before you hit the 2‑hour refund limit.

## What you need
- Windows 10/11
- Python 3.11 or newer

If you don’t have Python yet:
- Download it here: https://www.python.org/downloads/
- During install, check **“Add Python to PATH”**

## Download the app
You can either:
- Click **Code → Download ZIP** on GitHub, then unzip it, or
- Clone the repo if you already use Git

## Run it
1. Open the folder you downloaded
2. Open a terminal in that folder
3. Run:

```powershell
python src\main.py
```

You’ll be asked:
- The Steam game name (as it appears in Steam)
- Status update interval (minutes)
- Whether to use Steam’s saved playtime (recommended)

## How it works
- RefundGuard matches the game’s **executable name** and ignores `.exe`, spaces, dashes, and punctuation.
- If Steam playtime is enabled, it reads your local Steam files to estimate remaining time, then uses the timer for the current session.
- If total playtime is already over the limit, the tool exits without closing the game.
- It exits gracefully if the game is closed early or if you press `Ctrl+C`.

## Troubleshooting
- **Game not found?** Try a simpler name (e.g., “Mirrors Edge” instead of “Mirror’s Edge”).
- **Steam installed in a custom location?** Set a `STEAM_PATH` environment variable to your Steam folder.
