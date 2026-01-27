const Utils = {

    /* PROJECT 3D WORLD POINT TO 2D SCREEN
     * Returns coordinates compatible with a Centered-X, Top-Y Canvas Context.*/
    projectWorldToScreen: function(cam, target, player, vw, vh, fov) {
        if (!cam || !target || !player) return null;

        // 1. Get Relative Vector (Target - Player) in Meters
        // DCS World: X=North, Y=Up, Z=East
        const metersPerLat = 111132.95;
        const metersPerLon = 111412.84 * Math.cos(player.lat * (Math.PI/180));

        const dx = (target.lat - player.lat) * metersPerLat; 
        const dy = target.alt - player.alt_sl; 
        const dz = (target.lon - player.lon) * metersPerLon;

        // 2. Transform to Camera View Space
        // DCS Camera Matrix (Standard): 
        // cam.x = Forward Vector (Depth)
        // cam.y = Up Vector
        // cam.z = Right Vector (Horizontal)

        // Depth (Forward distance) -> Dot Product with Cam X
        const locZ = dx * cam.x.x + dy * cam.x.y + dz * cam.x.z;

        // Horizontal (Right distance) -> Dot Product with Cam Z
        const locX = dx * cam.z.x + dy * cam.z.y + dz * cam.z.z;

        // Vertical (Up distance) -> Dot Product with Cam Y
        const locY = dx * cam.y.x + dy * cam.y.y + dz * cam.y.z;

        // 3. Check if target is behind the camera
        if (locZ < 0) return null; 

        // 4. Project to Screen (Pinhole Model)
        // We calculate Focal Length based on Screen Width and FOV (assuming Horizontal FOV)
        const fovRad = (fov * Math.PI) / 180;
        const f = (vw / 2) / Math.tan(fovRad / 2);

        const screenX = (locX / locZ) * f;
        const screenY = (locY / locZ) * f;

        // 5. Map to Canvas Coordinates
        // HUD Context: X=0 is Center, Y=0 is Top.
        // Math: screenX is offset from center. screenY is offset from center (Up is positive).
        
        return {
            x: screenX,               // 0 is Center (Matches HUD context)
            y: (vh / 2) - screenY     // 0 is Top (Matches HUD context), subtract Y to go "Up"
        };
    }
};