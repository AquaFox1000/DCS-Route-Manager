window.registerHudProfile('su25', {
    config: {
        font: "22px 'Changa', sans-serif",
        bigFont: "40px 'Changa', sans-serif",
        medFont: "28px 'Changa', sans-serif",
        smallFont: "16px 'Changa', sans-serif",
        lineWidth: 2.5,
        defaultColor: '#ff9d00' // Amber
    },

    draw: function(ctx, data, vw, vh) {
        const T = this.config;
        const color = data.settings.color || T.defaultColor;
        
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = T.lineWidth;
        ctx.font = T.font;

        const tel = data.telemetry;
        const nav = data.nav;

        // --- CONSTANTS FOR LEGACY LAYOUT ---
        // We stick to a fixed box size to preserve the "optic" look
        const BOX_W = 520; 
        const BOX_H = 520;
        
        // Center the coordinate system
        // (0,0) is TOP-CENTER of screen coming from loader
        const CX = 0; 
        const TOP = 20; 
        const LEFT = -BOX_W / 2;
        const RIGHT = BOX_W / 2;

        // --- 1. HEADING TAPE ---
        const tapeY = TOP + 60;
        const pxPerDeg = 10; // Tighter scale for classic HUD

        ctx.save();
        ctx.beginPath(); ctx.rect(LEFT, TOP, BOX_W, 120); ctx.clip();

        // Base Line & Center Marker
        ctx.beginPath(); ctx.moveTo(LEFT, tapeY + 30); ctx.lineTo(RIGHT, tapeY + 30); ctx.stroke();
        ctx.lineWidth = 2; 
        ctx.beginPath(); ctx.moveTo(0, tapeY + 30); ctx.lineTo(-8, tapeY + 45); ctx.lineTo(8, tapeY + 45); ctx.closePath(); ctx.stroke();

        ctx.textAlign = "center";
        const startHdg = Math.floor(tel.hdg - 25);
        const endHdg = Math.floor(tel.hdg + 25);

        for (let i = startHdg; i <= endHdg; i++) {
            if (i % 5 === 0) {
                const diff = i - tel.hdg;
                const x = diff * pxPerDeg;
                const isTen = (i % 10 === 0);
                
                const tickH = isTen ? 15 : 8;
                ctx.beginPath(); ctx.moveTo(x, tapeY + 30); ctx.lineTo(x, tapeY + 30 - tickH); ctx.stroke();
                
                if (isTen) {
                    let val = (i + 360) % 360; 
                    let num = val / 10; 
                    ctx.fillText(String(Math.round(num)).padStart(2, '0'), x, tapeY + 5); 
                }
            }
        }

        // Nav Bug
        if (nav.hasRoute) {
            let cx = nav.turn * pxPerDeg;
            // Clamp
            if (cx > RIGHT - 15) cx = RIGHT - 15; 
            if (cx < LEFT + 15) cx = LEFT + 15;
            
            ctx.lineWidth = 3;
            // Classic Su-25 double-triangle bug
            ctx.beginPath(); ctx.moveTo(cx - 8, tapeY - 25); ctx.lineTo(cx + 8, tapeY - 25); ctx.lineTo(cx, tapeY - 10); ctx.fill();
        }
        ctx.restore();

        // --- 2. DIRECTOR CIRCLE ---
        if (nav.hasRoute) {
            const iconY = tapeY + 110;
            // Director Logic
            let hdgErr = nav.turn; 
            // Simple Pitch Logic (Target Alt vs Current Alt)
            let targetM = nav.alt; // data.nav.alt is usually meters for Su-25
            let diffM = targetM - tel.alt; 
            let cmdPitch = diffM * 0.05; 
            if(cmdPitch > 10) cmdPitch = 10; if(cmdPitch < -10) cmdPitch = -10;
            let pitchErr = cmdPitch - tel.pitch; 

            // Static Center Circle
            ctx.lineWidth = 2;
            const radius = 10; 
            ctx.beginPath(); ctx.arc(0, iconY, radius, 0, Math.PI*2); ctx.stroke();

            // Moving Director Dot
            let dx = hdgErr * 3; 
            let dy = -pitchErr * 3; 
            
            // Limit travel
            if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
                let len = Math.sqrt(dx*dx + dy*dy); 
                if(len > 50) len = 50; 
                if(len < radius) len = radius + 5; 
                
                let rad = Math.atan2(dy, dx); 
                let endX = Math.cos(rad) * len; 
                let endY = Math.sin(rad) * len;
                
                ctx.beginPath(); 
                ctx.moveTo(Math.cos(rad)*radius, iconY + Math.sin(rad)*radius); 
                ctx.lineTo(endX, iconY + endY); 
                ctx.stroke(); 
                
                ctx.beginPath(); ctx.arc(endX, iconY + endY, 2, 0, Math.PI*2); ctx.fill();
            }
        }

        // --- 3. TEXT INFO ---
        if (nav.hasRoute) {
            const iconY = tapeY + 110;
            
            // Distance (Center)
            ctx.font = T.medFont;
            ctx.textAlign = "center";
            let distKm = nav.dist.toFixed(1);
            ctx.fillText(distKm, 0, tapeY + 75);

            // Waypoint Info (Right Side)
            const infoX = RIGHT - 60;
            const startY = tapeY + 40;
            
            ctx.textAlign = "left";
            ctx.font = T.bigFont;
            ctx.fillText(Math.round(nav.alt), infoX, startY); // Target Alt
            
            ctx.font = T.medFont;
            ctx.fillText(nav.wpName, infoX, startY + 35); // WP Name
        }
    }
});