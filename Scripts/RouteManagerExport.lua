-- =============================================================
--   DCS FLIGHT COMPANION - EXPORT SCRIPT (STATELESS QUEUE)
-- =============================================================
local navExport       = {}

-- 1. CONFIGURATION
navExport.host        = "127.0.0.1"
navExport.port        = 11000
navExport.inputPort   = 11001
navExport.rate        = 0.02 -- 50Hz Loop

-- 2. DEPENDENCIES
package.path          = package.path .. ";.\\LuaSocket\\?.lua"
package.cpath         = package.cpath .. ";.\\LuaSocket\\?.dll"

local socket          = require("socket")
local udp             = socket.udp()
local inputUdp        = socket.udp()

-- Load the Raycast Module
local Raycast         = dofile(lfs.writedir() .. "Scripts/Raycast.lua")

-- 3. STATE VARIABLES
local request_raycast = false
local last_ray_time   = 0
local cmd_queue       = {}

-- 4. HELPER FUNCTIONS
function navExport.log_debug(msg)
    local path = lfs.writedir() .. "Logs/Raycast_Debug.log"
    local f = io.open(path, "a")
    if f then
        f:write(os.date("[%H:%M:%S] ") .. msg .. "\n")
        f:close()
    end
end

function navExport.clean(str)
    if not str then return "" end
    str = string.gsub(str, '\\', '')
    str = string.gsub(str, '"', '')
    return str
end

function navExport.jsonify(data)
    local parts = {}
    table.insert(parts, "{")
    for k, v in pairs(data) do
        local valStr = "0"
        if type(v) == "number" then
            valStr = string.format("%.9f", v)
        elseif type(v) == "string" then
            valStr = string.format('"%s"', navExport.clean(v))
        elseif type(v) == "boolean" then
            valStr = tostring(v)
        end
        table.insert(parts, string.format('"%s":%s,', k, valStr))
    end
    if #parts > 1 then parts[#parts] = string.sub(parts[#parts], 1, -2) end
    table.insert(parts, "}")
    return table.concat(parts)
end

-- SETUP SOCKETS
if udp then
    udp:settimeout(0); udp:setpeername(navExport.host, navExport.port)
end
if inputUdp then
    inputUdp:settimeout(0); inputUdp:setsockname("*", navExport.inputPort)
end

