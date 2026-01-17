-- Route Manager Hook (Block 1: Strict FSM & Heartbeat)
-- Compliant with "High-Reliability" Architecture

local routeManagerHook = {}

-- 1. Library Initialization & Path Setup
-- Safely add paths without duplication/errors
if package.path then
    package.path = package.path .. ";./Scripts/?.lua"
end
if package.cpath then
    package.cpath = package.cpath .. ";./Scripts/?.dll;./Scripts/socket/?.dll"
end

local socket                  = require("socket")
local json                    = require("json")
local lfs                     = require("lfs")

-- Configuration
local TCP_PORT                = 11002
local HEARTBEAT_RATE          = 0.5 -- 2Hz (Send every 0.5s)
local log_file_path           = lfs.writedir() .. "Logs/RouteManagerHook.log"

-- State
local tcp_server              = nil
local tcp_client              = nil
local last_heartbeat_time     = 0
local self_data_found         = false -- SMART POLLING FLAG
local last_world_objects_time = 0     -- Phase 2b Timer

-- Logging Helper
local function log_debug(msg)
    local f = io.open(log_file_path, "a")
    if f then
        f:write(string.format("[%s] %s\n", os.date("%H:%M:%S"), msg))
        f:close()
    end
end

-- TRIGGER: Local Player Enters Unit
function routeManagerHook.onPlayerEnterUnit(id)
    local my_id = net.get_my_player_id()
    if id == my_id then
        log_debug("👤 Local Player Entered Unit (ID: " .. tostring(id) .. "). Starting Smart Poll...")
        self_data_found = false
    end
end

local function setup_server()
    if tcp_server then
        log_debug("⚠️ Server already exists")
        return
    end

    log_debug("🔧 Creating TCP Socket...")
    local server, err = socket.tcp()
    if not server then
        log_debug("❌ Socket Create Failed: " .. tostring(err))
        return
    end

    -- Critical: setoption is the standard method (setsockopt is deprecated/missing)
    if server.setoption then
        server:setoption("reuseaddr", true)
    elseif server.setsockopt then
        server:setsockopt("reuseaddr", true)
    end

    -- Critical: Bind to * to listen on all interfaces
    local res, err = server:bind("*", TCP_PORT)
    if not res then
        log_debug("❌ Bind Failed: " .. tostring(err))
        return
    end

    res, err = server:listen(1)
    if not res then
        log_debug("❌ Listen Failed: " .. tostring(err))
        return
    end

    -- CRITICAL: Master socket must be non-blocking
    if server.settimeout then
        server:settimeout(0)
    end

    tcp_server = server
    log_debug("🎧 TCP Server LISTENING on *:" .. TCP_PORT)
    log_debug("✅ Block 1 FSM Initialized: Waiting for Client...")
end

-- Helper: Safe Send with Disconnect Handling
local function safe_send(payload)
    if not tcp_client then return end

    local i, err = tcp_client:send(payload)

    -- If error (closed, broken pipe, etc.)
    -- Note: 'timeout' on send usually means buffer full, which is rare for us but not a fatal disconnect.
    -- However, if server died, we likely get 'closed' or 'broken pipe'.
    if err and err ~= "timeout" then
        log_debug("❌ Send Failed (" .. tostring(err) .. "). Closing Connection.")
        tcp_client:close()
        tcp_client = nil
        self_data_found = false
    end
end

