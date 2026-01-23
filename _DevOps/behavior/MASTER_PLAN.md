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
- [x] **Final Verification:** Perform a final "clean" backup of the new workflow files.

### Phase 2: Refactoring & Cleanup (Deep Audit)
**Methodology:**
*   **One File at a Time:** Focus on the "Current File". Read others only for context.
*   **Cross-File Edits:** If an edit requires changing another file, log it in `CLEANUP_NOTES.md` for later. Do not context-switch.
*   **Analysis Goals:**
    *   Identify duplicate variables/functions.
    *   Refine logic and file structure.
    *   Identify and explain deprecated/unused code (with snippets).
*   **Sub-Stages per File:**
    1.  Read Literature (if available).
    2.  Lift & Dissect (Analyze content).
    3.  Discuss & Analyze (Propose improvements).
    4.  Apply Changes.
    5.  Test & Verify.

**Audit Queue (Upstream -> Downstream):**
1.  [x] **Scripts/RouteManagerExport.lua** (The Data Source)
2.  [x] **Scripts/Hooks/RouteManagerHook.lua** (The Game Hook)
3.  [x] **Scripts/Raycast.lua** (Spatial Logic)
4.  [x] **server.py** (The Backend Hub)
    *   *Extracted:* `modules/tcp_connector.py` (TCP Logic)
    *   *Potential Extraction:* `import_manager`, `raycast_manager`, `udp_listener`, `websocket_server`
5.  [x] **modules/overlay.py**
6.  [x] **modules/nav_computer.py**
7.  [x] **modules/mouse_tracker.py**
8.  [x] **modules/utils.py**
9.  [x] **static/js/hud.js** (Frontend Display)
10. [ ] **static/js/map.js** (Frontend Map)
11. [ ] **static/js/overlay.js** (Frontend Logic)
12. [ ] **static/hud_profiles/** (HUD Templates)

### Phase 3: Feature Expansion (User Requests)
- [ ] **Virtual Pointer Expansion:**
    - [x] **1. Input Manager Upgrade (`modules/input_manager.py`)** (Backend)
        - [x] Add Axis Support (`pygame.JOYAXISMOTION` -> deadzone -> normalize).
        - [x] Add Mouse Motion (Relative via hook, Absolute via screen mapping).
        - [x] Add Digital Directional Logic (Buttons -> Axis).
        - [x] Unify Signals: `pointer_motion(dx, dy, mode)` and `pointer_button(action, state)`.
    - [x] **2. Overlay UI (`modules/overlay.py`)** (Configuration)
        - [x] Create `PointerTab` Class.
        - [x] Implement Activation Toggle & Bind.
        - [x] Implement Movement Source Config (Analog/Digital).
        - [x] Implement Interaction Config (Click/Hold/Drag).
        - [x] Add Sensitivity & Deadzone Sliders.
    - [x] **3. Server Bridge (`server.py`)** (State & Relay)
        - [x] Implement `virtual_pointer_active` state & `virtual_cursor_pos`.
        - [x] Handle `virtual_pointer_update` (Motion Relay).
        - [x] Handle `virtual_click` (Interaction Relay).
        - [x] Persist settings in `hud_config.json`.
    - [x] **4. Frontend Map (`static/js/map.js` & `Templates/map.html`)** (Visuals)
        - [x] Add `#virtual-cursor` element & styling.
        - [x] Implement VirtualPointer object with state machine (IDLE/HOVER/DRAG).
        - [x] Implement hit testing for waypoints, POIs, units, player.
        - [x] Implement click interactions (< 500ms press).
        - [x] Implement drag interactions for waypoints.
        - [x] Align socket events with server API.
        - [x] Block native mouse events when Pointer Mode is Active.
    - [ ] **5. Enhanced Visual Feedback** (Phase 3.5 - Optional)
        - [ ] Cursor shape changes when over draggable objects.
        - [ ] Highlight hovered objects with glow/outline.
        - [ ] Edge-snapping for waypoints.
        - [ ] Custom cursors per interaction mode.
    - [ ] **6. Advanced Interactions** (Phase 3.6 - Optional)
        - [ ] Double-click support for waypoint editing.
        - [ ] Right-click context menu for markers.
        - [ ] Multi-select with modifier keys.
        - [ ] Drag POIs (not just waypoints).
    - [ ] **7. Performance Optimization** (Phase 3.7 - Optional)
        - [ ] Throttle hit testing (requestAnimationFrame).
        - [ ] Spatial indexing for large object counts.
        - [ ] Minimize DOM updates during drag.
        - [ ] Configurable detection radius (DPI-aware).

## 📝 Known Issues / Constraints
* **Backups:** Zip files are stored in `.\_DevOps\backups`.
* **Node.js:** Required for `npm` commands (installed via winget).
