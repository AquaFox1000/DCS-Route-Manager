// static/hud_profiles/su25hmd.js

// 1. REGISTER BY NAME
window.registerHudProfile('su25hmd', {
    
    // Configuration
    config: {
        font: "bold 24px 'Changa', sans-serif",
        bigFont: "bold 36px 'Changa', sans-serif",
        smallFont: "bold 18px 'Changa', sans-serif",
        lineWidth: 3
    },

    draw: function(ctx, data, vw, vh) {
        const T = this.config;
        const color = data.settings.color;
        
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = T.lineWidth;

        // --- DATA ---
        const tel = data.telemetry;
        const nav = data.nav;
        const phys = data.physics;

        // --- LAYOUT ---
        // Top-Center Origin (0,0) is center of top edge of screen.
        // We define a 50% width box for the elements.
        const BOX_W = vw * 0.5; 
        const HALF_W = BOX_W / 2;
        
        const LEFT = -HALF_W;
        const RIGHT = HALF_W;
        const TOP = 20; 
        const BOTTOM = vh - 20; 

        // ==========================================
        // 1. HEADING TAPE (The Su-25 Style)
        // ==========================================
        const tapeY = TOP + 50;
        const pxPerDeg = BOX_W / 35; // How spread out the numbers are
        
        ctx.save();
        ctx.beginPath(); ctx.rect(LEFT, 0, BOX_W, 150); ctx.clip(); // Clip to top box

        // The Baseline
        ctx.beginPath(); 
        ctx.moveTo(LEFT, tapeY); 
        ctx.lineTo(RIGHT, tapeY); 
        ctx.stroke();
        
        ctx.textAlign = "center"; 
        ctx.font = T.font;
        const startHdg = tel.hdg - 20; 
        const endHdg = tel.hdg + 20;

        for (let i = Math.floor(startHdg); i <= Math.ceil(endHdg); i++) {
            const diff = i - tel.hdg;
            const x = diff * pxPerDeg; 
            
            // Su-25 Logic: Ticks hang DOWN from the line
            if (i % 10 === 0) {
                // Major Tick (Long)
                ctx.beginPath(); ctx.moveTo(x, tapeY); ctx.lineTo(x, tapeY + 20); ctx.stroke();
                
                // Number (00 - 35)
                let val = (i + 360) % 360; 
                let num = val / 10;
                // Draw number ABOVE the line
                ctx.fillText(String(Math.round(num)).padStart(2,'0'), x, tapeY - 10);
            } else if (i % 5 === 0) {
                // Minor Tick (Short)
                ctx.beginPath(); ctx.moveTo(x, tapeY); ctx.lineTo(x, tapeY + 10); ctx.stroke();
            }
        }
        
        // The Caret (Double Triangle Style)
        ctx.beginPath(); 
        ctx.moveTo(0, tapeY + 20); 
        ctx.lineTo(-8, tapeY + 35); 
        ctx.lineTo(8, tapeY + 35); 
        ctx.fill();
        ctx.restore();

        // ==========================================
        // 2. SPEED (Top Left)
        // ==========================================
        const spdX = LEFT + 60; 
        const spdY = tapeY + 60;
        
        // Convert to KM/H
        let spdVal = tel.spd * 3.6; 
        
        ctx.textAlign = "right"; 
        ctx.font = T.bigFont;
        ctx.fillText(Math.round(spdVal), spdX, spdY);
        
        // Target Speed (Small)
        ctx.font = T.smallFont; 
        ctx.fillText("600", spdX, spdY - 40);

        // Acceleration Triangle
        const accX = spdX - 25; 
        const accY = spdY + 20;
        let accOffset = 0;
        
        if (phys.accel > 0.5) accOffset = 20;   // Speeding up
        else if (phys.accel < -0.5) accOffset = -20; // Slowing down
        
        // Draw Scale
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(accX - 20, accY+14); ctx.lineTo(accX + 20, accY+14); ctx.stroke(); 
        ctx.lineWidth = T.lineWidth;
        
        // Draw Triangle
        ctx.beginPath(); 
        ctx.moveTo(accX + accOffset, accY); 
        ctx.lineTo(accX + accOffset - 6, accY + 12); 
        ctx.lineTo(accX + accOffset + 6, accY + 12); 
        ctx.fill();

        // ==========================================
        // 3. ALTITUDE (Top Right)
        // ==========================================
        const altX = RIGHT - 60; 
        const altY = spdY;
        
        ctx.textAlign = "left"; 
        ctx.font = T.bigFont;
        ctx.fillText(Math.round(tel.alt), altX, altY);
        
        ctx.font = T.smallFont; 
        ctx.fillText("ALT", altX, altY - 40);
        
        // Radar Alt Indicator
        if (tel.alt < 1500) {
            ctx.font = "bold 26px 'Changa', sans-serif"; 
            ctx.fillText("R", altX + 90, altY);
        }

        // ==========================================
        // 4. PITCH LADDER (Soviet Style)
        // ==========================================
        // We pass 'vh' (Height) so we can scale the pitch lines vertically
        this.drawSovietPitch(ctx, tel, vh, T.smallFont);

        // ==========================================
        // 5. FLIGHT DIRECTOR (The Circle)
        // ==========================================
        if (nav.hasRoute) {
            let cueX = nav.turn * pxPerDeg;
            
            // Clamp to the 50% box limits
            if (cueX < LEFT + 30) cueX = LEFT + 30; 
            if (cueX > RIGHT - 30) cueX = RIGHT - 30;
            
            // Draw Circle
            ctx.lineWidth = 2;
            ctx.beginPath(); 
            ctx.arc(cueX, 0, 15, 0, Math.PI*2); // 0 Y = Center line
            ctx.stroke();
            
            // Draw "Leash"
            ctx.beginPath(); 
            ctx.moveTo(0, 0); 
            ctx.lineTo(cueX, 0); 
            ctx.setLineDash([5, 5]); 
            ctx.stroke(); 
            ctx.setLineDash([]);
            ctx.lineWidth = T.lineWidth;
        }

        // ==========================================
        // 6. BOTTOM INFO
        // ==========================================
        const botY = BOTTOM - 40;
        
        ctx.textAlign = "left"; 
        ctx.font = T.font;
        const wpText = nav.hasRoute ? `WP ${nav.index + 1}` : "NO ROUTE";
        ctx.fillText(wpText, LEFT, botY);
        
        ctx.textAlign = "right";
        const distText = nav.hasRoute ? `D: ${nav.dist.toFixed(1)} km` : "--.- km";
        ctx.fillText(distText, RIGHT, botY);
    },

    // Helper: Draw simple Soviet-style pitch lines
    drawSovietPitch: function(ctx, tel, totalHeight, font) {
        // Calculate Scale: 25 degrees = Half Screen Height
        const pitchPx = (totalHeight / 2) / 25;

        ctx.save();
        // Shift context to vertical center of screen (since we started at Top)
        ctx.translate(0, totalHeight / 2);
        
        // Rotate for Roll
        ctx.rotate(-tel.roll * Math.PI / 180);
        
        // Translate for Pitch
        ctx.translate(0, tel.pitch * pitchPx);

        // Horizon Line (Long)
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(-300, 0); ctx.lineTo(300, 0); ctx.stroke();

        ctx.font = font; 
        ctx.textAlign = "right"; 
        ctx.textBaseline = "middle";
        
        // Draw lines every 10 degrees
        // Limit drawing to what is visible (+/- 35 deg from center)
        const start = Math.floor((tel.pitch - 35)/10)*10;
        const end = Math.floor((tel.pitch + 35)/10)*10;
        
        for (let p = start; p <= end; p += 10) {
            if (p === 0 || p > 90 || p < -90) continue;
            
            let y = -p * pitchPx;
            
            // Left Tick
            ctx.beginPath(); ctx.moveTo(-120, y); ctx.lineTo(-80, y); ctx.stroke();
            // Right Tick
            ctx.beginPath(); ctx.moveTo(120, y); ctx.lineTo(80, y); ctx.stroke();
            
            // Number on Left
            ctx.fillText(Math.abs(p), -130, y);
        }
        ctx.restore();
    }
});