# GitHub Protocol & Branching Strategy

## Core Philosophy
We maintain a strict separation between **Source Code** and **Release Binaries**.
- **User Source (`main`)**: Pure python code, assets, and raw data. NO binaries. NO dev tools.
- **Public Release (`release`)**: Compiled executable and game hook, structured exactly as the DCS Mod folder.

## Branch Structure

### 1. `main` (Source)
- **Content**:
    - `RouteManager.py`
    - `modules/`
    - `static/`
    - `Templates/`
    - `DATA/`
    - `Scripts/` (Source version of Lua scripts)
- **Excluded** (via `.gitignore` or script logic):
    - `_DevOps/`
    - `.cursorrules`, `task.md`, etc.
    - `build/`, `dist/`
    - Virtual Environment
- **Sync Method**: `_DevOps/scripts/git_sync_main.ps1`

### 2. `release` (Deployment)
- **Content** (DCS Mod Structure):
    - `Scripts/Hooks/RouteManagerHook.lua`
    - `Mods/tech/RouteManager/`
        - `bin/RouteManager.exe`
        - `data/`
        - `static/`
        - `Templates/`
- **Sync Method**: `_DevOps/scripts/git_sync_release.ps1`

## Automation Scripts

### `git_sync_main.ps1`
**Usage**: `.\_DevOps\scripts\git_sync_main.ps1`
- Switches to `main`.
- Force-adds only the allowed source folders.
- Commits with "Auto-Sync Source [Timestamp]".
- Pushes to origin.

### `git_sync_release.ps1`
**Usage**: `.\_DevOps\scripts\git_sync_release.ps1`
- **Builds** the project using PyInstaller.
- **Fetches** the latest Lua hook from your DCS Saved Games folder (`C:\Users\pino4\Saved Games\DCS.openbeta\Scripts\Hooks`).
- **Packages** everything into a temporary staging area.
- **Switches** to `release` branch (orphan).
- **Wipes** the previous release content.
- **Commits** the new build.
- **Pushes** to origin.

## Restoration (If disaster strikes)
- **Source**: Clone `main`. You will have the code, but not the dev tools (`_DevOps` is local-only, but recommended to back up periodically or keep in a separate `dev` branch if strict adherence allows).
    - *Correction*: `_DevOps` is ignored from `main`, so ensure you backup `_DevOps` separately or adjust protocol if cloud backup of dev tools is required. (Current instruction: `main` has base code `no rules, tests, behaviors, dev info`).
- **Release**: Download from `release` branch for a working mod.
