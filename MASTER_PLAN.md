# PROJECT: DCS Route Manager
**Status:** Active
**Current Focus:** Workflow & Backup Infrastructure

## 📌 Context Map (For AI Reference)
* **.scripts/:** Backup and Undo scripts (`smart-backup.ps1`, `smart-undo.ps1`).
* **project_diary.md:** History of changes and backup logs.
* **.cursorrules:** Agent Behavior Protocols (Constitution).
* **package.json:** NPM scripts for agent commands.

## 🛠️ Task Queue (The "Ticket" System)
**Instructions for Agent:** Read this list. Execute ONLY the first unchecked item `[ ]`. Do not touch subsequent items.

### Phase 1: Workflow Setup (Priority)
- [x] **Git Init:** Initialize repo and remote.
- [x] **Backup System:** Implement `smart-backup.ps1` and `.cursorrules`.
- [x] **Project Diary:** Create diary with tagging support.
- [x] **Undo System:** Create `smart-undo.ps1`.
- [x] **Constitution:** Update `.cursorrules` with strict protocols.
- [ ] **Final Verification:** Perform a final "clean" backup of the new workflow files.

### Phase 2: Refactoring & Cleanup
- [ ] **Audit:** List all duplicate variables in Lua/JS files (output to `CLEANUP_NOTES.md`).

## 📝 Known Issues / Constraints
* **Backups:** Zip files are stored in `.\backups`.
* **Node.js:** Required for `npm` commands (installed via winget).
