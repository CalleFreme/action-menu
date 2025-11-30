# Action Menu

Action Menu is a Tkinter-based productivity cockpit that helps you plan SMART goals, design habits, schedule deep-work blocks, capture journal insights, and keep quick thoughts triaged. Everything persists locally via JSON so you can close the app, come back later, and pick up exactly where you left off.

## Features

- North-star prompts for values, milestones, and energy rituals.
- SMART goal designer with category tagging for later analytics.
- Habit builder plus “weekly menu” board to organize actions across time horizons.
- Deep-work timer that logs effort, captures flow/emotion checkouts, and summarizes hours by category.
- Daily journal with NLP-powered suggestion extraction that can spawn goals, habits, or quick actions.
- Quick capture inbox with simple Inbox → Today → Later → Archived workflow.
- JSON persistence via `StorageManager`, keeping state in `action_menu_state.json` inside your user data directory.
- Modular codebase (`models.py`, `storage.py`, `journal_ai.py`, `action_menu.py`) to ease future experimentation.

## Requirements

- Python 3.11+ with Tkinter support (Windows Store builds are fine; ensure Tcl/Tk is installed).
- Git (for cloning).
- No third-party dependencies—everything runs on the standard library.

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/CalleFreme/action-menu.git
   cd action-menu
   ```

2. **Create a virtual environment** (optional but recommended)

   ```bash
   python -m venv .venv
   ```

3. **Activate the environment**

   - **Git Bash / PowerShell / Command Prompt on Windows**

     ```bash
     source .venv/Scripts/activate      # Git Bash
     # or
     .\.venv\Scripts\activate         # cmd.exe / PowerShell
     ```

   - **macOS / Linux**

     ```bash
     source .venv/bin/activate
     ```

4. **(Optional) Verify Tk is available**

   ```bash
   python - <<'PY'
   import tkinter
   tkinter.Tk().destroy()
   print('Tk OK')
   PY
   ```

   If this raises `Can't find a usable init.tcl`, reinstall Python with the Tcl/Tk option (on Windows) or `sudo apt install python3-tk` on Debian-based systems.

## Running the App

With the environment active:

```bash
python action_menu.py
```

The Tkinter window opens with tabs for North Star, SMART Goals, Habits & Actions, Weekly Menu, Time & Flow, Journal, Quick Capture, and Integrations.

## Running Tests

Unit tests live under `tests/` and use Python's built-in `unittest` discovery.

```bash
python -m unittest discover
```

This exercises the storage round-trips and journal suggestion helpers. Add new tests next to the related modules and `discover` will pick them up automatically.

## Data & Persistence

- State lives in `action_menu_state.json` under your user-specific app directory (see `storage.get_default_store_path`).
- You can back up or version-control that file to move your data between machines.
- Deleting the file resets the app to a clean slate.

## Troubleshooting

- **Tkinter import errors**: ensure the Python build ships with Tk. On Windows, download Python from python.org and check “tcl/tk and IDLE”.
- **State resets unexpectedly**: confirm the process can write to the store path (check filesystem permissions).
- **UI looks cramped**: resize the window; layout uses responsive Tk grid/pack.

## Roadmap Ideas

- Real calendar sync via Google API.
- Analytics dashboards for time allocation and habit adherence.
- Cloud storage or multi-device sync.

Happy building! Experiment with the tabs, integrate them into your weekly review, and adapt the code to suit your rituals.
