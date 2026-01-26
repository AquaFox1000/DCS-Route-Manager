window.registerHudProfile('uh60l_minimal', {
    config: {
        color: '#00ff00',
        shadowBlur: 1,
        lineWidth: 2,

        // Simplified fonts
        fontBig: "400 40px 'VT323', monospace",
        fontMed: "400 28px 'VT323', monospace",
    },

    draw: function (ctx, data, vw, vh) {
        const C = this.config;
        const T = data.telemetry;
        const N = data.nav;

        ctx.strokeStyle = data.settings.color || C.color;
        ctx.fillStyle = data.settings.color || C.color;
        ctx.lineWidth = C.lineWidth;
        ctx.shadowBlur = C.shadowBlur;
        ctx.textAlign = "center";

        const REF_H = 1000;
        const scale = vh / REF_H;

        ctx.save();
        ctx.scale(scale, scale);

        // Center of Logic Screen
        const CX = 0;
        const CY = REF_H / 2; // Not used much in minimal

        // ==================================================
        // 1. TOP BANNER STRIP (Like Su-25T Minimal)
        // ==================================================
        const TOP_Y = 80;

        // A. Heading (Digital Center)
        let hdgVal = Math.round(T.hdg).toString().padStart(3, '0');
        ctx.font = C.fontBig;
        ctx.fillText(hdgVal + "°", 0, TOP_Y);

        // B. Torque (Left)
        // "XX%"
        const TRQ_X = -300;
        ctx.textAlign = "right";
        ctx.fillText("TRQ XX%", TRQ_X, TOP_Y); // Placeholder

        // C. Speed (Far Left)
        const SPD_X = -500;
        let knots = Math.round(T.spd * 1.94384);
        ctx.fillText(knots + " KTS", SPD_X, TOP_Y);

        // D. Altitude (Right)
        const ALT_X = 300;
        ctx.textAlign = "left";
        let radarFt = T.alt_r * 3.28084;
        let baroFt = T.alt_baro * 3.28084;
        let altVal = Math.round(radarFt < 1500 ? radarFt : baroFt);
        let altLabel = radarFt < 1500 ? "R" : "M";
        ctx.fillText(altVal + " FT " + altLabel, ALT_X, TOP_Y);

        // ==================================================
        // 2. CENTER RETICLE (Minimal)
        // ==================================================
        ctx.translate(0, CY);

        // Simple Flight Path Marker behavior (Static for now)
        ctx.beginPath();
        ctx.arc(0, 0, 10, 0, Math.PI * 2);
        ctx.moveTo(10, 0); ctx.lineTo(20, 0);
        ctx.moveTo(-10, 0); ctx.lineTo(-20, 0);
        ctx.moveTo(0, -10); ctx.lineTo(0, -20);
        ctx.stroke();

        // ==================================================
        // 3. WAYPOINT (Bottom)
        // ==================================================
        if (N.hasRoute) {
            ctx.font = C.fontMed;
            const BOT_Y = REF_H / 2 - 100; // Relative to center translation

            let distNm = (N.dist / 1852).toFixed(1);
            let bearing = Math.round(N.turn); // Relative turn

            let arrow = bearing > 0 ? "→" : "←";
            if (Math.abs(bearing) < 5) arrow = "↑";

            ctx.fillText(`${arrow} WP${N.index + 1} ${distNm}NM`, 0, BOT_Y);
        }

        ctx.restore();
    }
});