-- =============================================================
--   MAIN LOOP
-- =============================================================
function LuaExportActivityNextEvent(t)
    local tNext = t + navExport.rate

    pcall(function()
        -- A. READ INPUT COMMANDS -> ADD TO QUEUE
        if inputUdp then
            while true do
                local cmd, _ = inputUdp:receive()
                if not cmd then break end

                -- Regex: Match single numbers (IDs) only
                for id_str in string.gmatch(cmd, "(%d+)") do
                    local c_id = tonumber(id_str)
                    if c_id then
                        table.insert(cmd_queue, c_id)
                    end
                end
            end
        end

        -- B. EXECUTE FROM QUEUE (Rate Limit: 2 per frame)
        local cmds_processed = 0
        while #cmd_queue > 0 and cmds_processed < 2 do
            local cmd_id = table.remove(cmd_queue, 1) -- Pop first ID

            -- RAYCAST CHECK
            if cmd_id == 10001 then
                if t > last_ray_time + 1.0 then
                    request_raycast = true
                    last_ray_time = t
                    navExport.log_debug("EXECUTE: Raycast Requested")
                end
            else
                -- STANDARD DISCRETE COMMAND
                LoSetCommand(cmd_id)
            end

            cmds_processed = cmds_processed + 1
        end

        -- C. GATHER DATA (Self & Physics)
        local o = LoGetSelfData()
        if not o then return end

        local selfPosJson = '"self_pos":null'
        if o.Position then
            selfPosJson = string.format('"self_pos":{"x":%.4f,"y":%.4f,"z":%.4f}',
                o.Position.x, o.Position.y, o.Position.z)
        end

        -- 1. Physics Data
        local selfVel = LoGetVectorVelocity()
        local vx, vy, vz = 0, 0, 0
        local groundSpeed, vvi = 0, 0

        if selfVel then
            vx, vy, vz = selfVel.x, selfVel.y, selfVel.z
            groundSpeed = math.sqrt(vx ^ 2 + vy ^ 2 + vz ^ 2)
            vvi = selfVel.y
        end

        local altBaro = o.LatLongAlt.Alt
        if LoGetAltitudeAboveSeaLevel then altBaro = LoGetAltitudeAboveSeaLevel() or altBaro end

        local ias = 0
        if LoGetIndicatedAirSpeed then ias = LoGetIndicatedAirSpeed() or 0 end

        local altAgl = 0
        if LoGetAltitudeAboveGroundLevel then altAgl = LoGetAltitudeAboveGroundLevel() or 0 end

        local gload = 1.0
        local acc = LoGetAccelerationUnits()
        if acc then gload = acc.y end

        local aoa = 0
        if o.AOA then aoa = o.AOA * 57.2958 end

        local stallFlag = 0
        local mcp = LoGetMCPState()
        if mcp and mcp.StallSignal then stallFlag = 1 end

        -- 2. Camera Matrix
        local camPos = LoGetCameraPosition()
        local camJson = '"cam":null'
        if camPos then
            camJson = string.format(
                '"cam":{"p":{"x":%.4f,"y":%.4f,"z":%.4f},"x":{"x":%.9f,"y":%.9f,"z":%.9f},"y":{"x":%.9f,"y":%.9f,"z":%.9f},"z":{"x":%.9f,"y":%.9f,"z":%.9f}}',
                camPos.p.x, camPos.p.y, camPos.p.z, camPos.x.x, camPos.x.y, camPos.x.z, camPos.y.x, camPos.y.y,
                camPos.y.z, camPos.z.x, camPos.z.y, camPos.z.z)
        end

        -- 3. Raycast Processing
        local lookLat, lookLon, lookAlt = 0, 0, 0
        if request_raycast then
            request_raycast = false
            -- OPTIMIZATION: Pass cached camera (camPos) and self (o) data
            local status, lat, lon, alt = pcall(Raycast.get_camera_intersection, camPos, o)
            if status and lat ~= 0 then
                lookLat = lat; lookLon = lon; lookAlt = alt
                navExport.log_debug(string.format("RAYCAST SUCCESS: %.4f, %.4f", lookLat, lookLon))
            end
        end

        -- 4. Weapon Info
        local sighting = LoGetSightingSystemInfo()
        local currentMode = sighting and sighting.master_mode or 1
        local pylonString = ""
        local activeWeaponName = ""

        if sighting and sighting.selected_usage then
            local payload = LoGetPayloadInfo()
            for i, p_idx in pairs(sighting.selected_usage) do
                pylonString = pylonString .. p_idx .. ","
                if activeWeaponName == "" and payload and payload.stations then
                    local st = payload.stations[p_idx]
                    if st and st.store and st.store.name then activeWeaponName = st.store.name end
                end
            end
        end
        if string.len(pylonString) > 0 then pylonString = string.sub(pylonString, 1, -2) end

        -- 5. Send Packet
        local packet = {
            type = "player",
            plane = o.Name,
            lat = o.LatLongAlt.Lat,
            lon = o.LatLongAlt.Long,
            alt_sl = o.LatLongAlt.Alt,
            alt_baro = altBaro,
            alt_r = altAgl,
            hdg = o.Heading * 57.2958,
            pitch = o.Pitch * 57.2958,
            roll = o.Bank * 57.2958,
            spd = groundSpeed,
            ias = ias,
            vvi = vvi,
            aoa = aoa,
            gload = gload,
            stall = stallFlag,
            vel_x = vx,
            vel_y = vy,
            vel_z = vz,
            look_lat = lookLat,
            look_lon = lookLon,
            look_alt = lookAlt,
            mode = currentMode,
            pylons = pylonString,
            weapon = activeWeaponName
        }

        if udp then
            local baseJson = navExport.jsonify(packet)
            -- Concatenate with pre-formatted JSON blocks
            local finalJson = baseJson:sub(1, -2) .. "," .. camJson .. "," .. selfPosJson .. "}"
            udp:send(finalJson)
        end

        -- UNIT POLLING REMOVED (Handled by RouteManagerHook.lua)
    end)

    return tNext
end

function LuaExportStart() navExport.log_debug("--- SESSION START ---") end

function LuaExportStop()
    if udp then udp:close() end; if inputUdp then inputUdp:close() end; navExport.log_debug("--- SESSION END ---")
end

return navExport
