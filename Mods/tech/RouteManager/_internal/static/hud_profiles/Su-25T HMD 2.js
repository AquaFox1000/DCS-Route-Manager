// static/hud_profiles/su25t.js

window.registerHudProfile('Su-25T HMD 2', {
    config: {
        color: '#33ff33', // "Russian HUD Green"
        shadowBlur: 5,    // Soft glow
        lineWidth: 2,
        
        // Fonts (Slim weight '400')
        fontBig: "400 50px 'Changa', sans-serif",    
        fontMed: "400 31px 'Changa', sans-serif",    
        fontTiny: "400 16px 'Changa', sans-serif",   
        fontSink: "400 20px 'Changa', sans-serif",   
    },

    draw: function(ctx, data, vw, vh) {
        const C = this.config;
        const T = data.telemetry;
        const N = data.nav;
        const P = data.physics;

        // --- SETUP ---
        ctx.strokeStyle = data.settings.color || C.color;
        ctx.fillStyle = data.settings.color || C.color;
        ctx.lineWidth = C.lineWidth;
        
        ctx.shadowBlur = C.shadowBlur;
        ctx.shadowColor = ctx.strokeStyle;
        
        ctx.textAlign = "center";
        ctx.textBaseline = "alphabetic";

        // --- CONSTANTS ---
        const CENTER_Y = vh / 2;
        const HSI_W = vw * 0.5; 
        const HSI_LEFT = -HSI_W / 2;
        const HSI_RIGHT = HSI_W / 2;
        const TAPE_Y = 100; 

        const VSI_X = HSI_RIGHT + 50; 
        const VSI_H = Math.min(vh * 0.8, 600);
        const PITCH_NUM_X = VSI_X - 30;
        const SPD_X = HSI_LEFT - 20;

        // ==================================================
        // 1. HORIZON & PITCH (STATIC)
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y); 
        
        const pitchScale = 18; 
        const pitchPx = T.pitch * pitchScale;
        ctx.translate(0, pitchPx);

        // A. Horizon Line 
        const HOR_W = vw * 0.5; 
        ctx.beginPath();
        ctx.moveTo(-HOR_W/2, 0); 
        ctx.lineTo(HOR_W/2, 0);
        ctx.stroke();

        ctx.font = C.fontTiny;
        ctx.textAlign = "left";
        ctx.fillText("0", (HOR_W/2) + 10, 5);

        // B. Pitch Scale (-90 to +90)
        // LOGIC: We calculate the screen Y position of every line.
        // If it falls outside the "Safe Zone", we skip drawing it.
        
        const TOP_SAFE = -CENTER_Y + 180;     // 100px from top of screen
        const BOT_SAFE = CENTER_Y - 195;      // 140px from bottom (clears WP Info)

        for (let p = -90; p <= 90; p += 10) {
            if (p === 0) continue;

            let y = -p * pitchScale;
            
            // Calculate where this line sits on the actual screen right now
            let screenY = y + pitchPx; 
            
            // CLIPPING: If outside safe zone, skip
            if (screenY < TOP_SAFE || screenY > BOT_SAFE) continue;

            const lineEnd = PITCH_NUM_X - 25; 
            const lineStart = lineEnd - 40;

            ctx.beginPath();
            ctx.setLineDash([3, 4]); 
            ctx.moveTo(lineStart, y);
            ctx.lineTo(lineEnd, y);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.textAlign = "right"; 
            ctx.fillText(p, PITCH_NUM_X, y + 5);
        }
        ctx.restore();

        // ==================================================
        // 2. CENTER CROSS & ROLL LINES (STATIC)
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y);

        // --- GEOMETRY CALCULATIONS ---
        const GAP_CENTER = 9;   
        const CROSS_SIZE = 35.5;

        // Wing Lines
        const WING_START = 48; 
        const OLD_WING_LEN = (vw * 0.4) / 2;
        const NEW_LINE_LEN = (OLD_WING_LEN - 45) * 0.7; // 70% of original
        const WING_LEN = WING_START + NEW_LINE_LEN;
        const ROLL_R = WING_LEN + 15;

        ctx.lineWidth = 3;

        // A. Center Cross (Static)
        ctx.beginPath();
        ctx.moveTo(-CROSS_SIZE, 0); ctx.lineTo(-GAP_CENTER, 0);
        ctx.moveTo(CROSS_SIZE, 0); ctx.lineTo(GAP_CENTER, 0);
        ctx.moveTo(0, -CROSS_SIZE); ctx.lineTo(0, -GAP_CENTER);
        ctx.moveTo(0, CROSS_SIZE); ctx.lineTo(0, GAP_CENTER);
        ctx.stroke();

        // B. Roll Lines (Static)
        function drawRollTick(deg) {
            let rad = (deg * Math.PI) / 180;
            let xl = -Math.cos(rad) * ROLL_R;
            let yl = Math.sin(rad) * ROLL_R;
            let xr = Math.cos(rad) * ROLL_R;
            let yr = Math.sin(rad) * ROLL_R;
            
            // Left Side
            ctx.beginPath(); ctx.moveTo(xl, yl); ctx.lineTo(xl * 1.1, yl * 1.1); ctx.stroke();
            // Right Side
            ctx.beginPath(); ctx.moveTo(xr, yr); ctx.lineTo(xr * 1.1, yr * 1.1); ctx.stroke();
        }
        
        drawRollTick(0);
        drawRollTick(30);
        drawRollTick(60);
        ctx.restore();

        // ==================================================
        // 3. THE BIRD (ROTATING)
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y);
        ctx.rotate(T.roll * Math.PI / 180); 

        const STAB_H = 168; 
        const STAB_GAP = GAP_CENTER + CROSS_SIZE + 5;
        const TICK_H = 24; 
        
        const WING_SPAN_LEN = WING_LEN - WING_START;
        const TICK_OFFSET = WING_START + (WING_SPAN_LEN * 0.2);

        ctx.lineWidth = 3;

        // Wings
        ctx.beginPath();
        ctx.moveTo(-WING_START, 0); ctx.lineTo(-WING_LEN, 0);
        ctx.moveTo(-TICK_OFFSET, 0); ctx.lineTo(-TICK_OFFSET, TICK_H); 
        ctx.moveTo(WING_START, 0); ctx.lineTo(WING_LEN, 0);
        ctx.moveTo(TICK_OFFSET, 0); ctx.lineTo(TICK_OFFSET, TICK_H);
        ctx.stroke();

        // Vert Stab
        ctx.beginPath();
        ctx.moveTo(0, -STAB_H); 
        ctx.lineTo(0, -STAB_GAP);
        ctx.stroke();
        ctx.restore();

        // ==================================================
        // 4. HSI TAPE
        // ==================================================
        ctx.save();
        const pxPerDeg = HSI_W / 40; 
        ctx.beginPath(); ctx.rect(HSI_LEFT, 0, HSI_W, TAPE_Y + 20); ctx.clip();

        ctx.beginPath(); ctx.moveTo(HSI_LEFT, TAPE_Y); ctx.lineTo(HSI_RIGHT, TAPE_Y); ctx.stroke();

        const startH = Math.floor(T.hdg - 25);
        const endH = Math.ceil(T.hdg + 25);
        ctx.font = C.fontMed; 
        ctx.lineWidth = C.lineWidth;
        
        const NUM_Y = TAPE_Y - 20;

        for (let i = startH; i <= endH; i++) {
            const x = (i - T.hdg) * pxPerDeg;
            if (x < HSI_LEFT || x > HSI_RIGHT) continue;
            if (i % 10 === 0) {
                ctx.beginPath(); ctx.moveTo(x, TAPE_Y); ctx.lineTo(x, TAPE_Y - 15); ctx.stroke();
                let val = (i + 360) % 360; 
                let numStr = (val / 10).toFixed(0).padStart(2, '0');
                ctx.fillText(numStr, x, NUM_Y);
            } else if (i % 5 === 0) {
                ctx.beginPath(); ctx.moveTo(x, TAPE_Y); ctx.lineTo(x, TAPE_Y - 8); ctx.stroke();
            }
        }

        // WP Indication
        if (N.hasRoute) {
            let wpX = N.turn * pxPerDeg;
            if (wpX > HSI_LEFT && wpX < HSI_RIGHT) {
                ctx.beginPath();
                const tipY = NUM_Y - 15;
                const baseY = NUM_Y - 30;
                
                ctx.moveTo(wpX - 8, baseY); 
                ctx.lineTo(wpX + 8, baseY); 
                ctx.lineTo(wpX, tipY);      
                ctx.fill();
            }
        }
        ctx.restore();

        // Heading Triangle
        ctx.beginPath();
        ctx.moveTo(0, TAPE_Y); ctx.lineTo(-8, TAPE_Y + 15); ctx.lineTo(8, TAPE_Y + 15); ctx.closePath();
        ctx.stroke();

        // ==================================================
        // 5. SPEED, ACCEL & ALT
        // ==================================================
        const DATA_Y = TAPE_Y; 
        
        // --- SPEED (Left Side) ---
        ctx.textAlign = "right";
        ctx.font = C.fontBig; 
        
        // Use Indicated Airspeed (m/s -> km/h)
        let kmh = T.ias * 3.6;
        let spdDisp = Math.floor(kmh / 10) * 10; 
        
        ctx.fillText(spdDisp, SPD_X, DATA_Y);
        
        // Target Speed
        if (N.targetSpeed) {
            ctx.font = C.fontMed; 
            // Server now sends m/s, convert to km/h for display
            let targetKmh = N.targetSpeed * 3.6;
            ctx.fillText(Math.round(targetKmh), SPD_X, DATA_Y - 50); 
        }

        // --- ACCEL TRIANGLE (3 Positions) ---
        let accel = P.accel || 0;
        
        // Get width of a single digit to snap to columns
        let digitW = ctx.measureText("0").width;
        let triX = 0;

        if (accel < -0.5) {
            // Decel: Position under Hundreds (3rd digit from right)
            triX = SPD_X - (digitW * 2.5);
        } else if (accel > 0.5) {
            // Accel: Position under Units (1st digit from right)
            triX = SPD_X - (digitW * 0.5);
        } else {
            // Stable: Position under Tens (2nd digit from right)
            triX = SPD_X - (digitW * 1.5);
        }

        const ACC_Y = DATA_Y + 15; 
        ctx.beginPath();
        ctx.moveTo(triX, ACC_Y);          
        ctx.lineTo(triX - 6, ACC_Y + 12); 
        ctx.lineTo(triX + 6, ACC_Y + 12); 
        ctx.closePath(); 
        ctx.stroke();

        // --- ALTITUDE (Right Side) ---
        const ALT_X = HSI_RIGHT + 20;
        ctx.textAlign = "left";
        
        // Logic Variables
        let displayedAlt = 0;
        let isRadar = false;

        // 1. Determine Mode & Value
        if (T.alt_r < 1500) {
            // --- RADAR MODE (AGL) ---
            isRadar = true;
            displayedAlt = Math.round(T.alt_r);
        } else {
            // --- BARO MODE (MSL) ---
            isRadar = false;
            // Round to nearest 10 (e.g. 3955 -> 3960)
            // T.alt_baro comes from server, already converted/verified
            displayedAlt = Math.round(T.alt_baro / 10) * 10;
        }

        // 2. Draw Main Altitude
        ctx.font = C.fontBig; 
        let altStr = displayedAlt.toString();
        ctx.fillText(altStr, ALT_X, DATA_Y);

        // 3. Draw "R" for Radar (Dynamic Positioning)
        if (isRadar) {
            let textWidth = ctx.measureText(altStr).width;
            // X: End of number + 10px padding
            // Y: Shifted down 25% of font size (~12px)
            ctx.fillText("R", ALT_X + textWidth + 10, DATA_Y + 12); 
        }
        
        // 4. Draw Waypoint Altitude (Above Primary)
        // Only if we have a route and valid altitude
        if (N.hasRoute && N.alt !== undefined) {
            ctx.font = C.fontMed; 
            // Server converted this to meters already
            ctx.fillText(Math.round(N.alt), ALT_X, DATA_Y - 50);
        }

        // ==================================================
        // 6. VERTICAL RATE
        // ==================================================
        ctx.beginPath();
        ctx.moveTo(VSI_X, CENTER_Y - VSI_H/2); ctx.lineTo(VSI_X, CENTER_Y + VSI_H/2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(VSI_X, CENTER_Y); ctx.lineTo(VSI_X - 25, CENTER_Y); ctx.stroke();

        // Use Native Telemetry VVI
        let vsiVal = T.vvi || 0;
        
        // Scale: 5 pixels per m/s
        let vsiPx = -vsiVal * 5; 
        
        if (vsiPx > VSI_H/2) vsiPx = VSI_H/2;
        if (vsiPx < -VSI_H/2) vsiPx = -VSI_H/2;

        const ay = CENTER_Y + vsiPx;
        const shaftLen = 20;
        
        ctx.beginPath();
        ctx.moveTo(VSI_X, ay); ctx.lineTo(VSI_X + 10, ay - 5); ctx.lineTo(VSI_X + 10, ay + 5); ctx.fill(); 
        ctx.beginPath(); ctx.moveTo(VSI_X, ay); ctx.lineTo(VSI_X + shaftLen, ay); ctx.stroke();

        ctx.textAlign = "center";
        ctx.font = C.fontSink; 
        let displayVsi = Math.round(Math.abs(vsiVal));
        if (displayVsi === 0) displayVsi = "0";
        ctx.fillText(displayVsi, VSI_X + (shaftLen/2) + 5, ay - 8);

        // ==================================================
        // 7. BOTTOM INFO
        // ==================================================
        const BOT_Y = vh - 120;

        ctx.textAlign = "right";
        ctx.font = C.fontBig;
        ctx.fillText("NAV", SPD_X, BOT_Y);

        ctx.textAlign = "center";
        let distStr = (N.dist !== undefined && N.dist !== null) ? N.dist.toFixed(1) : "0.0";
        ctx.fillText(distStr, 0, BOT_Y);

        ctx.textAlign = "right";
        ctx.font = C.fontMed; 
        
        let wpStr = "WP 0";
        if (N.hasRoute) {
            let typeText = N.type ? (N.type.toUpperCase() + " ") : "";
            wpStr = `${typeText}${N.index + 1}`;
        }
        ctx.fillText(wpStr, PITCH_NUM_X, BOT_Y);
    }
});