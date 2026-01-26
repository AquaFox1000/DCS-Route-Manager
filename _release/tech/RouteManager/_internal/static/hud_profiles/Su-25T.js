// static/hud_profiles/su25t.js

window.registerHudProfile('Su-25T', {
    config: {
        color: '#33ff33', // "Russian HUD Green"
        shadowBlur: 3,    // Soft glow
        lineWidth: 5,     // THICKER LINES

        // Fonts
        fontBig: "400 80px 'Changa', sans-serif",
        fontMed: "400 55px 'Changa', sans-serif",
        fontTiny: "400 38px 'Changa', sans-serif",
        fontSink: "400 45px 'Changa', sans-serif",
    },

    draw: function (ctx, data, vw, vh) {
        // ==================================================
        // CANVAS SCALING & REFERENCE SETUP
        // ==================================================
        // We define the strict canvas size the HUD was designed for.
        const REF_W = 1920;
        const REF_H = 1200;

        // Calculate scaling to fit the height (maintaining aspect ratio & vertical FOV)
        const scale = vh / REF_H;

        // Calculate offset to center the HUD horizontally
        const offsetX = (vw - (REF_W * scale)) / 2;

        // Apply the transformation
        ctx.save();
        ctx.translate(offsetX, 0);
        ctx.scale(scale, scale);

        // Define "Virtual" Dimensions to be used in drawing logic instead of raw vw/vh
        const cvw = REF_W;
        const cvh = REF_H;

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

        // ==================================================
        // 0. GEOMETRY & CONSTANTS
        // ==================================================
        const CENTER_Y = cvh / 2; // Fixed to Reference Height
        const TAPE_Y = 100;

        // --- STEP 1: CALCULATE ROLL/WING GEOMETRY ---
        const GAP_CENTER = 9;
        const CROSS_SIZE = 35.5;
        const WING_START = 48;

        // Reference Calculations (Fixed to Reference Width)
        const REF_WING_LEN_OLD = (cvw * 0.4) / 2;
        const REF_NEW_LINE_LEN = (REF_WING_LEN_OLD - 45) * 0.7;
        const REF_BASE_WING_LEN = WING_START + REF_NEW_LINE_LEN;
        const REF_BASE_ROLL_R = REF_BASE_WING_LEN + 15;
        const REF_BASE_TICK_LEN = REF_BASE_ROLL_R * 0.1;
        const REF_EXTENSION = REF_BASE_TICK_LEN * 0.3;
        const REF_TICK_INNER_R = REF_BASE_ROLL_R - REF_EXTENSION;

        // Lock VSI Position
        const VSI_X = REF_TICK_INNER_R + 88;

        // New Roll Geometry
        const MIDDLE_DOT_X = (VSI_X - 95) + 20;
        const NEW_TICK_OUTER_R = MIDDLE_DOT_X;
        const NEW_BASE_ROLL_R = NEW_TICK_OUTER_R / 1.1;
        const NEW_BASE_TICK_LEN = NEW_BASE_ROLL_R * 0.1;
        const NEW_EXTENSION = NEW_BASE_TICK_LEN * 0.3;
        const NEW_TICK_INNER_R = NEW_BASE_ROLL_R - NEW_EXTENSION;
        const FINAL_WING_LEN = NEW_BASE_ROLL_R - 15 - NEW_EXTENSION;

        const TICK_INNER_R = NEW_TICK_INNER_R;
        const TICK_OUTER_R = NEW_TICK_OUTER_R;

        // --- STEP 2: HSI COMPRESSION ---
        const HSI_RIGHT = TICK_INNER_R;
        const HSI_LEFT = -TICK_INNER_R;
        const HSI_W = HSI_RIGHT - HSI_LEFT;

        // --- STEP 3: MARKER POSITIONING ---
        const SPD_X = HSI_LEFT - 20;
        const ALT_X = HSI_RIGHT + 20;

        const VSI_H = Math.min(cvh * 0.8, 600); // Fixed to Reference Height
        const PITCH_NUM_X = VSI_X - 30;

        // ==================================================
        // 1. HORIZON & PITCH (STATIC)
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y);

        const pitchScale = 18;
        const pitchPx = T.pitch * pitchScale;
        ctx.translate(0, pitchPx);

        // --- 1. DEFINE SAFE ZONES ---
        const TOP_SAFE = -CENTER_Y + 180;
        const BOT_SAFE = CENTER_Y - 195;

        // --- APPLY FONT FIX ---
        // We define the font here so it persists even if the Horizon Line if-statement is skipped
        ctx.font = C.fontTiny;
        ctx.textAlign = "center";

        // --- 2. HORIZON LINE (NOW CLIPPED) ---
        if (pitchPx >= TOP_SAFE && pitchPx <= BOT_SAFE) {
            const HOR_STOP = PITCH_NUM_X - 15;
            ctx.beginPath();
            ctx.moveTo(-HOR_STOP, 0);
            ctx.lineTo(HOR_STOP, 0);
            ctx.stroke();

            // Right side "0"
            ctx.fillText("0", PITCH_NUM_X, 5);

            // REMOVED: Left side "0"
            // ctx.fillText("0", -PITCH_NUM_X, 5);
        }

        // --- 3. PITCH SCALE ---
        for (let p = -90; p <= 90; p += 10) {
            if (p === 0) continue;

            let y = -p * pitchScale;
            let screenY = y + pitchPx;

            if (screenY < TOP_SAFE || screenY > BOT_SAFE) continue;

            const lineEnd = PITCH_NUM_X - 25;
            const lineStart = lineEnd - 40;

            ctx.beginPath();
            ctx.setLineDash([10, 12]);
            ctx.moveTo(lineStart, y);
            ctx.lineTo(lineEnd, y);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.textAlign = "right";
            ctx.fillText(p, PITCH_NUM_X, y + 10);
        }
        ctx.restore();

        // ==================================================
        // 2. CENTER CROSS & ROLL LINES (STATIC)
        // ==================================================
        ctx.save();
        ctx.translate(0, CENTER_Y);
        ctx.lineWidth = C.lineWidth;

        // A. Center Cross
        ctx.beginPath();
        ctx.moveTo(-CROSS_SIZE, 0); ctx.lineTo(-GAP_CENTER, 0);
        ctx.moveTo(CROSS_SIZE, 0); ctx.lineTo(GAP_CENTER, 0);
        ctx.moveTo(0, -CROSS_SIZE); ctx.lineTo(0, -GAP_CENTER);
        ctx.moveTo(0, CROSS_SIZE); ctx.lineTo(0, GAP_CENTER);
        ctx.stroke();

        // B. Roll Lines
        function drawRollTick(deg) {
            let rad = (deg * Math.PI) / 180;
            let xl = -Math.cos(rad) * TICK_INNER_R;
            let yl = Math.sin(rad) * TICK_INNER_R;
            let xr = Math.cos(rad) * TICK_INNER_R;
            let yr = Math.sin(rad) * TICK_INNER_R;

            let xl_out = -Math.cos(rad) * TICK_OUTER_R;
            let yl_out = Math.sin(rad) * TICK_OUTER_R;
            let xr_out = Math.cos(rad) * TICK_OUTER_R;
            let yr_out = Math.sin(rad) * TICK_OUTER_R;

            ctx.beginPath(); ctx.moveTo(xl, yl); ctx.lineTo(xl_out, yl_out); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(xr, yr); ctx.lineTo(xr_out, yr_out); ctx.stroke();
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

        const WING_SPAN_LEN = FINAL_WING_LEN - WING_START;
        const TICK_OFFSET = WING_START + (WING_SPAN_LEN * 0.2);

        ctx.lineWidth = C.lineWidth;

        // Wings
        ctx.beginPath();
        ctx.moveTo(-WING_START, 0); ctx.lineTo(-FINAL_WING_LEN, 0);
        ctx.moveTo(-TICK_OFFSET, 0); ctx.lineTo(-TICK_OFFSET, TICK_H);
        ctx.moveTo(WING_START, 0); ctx.lineTo(FINAL_WING_LEN, 0);
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
        const pxPerDeg = HSI_W / 30;

        ctx.beginPath(); ctx.rect(HSI_LEFT, 0, HSI_W, TAPE_Y + 20); ctx.clip();
        ctx.beginPath(); ctx.moveTo(HSI_LEFT, TAPE_Y); ctx.lineTo(HSI_RIGHT, TAPE_Y); ctx.stroke();

        const startH = Math.floor(T.hdg - 20);
        const endH = Math.ceil(T.hdg + 20);
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

            // Default: No rotation, draw exactly at calculated X
            let drawX = wpX;
            let rotation = 0;
            const PADDING = 25; // Push it inside slightly so it isn't cut by the clip

            // Out of bounds logic
            if (wpX < HSI_LEFT + PADDING) {
                drawX = HSI_LEFT + PADDING;
                rotation = Math.PI / 2; // Rotate +90 deg (Points Left)
            } else if (wpX > HSI_RIGHT - PADDING) {
                drawX = HSI_RIGHT - PADDING;
                rotation = -Math.PI / 2; // Rotate -90 deg (Points Right)
            }

            // Draw Triangle
            ctx.save();
            // Move to the center of where the marker should be
            const markCenterY = NUM_Y - 60;
            ctx.translate(drawX, markCenterY);
            ctx.rotate(rotation);

            ctx.beginPath();
            // Draw relative to center (0,0)
            // Tip points down (0, 15), Base is up (-15)
            ctx.moveTo(-20, -15); // Top Left
            ctx.lineTo(20, -15);  // Top Right
            ctx.lineTo(0, 15);    // Bottom Tip
            ctx.fill();

            ctx.restore();
        }
        ctx.restore();

        // Heading Triangle
        ctx.beginPath();
        ctx.moveTo(0, TAPE_Y); ctx.lineTo(-20, TAPE_Y + 30); ctx.lineTo(20, TAPE_Y + 30); ctx.closePath();
        ctx.stroke();

        // ==================================================
        // 5. SPEED, ACCEL & ALT
        // ==================================================
        const DATA_Y = TAPE_Y;

        ctx.textAlign = "right";
        ctx.font = C.fontBig;

        let kmh = T.ias * 3.6;
        let spdDisp = Math.floor(kmh / 10) * 10;
        ctx.fillText(spdDisp, SPD_X, DATA_Y);

        if (N.targetSpeed) {
            ctx.font = C.fontMed;
            let targetKmh = N.targetSpeed * 3.6;
            ctx.fillText(Math.round(targetKmh), SPD_X, DATA_Y - 60);
        }

        // Accel Triangle
        let accel = P.accel || 0;
        let digitW = ctx.measureText("0").width;
        let triX = 0;
        if (accel < -0.5) triX = SPD_X - (digitW * 2.5);
        else if (accel > 0.5) triX = SPD_X - (digitW * 0.5);
        else triX = SPD_X - (digitW * 1.5);

        const ACC_Y = DATA_Y + 15;
        ctx.beginPath();
        ctx.moveTo(triX, ACC_Y); ctx.lineTo(triX - 16, ACC_Y + 24); ctx.lineTo(triX + 16, ACC_Y + 24);
        ctx.closePath(); ctx.stroke();

        // Altitude
        ctx.textAlign = "left";
        let displayedAlt = 0;
        let isRadar = false;

        if (T.alt_r < 1500) {
            isRadar = true;
            displayedAlt = Math.round(T.alt_r);
        } else {
            isRadar = false;
            displayedAlt = Math.round(T.alt_baro / 10) * 10;
        }

        ctx.font = C.fontBig;
        let altStr = displayedAlt.toString();
        ctx.fillText(altStr, ALT_X, DATA_Y);

        if (isRadar) {
            let textWidth = ctx.measureText(altStr).width;
            ctx.fillText("R", ALT_X + textWidth + 10, DATA_Y + 12);
        }

        if (N.hasRoute && N.alt !== undefined) {
            ctx.font = C.fontMed;
            ctx.fillText(Math.round(N.alt), ALT_X, DATA_Y - 60);
        }

        // ==================================================
        // 6. VERTICAL RATE
        // ==================================================
        ctx.beginPath();
        ctx.moveTo(VSI_X, CENTER_Y - VSI_H / 2); ctx.lineTo(VSI_X, CENTER_Y + VSI_H / 2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(VSI_X, CENTER_Y); ctx.lineTo(VSI_X - 25, CENTER_Y); ctx.stroke();

        let vsiVal = T.vvi || 0;
        const VSI_LIMIT = 30;
        const pxPerMs = (VSI_H / 2) / VSI_LIMIT;

        let vsiPx = -vsiVal * pxPerMs;
        if (vsiPx > VSI_H / 2) vsiPx = VSI_H / 2;
        if (vsiPx < -VSI_H / 2) vsiPx = -VSI_H / 2;

        const ay = CENTER_Y + vsiPx;
        const shaftLen = 80;

        ctx.beginPath();
        ctx.moveTo(VSI_X, ay); ctx.lineTo(VSI_X + 10, ay - 5); ctx.lineTo(VSI_X + 10, ay + 5); ctx.fill();
        ctx.beginPath(); ctx.moveTo(VSI_X, ay); ctx.lineTo(VSI_X + shaftLen, ay); ctx.stroke();

        ctx.font = C.fontSink;
        let displayVsi = Math.round(Math.abs(vsiVal));
        if (displayVsi === 0) displayVsi = "0";

        let showText = true;
        if (Math.abs(vsiVal) > VSI_LIMIT) {
            const phase = Date.now() % 1000;
            if (phase > 750) showText = false;
        }

        if (showText) {
            let vsiStr = displayVsi.toString();
            ctx.textAlign = "left";
            ctx.fillText(vsiStr, VSI_X + 15, ay - 8);
        }

        // ==================================================
        // 7. BOTTOM INFO & MODES
        // ==================================================
        const BOT_Y = cvh - 120; // Fixed to Reference Height

        ctx.textAlign = "right";
        ctx.font = C.fontBig;
        // --- MODE LOGIC ---
        let modeStr = "NAV";
        let isCombatMode = false;

        // DCS Modes: 6=A-A, 7=A-G
        if (T.mode === 6) { modeStr = "A-A"; isCombatMode = true; }
        if (T.mode === 7) { modeStr = "A-G"; isCombatMode = true; }

        // 1. Draw Base Mode (Stationary)
        // Alignment is already set to "right" in previous lines
        // "NAV" stays anchored at SPD_X
        if (isCombatMode || N.hasRoute) {
            ctx.fillText(modeStr, SPD_X, BOT_Y);
        }

        // 2. AP Logic (Blinking + Position Fix)
        let showAp = N.apStatus; // Default: Show if active

        // Blink Logic (Relies on hud.html update)
        if (!isCombatMode && !showAp && N.apDisconnectTime) {
            const diff = Date.now() - N.apDisconnectTime;
            const BLINK_TOTAL_MS = 1800;
            const BLINK_SPEED_MS = 300;

            if (diff < BLINK_TOTAL_MS) {
                // Toggle True/False based on time
                showAp = Math.floor(diff / BLINK_SPEED_MS) % 2 !== 0;
            } else {
                N.apDisconnectTime = 0; // Stop blinking
            }
        }

        // 3. Draw "-AP" to the RIGHT of the stationary text
        // Only show if we are in NAV mode (Combat modes don't show AP usually)
        if (!isCombatMode && showAp) {
            ctx.save();
            ctx.textAlign = "left"; // Switch anchor to Left so text grows to the right
            ctx.fillText("-AP", SPD_X, BOT_Y);
            ctx.restore();
        }
        // Distance & WP Info (Strictly Nav dependent)
        if (N.hasRoute) {
            ctx.textAlign = "center";
            let distStr = (N.dist !== undefined && N.dist !== null) ? N.dist.toFixed(1) : "0.0";
            ctx.fillText(distStr, 0, BOT_Y);

            ctx.textAlign = "right";
            ctx.font = C.fontMed;

            let wpStr = "";

            // Check if it is a POI (Visual Target)
            if (N.type === 'poi') {
                // For POIs, we want "T <index+1>"
                wpStr = `T ${N.index + 1}`;
            } else {
                // For Standard Routes
                let typeText = N.type ? (N.type.toUpperCase() + " ") : "";
                wpStr = `${typeText}${N.index + 1}`;
            }

            ctx.fillText(wpStr, PITCH_NUM_X, BOT_Y);
        }

        // ==================================================
        // 8. FLIGHT DIRECTOR (NAV ASSISTANT)
        // ==================================================
        // VISIBILITY RULE: Only present if we have an active route
        if (N.hasRoute && data.settings.showDirector) {
            ctx.save();
            ctx.translate(0, CENTER_Y);
            let pitchErr = N.fd_pitch || 0;
            let bankErr = N.fd_bank || 0;

            // Visual Scaling
            // Pitch: 18 px/deg (Same as ladder)
            let yDir = -pitchErr * 18;
            // Roll: 18 px/deg (Matched to ladder scale roughly)
            let xDir = bankErr * 18;

            // Visual Clamping (The Box) - Keeps the circle from leaving the HUD view
            const MAX_PITCH_PX = 20 * 18; // 20 deg Up/Down limits
            const MAX_ROLL_PX = 20 * 18;  // Limit side movement to Keep it visible

            if (yDir > MAX_PITCH_PX) yDir = MAX_PITCH_PX;
            if (yDir < -MAX_PITCH_PX) yDir = -MAX_PITCH_PX;
            if (xDir > MAX_ROLL_PX) xDir = MAX_ROLL_PX;
            if (xDir < -MAX_ROLL_PX) xDir = -MAX_ROLL_PX;

            // Draw Circle
            ctx.beginPath();
            ctx.lineWidth = 5;
            ctx.strokeStyle = data.settings.color || C.color;

            // Draw the Director Circle
            ctx.arc(xDir, yDir, 45, 0, 2 * Math.PI);
            ctx.stroke();

            // Optional: Draw a dot in the center for precision
            //ctx.beginPath();
            //ctx.arc(xDir, yDir, 3, 0, 2 * Math.PI);
            //ctx.fill();
            ctx.restore();
        }

        // ==================================================
        // 9. 3D WORLD MARKERS
        // ==================================================
        ctx.restore(); // Go back to "Real World" pixel coordinates

        if (typeof Utils !== 'undefined' && data.camera && N.hasRoute && data.settings.showWpInfo) {

            const targetObj = { lat: N.lat, lon: N.lon, alt: N.alt || 0 };
            const screenPos = Utils.projectWorldToScreen(data.camera, targetObj, T, vw, vh, data.settings.fov);
            const limitX = vw * 0.3;

            if (screenPos && screenPos.x >= -limitX && screenPos.x <= limitX) {
                ctx.save();
                ctx.translate(screenPos.x, screenPos.y);

                // --- RESTORE HUD STYLING ---
                ctx.strokeStyle = data.settings.color || C.color;
                ctx.lineWidth = C.lineWidth;         // 5px Thickness
                ctx.shadowBlur = C.shadowBlur;       // The Glow
                ctx.shadowColor = ctx.strokeStyle;   // Glow Color

                const isCombat = (N.type === 'tgt' || N.type === 'poi');

                if (isCombat) {
                    ctx.beginPath();
                    ctx.moveTo(0, -25);
                    ctx.lineTo(15, 0);
                    ctx.lineTo(0, 25);
                    ctx.lineTo(-15, 0);
                    ctx.closePath();
                    ctx.stroke();
                } else {
                    ctx.strokeRect(-15, -15, 30, 30);
                }

                ctx.restore();
            }
        }
    }
});