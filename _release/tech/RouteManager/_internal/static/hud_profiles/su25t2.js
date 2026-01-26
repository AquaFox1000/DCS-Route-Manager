/**
 * SU-25T HUD Profile (Red/Night Mode)
 * Accurate recreation of the Su-25T symbology.
 * * COORDINATE SYSTEM: 
 * Center (0,0) is the middle of the HUD/Screen.
 */

window.registerHudProfile('su25t2', {

    // --- CONFIGURATION ---
    config: {
        // Precise Amber/Red color for Su-25T Night/Contrast mode
        color: '#ff4400', 
        shadowColor: '#441100', // Slight glow effect
        
        // Line weights
        strokeThick: 3,
        strokeThin: 2,
        
        // Typography (using VT323 for that CRT look)
        fontBig: 'bold 36px "VT323", monospace',
        fontMed: 'bold 24px "VT323", monospace',
        fontSmall: '20px "VT323", monospace',

        // Scaling Factors
        scalePitch: 14,      // Pixels per degree of pitch
        tapeScale: 7,        // Pixels per degree of heading
        
        // Positioning (Relative to 0,0 center)
        tapeY: -280,         // Heading tape vertical position
        statsY: -120,        // Speed/Alt vertical position
        bankY: 240,          // Bank scale vertical position
        bankRadius: 180      // Size of the bank arc
    },

    // --- MAIN DRAW LOOP ---
    draw: function(ctx, HUD, width, height) {
        const C = this.config;
        const d = HUD.telemetry;

        // 1. Setup Center Coordinate System
        ctx.save();
        ctx.translate(width / 2, height / 2); // (0,0) is now center

        // 2. Global Styles
        ctx.strokeStyle = C.color;
        ctx.fillStyle = C.color;
        ctx.lineWidth = C.strokeThin;
        ctx.lineCap = 'butt'; // Sharper lines for digital HUD
        ctx.lineJoin = 'miter';
        
        // Optional: Add CRT Glow
        ctx.shadowBlur = 4;
        ctx.shadowColor = C.color;

        // --- 3. STATIC SYMBOLOGY (Screen Fixed) ---
        this.drawHeadingTape(ctx, C, d.hdg);
        this.drawDigitalStats(ctx, C, d.ias, d.alt_r, d.alt_baro);
        this.drawBankIndicator(ctx, C, d.roll);
        this.drawReticle(ctx, C);

        // --- 4. DYNAMIC SYMBOLOGY (Horizon Fixed) ---
        // We clip the middle area so the pitch ladder doesn't overlap the header/footer
        ctx.save();
        ctx.beginPath();
        ctx.rect(-400, -220, 800, 440); // Central field of view
        ctx.clip();

        this.drawPitchLadder(ctx, C, d.pitch, d.roll);
        
        ctx.restore(); // End Clip
        ctx.restore(); // End Main Transform
    },

    // --- COMPONENT DRAWERS ---

    drawHeadingTape: function(ctx, C, hdg) {
        const y = C.tapeY;
        const w = 400; // Width of tape window
        const h = 45;

        ctx.save();
        
        // 1. Clip Window
        ctx.beginPath();
        ctx.rect(-w/2, y - 10, w, h); 
        ctx.clip();

        // 2. Draw Bottom Line
        ctx.beginPath();
        ctx.lineWidth = C.strokeThick;
        ctx.moveTo(-w/2, y + 30);
        ctx.lineTo(w/2, y + 30);
        ctx.stroke();

        // 3. Draw Ticks
        // Render 30 degrees either side
        const range = 35; 
        const start = Math.floor(hdg - range);
        const end = Math.floor(hdg + range);

        ctx.font = C.fontMed;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.lineWidth = C.strokeThin;

        for (let i = start; i <= end; i++) {
            // X position relative to center
            let x = (i - hdg) * C.tapeScale;

            if (i % 10 === 0) {
                // Major Tick (Long with Number)
                ctx.beginPath();
                ctx.moveTo(x, y + 30);
                ctx.lineTo(x, y + 15);
                ctx.stroke();

                // Number Logic (01..36)
                let val = i;
                while (val < 0) val += 360;
                while (val >= 360) val -= 360;
                let txt = (val / 10).toString().padStart(2, '0');
                if (val === 0) txt = "00";

                ctx.fillText(txt, x, y + 12);
            } else if (i % 5 === 0) {
                // Minor Tick (Short)
                ctx.beginPath();
                ctx.moveTo(x, y + 30);
                ctx.lineTo(x, y + 22);
                ctx.stroke();
            }
        }
        ctx.restore();

        // 4. Center Marker (Fixed)
        // Inverted Triangle pointing down at the tape
        ctx.beginPath();
        ctx.fillStyle = C.color;
        ctx.moveTo(0, y + 32); 
        ctx.lineTo(-6, y + 42);
        ctx.lineTo(6, y + 42);
        ctx.fill();
    },

    drawDigitalStats: function(ctx, C, ias, altR, altBaro) {
        // Left Side: IAS (Speed)
        const leftX = -320;
        const rightX = 320;
        const y = C.statsY;

        ctx.textAlign = 'right';
        
        // Value
        ctx.font = C.fontBig;
        ctx.fillText(Math.floor(ias).toString(), leftX, y);
        
        // Label
        ctx.font = C.fontSmall;
        ctx.fillText("SPD", leftX, y - 35);
        
        // Decorative box line (Su-25 style underline/corner)
        ctx.lineWidth = C.strokeThin;
        ctx.beginPath();
        ctx.moveTo(leftX + 10, y - 40);
        ctx.lineTo(leftX + 10, y + 5);
        ctx.lineTo(leftX - 80, y + 5);
        ctx.stroke();


        // Right Side: Altitude
        // Logic: Switch to Baro if Radar Alt is too high (>1000m usually)
        let altVal = altR;
        let altLabel = "R"; // Radar
        if (altR > 1500) { // arbitrary switch point for HUD
            altVal = altBaro;
            altLabel = "";
        }

        ctx.textAlign = 'left';
        
        // Value
        ctx.font = C.fontBig;
        ctx.fillText(Math.floor(altVal).toString(), rightX, y);

        // Label
        ctx.font = C.fontSmall;
        ctx.fillText("ALT " + altLabel, rightX, y - 35);

        // Decorative box line
        ctx.beginPath();
        ctx.moveTo(rightX - 10, y - 40);
        ctx.lineTo(rightX - 10, y + 5);
        ctx.lineTo(rightX + 80, y + 5);
        ctx.stroke();
    },

    drawBankIndicator: function(ctx, C, roll) {
        const y = C.bankY;
        const r = C.bankRadius;

        ctx.save();
        ctx.translate(0, y); // Move to bottom center area

        // 1. The Scale (Static Arc)
        ctx.beginPath();
        ctx.lineWidth = C.strokeThick;
        // Draw arc from -45 to +45
        // Math: -PI/2 is Up. We want an arc opening Upwards.
        ctx.arc(0, 0, r, Math.PI + 0.8, (Math.PI * 2) - 0.8);
        ctx.stroke();

        // 2. Ticks on Scale
        const ticks = [-45, -30, -15, 0, 15, 30, 45];
        ctx.lineWidth = C.strokeThin;
        
        ticks.forEach(deg => {
            // Convert to radians. -90 is Up.
            let rad = (deg - 90) * (Math.PI / 180);
            
            let x1 = Math.cos(rad) * r;
            let y1 = Math.sin(rad) * r;
            let x2 = Math.cos(rad) * (r + 15); // Ticks point OUTWARDS on Su-25
            let y2 = Math.sin(rad) * (r + 15);

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        });

        // 3. The Pointer (Moves with Roll)
        // Roll Left (negative) -> Pointer moves Left (negative angle on arc)
        const ptrRad = (roll - 90) * (Math.PI / 180);
        
        const px = Math.cos(ptrRad) * (r - 5);
        const py = Math.sin(ptrRad) * (r - 5);

        // Draw Triangle Pointer (pointing OUT from center)
        ctx.save();
        ctx.translate(px, py);
        ctx.rotate(ptrRad); // Align with radius
        
        ctx.beginPath();
        ctx.moveTo(0, 0); // Tip touching the arc
        ctx.lineTo(-8, 15);
        ctx.lineTo(8, 15);
        ctx.closePath();
        ctx.fill();
        ctx.restore();

        ctx.restore();
    },

    drawPitchLadder: function(ctx, C, pitch, roll) {
        ctx.save();

        // Roll Rotation
        ctx.rotate(-roll * Math.PI / 180);
        
        // Pitch Translation
        const yOffset = pitch * C.scalePitch;
        ctx.translate(0, yOffset);

        // Artificial Horizon Line (0 deg) - The "Earth" line
        // Su-25T often has a solid line across the whole FOV
        ctx.beginPath();
        ctx.lineWidth = C.strokeThin;
        ctx.moveTo(-600, 0);
        ctx.lineTo(600, 0);
        ctx.stroke();

        // Draw Bars
        const visibleDeg = 25;
        const start = Math.floor((pitch - visibleDeg) / 5) * 5;
        const end = Math.floor((pitch + visibleDeg) / 5) * 5;

        ctx.textAlign = 'right';
        ctx.font = C.fontSmall;

        for (let p = start; p <= end; p += 5) {
            if (p === 0) continue; // Already drew horizon

            let y = -p * C.scalePitch;
            let w = (p % 10 === 0) ? 80 : 40; // Width of bars
            let gap = 60; // Center gap

            ctx.beginPath();

            // Left Bar
            ctx.moveTo(-gap - w, y);
            ctx.lineTo(-gap, y);
            // Tab (always points towards horizon in Su-25T)
            let tabDir = (p > 0) ? 1 : -1; 
            ctx.lineTo(-gap, y + (8 * tabDir));

            // Right Bar
            ctx.moveTo(gap + w, y);
            ctx.lineTo(gap, y);
            // Tab
            ctx.lineTo(gap, y + (8 * tabDir));

            ctx.stroke();

            // Numbers (on 10s only)
            if (p % 10 === 0) {
                let txt = Math.abs(p).toString();
                // Left Text
                ctx.textAlign = 'right';
                ctx.fillText(txt, -gap - w - 10, y + 5);
                // Right Text
                ctx.textAlign = 'left';
                ctx.fillText(txt, gap + w + 10, y + 5);
            }
        }
        ctx.restore();
    },

    drawReticle: function(ctx, C) {
        // Standard "Piper" (Dot with small wings)
        ctx.lineWidth = C.strokeThick;
        ctx.beginPath();
        
        // Center Circle
        ctx.arc(0, 0, 4, 0, Math.PI * 2);
        
        // Wings
        ctx.moveTo(-20, 0); ctx.lineTo(-8, 0);
        ctx.moveTo(20, 0); ctx.lineTo(8, 0);
        
        // Top vertical tick
        ctx.moveTo(0, -20); ctx.lineTo(0, -8);
        
        ctx.stroke();
    }
});