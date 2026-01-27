# Cleanup Notes
*Run audit prompts to populate this file.*

## Architecture Ideas
*   **server.py**: Consider splitting duplicate logic into:
    *   `modules/import_manager.py`
    *   `modules/raycast_manager.py`
    *   `modules/udp_listener.py`
    *   `modules/websocket_server.py`

## Phase 2: Deferred Optimizations

### Raycast.lua (Pending Audit)
*   **Optimization**: `get_camera_intersection` currently calls `LoGetCameraPosition` and `LoGetSelfData` internally. These are redundant as `RouteManagerExport.lua` (and potential other callers) already have this data.
*   **Plan**: Refactor `get_camera_intersection` to accept `camera_data` and `self_data` as arguments.
*   **Caller Update**: When `Raycast.lua` is updated, `RouteManagerExport.lua` must also be updated to pass the `camPos` and `o` (self object) it has already fetched in its main loop.
*   **Done**: This was completed in Phase 2 Raycast step.

### RouteManagerExport.lua (Future)
*   **Update**: Once `Raycast.lua` signature is updated, update the `request_raycast` block to pass the cached data.
*   **Done**: This was completed in Phase 2 Raycast step.

### server.py
*   **Legacy Code**: `command_looper` (Line ~969) is used for continuous command firing (loops). Frontend usage is unconfirmed.
    *   *Status*: **KEEP** for now (Block 2).
    *   *Action*: Mark for potential deletion if frontend audit confirms `dcs_loop_start` is never emitted.

### Alignment Verification (NavComputer)
*   **Context**: `RouteManagerExport.lua` sends Heading/Pitch/Bank in **DEGREES**. `utils.py` converts them back to **RADIANS** for `math` library operations.
*   **Action**: Future Test Required. Verify that `get_rotation_matrix` output aligns perfectly with DCS World coordinates (Test: Bank 90 deg -> Matrix should rotate vector 90 deg). Currently implicitly trusted based on code inspection.
