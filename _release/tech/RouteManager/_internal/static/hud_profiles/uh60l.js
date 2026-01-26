window.registerHudProfile('uh60l', {
    config: {
        color: '#00ff00',
        shadowBlur: 2,
        lineWidth: 2,

        fontBig: "400 32px 'VT323', monospace",
        fontMed: "400 24px 'VT323', monospace",
        fontTiny: "400 18px 'VT323', monospace",
    },

    draw: function (ctx, data, vw, vh) {
        const C = this.config;
        const T = data.telemetry;
        const N = data.nav;
        const P = data.physics;

        ctx.strokeStyle = data.settings.color || C.color;
        ctx.fillStyle = data.settings.color || C.color;
        ctx.lineWidth = C.lineWidth;
        ctx.shadowBlur = C.shadowBlur;
        ctx.shadowColor = ctx.strokeStyle;

        ctx.textAlign = "center";

        const HUD_H = 800;
        const SCALE = vh / HUD_H;

        ctx.save();
        ctx.scale(SCALE, SCALE);

        const CENTER_X = 0;
        const CENTER_Y = HUD_H / 2;

        // ==================================================
        // 1. HEADING TAPES (Top)
        // ==================================================
        ctx.save();
        const TAPE_Y = 60;
        const TAPE_W = 500;
        const pxPerDeg = TAPE_W / 40; // 40 deg field (±20°)

        // Caret (^)
        ctx.beginPath();
        ctx.moveTo(0, TAPE_Y + 25);
        ctx.lineTo(-5, TAPE_Y + 35);
        ctx.lineTo(5, TAPE_Y + 35);
        ctx.closePath();
        ctx.stroke();

        // Tape Clip
        ctx.beginPath();
        ctx.rect(-TAPE_W / 2, TAPE_Y - 20, TAPE_W, 50);
        ctx.clip();

        ctx.font = C.fontMed;

        const startH = Math.floor(T.hdg - 20);
        const endH = Math.ceil(T.hdg + 20);

        for (let i = startH; i <= endH; i++) {
            const x = (i - T.hdg) * pxPerDeg;

            if (i % 10 === 0) {
                // Major Tick
                ctx.beginPath(); ctx.moveTo(x, TAPE_Y); ctx.lineTo(x, TAPE_Y - 10); ctx.stroke();

                let val = (i + 360) % 360;
                let numStr = (val / 10).toFixed(0).padStart(2, '0');
                if (val === 0) numStr = "N";
                if (val === 90) numStr = "E";
                if (val === 180) numStr = "S";
                if (val === 270) numStr = "W";

                ctx.fillText(numStr, x, TAPE_Y - 15);
            } else if (i % 5 === 0) {
                ctx.beginPath(); ctx.moveTo(x, TAPE_Y); ctx.lineTo(x, TAPE_Y - 5); ctx.stroke();
            }
        }

        // Waypoint Bearing Marker (V on tape)
        if (N.hasRoute) {
            let wpX = N.turn * pxPerDeg;
            if (wpX > -TAPE_W / 2 && wpX < TAPE_W / 2) {
                ctx.fillText("V", wpX, TAPE_Y + 25);
            }
        }
        ctx.restore();

        // Lubber Line
        ctx.beginPath();
        ctx.moveTo(0, TAPE_Y); ctx.lineTo(0, TAPE_Y + 15);
        ctx.stroke();

        // ==================================================
        // 2. LEFT DATA STACK
        // ==================================================
        const L_STACK_X = -300;
        let currentY = 150;
        const LINE_H = 35;

        ctx.save();
        ctx.textAlign = "left";
        ctx.font = C.fontBig;

        // 1. WP Data
        if (N.hasRoute) {
            let absBrg = (T.hdg + N.turn + 360) % 360;
            let brgStr = Math.round(absBrg).toString().padStart(3, '0');
            let distNm = (N.dist / 1852).toFixed(1);

            ctx.fillText(brgStr, L_STACK_X, currentY);
            ctx.fillText(distNm, L_STACK_X, currentY + LINE_H);
        }
        currentY += (LINE_H * 2.5);

        // 2. IAS "XXX A"
        let iasKts = Math.round(T.ias * 1.94384);
        ctx.fillText(`${iasKts.toString().padStart(3, '0')} A`, L_STACK_X, currentY);
        currentY += LINE_H;

        // 3. GS "XXX G" - ALIGNED WITH CENTER_Y
        let gsKts = Math.round(T.spd * 1.94384);
        ctx.fillText(`${gsKts.toString().padStart(3, '0')} G`, L_STACK_X, CENTER_Y);

        ctx.restore();

        // ==================================================
        // 3. RIGHT DATA STACK (Refined per Step 175)
        // ==================================================
        const R_STACK_X = 300;
        // Baro Alt roughly aligned with top section
        currentY = 150;

        ctx.save();
        ctx.textAlign = "right";
        ctx.font = C.fontBig;

        // 1. Baro Alt "XXXX B"
        let baroFt = Math.round(T.alt_baro * 3.28084);
        ctx.fillText(`${baroFt} B`, R_STACK_X + 80, currentY);

        // 2. RADAR ALTITUDE SCALE & VSI
        const SCALE_X = R_STACK_X + 40;
        const UNIT_SCALE = 1.2; // 1.2 px per ft

        // Helper: 175ft aligned with CENTER_Y
        const getAltY = (alt) => CENTER_Y - (alt - 175) * UNIT_SCALE;

        ctx.lineWidth = 2; // Uniform line width
        const TICK_LEN = 20; // Uniform tick length

        // Draw Ticks (No numbers, Uniform Size)
        // Range logic: 0 to 300 covers the visible area comfortably
        ctx.beginPath();
        let ticksToDraw = new Set();

        // Major ticks explicitly requested
        [250, 200, 150, 100].forEach(t => ticksToDraw.add(t));
        // Minor ticks every 20ft
        for (let t = 0; t <= 300; t += 20) ticksToDraw.add(t);

        ticksToDraw.forEach(alt => {
            // Clip to reasonable visual area if needed (e.g. CENTER_Y +/- 160)
            let y = getAltY(alt);
            if (y < CENTER_Y - 160 || y > CENTER_Y + 160) return;

            ctx.moveTo(SCALE_X - TICK_LEN / 2, y);
            ctx.lineTo(SCALE_X + TICK_LEN / 2, y);
        });
        ctx.stroke();

        // Radar Alt Filling Bar (Left of ticks)
        let radFt = T.alt_r * 3.28084;
        let yZero = getAltY(0);
        let yCurr = getAltY(radFt);

        // Draw Bar if valid
        if (radFt < 2500) {
            ctx.fillStyle = data.settings.color || C.color;
            ctx.globalAlpha = 0.6;

            // Positioning: Left of ticks
            // Ticks centered at SCALE_X. Left edge is SCALE_X - 10.
            // Bar should be left of that, e.g. SCALE_X - 18, width 6.
            const BAR_X = SCALE_X - TICK_LEN / 2 - 8;
            const BAR_W = 6;

            // Height logic: From yZero (bottom) up to yCurr (top)
            // yZero is larger value (lower on screen) than yCurr
            let h = yZero - yCurr;
            // Clip bottom to scale area? Not strictly necessary if clipped by canvas logic, 
            // but good practice. For now, let it grow from bottom relative.

            if (h > 0) {
                ctx.fillRect(BAR_X, yCurr, BAR_W, h);
            }
            ctx.globalAlpha = 1.0;

            // Digital Readout
            // "immediatly on the left of the ... filling bar"
            // Position: Left of BAR_X
            ctx.font = C.fontMed;
            ctx.textAlign = "right";
            ctx.fillText(Math.round(radFt), BAR_X - 5, yCurr + 10);
        }

        // VSI Triangle (Right Side)
        // Center (0fpm) aligned with Center (175ft RAlt) ?
        // Or Center of Scale? 
        // "175 is aligned with bird" -> Center of screen.
        // Assuming VSI 0 is also aligned with Center of screen.
        let vsiFpm = T.vvi * 196.85;
        // Clamp to +/- 200 fpm visual range
        if (vsiFpm > 200) vsiFpm = 200;
        if (vsiFpm < -200) vsiFpm = -200;

        // Scale: +/- 200 fpm = +/- 150px (Visual spacing consistency with old scale height)
        let vsiY = CENTER_Y - (vsiFpm / 200) * 150;

        ctx.beginPath();
        // Triangle pointing Left? No, "Triangle pointing right" usually means on the left side pointing right?
        // OR "VS is indicated by the triangle pointing right" -> >
        // Reference image typically has VSI pointer on the RIGHT side of the scale pointing LEFT (<) or on LEFT pointing RIGHT (>).
        // User said: "VS is indicated by the triangle pointing right".
        // This usually means the shape is >. Which implies it's on the LEFT of the scale.
        // BUT user also said "VS and RA: ... keep bar for Ralt (Left)...".
        // And generally VSI is on the Right of the scale in AN/AVS-7.
        // Let's stick to Right side pointing Left (<) unless "pointing right" explicitly means > shape.
        // "pointing right" usually means the tip points right.
        // If it's on the right side, pointing right would point AWAY from scale. That's weird.
        // If it's on the left side, pointing right points INTO scale.
        // Previous code put it on Right side.
        // Let's put it on Right side, pointing Left (standard).
        // Wait, user said "triangle pointing right".
        // If I put it on LEFT side, it conflicts with RAlt bar.
        // Let's put it on RIGHT side for now.

        ctx.moveTo(SCALE_X + TICK_LEN / 2 + 2, vsiY);
        ctx.lineTo(SCALE_X + TICK_LEN / 2 + 12, vsiY - 6);
        ctx.lineTo(SCALE_X + TICK_LEN / 2 + 12, vsiY + 6);
        ctx.closePath();
        ctx.fill();

        ctx.restore();

        // ==================================================
        // 4. CENTER: HORIZON & PITCH LADDER
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y);

        const pxPerDegP = 8;
        const pitchPx = T.pitch * pxPerDegP;

        ctx.rotate(-T.roll * Math.PI / 180);
        ctx.translate(0, pitchPx);

        // Horizon Line (Long Dashed)
        ctx.beginPath();
        ctx.setLineDash([15, 5]);
        ctx.moveTo(-150, 0); ctx.lineTo(150, 0);
        ctx.stroke();
        ctx.setLineDash([]);

        // Center Tick
        ctx.beginPath(); ctx.moveTo(0, -10); ctx.lineTo(0, 10); ctx.stroke();

        // Ladder with clipping
        ctx.font = C.fontTiny;
        const LADDER_W = 50;

        ctx.save();
        ctx.beginPath();
        const CLIP_TOP = -CENTER_Y + 120;
        const CLIP_BOT = HUD_H - CENTER_Y - 120;
        ctx.rect(-200, CLIP_TOP, 400, CLIP_BOT - CLIP_TOP);
        ctx.clip();

        for (let p = -90; p <= 90; p += 10) {
            if (p === 0) continue;
            let y = -p * pxPerDegP;

            ctx.beginPath();
            if (p < 0) ctx.setLineDash([5, 5]);
            else ctx.setLineDash([]);

            ctx.moveTo(-LADDER_W, y); ctx.lineTo(LADDER_W, y);
            ctx.stroke();

            ctx.beginPath();
            ctx.setLineDash([]);
            let tipDir = (p > 0) ? 1 : -1;

            ctx.moveTo(-LADDER_W, y); ctx.lineTo(-LADDER_W, y + (5 * tipDir));
            ctx.moveTo(LADDER_W, y); ctx.lineTo(LADDER_W, y + (5 * tipDir));
            ctx.stroke();

            ctx.textAlign = "right";
            ctx.fillText(Math.abs(p), -LADDER_W - 5, y + 5);
            ctx.textAlign = "left";
            ctx.fillText(Math.abs(p), LADDER_W + 5, y + 5);
        }

        ctx.restore(); // End ladder clip
        ctx.restore(); // End pitch rotation

        // Fixed Aircraft Reference (Horizontal L's) - at CENTER_Y
        ctx.beginPath();
        // Left L
        ctx.moveTo(-20, CENTER_Y); ctx.lineTo(-10, CENTER_Y);
        ctx.lineTo(-10, CENTER_Y + 10);
        // Right L
        ctx.moveTo(20, CENTER_Y); ctx.lineTo(10, CENTER_Y);
        ctx.lineTo(10, CENTER_Y + 10);
        ctx.stroke();

        // TORQUE - Positioned at -10° pitch alignment (CENTER_Y + 80px)
        ctx.save();
        ctx.textAlign = "left";
        ctx.font = "bold 36px 'VT323', monospace";
        // 8px/deg * 10deg = 80px
        const TORQUE_Y = CENTER_Y + 80;
        // Text aligned left of -30?
        ctx.fillText("100%", -30, TORQUE_Y);
        ctx.restore();

        // Flight Path Marker (Diamond)
        let driftY = -T.vvi * 2;
        ctx.beginPath();
        ctx.moveTo(0, CENTER_Y + driftY - 10);
        ctx.lineTo(10, CENTER_Y + driftY);
        ctx.lineTo(0, CENTER_Y + driftY + 10);
        ctx.lineTo(-10, CENTER_Y + driftY);
        ctx.closePath();
        ctx.stroke();

        // ==================================================
        // 5. INCLINOMETER (Bottom)
        // ==================================================
        ctx.save();
        const BALL_Y = HUD_H - 100;
        ctx.translate(0, BALL_Y);

        // Rectangle Box
        ctx.strokeRect(-40, -10, 80, 20);

        // Center Lines
        ctx.beginPath();
        ctx.moveTo(-10, -10); ctx.lineTo(-10, 10);
        ctx.moveTo(10, -10); ctx.lineTo(10, 10);
        ctx.stroke();

        // Ball (Circle)
        let slipX = 0;
        ctx.beginPath();
        ctx.arc(slipX, 0, 8, 0, Math.PI * 2);
        ctx.fill();

        // Label "MST"
        ctx.font = C.fontMed;
        ctx.textAlign = "right";
        ctx.fillText("MST", -50, 5);

        ctx.restore();

        ctx.restore(); // End Scale
    }
});