-- safe_frame: The Core FSM Loop
local function safe_frame()
    local current_time = os.clock()

    -- STATE: LISTENING
    if tcp_server and not tcp_client then
        local client, err = tcp_server:accept()
        if client then
            -- Transition to CONNECTED
            tcp_client = client
            self_data_found = false -- Reset logic on new connection too

            -- CRITICAL: Client must also be non-blocking
            if client.settimeout then client:settimeout(0) end
            if client.setoption then client:setoption("tcp-nodelay", true) end

            log_debug("🔗 Client Connected (Transition to CONNECTED). Starting Smart Poll...")
        end
    end

    -- STATE: CONNECTED
    if tcp_client then
        -- 1. Check for Disconnect (Read 0 bytes)
        -- In LuaSocket non-blocking, receive(0) checks buffer/status
        local data, err, partial = tcp_client:receive(0)
        if err == "closed" then
            tcp_client:close()
            tcp_client = nil
            self_data_found = false
            log_debug("❌ Client Disconnected (Receive Check)")
            return
        end

        -- 2. Phase 2a: Metadata Extraction (One-Shot Smart Poll)
        if not self_data_found and (current_time - last_heartbeat_time > 1.0) then
            -- Safety: Wrap API access in pcall
            local status, meta = pcall(function()
                local data = {}

                -- 1. Identity (Net API)
                local my_id = net.get_my_player_id()
                local p_info = net.get_player_info(my_id)
                if p_info then
                    data.player_name = p_info.name or "Unknown"
                    data.unit_id = p_info.slot or 0
                else
                    return nil -- Retry if net info not ready
                end

                -- 2. Unit Context (Export API)
                -- We ONLY want the Name, not the physics
                if Export and Export.LoGetSelfData then
                    local lo_data = Export.LoGetSelfData()
                    if lo_data then
                        data.unit_name = lo_data.Name or "Unknown"
                    else
                        -- If LoGetSelfData is nil, likely not spawned yet
                        return nil
                    end
                else
                    -- If Export not available, might be Mission Scripting restriction
                    return nil
                end

                return data
            end)

            if status and meta then
                -- LOG BEFORE SEND
                log_debug(string.format("👤 METADATA: Player=%s, Unit=%s", meta.player_name, meta.unit_name))

                local packet = {
                    type = "metadata",
                    data = meta
                }

                local payload = json:encode(packet) .. "\n"
                safe_send(payload)

                self_data_found = true -- STOP POLLING
                log_debug("✅ Sent Metadata Packet. Polling Stopped.")
            else
                -- Still nil (Cockpit not ready). Keep polling next heartbeat.
            end
        end

        -- 3. Phase 2b: World Objects (Optimized 1Hz Loop)
        local WORLD_RATE = 1.0

        if current_time - last_world_objects_time > WORLD_RATE then
            local t0 = os.clock()

            local status, world_objects = pcall(function()
                if Export and Export.LoGetWorldObjects then
                    return Export.LoGetWorldObjects()
                end
                return nil
            end)

            local t1 = os.clock() -- API Time

            if status and world_objects then
                -- OPTIMIZATION: Filter minimal data
                local clean_list = {}
                local count = 0

                for id, obj in pairs(world_objects) do
                    local minimal_obj = {
                        id = id,
                        name = obj.Name or "Unknown",
                        type = (obj.Type and obj.Type.level2) or 0,
                        coalition = obj.CoalitionID or 0,
                        country = obj.CountryID or 0,
                        lat = (obj.LatLongAlt and obj.LatLongAlt.Lat) or 0,
                        long = (obj.LatLongAlt and obj.LatLongAlt.Long) or 0,
                        alt = (obj.LatLongAlt and obj.LatLongAlt.Alt) or 0,
                        heading = obj.Heading or 0
                    }
                    table.insert(clean_list, minimal_obj)
                    count = count + 1
                end

                local t2 = os.clock() -- Filter Time

                local packet = {
                    type = "theater_state",
                    data = clean_list
                }

                local payload = json:encode(packet) .. "\n"

                local t3 = os.clock() -- JSON Time

                -- Send (Safe)
                safe_send(payload)

                local t4 = os.clock() -- Net Time

                -- LOG TIMING to prove Filtering is fast
                local dt_api = (t1 - t0) * 1000
                local dt_filter = (t2 - t1) * 1000
                local dt_json = (t3 - t2) * 1000
                local dt_net = (t4 - t3) * 1000
                local dt_total = (t4 - t0) * 1000

                if dt_total > 10 then -- Only log if it takes > 10ms
                    log_debug(string.format(
                        "⏱️ PERF: Total=%.1fms | API=%.1fms | Filter=%.1fms | JSON=%.1fms | NET=%.1fms | Objs=%d",
                        dt_total, dt_api, dt_filter, dt_json, dt_net, count))
                end
            end

            last_world_objects_time = current_time
        end

        -- 4. Heartbeat Logic (Keep alive, 2Hz)
        if current_time - last_heartbeat_time > HEARTBEAT_RATE then
            local packet = {
                type = "heartbeat",
                time = current_time,
                msg = "BLOCK_1_ALIVE"
            }
            local payload = json:encode(packet) .. "\n"
            safe_send(payload)
            last_heartbeat_time = current_time
        end
    end
end

-- Callbacks
function routeManagerHook.onSimulationStart()
    local status, err = pcall(function()
        log_debug("=== Simulation Started (Block 1 v1.0) ===")

        -- Force cleanup
        if tcp_server then
            pcall(function() tcp_server:close() end)
            tcp_server = nil
        end

        setup_server()
    end)

    if not status then
        log_debug("☠️ CRASH in onSimulationStart: " .. tostring(err))
    end
end

function routeManagerHook.onSimulationFrame()
    local status, err = pcall(safe_frame)
    if not status then
        log_debug("☠️ CRASH in onSimulationFrame: " .. tostring(err))
    end
end

function routeManagerHook.onSimulationStop()
    log_debug("=== Simulation Stopped ===")
    if tcp_client then
        tcp_client:close()
        tcp_client = nil
    end
    -- Server stays alive across missions if possible, but we clean up on start anyway
end

DCS.setUserCallbacks({
    onSimulationStart = function() routeManagerHook.onSimulationStart() end,
    onSimulationStop = function() routeManagerHook.onSimulationStop() end,
    onSimulationFrame = function() routeManagerHook.onSimulationFrame() end,
    onPlayerEnterUnit = function(id) routeManagerHook.onPlayerEnterUnit(id) end
})

log_debug("RouteManagerHook (Block 1) Loaded")
