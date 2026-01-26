// static/hud_profiles/a10a.js

window.registerHudProfile('a10a', {
    config: {
        color: '#00ff44', 
        shadowBlur: 0, // Sharp lines
        lineWidth: 2,
        
        // Fonts: "400" weight for sharp/slim look
        fontBig: "400 36px 'VT323', monospace",   
        fontMed: "400 24px 'VT323', monospace",    
        fontPitch: "400 24px 'VT323', monospace",
        fontSmall: "400 20px 'VT323', monospace",   
    },

    draw: function(ctx, data, vw, vh) {
        const C = this.config;
        const T = data.telemetry;
        const N = data.nav;

        // --- SETUP ---
        // (0,0) is ALREADY Top-Center due to the Loader.
        
        ctx.strokeStyle = data.settings.color || C.color;
        ctx.fillStyle = data.settings.color || C.color;
        ctx.lineWidth = C.lineWidth;
        ctx.shadowBlur = 0; // Sharp

        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        const CENTER_Y = Math.floor(vh / 2);
        const TAPE_Y = Math.floor(vh - 100); 

        // Helper for sharp lines
        const crisp = (val) => Math.floor(val) + 0.5;

        // ==================================================
        // 1. HORIZON & PITCH LADDER
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y); 
        ctx.rotate(-T.roll * Math.PI / 180); 
        
        const distToTape = TAPE_Y - CENTER_Y;
        const pxPerDegPitch = distToTape / 15;
        const pitchPx = T.pitch * pxPerDegPitch;
        ctx.translate(0, pitchPx);

        // A. Horizon Line 
        const HOR_W = 120; 
        const HOR_GAP = 40; 
        ctx.beginPath();
        ctx.moveTo(crisp(-HOR_W - 80), 0.5); ctx.lineTo(crisp(-HOR_GAP), 0.5);
        ctx.moveTo(crisp(HOR_GAP), 0.5); ctx.lineTo(crisp(HOR_W + 80), 0.5);
        ctx.stroke();

        // B. Pitch Lines (Max 5 deg top)
        const MAX_PITCH_DRAW = 5; 
        const CLIP_DIST = CENTER_Y - 50;

        for (let p = -90; p <= 90; p += 5) {
            if (p === 0) continue;
            if (p > MAX_PITCH_DRAW) continue;
            
            let y = -p * pxPerDegPitch;
            if (Math.abs(y + pitchPx) > CLIP_DIST) continue;
            y = Math.floor(y) + 0.5;

            const barW = 80; 
            const gap = 50; 
            
            ctx.beginPath();
            if (p < 0) {
                const segLen = barW / 3;
                for(let k=0; k<3; k++) {
                   let start = -barW - gap + (k * segLen);
                   ctx.moveTo(crisp(start), y); ctx.lineTo(crisp(start + (segLen * 0.6)), y);
                }
                for(let k=0; k<3; k++) {
                   let start = gap + (k * segLen);
                   ctx.moveTo(crisp(start), y); ctx.lineTo(crisp(start + (segLen * 0.6)), y);
                }
            } else {
                ctx.moveTo(crisp(-barW - gap), y); ctx.lineTo(crisp(-gap), y);
                ctx.moveTo(crisp(gap), y); ctx.lineTo(crisp(barW + gap), y);
            }
            ctx.stroke();

            const tickLen = 10;
            const tickDir = (p > 0) ? 1 : -1;
            const tipY = y + (tickLen * tickDir);
            
            ctx.beginPath();
            ctx.moveTo(crisp(-barW - gap), y); ctx.lineTo(crisp(-barW - gap), tipY);
            ctx.moveTo(crisp(barW + gap), y); ctx.lineTo(crisp(barW + gap), tipY);
            ctx.stroke();

            ctx.font = C.fontPitch;
            ctx.textAlign = "right"; ctx.fillText(Math.abs(p), -barW - gap - 10, y);
            ctx.textAlign = "left"; ctx.fillText(Math.abs(p), barW + gap + 10, y);
        }
        ctx.restore();

        // ==================================================
        // 2. TVV (Center)
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y); 
        const TVV_R = 12; 
        const TVV_WING = 35; 
        const TVV_TOP = 25; 
        ctx.beginPath();
        ctx.arc(0, 0, TVV_R, 0, Math.PI*2);
        ctx.moveTo(0, -TVV_R); ctx.lineTo(0, -TVV_TOP);
        ctx.moveTo(-TVV_R, 0); ctx.lineTo(-TVV_WING, 0);
        ctx.moveTo(TVV_R, 0); ctx.lineTo(TVV_WING, 0);
        ctx.stroke();
        ctx.restore();

        // ==================================================
        // 3. HEADING TAPE
        // ==================================================
        const TAPE_W = 255; 
        const pxPerDegHdg = TAPE_W / 30; 

        ctx.save();
        ctx.beginPath();
        ctx.rect(-TAPE_W/2, TAPE_Y - 40, TAPE_W, 80);
        ctx.clip();

        const startH = Math.floor(T.hdg - 20);
        const endH = Math.ceil(T.hdg + 20);

        ctx.font = C.fontMed;
        ctx.textAlign = "center";
        
        const LINE_H = 8; 
        const NUM_Y = TAPE_Y - 20; 
        const LINE_START_Y = NUM_Y + 12; 

        for (let i = startH; i <= endH; i++) {
            const x = crisp((i - T.hdg) * pxPerDegHdg);
            if (i % 10 === 0) {
                let val = (i + 360) % 360; 
                let numStr = (val / 10).toFixed(0).padStart(2, '0');
                ctx.fillText(numStr, x, NUM_Y); 
                ctx.beginPath(); ctx.moveTo(x, LINE_START_Y); ctx.lineTo(x, LINE_START_Y + LINE_H); ctx.stroke();
            } else if (i % 5 === 0) {
                ctx.beginPath(); ctx.moveTo(x, LINE_START_Y); ctx.lineTo(x, LINE_START_Y + (LINE_H * 0.8)); ctx.stroke();
            }
        }
        ctx.restore();

        const TRI_Y = LINE_START_Y + LINE_H + 2;
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(0, TRI_Y); ctx.lineTo(-6, TRI_Y + 10); ctx.lineTo(6, TRI_Y + 10); ctx.closePath(); ctx.fill(); 
        
        const BUG_Y = TRI_Y + 12; 
        let wpX = N.turn * pxPerDegHdg;
        if (Math.abs(wpX) < TAPE_W/2 + 10) {
            ctx.fillRect(Math.floor(wpX) - 3, BUG_Y, 6, 10); 
        }
        ctx.restore();

        // ==================================================
        // 4. DATA (Speed, Alt, WP)
        // ==================================================
        const INFO_Y = Math.floor((TAPE_Y - 80 + CENTER_Y) / 2);
        const OFFSET_X = 220; 
        
        ctx.save();
        
        // --- SPEED (Left) ---
        let knots = Math.round(T.spd * 1.94384);
        ctx.textAlign = "right";
        ctx.font = C.fontBig;
        ctx.fillText(knots, -OFFSET_X, INFO_Y);

        // --- ALTITUDE (Right) ---
        let feet = Math.round(T.alt * 3.28084);
        ctx.textAlign = "left";
        ctx.font = C.fontBig;
        ctx.fillText(feet, OFFSET_X, INFO_Y);
        if (T.alt < 1500) ctx.fillText("R", OFFSET_X + 90, INFO_Y);

        // --- WAYPOINT INFO (Below Altitude, halfway to HSI) ---
        // "Move WP and distance half way down between current altitude positions and HSI"
        // Altitude is at INFO_Y. HSI is at TAPE_Y.
        // Let's find the midpoint gap. Note: TAPE_Y is the tape center, top is approx TAPE_Y - 40.
        const WP_BLOCK_Y = Math.floor((INFO_Y + (TAPE_Y - 40)) / 2);

        ctx.textAlign = "left";
        ctx.font = C.fontSmall;
        
        const LINE_HEIGHT = 20;
        
        // WP Name
        ctx.fillText("WP 0", OFFSET_X, WP_BLOCK_Y - 10);

        // Distance (No Unit)
        // "Remove unit type from distance"
        ctx.fillText("0", OFFSET_X, WP_BLOCK_Y + 10);

        ctx.restore();

        // ==================================================
        // 5. EXTRAS
        // ==================================================
        ctx.save();
        
        // G-Meter
        ctx.textAlign = "center";
        ctx.font = C.fontMed;
        ctx.fillText("1.0", -250, CENTER_Y - 150);

        // Pipper
        const PIP_Y = CENTER_Y - 120; 
        ctx.beginPath();
        ctx.setLineDash([2, 4]); ctx.arc(0, PIP_Y, 15, 0, Math.PI*2); ctx.stroke();
        ctx.setLineDash([]); ctx.beginPath(); ctx.arc(0, PIP_Y, 1, 0, Math.PI*2); ctx.fill();
        
        ctx.restore();
    }
});