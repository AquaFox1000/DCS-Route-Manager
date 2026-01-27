window.registerHudProfile('Su-25T minimalistic', {
    config: {
        // --- STYLING (Exact match to su25t.js) ---
        color: '#33ff33', 
        shadowBlur: 3,    
        lineWidth: 5,     
        
        fontBig: "400 80px 'Changa', sans-serif",    
        fontMed: "400 55px 'Changa', sans-serif",    
        fontTiny: "400 38px 'Changa', sans-serif",   
        fontSink: "400 45px 'Changa', sans-serif",   
    },

    draw: function(ctx, data, vw, vh) {
        // ==================================================
        // 1. SCALING ONLY (No Offset Calculation)
        // ==================================================
        const REF_H = 1200; // Reference height for font scaling
        const scale = vh / REF_H;

        ctx.save();
        ctx.scale(scale, scale);
        
        // At this point:
        // X=0 is Center Screen
        // Y=0 is Top of Screen

        const C = this.config;
        const T = data.telemetry;
        const N = data.nav;
        const P = data.physics;

        // Apply Global Styles
        ctx.strokeStyle = data.settings.color || C.color;
        ctx.fillStyle = data.settings.color || C.color;
        ctx.lineWidth = C.lineWidth;
        ctx.shadowBlur = C.shadowBlur;
        ctx.shadowColor = ctx.strokeStyle;
        
        ctx.textAlign = "center";
        ctx.textBaseline = "alphabetic";

        // ==================================================
        // 2. LAYOUT CALCULATIONS
        // ==================================================
        const TAPE_Y = 120;       // The main horizontal axis
        const HSI_W  = 400;       // Width from su25t.js logic
        const HSI_HALF = HSI_W / 2;
        
        // --- Position Anchors (Relative to 0) ---
        
        // 1. SPEED (Left of HSI)
        // HSI ends at -415. We pad 50px left.
        const X_SPD = -HSI_HALF - 50; 
        
        // 2. NAV/AP (Left of Speed)
        // Speed string width approx 150px. We pad another 200px.
        const X_NAV = X_SPD - 200;

        // 3. ALTITUDE (Right of HSI)
        // HSI ends at +415. Pad 50px right.
        const X_ALT = HSI_HALF + 50;

        // 4. WP INFO (Right of Altitude)
        // Alt string width approx 150px. We pad another 200px.
        const X_WP  = X_ALT + 220; 

        // ==================================================
        // 3. HEADING TAPE (HSI) - Centered at 0
        // ==================================================
        ctx.save();
        
        const pxPerDeg = HSI_W / 30; // 30 degrees visible

        // Clip
        ctx.beginPath();
        ctx.rect(-HSI_HALF, 0, HSI_W, TAPE_Y + 20);
        ctx.clip();

        // Line
        ctx.beginPath();
        ctx.moveTo(-HSI_HALF, TAPE_Y);
        ctx.lineTo(HSI_HALF, TAPE_Y);
        ctx.stroke();

        const startH = Math.floor(T.hdg - 20);
        const endH = Math.ceil(T.hdg + 20);

        ctx.font = C.fontMed; 
        
        for (let i = startH; i <= endH; i++) {
            const x = (i - T.hdg) * pxPerDeg;
            
            // Optimization: Skip if off-tape
            if (x < -HSI_HALF || x > HSI_HALF) continue;

            if (i % 10 === 0) {
                // Major Tick
                ctx.beginPath(); ctx.moveTo(x, TAPE_Y); ctx.lineTo(x, TAPE_Y - 15); ctx.stroke();
                // Number
                let val = (i + 360) % 360; 
                let numStr = (val / 10).toFixed(0).padStart(2, '0');
                ctx.fillText(numStr, x, TAPE_Y - 50);
            } else if (i % 5 === 0) {
                // Minor Tick
                ctx.beginPath(); ctx.moveTo(x, TAPE_Y); ctx.lineTo(x, TAPE_Y - 8); ctx.stroke();
            }
        }

        // --- WP HEADING BUG (Inverted Full Triangle) ---
        if (N.hasRoute) {
            let wpX = N.turn * pxPerDeg;
            let drawX = wpX;
            let rotation = 0;
            const PADDING = 25;

            // Clamp to tape edges
            if (wpX < -HSI_HALF + PADDING) { drawX = -HSI_HALF + PADDING; rotation = Math.PI / 2; }
            else if (wpX > HSI_HALF - PADDING) { drawX = HSI_HALF - PADDING; rotation = -Math.PI / 2; }

            ctx.save();
            ctx.translate(drawX, TAPE_Y - 25);
            ctx.rotate(rotation);
            ctx.beginPath();
            ctx.moveTo(-15, -15); 
            ctx.lineTo(15, -15);
            ctx.lineTo(0, 10);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
        }
        ctx.restore();

        // --- CURRENT HEADING MARKER (Center 0) ---
        ctx.beginPath();
        ctx.moveTo(0, TAPE_Y); 
        ctx.lineTo(-20, TAPE_Y + 30); 
        ctx.lineTo(20, TAPE_Y + 30); 
        ctx.closePath();
        ctx.stroke();

        // ==================================================
        // 4. SPEED GROUP (Left Side)
        // ==================================================
        
        // --- SPEED (Aligned with HSI Line) ---
        ctx.textAlign = "right";
        ctx.font = C.fontBig;
        
        let kmh = T.ias * 3.6;
        let spdDisp = Math.floor(kmh / 10) * 10; 
        ctx.fillText(spdDisp, X_SPD, TAPE_Y);

        // Accel Triangle
        let digitW = ctx.measureText("0").width;
        let accel = P.accel || 0;
        let triX = X_SPD - (digitW * 1.5);
        if (accel < -0.5) triX = X_SPD - (digitW * 2.5);
        else if (accel > 0.5) triX = X_SPD - (digitW * 0.5);

        ctx.beginPath();
        ctx.moveTo(triX, TAPE_Y + 15); 
        ctx.lineTo(triX - 12, TAPE_Y + 30); 
        ctx.lineTo(triX + 12, TAPE_Y + 30); 
        ctx.closePath(); 
        ctx.stroke();

        // --- NAV | AP (Left of Speed) ---
        ctx.textAlign = "right";
        ctx.font = C.fontBig;

        let modeStr = "NAV";
        if (T.mode === 6) modeStr = "A-A";
        if (T.mode === 7) modeStr = "A-G";

        let showAp = N.apStatus; 
        if (!showAp && N.apDisconnectTime) {
            let diff = Date.now() - N.apDisconnectTime;
            if (diff < 1800) showAp = (Math.floor(diff / 300) % 2 !== 0);
        }
        
        // Format: "NAV -AP" or just "NAV"
        let fullModeStr = modeStr;
        if (showAp) fullModeStr += " -AP";
        
        ctx.fillText(fullModeStr, X_NAV, TAPE_Y);

        // ==================================================
        // 5. ALTITUDE GROUP (Right Side)
        // ==================================================
        
        // --- ALTITUDE (Aligned with HSI Line) ---
        ctx.textAlign = "left";
        ctx.font = C.fontBig;

        let isRadar = (T.alt_r < 1500);
        let altDisp = isRadar ? Math.round(T.alt_r) : Math.round(T.alt_baro / 10) * 10;
        let altStr = altDisp.toString();

        ctx.fillText(altStr, X_ALT, TAPE_Y);

        if (isRadar) {
            let tw = ctx.measureText(altStr).width;
            ctx.font = C.fontTiny;
            ctx.fillText("R", X_ALT + tw + 10, TAPE_Y);
        }

        // --- DESIRED ALTITUDE (Above Main Alt) ---
        // Aligned Left with Main Alt
        if (N.hasRoute && N.alt !== undefined) {
            ctx.font = C.fontMed;
            // Y: Shifted up by 65px
            ctx.fillText(Math.round(N.alt), X_ALT, TAPE_Y - 65);
        }

        // ==================================================
        // 6. WAYPOINT GROUP (Far Right)
        // ==================================================
        
        if (N.hasRoute) {
            // --- WP NAME (Aligned with Desired Alt) ---
            ctx.textAlign = "left";
            ctx.font = C.fontMed; 

            let wpName = "";
            if (N.type === 'poi') wpName = `T ${N.index + 1}`;
            else wpName = `WP ${N.index + 1}`;
            
            ctx.fillText(wpName, X_WP, TAPE_Y - 65);

            // --- DISTANCE (Aligned with Main Alt) ---
            // Below WP Name
            ctx.font = C.fontBig; 
            
            let distStr = (N.dist !== undefined && N.dist !== null) ? N.dist.toFixed(1) : "0.0";           
            ctx.fillText(distStr, X_WP, TAPE_Y);
        }

        ctx.restore();
    }
});