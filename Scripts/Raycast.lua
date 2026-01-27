local Raycast   = {}

-- =============================================================
-- CONFIGURATION
-- =============================================================
local MAX_STEPS = 100   -- Max steps (ensures convergence from high alt)
local PRECISION = 2.0   -- Hit precision in meters
local MAX_DIST  = 30000 -- 30km Max Range (Abort if further)

-- =============================================================
-- LOGGING (Minimal)
-- =============================================================
local log_file  = lfs.writedir() .. "Logs/raycast_debug.log"
local function log_debug(msg)
    local f = io.open(log_file, "a")
    if f then
        f:write(os.date("[%H:%M:%S] ") .. msg .. "\n")
        f:close()
    end
end

-- =============================================================
-- MAIN FUNCTION
-- =============================================================
function Raycast.get_camera_intersection(opt_cam, opt_self)
    -- 1. GET CAMERA DATA (Internal Meters)
    local cam = opt_cam
    if not cam then
        local status, c = pcall(LoGetCameraPosition)
        if status and c then cam = c end
    end
    if not cam then return 0, 0, 0 end

    local start_x = cam.p.x -- North/South axis
    local start_z = cam.p.z -- East/West axis
    local start_y = cam.p.y -- Altitude

    local dir_x = cam.x.x
    local dir_y = cam.x.y
    local dir_z = cam.x.z

    -- 2. GET PLAYER GPS ANCHOR
    -- We use the aircraft's own GPS as the reference point for conversion
    local selfData = opt_self
    if not selfData then
        selfData = LoGetSelfData()
    end
    if not selfData or not selfData.LatLongAlt then return 0, 0, 0 end

    local ref_lat = selfData.LatLongAlt.Lat
    local ref_lon = selfData.LatLongAlt.Long

    -- 3. EARLY ABORT: LOOKING AT SKY
    -- If Y component is positive, we are looking up.
    if dir_y >= 0 then return 0, 0, 0 end

    -- 4. RAY MARCHING LOOP
    local curr_x, curr_y, curr_z = start_x, start_y, start_z
    local hit = false
    local total_dist = 0
    local hit_ele = 0

    for i = 1, MAX_STEPS do
        -- A. Terrain Height
        local terrain_y = LoGetAltitude(curr_x, curr_z)

        -- B. Object Height (Buildings/Trees/Bunkers)
        local object_y = 0
        if LoGetHeightWithObjects then
            object_y = LoGetHeightWithObjects(curr_x, curr_z) or 0
        end

        -- Use whichever is higher (The surface we would hit)
        local ground_y = math.max(terrain_y, object_y)

        local agl = curr_y - ground_y

        -- Convergence Check (Are we close enough to surface?)
        if agl < PRECISION and agl > -PRECISION then
            hit = true
            hit_ele = ground_y
            break
        end

        -- Underground Safety (Bounce up slightly if we clipped through)
        if agl < 0 then agl = 2.0 end

        -- Distance Check
        total_dist = total_dist + agl
        if total_dist > MAX_DIST then break end

        -- Step Forward along the vector
        curr_x = curr_x + (dir_x * agl)
        curr_y = curr_y + (dir_y * agl)
        curr_z = curr_z + (dir_z * agl)
    end

    -- 5. MANUAL COORDINATE CONVERSION
    if hit then
        -- Calculate displacement from aircraft (Meters)
        local delta_x = curr_x - start_x
        local delta_z = curr_z - start_z

        -- Earth Constants (Meters per Degree at this Latitude)
        local meters_per_deg_lat = 111132.92
        local meters_per_deg_lon = 111412.84 * math.cos(math.rad(ref_lat))

        -- Apply Offset to Reference GPS
        local final_lat = ref_lat + (delta_x / meters_per_deg_lat)
        local final_lon = ref_lon + (delta_z / meters_per_deg_lon)

        log_debug(string.format("🎯 TARGET LOCKED: Lat: %.9f, Lon: %.9f, Alt: %.9fm", final_lat, final_lon, hit_ele))

        return final_lat, final_lon, hit_ele
    end

    -- log_debug("❌ MISS: No ground intersection found.")
    return 0, 0, 0
end

return Raycast
