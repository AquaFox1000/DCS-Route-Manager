// DCS Route Manager - Map Logic
// Refactored from map.html
// Socket initialized in map.html



// --- UTILITY FUNCTIONS ---

function pad(val) {
    if (val < 10) { val = '0000' + val }
    else if (val < 100) { val = '000' + val }
    else if (val < 1000) { val = '00' + val }
    else if (val < 10000) { val = '0' + val };
    return val
};

function MGRSString(Lat, Long) {
    if (Lat < -80) return 'Too far South'; if (Lat > 84) return 'Too far North';
    var c = 1 + Math.floor((Long + 180) / 6); var e = c * 6 - 183; var k = Lat * Math.PI / 180; var l = Long * Math.PI / 180; var m = e * Math.PI / 180; var n = Math.cos(k); var o = 0.006739496819936062 * Math.pow(n, 2); var p = 40680631590769 / (6356752.314 * Math.sqrt(1 + o)); var q = Math.tan(k); var r = q * q; var s = (r * r * r) - Math.pow(q, 6); var t = l - m; var u = 1.0 - r + o; var v = 5.0 - r + 9 * o + 4.0 * (o * o); var w = 5.0 - 18.0 * r + (r * r) + 14.0 * o - 58.0 * r * o; var x = 61.0 - 58.0 * r + (r * r) + 270.0 * o - 330.0 * r * o; var y = 61.0 - 479.0 * r + 179.0 * (r * r) - (r * r * r); var z = 1385.0 - 3111.0 * r + 543.0 * (r * r) - (r * r * r);
    var aa = p * n * t + (p / 6.0 * Math.pow(n, 3) * u * Math.pow(t, 3)) + (p / 120.0 * Math.pow(n, 5) * w * Math.pow(t, 5)) + (p / 5040.0 * Math.pow(n, 7) * y * Math.pow(t, 7));
    var ab = 6367449.14570093 * (k - (0.00251882794504 * Math.sin(2 * k)) + (0.00000264354112 * Math.sin(4 * k)) - (0.00000000345262 * Math.sin(6 * k)) + (0.000000000004892 * Math.sin(8 * k))) + (q / 2.0 * p * Math.pow(n, 2) * Math.pow(t, 2)) + (q / 24.0 * p * Math.pow(n, 4) * v * Math.pow(t, 4)) + (q / 720.0 * p * Math.pow(n, 6) * x * Math.pow(t, 6)) + (q / 40320.0 * p * Math.pow(n, 8) * z * Math.pow(t, 8));
    aa = aa * 0.9996 + 500000.0; ab = ab * 0.9996; if (ab < 0.0) ab += 10000000.0;
    var ad = 'CDEFGHJKLMNPQRSTUVWXX'.charAt(Math.floor(Lat / 8 + 10)); var ae = Math.floor(aa / 100000); var af = ['ABCDEFGH', 'JKLMNPQR', 'STUVWXYZ'][(c - 1) % 3].charAt(ae - 1); var ag = Math.floor(ab / 100000) % 20; var ah = ['ABCDEFGHJKLMNPQRSTUV', 'FGHJKLMNPQRSTUVABCDE'][(c - 1) % 2].charAt(ag);
    // pad function extracted to global scope
    aa = Math.floor(aa % 100000); aa = pad(aa); ab = Math.floor(ab % 100000); ab = pad(ab);
    return c + ad + ' ' + af + ah + ' ' + aa + ' ' + ab;
}

function LatLongFromMGRSstring(a) {
    var b = a.trim(); b = b.match(/\S+/g);
    if (b == null || b.length != 4) return [false, null, null];
    var c = (b[0].length < 3) ? b[0][0] : b[0].slice(0, 2); var d = (b[0].length < 3) ? b[0][1] : b[0][2]; var e = (c * 6 - 183) * Math.PI / 180; var f = ["ABCDEFGH", "JKLMNPQR", "STUVWXYZ"][(c - 1) % 3].indexOf(b[1][0]) + 1; var g = "CDEFGHJKLMNPQRSTUVWXX".indexOf(d); var h = ["ABCDEFGHJKLMNPQRSTUV", "FGHJKLMNPQRSTUVABCDE"][(c - 1) % 2].indexOf(b[1][1]); var i = [1.1, 2.0, 2.8, 3.7, 4.6, 5.5, 6.4, 7.3, 8.2, 9.1, 0, 0.8, 1.7, 2.6, 3.5, 4.4, 5.3, 6.2, 7.0, 7.9]; var j = [0, 2, 2, 2, 4, 4, 6, 6, 8, 8, 0, 0, 0, 2, 2, 4, 4, 6, 6, 6]; var k = i[g]; var l = Number(j[g]) + h / 10; if (l < k) l += 2; var m = f * 100000.0 + Number(b[2]); var n = l * 1000000 + Number(b[3]); m -= 500000.0; if (d < 'N') n -= 10000000.0; m /= 0.9996; n /= 0.9996; var o = n / 6367449.14570093; var p = o + (0.0025188266133249035 * Math.sin(2.0 * o)) + (0.0000037009491206268 * Math.sin(4.0 * o)) + (0.0000000074477705265 * Math.sin(6.0 * o)) + (0.0000000000170359940 * Math.sin(8.0 * o)); var q = Math.tan(p); var r = q * q; var s = r * r; var t = Math.cos(p); var u = 0.006739496819936062 * Math.pow(t, 2); var v = 40680631590769 / (6356752.314 * Math.sqrt(1 + u)); var w = v; var x = 1.0 / (w * t); w *= v; var y = q / (2.0 * w); w *= v; var z = 1.0 / (6.0 * w * t); w *= v; var aa = q / (24.0 * w); w *= v; var ab = 1.0 / (120.0 * w * t); w *= v; var ac = q / (720.0 * w); w *= v; var ad = 1.0 / (5040.0 * w * t); w *= v; var ae = q / (40320.0 * w); var af = -1.0 - u; var ag = -1.0 - 2 * r - u; var ah = 5.0 + 3.0 * r + 6.0 * u - 6.0 * r * u - 3.0 * (u * u) - 9.0 * r * (u * u); var ai = 5.0 + 28.0 * r + 24.0 * s + 6.0 * u + 8.0 * r * u; var aj = -61.0 - 90.0 * r - 45.0 * s - 107.0 * u + 162.0 * r * u; var ak = -61.0 - 662.0 * r - 1320.0 * s - 720.0 * (s * r); var al = 1385.0 + 3633.0 * r + 4095.0 * s + 1575 * (s * r); var lat = p + y * af * (m * m) + aa * ah * Math.pow(m, 4) + ac * aj * Math.pow(m, 6) + ae * al * Math.pow(m, 8); var lng = e + x * m + z * ag * Math.pow(m, 3) + ab * ai * Math.pow(m, 5) + ad * ak * Math.pow(m, 7);
    lat = lat * 180 / Math.PI; lng = lng * 180 / Math.PI; return [true, lat, lng];
}

// --- GLOBAL VARIABLES ---
let settings = { coords: 'latlon', altUnit: 'ft', distUnit: 'nm', defAlt: 20000 };
let missions = {};
let dcsMaps = ["Caucasus", "Persian Gulf", "Nevada", "Normandy", "Syria", "Marianas", "South Atlantic", "Sinai", "Kola", "Afghanistan"];
let activeMissionName = null;
let allSavedRoutes = {};
let allPois = [];
let activeRouteName = null;
let activeRouteData = [];
let activeWpIndex = -1;
let activeEditIndex = -1;
let wpCounter = 1;
let editingRouteName = "";
let editingRouteData = [];
let showWpLabels = false;
let visibleRoutes = new Set();
let clickMode = 'none';
let distMode = false;
let distStart = null;
let activePoiIndex = -1;
let selectedPoiSidcPartial = 'PIN';
let followMode = true; let headingUp = false;
let planeMarker = null;
let lastTelemetry = null;
let myUnitId = null;
let theaterUnits = {};
let tacticalUnits = {};
let phonebook = {}; // Unit ID → Player Name mapping
let pendingImportData = null;
let activeInputId = null;
let mapMoveTimer = null;
let isProgrammaticMove = false;
let autoSeq = true;
let hudMode = 0;
let extHudWindow = null;
let currentMapLayerName = 'dark';
let lastThreatDetect = 0;
let lastThreatDeadly = 0;
threatFillOpacity = 0.2;
let pressTimer; // Global timer for long-press


// --- API KEYS ---
const apiKey_Thunderforest = '6072325a7dae4cefa200e61b9c60be7e';
const apiKey_MapTiler = '9BuMXBfiB423LWz8K4LP';

// --- LAYERS & MAP STATE ---
// Re-added missing initialization
const map = L.map('map', {
    center: [42.15, 42.15],
    zoom: 7,
    zoomControl: false,
    attributionControl: false,
    wheelPxPerZoomLevel: 150 // Increase to reduce sensitivity (default 60)
});

let layers = {};
// Define Base Layers
layers['dark'] = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 });
layers['light'] = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 });
layers['opentopo'] = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { maxZoom: 17 });
layers['sat'] = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 });
layers['cyclosm'] = L.tileLayer('https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png', { maxZoom: 20 });
layers['darkstreet'] = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 20, className: 'invert-map' }); // Voyager (Streets) + Invert
layers['vfr'] = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }); // Placeholder
layers['vfr_night'] = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, className: 'invert-map' });
layers['relief'] = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}', { maxZoom: 13 });
layers['winter'] = L.tileLayer(`https://api.maptiler.com/maps/winter-v4/256/{z}/{x}/{y}.png?key=${apiKey_MapTiler}`, { maxZoom: 22 });

// Thunderforest Base Maps
layers['tf_landscape'] = L.tileLayer(`https://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=${apiKey_Thunderforest}`, { maxZoom: 22 });
layers['tf_outdoors'] = L.tileLayer(`https://{s}.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=${apiKey_Thunderforest}`, { maxZoom: 22 });


// Set Default Layer
layers['dark'].addTo(map);

let overlayLayers = {};
// Initialize Overlay Layers (Restored Legacy)
// Initialize Overlay Layers
// labels: Stamen Toner Labels (Raster currently works better for heavy labels than simplified vector)
overlayLayers['labels'] = L.tileLayer(`https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png`, { maxZoom: 20, zIndex: 600 });
// roads: MapTiler Toner Lines (Raster) - User requested Black/Grey. Removing invert.
overlayLayers['roads'] = L.tileLayer(`https://api.maptiler.com/maps/toner-lines/256/{z}/{x}/{y}.png?key=${apiKey_MapTiler}`, { maxZoom: 20, zIndex: 500, className: 'road-overlay' });

// contours: Vector Tiles (PBF) using Leaflet.VectorGrid
// STYLE: Thin orange/brown lines for elevation
const contourStyle = {
    color: '#673c0cff',
    weight: 0.2,
    opacity: 0.6,
    fill: false
};
overlayLayers['contours'] = L.vectorGrid.protobuf(`https://api.maptiler.com/tiles/contours-v2/{z}/{x}/{y}.pbf?key=${apiKey_MapTiler}`, {
    rendererFactory: L.canvas.tile,
    vectorTileLayerStyles: {
        'contour': contourStyle,
        'contour_ft': contourStyle
    },
    interactive: false,
    zIndex: 450,
    maxNativeZoom: 14
});

// buildings: Vector Tiles (PBF)
const buildingStyle = {
    color: '#333',
    weight: 0.5,
    fillColor: '#555',
    fillOpacity: 0.4,
    fill: true
};
overlayLayers['buildings'] = L.vectorGrid.protobuf(`https://api.maptiler.com/tiles/buildings/{z}/{x}/{y}.pbf?key=${apiKey_MapTiler}`, {
    rendererFactory: L.canvas.tile,
    vectorTileLayerStyles: {
        'building': buildingStyle,
        'building_part': buildingStyle
    },
    interactive: false,
    zIndex: 460,
    maxNativeZoom: 16
});


// urban: Mundialis WMS with Tactical Filter - Increased Opacity
overlayLayers['urban'] = L.tileLayer.wms('http://ows.mundialis.de/services/service?', { layers: 'OSM-Overlay-WMS', format: 'image/png', transparent: true, opacity: 0.7, className: 'tactical-overlay' });

// NEW LAYERS
overlayLayers['hillshade'] = L.tileLayer(`https://api.maptiler.com/tiles/hillshade/{z}/{x}/{y}.png?key=${apiKey_MapTiler}`, { opacity: 0.6, zIndex: 300 });

let activeOverlays = { 'contours': false, 'urban': false, 'roads': true, 'labels': true, 'buildings': false, 'hillshade': false };
// Initialize Overlay Layers
let airportLayer = L.layerGroup().addTo(map);
let unitLayer = L.layerGroup().addTo(map);
let routeLayer = L.layerGroup().addTo(map);
let activeLegLayer = L.layerGroup().addTo(map);
let measureLayer = L.layerGroup().addTo(map);
let poiLayer = L.layerGroup().addTo(map);
let editorLayer = L.layerGroup().addTo(map);
let threatLayer = L.layerGroup().addTo(map);
let terminatorLayer = L.terminator();

let airportMarkers = {};
let currentNvgMode = 'off';
let wakeLock = null;

// --- LAYER & GRID FUNCTIONS ---
function setMapLayer(name, skipSave) {
    if (!name || !layers[name]) return;
    if (currentMapLayerName && map.hasLayer(layers[currentMapLayerName])) {
        map.removeLayer(layers[currentMapLayerName]);
    }
    layers[name].addTo(map);
    currentMapLayerName = name;

    // Update active label
    const lbl = document.getElementById('lbl-active-map-name');
    if (lbl) lbl.innerText = name.toUpperCase();

    // Apply filters for this layer
    if (!skipSave) saveMapSettings();
    if (typeof applyVisualFilters === 'function') applyVisualFilters();
}

function toggleLayer(layer, forceState) {
    if (!layer) return;
    if (forceState !== undefined && forceState !== null) {
        if (forceState) { if (!map.hasLayer(layer)) map.addLayer(layer); }
        else { if (map.hasLayer(layer)) map.removeLayer(layer); }
    } else {
        if (map.hasLayer(layer)) map.removeLayer(layer);
        else map.addLayer(layer);
    }

    // Grid Special Handling
    if (layer === gridLayer && map.hasLayer(gridLayer)) updateGrid();
    if (layer === mgrsGridLayer && map.hasLayer(mgrsGridLayer)) updateMgrsGrid();
}

function updateGrid() {
    gridLayer.clearLayers();
    if (!map.hasLayer(gridLayer)) return;
    const bounds = map.getBounds();
    const zoom = map.getZoom();
    const color = document.getElementById('col-latlon').value || "#00ffcc";

    let interval = 10;
    if (zoom >= 10) interval = 0.1;
    else if (zoom >= 7) interval = 1;
    else if (zoom >= 5) interval = 5;

    // Simple Lat/Lon Grid lines
    for (let lat = Math.floor(bounds.getSouth() / interval) * interval; lat <= bounds.getNorth(); lat += interval) {
        L.polyline([[lat, -180], [lat, 180]], { color: color, weight: 1, opacity: 0.5 }).addTo(gridLayer);
    }
    for (let lng = Math.floor(bounds.getWest() / interval) * interval; lng <= bounds.getEast(); lng += interval) {
        L.polyline([[-85, lng], [85, lng]], { color: color, weight: 1, opacity: 0.5 }).addTo(gridLayer);
    }
}

function updateMgrsGrid() {
    mgrsGridLayer.clearLayers();
    if (!map.hasLayer(mgrsGridLayer)) return;

    const zoom = map.getZoom();
    if (zoom < 6) return; // Too broad for MGRS

    // Use existing draw helpers if available, or simple redraw
    if (typeof drawGZDLines === 'function') drawGZDLines('mgrs-line-base mgrs-line-gzd-high');
    if (typeof drawAllVisibleGZDs === 'function') drawAllVisibleGZDs();
    if (typeof drawGZDAxisLabels === 'function') drawGZDAxisLabels();

    if (typeof drawGridForSquare === 'function') {
        const bounds = map.getBounds();
        const visible = getVisibleMgrsSquares(bounds);
        visible.forEach(tag => {
            const p = tag.split(' ');
            if (zoom >= 14) drawGridForSquare(p[0], p[1], 1000, 'mgrs-line-base mgrs-line-low', 'mgrs-line-base mgrs-line-high', 2, 10000);
            else if (zoom >= 10) drawGridForSquare(p[0], p[1], 10000, 'mgrs-line-base mgrs-line-low', 'mgrs-line-base mgrs-line-high', 1, 100000);
            else drawGridForSquare(p[0], p[1], 100000, 'mgrs-line-base mgrs-line-low', 'mgrs-line-base mgrs-line-high', 0, 100000);
        });
    }
}

// --- FILTER SETTINGS ---
let filterSettings = {
    map: JSON.parse(localStorage.getItem('map_filters')) || {
        'dark': { br: 1.2, con: 1.2, op: 1.0 },
        'light': { br: 0.6, con: 1.8, op: 1.0 },
        'start_dark': { br: 1.2, con: 1.2, op: 1.0 }, // Added missing defaults based on common patterns if needed, but 'dark' covers current default.
        'winter': { br: 1.0, con: 1.0, op: 1.0 },
        'darkstreet': { br: 0.8, con: 1.2, op: 1.0 },
        'sat': { br: 0.9, con: 1.0, op: 1.0 },
        'vfr': { br: 0.6, con: 1.7, op: 1.0 },
        'vfr_night': { br: 1.8, con: 1.0, op: 1.0 },
        'relief': { br: 0.7, con: 1.2, op: 1.0 },
        'opentopo': { br: 1.0, con: 1.0, op: 1.0 },
        'cyclosm': { br: 1.0, con: 1.0, op: 1.0 }
    },
    nvg: JSON.parse(localStorage.getItem('nvg_filters')) || { br: 0.7, con: 0.9, op: 1.0, sep: 1.0 }
};

// --- UI FUNCTIONS ---

function toggleSidebar(side) {
    const el = document.getElementById(`sidebar-${side}`);
    const isHidden = el.classList.toggle(`hidden-${side}`);
    document.getElementById(`chk-${side}`).className = isHidden ? 'fa-regular fa-square' : 'fa-solid fa-square-check';
}

function toggleLabels() {
    showWpLabels = !showWpLabels;
    document.getElementById('btn-labels').classList.toggle('active', showWpLabels);
    if (typeof renderMapRoutes === 'function') renderMapRoutes();
    if (typeof renderPois === 'function') renderPois();
    if (typeof renderAirports === 'function') renderAirports();

    // FORCE Theater Unit Update
    // We iterate through existing units and re-bind tooltips with new permanent setting
    for (let id in theaterUnits) {
        if (theaterUnits[id] && theaterUnits[id].marker) {
            const m = theaterUnits[id].marker;
            const content = m.getTooltip().getContent(); // Get existing content
            m.unbindTooltip();
            m.bindTooltip(content, {
                permanent: showWpLabels,
                direction: 'top',
                offset: [0, -5], // Simplify offset for generic update, or check isDot if critical
                className: 'active-leg-label'
            });
        }
    }
}

function toggleDrawer(name) {
    document.querySelectorAll('.drawer-panel').forEach(d => {
        if (d.id !== `${name}-drawer`) d.classList.remove('open');
    });

    if (name !== 'route' && document.getElementById('view-editor').style.display === 'flex') {
        if (typeof showBrowser === 'function') showBrowser();
    }

    const el = document.getElementById(`${name}-drawer`);
    if (el) el.classList.toggle('open');

    if (name === 'route') {
        if (activeMissionName && missions[activeMissionName]) {
            if (document.getElementById('view-editor').style.display === 'none') {
                document.getElementById('view-missions').style.display = 'none';
                document.getElementById('view-browser').style.display = 'flex';
                if (typeof renderBrowserList === 'function') renderBrowserList();
            }
        } else {
            if (typeof showMissionList === 'function') showMissionList();
        }
    }
    if (name === 'poi' && typeof renderPoiList === 'function') renderPoiList();
}

function toggleLayer(layer, btn) {
    if (map.hasLayer(layer)) {
        map.removeLayer(layer);
        // Local Persistence for Grids
        if (typeof gridLayer !== 'undefined' && layer === gridLayer) localStorage.setItem('vis_grid', 'false');
        if (typeof mgrsGridLayer !== 'undefined' && layer === mgrsGridLayer) localStorage.setItem('vis_mgrs', 'false');
    } else {
        map.addLayer(layer);
        // Local Persistence for Grids
        if (typeof gridLayer !== 'undefined' && layer === gridLayer) { updateGrid(); localStorage.setItem('vis_grid', 'true'); }
        if (typeof mgrsGridLayer !== 'undefined' && layer === mgrsGridLayer) { updateMgrsGrid(); localStorage.setItem('vis_mgrs', 'true'); }
    }
    if (btn) btn.classList.toggle('active');
}

function toggleInfo(type) {
    document.getElementById(`pill-${type}`).classList.toggle('visible');
}

function toggleMapMenu() {
    const menu = document.getElementById('map-menu');
    const btn = document.getElementById('btn-map-layers');
    if (menu.classList.contains('show')) {
        menu.classList.remove('show');
    } else {
        const rect = btn.getBoundingClientRect();
        // Updated to center vertically and maximize space (User Request)
        menu.style.top = '50%';
        menu.style.transform = 'translateY(-50%)';
        menu.style.maxHeight = 'calc(100vh - 40px)';

        const rightOffset = (window.innerWidth - rect.left) + 10;
        menu.style.right = rightOffset + 'px';
        menu.classList.add('show');
    }
}

function setMapLayer(name, skipSave = false) {
    for (let key in layers) {
        if (map.hasLayer(layers[key])) map.removeLayer(layers[key]);
    }
    // Consolidated from monkey-patch
    // FIX: Apply filters BEFORE saving, so we save the *current* state of the new layer, 
    // instead of saving the *previous* layer's state relative to the new layer name.
    // Consolidated from monkey-patch
    // FIX: Apply filters BEFORE saving - functionality moved to sync block below
    // applyVisualFilters();

    if (layers[name]) {
        layers[name].addTo(map);
        currentMapLayerName = name;

        // FIX: Sync Sliders with new Layer Settings
        if (typeof filterSettings !== 'undefined' && filterSettings.map) {
            // Ensure defaults exist
            if (!filterSettings.map[name]) filterSettings.map[name] = { br: 1.0, con: 1.0, op: 1.0 };

            // Apply Filters via Centralized Function
            applyVisualFilters();
        }

        if (!skipSave && typeof saveMapSettings === 'function') saveMapSettings();
    }
    document.getElementById('map-menu').classList.remove('show');
    document.querySelectorAll('.menu-item').forEach(el => {
        if (el.dataset.layer === name) {
            el.classList.add('active');
        } else if (el.dataset.layer) {
            // Only remove active if it's a map layer button (has data-layer)
            // This prevents interfering with overlays if they share this class
            el.classList.remove('active');
        }
    });
}

function toggleOverlay(name, forceState = null, skipSave = false) {
    const layer = overlayLayers[name];
    if (!layer) {
        // console.warn(`Overlay layer '${name}' not found.`); 
        // Silent return to avoid log spam on stale Data
        return;
    }
    const chk = document.getElementById(`chk-ov-${name}`);
    const btn = document.getElementById(`btn-ov-${name}`);

    let newState = !activeOverlays[name];
    if (forceState !== null) newState = forceState;

    if (newState) {
        if (!map.hasLayer(layer)) map.addLayer(layer);
        activeOverlays[name] = true;
        if (chk) chk.checked = true;
        if (btn) btn.classList.add('active');
    } else {
        if (map.hasLayer(layer)) map.removeLayer(layer);
        activeOverlays[name] = false;
        if (chk) chk.checked = false;
        if (btn) btn.classList.remove('active');
    }

    if (forceState === null && !skipSave && typeof saveMapSettings === 'function') saveMapSettings();
}

function showToast(msg) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
}

// --- VISUAL FILTER LOGIC ---
function tuneFilter(category, property, value) {
    // RUNTIME CLAMPING (Defense in Depth)
    let v = parseFloat(value);
    if (isNaN(v)) v = 1.0;

    if (category === 'map') {
        // Map: Br/Con max 2.0, Op max 1.0
        const max = (property === 'op') ? 1.0 : 2.0;
        if (v > max && v > 5.0) v = v / 100; // Legacy fix
        if (v > max) v = max;
        if (v < 0) v = 0; // Min

        const currentLayer = currentMapLayerName;
        if (!filterSettings.map[currentLayer]) {
            filterSettings.map[currentLayer] = { br: 1.0, con: 1.0, op: 1.0 };
        }
        filterSettings.map[currentLayer][property] = v;
        localStorage.setItem('map_filters', JSON.stringify(filterSettings.map));
    } else {
        // NVG: 0.0 to 2.0 depending on prop
        let max = 2.0;
        if (property === 'op' || property === 'sep') max = 1.0;
        if (v > max) v = max;
        filterSettings.nvg[property] = v;
        localStorage.setItem('nvg_filters', JSON.stringify(filterSettings.nvg));
    }
    applyVisualFilters();
}

function applyVisualFilters() {
    const curMap = filterSettings.map[currentMapLayerName] || { br: 1.0, con: 1.0, op: 1.0 };
    const curNvg = filterSettings.nvg;

    document.documentElement.style.setProperty('--map-br', curMap.br);
    document.documentElement.style.setProperty('--map-con', curMap.con);
    document.documentElement.style.setProperty('--map-op', curMap.op);

    const tintFactor = curNvg.sep !== undefined ? curNvg.sep : 1.0;
    const sepiaPercent = tintFactor * 100;
    const hueVal = (currentNvgMode === 'green') ? (100 * tintFactor) : (-50 * tintFactor);
    const baseSat = (currentNvgMode === 'green' ? 400 : 600);
    const saturatePercent = 100 + (curNvg.op * (baseSat - 100) * tintFactor);

    document.documentElement.style.setProperty('--nvg-sepia', `${sepiaPercent}%`);
    document.documentElement.style.setProperty('--nvg-hue', `${hueVal}deg`);
    document.documentElement.style.setProperty('--nvg-saturate', `${saturatePercent}%`);
    document.documentElement.style.setProperty('--nvg-br', curNvg.br);
    document.documentElement.style.setProperty('--nvg-con', curNvg.con);

    updateSliderUI('map', curMap);
    updateSliderUI('nvg', curNvg);
}

function updateSliderUI(cat, data) {
    const props = ['br', 'con', 'op', 'sep'];
    props.forEach(prop => {
        const sld = document.getElementById(`sld-${cat}-${prop}`);
        const valLabel = document.getElementById(`val-${cat}-${prop}`);
        if (data[prop] !== undefined) {
            let val = parseFloat(data[prop]);

            // Final safety clamp for UI
            if (cat === 'map') {
                const max = (prop === 'op') ? 1.0 : 2.0;
                if (val > max) val = max;
            }

            if (sld) sld.value = val;
            if (valLabel) valLabel.innerText = val.toFixed(2); // Cleaner display
        }
    });
}

function cycleNvgMode() {
    if (currentNvgMode === 'off') setNightVision('red');
    else if (currentNvgMode === 'red') setNightVision('green');
    else setNightVision('off');
}

function setNightVision(mode) {
    currentNvgMode = mode;
    const body = document.body;
    const btn = document.getElementById('btn-ov-nvg');
    const icon = document.getElementById('icon-nvg-state');

    body.classList.remove('nvg-red', 'nvg-green');
    if (btn) btn.classList.remove('active');
    if (icon) {
        icon.className = 'fa-regular fa-square';
        icon.style.color = '';
        icon.style.textShadow = 'none';
    }

    if (mode === 'red') {
        body.classList.add('nvg-red');
        if (btn) btn.classList.add('active');
        if (icon) {
            icon.className = 'fa-solid fa-square-check';
            icon.style.color = '#e74c3c';
            icon.style.textShadow = '0 0 5px #e74c3c';
        }
    } else if (mode === 'green') {
        body.classList.add('nvg-green');
        if (btn) btn.classList.add('active');
        if (icon) {
            icon.className = 'fa-solid fa-square-check';
            icon.style.color = '#2ecc71';
            icon.style.textShadow = '0 0 5px #2ecc71';
        }
    }

    applyVisualFilters();
    localStorage.setItem('dcs_nvg_mode', mode);
    if (typeof saveMapSettings === 'function') saveMapSettings();
}

// --- FULLSCREEN & WAKELOCK ---
function toggleFullScreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error('Error enabling full-screen mode:', err.message);
        });
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
    }
}

function updateFullScreenIcon() {
    const btn = document.getElementById('btn-fullscreen');
    if (!btn) return;
    const icon = btn.querySelector('i');
    if (document.fullscreenElement) {
        icon.classList.remove('fa-expand');
        icon.classList.add('fa-compress');
        btn.classList.add('active');
    } else {
        icon.classList.remove('fa-compress');
        icon.classList.add('fa-expand');
        btn.classList.remove('active');
    }
}
document.addEventListener('fullscreenchange', updateFullScreenIcon);

async function toggleWakeLock() {
    const isChecked = document.getElementById('chk-opt-wakelock').checked;
    if (isChecked) await requestWakeLock(); else await releaseWakeLock();
}

async function requestWakeLock() {
    if ('wakeLock' in navigator) {
        try {
            wakeLock = await navigator.wakeLock.request('screen');
            wakeLock.addEventListener('release', () => console.debug('Wake Lock released'));
        } catch (err) {
            console.error(err.name, err.message);
            const chk = document.getElementById('chk-opt-wakelock');
            if (chk) chk.checked = false;
        }
    } else {
        console.warn('Wake Lock API not supported');
    }
}
async function releaseWakeLock() { if (wakeLock !== null) { await wakeLock.release(); wakeLock = null; } }
document.addEventListener('visibilitychange', async () => {
    if (wakeLock !== null && document.visibilityState === 'visible') {
        const chk = document.getElementById('chk-opt-wakelock');
        if (chk && chk.checked) await requestWakeLock();
    }
});

function cycleHudMode(forceMode = null) {
    if (forceMode !== null) hudMode = forceMode; else hudMode = (hudMode + 1) % 3;
    const overlay = document.getElementById('hud-overlay'); const btn = document.getElementById('btn-opt-hud');
    overlay.classList.remove('visible'); if (extHudWindow && !extHudWindow.closed) extHudWindow.close();
    if (hudMode === 0) { overlay.src = "about:blank"; if (btn) { btn.innerText = "OFF"; btn.style.color = "#aaa"; btn.style.borderColor = "#555"; } }
    else if (hudMode === 1) { overlay.src = "/hud?bg=transparent"; overlay.classList.add('visible'); if (btn) { btn.innerText = "OVERLAY"; btn.style.color = "#f1c40f"; btn.style.borderColor = "#f1c40f"; } }
    else if (hudMode === 2) { overlay.src = "about:blank"; extHudWindow = window.open('/hud', 'HUD', 'width=800,height=600,menubar=no,toolbar=no'); if (btn) { btn.innerText = "WINDOW"; btn.style.color = "#e74c3c"; btn.style.borderColor = "#e74c3c"; } }
}

// --- FORMAT HELPERS ---
function toDisplayAlt(meters) { if (settings.altUnit === 'ft') return Math.round(meters * 3.28084); return Math.round(meters); }
function fromDisplayAlt(userVal) { if (settings.altUnit === 'ft') return userVal / 3.28084; return userVal; }

function toDmsInput(deg, isLat) {
    const absDeg = Math.abs(deg); const d = Math.floor(absDeg); const m = Math.floor((absDeg - d) * 60); const s = ((absDeg - d - m / 60) * 3600).toFixed(2);
    let dir = ""; if (isLat) dir = deg >= 0 ? "N" : "S"; else dir = deg >= 0 ? "E" : "W";
    return `${dir} ${String(d).padStart(isLat ? 2 : 3, '0')} ${String(m).padStart(2, '0')} ${String(s).padStart(5, '0')}`;
}
function parseDMS(dmsString) {
    if (!dmsString) return 0; const s = dmsString.trim().toUpperCase();
    let isNeg = false; if (s.includes('S') || s.includes('W')) isNeg = true;
    const matches = s.match(/[\d.]+/g); if (!matches || matches.length < 3) return 0;
    const deg = parseFloat(matches[0]); const min = parseFloat(matches[1]); const sec = parseFloat(matches[2]);
    let val = deg + (min / 60.0) + (sec / 3600.0); if (isNeg) val = -val; return val;
}
function maskDMS(input, type) {
    let v = input.value.toUpperCase().replace(/[^NESW\d.]/g, '');
    if (v.length > 0 && !['N', 'S', 'E', 'W'].includes(v[0])) { v = (type === 'lat' ? 'N' : 'E') + v; }
    let dir = v.charAt(0); if (type === 'lat' && !['N', 'S'].includes(dir)) v = 'N' + v.substring(1);
    if (type === 'lon' && !['E', 'W'].includes(dir)) v = 'E' + v.substring(1);
    let raw = v.substring(1).replace(/[^\d]/g, '');
    if (type === 'lon' && raw.length >= 1 && !['0', '1'].includes(raw[0])) raw = '0' + raw.substring(1);
    let degLen = (type === 'lat') ? 2 : 3; let out = dir + " ";
    if (raw.length > 0) out += raw.substring(0, degLen);
    if (raw.length >= degLen) out += " " + raw.substring(degLen, degLen + 2);
    if (raw.length > degLen) { let m1 = raw.charAt(degLen); if (parseInt(m1) > 5) raw = raw.substring(0, degLen) + '5' + raw.substring(degLen + 1); }
    if (raw.length >= degLen + 2) out += " " + raw.substring(degLen + 2, degLen + 4);
    if (raw.length > degLen + 2) { let s1 = raw.charAt(degLen + 2); if (parseInt(s1) > 5) raw = raw.substring(0, degLen + 2) + '5' + raw.substring(degLen + 3); }
    if (raw.length >= degLen + 4) { out += "." + raw.substring(degLen + 4, degLen + 6); }
    input.value = out;
}
function maskMGRS(input) {
    let v = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    let out = ""; if (v.length > 0) out += v.substring(0, 3);
    if (v.length > 3) out += " " + v.substring(3, 5);
    if (v.length > 5) out += " " + v.substring(5, 10);
    if (v.length > 10) out += " " + v.substring(10, 15);
    input.value = out;
}
function formatCoordDisplay(lat, lon) {
    if (settings.coords === 'mgrs') {
        try { return MGRSString(lat, lon); } catch (e) { return "MGRS Err"; }
    }
    const toDms = (deg, isLat) => { const d = Math.floor(deg); const m = Math.floor((deg - d) * 60); const s = ((deg - d - m / 60) * 3600).toFixed(2); return `${isLat ? 'N' : 'E'} ${String(d).padStart(isLat ? 2 : 3, '0')}° ${String(m).padStart(2, '0')}' ${s}"`; };
    return `${toDms(lat, true)}\n${toDms(lon, false)}`;
}

// --- GRID SYSTEMS ---

// 8.1 GRID SETUP latlng
const gridLayer = L.layerGroup();

function updateGrid() {
    if (!map.hasLayer(gridLayer)) return;
    gridLayer.clearLayers();

    const bounds = map.getBounds();
    const zoom = map.getZoom();

    // 1. Determine Grid Interval
    let interval = 20;
    if (zoom >= 4) interval = 10;
    if (zoom >= 6) interval = 5;
    if (zoom >= 8) interval = 1;
    if (zoom >= 10) interval = 0.5;
    if (zoom >= 12) interval = 0.1;
    if (zoom >= 14) interval = 0.05;

    // 2. CSS Classes used instead of inline styles
    // .grid-line defined in map.html using var(--latlon-color)
    // .grid-text defined in map.html using var(--latlon-color)

    const lineOptions = { className: 'grid-line', interactive: false };

    // 3. Draw Longitude (Vertical) Lines
    const west = Math.floor(bounds.getWest() / interval) * interval;
    const east = Math.ceil(bounds.getEast() / interval) * interval;

    for (let lng = west; lng <= east; lng += interval) {
        const curLng = parseFloat(lng.toFixed(4));
        L.polyline([[bounds.getSouth(), curLng], [bounds.getNorth(), curLng]], lineOptions).addTo(gridLayer);

        const labelPos = L.latLng(bounds.getNorth() - (bounds.getNorth() - bounds.getSouth()) * 0.05, curLng);
        const icon = L.divIcon({
            className: 'grid-label-lng',
            html: `<div class="grid-text">${curLng.toFixed(2)}°</div>`,
            iconSize: [40, 20],
            iconAnchor: [20, 0]
        });
        L.marker(labelPos, { icon: icon, interactive: false }).addTo(gridLayer);
    }

    // 4. Draw Latitude (Horizontal) Lines
    const south = Math.floor(bounds.getSouth() / interval) * interval;
    const north = Math.ceil(bounds.getNorth() / interval) * interval;

    for (let lat = south; lat <= north; lat += interval) {
        const curLat = parseFloat(lat.toFixed(4));
        L.polyline([[curLat, bounds.getWest()], [curLat, bounds.getEast()]], lineOptions).addTo(gridLayer);

        const labelPos = L.latLng(curLat, bounds.getWest() + (bounds.getEast() - bounds.getWest()) * 0.05);
        const icon = L.divIcon({
            className: 'grid-label-lat',
            html: `<div class="grid-text">${curLat.toFixed(2)}°</div>`,
            iconSize: [40, 20],
            iconAnchor: [0, 10]
        });
        L.marker(labelPos, { icon: icon, interactive: false }).addTo(gridLayer);
    }
}

// 8.2 MGRS GRID SYSTEM
const mgrsGridLayer = L.layerGroup();

function updateMgrsGrid() {
    if (!map.hasLayer(mgrsGridLayer)) return;
    mgrsGridLayer.clearLayers();

    const zoom = map.getZoom();
    const bounds = map.getBounds();

    // --- TIER 0: Zoom < 2 (Hidden) ---
    if (zoom < 2) return;

    // --- TIER 1: Zoom 2 to < 7 (Axis Labels) ---
    else if (zoom < 7) {
        drawGZDLines('mgrs-line-base mgrs-line-gzd-low');
        drawGZDAxisLabels();
    }

    // --- TIER 2: Zoom 7 to < 10 (100km Squares) ---
    else if (zoom < 10) {
        drawGZDLines('mgrs-line-base mgrs-line-gzd-high');
        drawGZDAxisLabels(); // Keep axis labels for global context

        // Draw 100km Square Boundaries
        const visible = getVisibleMgrsSquares(bounds);
        visible.forEach(tag => {
            const p = tag.split(' ');
            // Interval 100000 = Only draw borders (0 and 100000)
            drawGridForSquare(p[0], p[1], 100000, 'mgrs-line-base mgrs-line-low', null, 0);
        });

        drawCenterSQLabels();
        drawAllVisibleGZDs();
    }

    // --- TIER 3: Zoom 10 to < 14 (10km Grid) ---
    else if (zoom < 14) {
        const visible = getVisibleMgrsSquares(bounds);
        visible.forEach(tag => {
            const p = tag.split(' ');
            // Interval 10000, Major 100000 (100km lines thick)
            drawGridForSquare(p[0], p[1], 10000, 'mgrs-line-base mgrs-line-low', 'mgrs-line-base mgrs-line-high', 1, 100000);
        });
        drawEdgeHeaders(false); // GZD false (redundant with floating label)
        drawAllVisibleGZDs(); // Persistent GZD Labels
        drawGZDLines('mgrs-line-base mgrs-line-gzd-high'); // GZD Boundaries
    }

    // --- TIER 4: Zoom 14+ (1km Grid) ---
    else {
        const visible = getVisibleMgrsSquares(bounds);
        visible.forEach(tag => {
            const p = tag.split(' ');
            // Interval 1000, Major 10000 (10km lines thick)
            drawGridForSquare(p[0], p[1], 1000, 'mgrs-line-base mgrs-line-low', 'mgrs-line-base mgrs-line-high', 2, 10000);
        });
        drawEdgeHeaders(false); // GZD false (redundant with floating label)
        drawAllVisibleGZDs(); // Persistent GZD Labels
        drawGZDLines('mgrs-line-base mgrs-line-gzd-high'); // GZD Boundaries
    }
}

function drawGZDAxisLabels() {
    const bounds = map.getBounds();
    for (let lng = -180; lng <= 180; lng += 6) {
        if (lng >= bounds.getWest() && lng <= bounds.getEast()) {
            const zone = Math.floor((lng + 180) / 6) + 1;
            L.marker([bounds.getNorth(), lng], {
                icon: L.divIcon({ className: 'mgrs-label-gzd-axis', html: zone.toString(), iconSize: [30, 20], iconAnchor: [15, 0] }),
                interactive: false
            }).addTo(mgrsGridLayer);
        }
    }
    const lats = [-80, -72, -64, -56, -48, -40, -32, -24, -16, -8, 0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 84];
    lats.forEach(lat => {
        if (lat >= bounds.getSouth() && lat <= bounds.getNorth()) {
            const letters = "CDEFGHJKLMNPQRSTUVWXX";
            const idx = Math.floor(lat / 8) + 10;
            const band = letters.charAt(Math.min(letters.length - 1, Math.max(0, idx)));
            L.marker([lat, bounds.getWest()], {
                icon: L.divIcon({ className: 'mgrs-label-gzd-axis', html: band, iconSize: [30, 20], iconAnchor: [0, 10] }),
                interactive: false
            }).addTo(mgrsGridLayer);
        }
    });
}


function getVisibleMgrsSquares(bounds) {
    const squares = new Set();
    // Scan coarse grid to find which 100km squares are visible
    // We scan every ~0.2 degrees which is safe for 100km squares (approx 1 degree size)
    const step = 0.2;
    for (let lat = bounds.getSouth(); lat < bounds.getNorth() + step; lat += step) {
        for (let lng = bounds.getWest(); lng < bounds.getEast() + step; lng += step) {
            try {
                const str = MGRSString(lat, lng);
                const parts = str.split(' ');
                // parts = ["38T", "KM", "12345", "67890"]
                if (parts.length >= 2) {
                    squares.add(`${parts[0]} ${parts[1]}`);
                }
            } catch (e) { }
        }
    }
    return Array.from(squares);
}





function drawGridForSquare(gzd, sq, interval, styleMinor, styleMajor, precision, majorInterval = 100000) {
    const bounds = map.getBounds(); // Viewport bounds for dynamic labels

    // Reconstruct a base point for this square to get projection params
    const centerStr = `${gzd} ${sq} 50000 50000`;
    const centerPt = LatLongFromMGRSstring(centerStr);
    if (!centerPt[0]) return;

    const zoneNum = parseInt(gzd);
    const minLng = (zoneNum - 1) * 6 - 180;
    const maxLng = zoneNum * 6 - 180;



    // Helper to clip a line segment to the zone's longitude bounds (Linear Interpolation)
    const clipLineToZone = (p1, p2) => {
        let lat1 = p1[0], lng1 = p1[1];
        let lat2 = p2[0], lng2 = p2[1];

        // 1. Trivial Reject
        if (lng1 < minLng && lng2 < minLng) return null;
        if (lng1 >= maxLng && lng2 >= maxLng) return null;

        // 2. Clip Start
        if (lng1 < minLng) {
            const r = (minLng - lng1) / (lng2 - lng1);
            lat1 = lat1 + (lat2 - lat1) * r;
            lng1 = minLng;
        } else if (lng1 > maxLng) {
            const r = (maxLng - lng1) / (lng2 - lng1);
            lat1 = lat1 + (lat2 - lat1) * r;
            lng1 = maxLng;
        }

        // 3. Clip End
        if (lng2 < minLng) {
            const r = (minLng - lng1) / (lng2 - lng1);
            lat2 = lat1 + (lat2 - lat1) * r;
            lng2 = minLng;
        } else if (lng2 > maxLng) {
            const r = (maxLng - lng1) / (lng2 - lng1);
            lat2 = lat1 + (lat2 - lat1) * r;
            lng2 = maxLng;
        }

        if (isNaN(lat1) || isNaN(lng1) || isNaN(lat2) || isNaN(lng2)) return null;
        if (Math.abs(lng1 - lng2) < 0.0000001 && Math.abs(lat1 - lat2) < 0.0000001) return null;

        return [[lat1, lng1], [lat2, lng2]];
    };

    // Loop 0 to 100,000 meters
    for (let m = 0; m <= 100000; m += interval) {
        // Use majorInterval to determine if line is "major" (Thick)
        const isMajor = (m % majorInterval === 0);
        let style = styleMinor;
        if (isMajor && styleMajor) style = styleMajor;

        const disp = String(m % 100000).padStart(5, '0');

        // --- VERTICAL LINES (constant Easting, vary North) ---
        const bStr = `${gzd} ${sq} ${String(m).padStart(5, '0')} 00000`;
        const tStr = `${gzd} ${sq} ${String(m).padStart(5, '0')} 99999`;

        const pBot = LatLongFromMGRSstring(bStr);
        const pTop = LatLongFromMGRSstring(tStr);

        if (pBot[0] && pTop[0]) {
            const clipped = clipLineToZone([pBot[1], pBot[2]], [pTop[1], pTop[2]]);
            if (clipped) {
                L.polyline(clipped, { className: style, interactive: false }).addTo(mgrsGridLayer);

                // Label Logic: Ruler Style (Top of Viewport)
                // Use interpolation to place label accurately on slanted lines
                if (precision > 0) {
                    const boundTop = bounds.getNorth();
                    const boundBot = bounds.getSouth();
                    const lineTop = clipped[1][0];
                    const lineBot = clipped[0][0];

                    // If line overlaps View Latitudes
                    if (lineTop > boundBot && lineBot < boundTop) {
                        // Clamped Lat = Min(LineTop, MapTop)
                        const targetLat = Math.min(Math.max(lineBot, boundBot), Math.min(lineTop, boundTop));
                        // Interpolate exact point on line at this Latitude
                        // SIMPLE PLACEMENT: Use the longitude of the TOP point.
                        const lat = Math.min(lineTop, boundTop);

                        L.marker([lat, clipped[1][1]], {
                            icon: L.divIcon({ className: 'mgrs-label-digit', html: disp.substring(0, precision), iconSize: [20, 15], iconAnchor: [10, 0] }),
                            interactive: false
                        }).addTo(mgrsGridLayer);
                    }
                }
            }
        }

        // --- HORIZONTAL LINES (constant Northing, vary East) ---
        const lStr = `${gzd} ${sq} 00000 ${String(m).padStart(5, '0')}`;
        const rStr = `${gzd} ${sq} 99999 ${String(m).padStart(5, '0')}`;

        const pLeft = LatLongFromMGRSstring(lStr);
        const pRight = LatLongFromMGRSstring(rStr);

        if (pLeft[0] && pRight[0]) {
            const clipped = clipLineToZone([pLeft[1], pLeft[2]], [pRight[1], pRight[2]]);
            if (clipped) {
                L.polyline(clipped, { className: style, interactive: false }).addTo(mgrsGridLayer);

                // Label Logic: Ruler Style (Left of Viewport)
                // Label Logic: Ruler Style (Left of Viewport)
                const pLeftIn = isPointInZone(pLeft[2], zoneNum);
                if (precision > 0 && pLeftIn) {
                    const mapLeft = bounds.getWest();
                    const mapRight = bounds.getEast();
                    const lineLeft = clipped[0][1];
                    const lineRight = clipped[1][1];

                    if (lineRight > mapLeft && lineLeft < mapRight) {
                        // Clamped Lng = Max(LineLeft, MapLeft)
                        const lng = Math.max(lineLeft, mapLeft);
                        // SIMPLE PLACEMENT: Use the latitude of the LEFT point.
                        L.marker([clipped[0][0], lng], {
                            icon: L.divIcon({ className: 'mgrs-label-digit', html: disp.substring(0, precision), iconSize: [20, 15], iconAnchor: [0, 8] }),
                            interactive: false
                        }).addTo(mgrsGridLayer);
                    }
                }
            }
        }
    }
}



function drawAllVisibleGZDs() {
    const bounds = map.getBounds();
    const latBands = [-80, -72, -64, -56, -48, -40, -32, -24, -16, -8, 0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 84];
    const startLng = Math.floor(bounds.getWest() / 6) * 6;
    const endLng = Math.ceil(bounds.getEast() / 6) * 6;

    for (let lng = startLng; lng < endLng; lng += 6) {
        for (let i = 0; i < latBands.length - 1; i++) {
            const latMin = latBands[i]; const latMax = latBands[i + 1];
            const interWest = Math.max(bounds.getWest(), lng);
            const interEast = Math.min(bounds.getEast(), lng + 6);
            const interSouth = Math.max(bounds.getSouth(), latMin);
            const interNorth = Math.min(bounds.getNorth(), latMax);

            if (interWest < interEast && interSouth < interNorth) {
                try {
                    // Use center of the actual GZD band to identify it
                    const sampleLat = (latMin + latMax) / 2;
                    const sampleLng = (lng + 6 + lng) / 2;
                    const str = MGRSString(sampleLat, sampleLng);
                    const gzd = str.split(' ')[0];

                    // Place label at the Top-Left corner of the visible intersection
                    // Use iconAnchor with negative values to push the label Down/Right into view (Padding)
                    // zIndexOffset 1000 ensures it sits on top of lines
                    L.marker([interNorth, interWest], {
                        icon: L.divIcon({ className: 'mgrs-label-gzd-corner', html: gzd, iconSize: [100, 40], iconAnchor: [-10, -10] }),
                        interactive: false,
                        zIndexOffset: 1000
                    }).addTo(mgrsGridLayer);
                } catch (e) { }
            }
        }
    }
}

function drawGZDLines(className) {
    for (let lng = -180; lng <= 180; lng += 6) {
        L.polyline([[-85, lng], [85, lng]], { className: className, interactive: false }).addTo(mgrsGridLayer);
    }
    [-80, -72, -64, -56, -48, -40, -32, -24, -16, -8, 0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 84].forEach(lat => {
        L.polyline([[lat, -180], [lat, 180]], { className: className, interactive: false }).addTo(mgrsGridLayer);
    });
}

function isPointInZone(lng, zone) {
    // Zone 1 = -180 to -174
    // lat/lon is standard -180 to 180
    const z = parseInt(zone);
    if (isNaN(z)) return true; // Fallback
    const minLng = (z - 1) * 6 - 180;
    const maxLng = z * 6 - 180;
    return (lng >= minLng && lng < maxLng);
}

function drawCenterSQLabels() {
    const bounds = map.getBounds();
    const step = 0.3;
    const drawn = new Set();

    // Use a unique key for drawn set that includes GZD to allow same SQ code in diff zones
    // but prevent duplicate drawing of the EXACT same square
    for (let la = bounds.getSouth(); la < bounds.getNorth(); la += step) {
        for (let lo = bounds.getWest(); lo < bounds.getEast(); lo += step) {
            try {
                const str = MGRSString(la, lo);
                const parts = str.split(' '); // [GZD, SQ, E, N]
                if (parts.length < 2) continue;

                const gzd = parts[0];
                const sq = parts[1];
                const key = `${gzd}-${sq}`;

                if (!drawn.has(key)) {
                    const centerStr = `${gzd} ${sq} 50000 50000`;
                    const pt = LatLongFromMGRSstring(centerStr); // [ok, lat, lng]

                    if (pt[0]) {
                        // FIX: Check if center is actually within the GZD
                        const zoneNum = parseInt(gzd);
                        if (isPointInZone(pt[2], zoneNum)) {
                            L.marker([pt[1], pt[2]], {
                                icon: L.divIcon({ className: 'mgrs-label-center', html: sq, iconSize: [40, 20] }),
                                interactive: false
                            }).addTo(mgrsGridLayer);
                        }
                    }
                    drawn.add(key);
                }
            } catch (e) { }
        }
    }
}



function drawEdgeHeaders(includeGZD) {
    const bounds = map.getBounds();
    let cornerTxt = null;

    const scan = (isTop) => {
        const steps = 30;
        const range = isTop ? (bounds.getEast() - bounds.getWest()) : (bounds.getNorth() - bounds.getSouth());

        // Initialize lastTxt. 
        // For Left Scan (isTop=false), start with cornerTxt so we don't duplicate the corner label.
        let lastTxt = (!isTop && cornerTxt) ? cornerTxt : "";

        for (let i = 0; i <= steps; i++) {
            let lat = isTop ? bounds.getNorth() : (bounds.getNorth() - range * (i / steps));
            let lng = isTop ? (bounds.getWest() + range * (i / steps)) : bounds.getWest();
            try {
                const p = MGRSString(lat, lng).split(' ');
                if (p.length < 2) continue;
                const txt = includeGZD ? `${p[0]} ${p[1]}` : p[1];

                // Capture Corner Text from Top Scan (i=0)
                if (isTop && i === 0) cornerTxt = txt;

                if (txt !== lastTxt) {
                    // Alignment Fix:
                    // GZD Label is at [-10, -10].
                    // Top Headers (isTop): Shift X to -10 to align. Shift Y to -30 to be BELOW GZD.
                    // Left Headers (!isTop): Shift X to -10 to align. Shift Y to -5 (standard).
                    const anchor = isTop ? [-10, -30] : [-5, -5];

                    L.marker([lat, lng], {
                        icon: L.divIcon({ className: 'mgrs-label-edge-header', html: txt, iconSize: [50, 30], iconAnchor: anchor }),
                        interactive: false
                    }).addTo(mgrsGridLayer);
                    lastTxt = txt;
                }
            } catch (e) { }
        }
    };
    scan(true); // Top Scan First (sets cornerTxt)
    scan(false); // Left Scan Second (uses cornerTxt)
}



// --- SCRATCHPAD ---
const Scratchpad = {
    mode: 0,
    canvas: null, ctx: null,
    isDrawing: false, lastX: 0, lastY: 0,
    currentTool: 'pen', currentColor: '#e74c3c', lineWidth: 2, eraserSize: 20, fontSize: 16,
    menuExpanded: false, pressTimer: null, longPressTriggered: false, pendingTextPos: null,

    init: function () {
        this.canvas = document.getElementById('scratchpad-canvas');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        window.addEventListener('resize', () => this.resize());
        this.resize(); this.load();

        this.canvas.addEventListener('mousedown', (e) => { if (e.button === 0) this.handleStart(e.clientX, e.clientY); });
        this.canvas.addEventListener('mousemove', (e) => this.handleMove(e.clientX, e.clientY));
        this.canvas.addEventListener('mouseup', () => this.handleEnd());

        this.canvas.addEventListener('touchstart', (e) => { if (this.currentTool !== 'none') e.preventDefault(); const touch = e.touches[0]; this.handleStart(touch.clientX, touch.clientY); }, { passive: false });
        this.canvas.addEventListener('touchmove', (e) => { if (this.currentTool !== 'none') e.preventDefault(); const touch = e.touches[0]; this.handleMove(touch.clientX, touch.clientY); }, { passive: false });
        this.canvas.addEventListener('touchend', (e) => { if (this.currentTool !== 'none') e.preventDefault(); this.handleEnd(); });
    },

    toggleMode: function () { this.mode = (this.mode + 1) % 3; if (this.mode === 0) this.menuExpanded = false; this.updateUI(); },
    toggleToolMenu: function () { this.menuExpanded = !this.menuExpanded; this.updateUI(); },

    updateUI: function () {
        const layer = document.getElementById('scratchpad-layer');
        const subSidebar = document.getElementById('sp-sub-sidebar');
        const btn = document.getElementById('btn-scratchpad');
        const icon = btn.querySelector('i');
        const expandBtn = document.getElementById('btn-sp-expand');

        layer.classList.remove('mode-active', 'mode-passive', 'cursor-text');
        btn.classList.remove('sp-active-glow', 'sp-passive-eye');
        subSidebar.classList.remove('visible', 'expanded');
        this.closeAllPopouts();

        if (this.mode === 0) {
            layer.style.display = 'none';
            icon.className = 'fa-solid fa-pen-ruler';
            btn.title = "Toggle Scratchpad";
            document.getElementById('sp-text-input-box').style.display = 'none';
        } else {
            layer.style.display = 'block';
            subSidebar.classList.add('visible');
            if (this.menuExpanded) { subSidebar.classList.add('expanded'); expandBtn.innerHTML = '<i class="fa-solid fa-chevron-down"></i>'; }
            else { expandBtn.innerHTML = '<i class="fa-solid fa-chevron-up"></i>'; }

            if (this.mode === 1) { layer.classList.add('mode-active'); icon.className = 'fa-solid fa-pen-nib'; btn.classList.add('sp-active-glow'); }
            else { layer.classList.add('mode-passive'); icon.className = 'fa-solid fa-eye'; btn.classList.add('sp-passive-eye'); }
            if (this.currentTool === 'text' && this.mode === 2) { layer.classList.add('cursor-text'); }
        }
    },

    handleStart: function (clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        this.lastX = clientX - rect.left; this.lastY = clientY - rect.top;
        if (this.currentTool === 'pen' || this.currentTool === 'eraser') { this.isDrawing = true; this.drawStep(this.lastX, this.lastY); }
    },
    handleMove: function (clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const x = clientX - rect.left; const y = clientY - rect.top;
        if (this.isDrawing) { this.drawStep(x, y); } else { this.lastX = x; this.lastY = y; }
    },
    handleEnd: function () {
        if (this.currentTool === 'text' && this.mode !== 0) { this.openTextCloud(this.lastX, this.lastY); return; }
        if (this.isDrawing) { this.isDrawing = false; this.save(); }
    },
    drawStep: function (x, y) {
        this.ctx.beginPath(); this.ctx.moveTo(this.lastX, this.lastY); this.ctx.lineTo(x, y);
        if (this.currentTool === 'pen') { this.ctx.globalCompositeOperation = 'source-over'; this.ctx.strokeStyle = this.currentColor; this.ctx.lineWidth = this.lineWidth; }
        else if (this.currentTool === 'eraser') { this.ctx.globalCompositeOperation = 'destination-out'; this.ctx.lineWidth = this.eraserSize; }
        this.ctx.stroke(); this.lastX = x; this.lastY = y;
    },
    handlePressStart: function (toolName) { this.longPressTriggered = false; this.pressTimer = setTimeout(() => { this.longPressTriggered = true; this.togglePopout(toolName, true); }, 500); },
    handlePressEnd: function (toolName) { clearTimeout(this.pressTimer); if (!this.longPressTriggered) { if (this.currentTool === toolName) this.setTool('none'); else this.setTool(toolName); } },
    setTool: function (tool) {
        this.currentTool = tool;
        document.querySelectorAll('.sp-tool-item .btn-square').forEach(b => b.classList.remove('sp-tool-active'));
        if (tool !== 'none') { const btn = document.getElementById('btn-tool-' + tool); if (btn) btn.classList.add('sp-tool-active'); }
        document.getElementById('sp-text-input-box').style.display = 'none';
        this.updateUI();
    },
    setColor: function (color) {
        this.currentColor = color; document.getElementById('sp-pen-color').value = color;
        const btn = document.getElementById('btn-tool-pen'); if (btn) btn.style.color = color;
        this.setTool('pen'); this.closeAllPopouts();
    },
    setOpacity: function (val) { document.getElementById('scratchpad-canvas').style.opacity = val; },
    openTextCloud: function (canvasX, canvasY) {
        const box = document.getElementById('sp-text-input-box'); const input = document.getElementById('sp-text-input');
        const rect = this.canvas.getBoundingClientRect();
        this.pendingTextPos = { x: canvasX, y: canvasY };
        const isMobile = window.innerWidth < 768;
        if (isMobile) { box.style.position = 'fixed'; box.style.left = '50%'; box.style.top = '80px'; box.style.transform = 'translateX(-50%)'; }
        else {
            box.style.position = 'absolute'; box.style.transform = 'none';
            const rawScreenX = rect.left + canvasX; const rawScreenY = rect.top + canvasY;
            const screenX = Math.min(window.innerWidth - 230, Math.max(10, rawScreenX));
            const screenY = Math.min(window.innerHeight - 100, Math.max(60, rawScreenY - 40));
            box.style.left = screenX + 'px'; box.style.top = screenY + 'px';
        }
        box.style.display = 'flex'; input.value = "";
        input.focus(); setTimeout(() => input.focus(), 50);
    },
    commitText: function () {
        const input = document.getElementById('sp-text-input'); const text = input.value;
        if (text && this.pendingTextPos) {
            this.ctx.globalCompositeOperation = 'source-over'; this.ctx.font = `bold ${this.fontSize}px Consolas`;
            this.ctx.fillStyle = this.currentColor; this.ctx.fillText(text, this.pendingTextPos.x, this.pendingTextPos.y);
            this.save();
        }
        document.getElementById('sp-text-input-box').style.display = 'none';
    },
    togglePopout: function (name, forceOpen = false) {
        const el = document.getElementById('pop-' + name);
        const wasOpen = el.classList.contains('show');
        this.closeAllPopouts();
        if (!wasOpen || forceOpen) el.classList.add('show');
    },
    closeAllPopouts: function () { document.querySelectorAll('.sp-popout').forEach(e => e.classList.remove('show')); },
    clear: function () { if (confirm("Clear Scratchpad?")) { this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); this.save(); } },
    resize: function () {
        const t = document.createElement('canvas'); const tx = t.getContext('2d');
        t.width = this.canvas.width; t.height = this.canvas.height;
        if (t.width > 0) tx.drawImage(this.canvas, 0, 0);
        this.canvas.width = window.innerWidth; this.canvas.height = window.innerHeight;
        this.ctx.drawImage(t, 0, 0); this.ctx.lineCap = 'round'; this.ctx.lineJoin = 'round';
    },
    save: function () { localStorage.setItem('dcs_Scratchpad_data', this.canvas.toDataURL()); },
    load: function () { const d = localStorage.getItem('dcs_Scratchpad_data'); if (d) { const i = new Image(); i.onload = () => { this.ctx.drawImage(i, 0, 0) }; i.src = d; } }
};
window.addEventListener('load', () => Scratchpad.init());


// --- SOCKET INITIALIZATION ---
// Socket initialized at top


// --- SETTINGS & SYNC HANDLERS ---
socket.on('map_settings_update', function (data) {
    console.debug("Settings Update Received", data);
    if (!data) return;

    // 1. Sync Logic (Non-Visual)
    if (data.coords) { settings.coords = data.coords; document.getElementById('opt-coords').value = data.coords; }
    if (data.altUnit) { settings.altUnit = data.altUnit; document.getElementById('opt-alt-unit').value = data.altUnit; }
    if (data.distUnit) { settings.distUnit = data.distUnit; document.getElementById('opt-dist-unit').value = data.distUnit; }
    if (data.defAlt) { settings.defAlt = data.defAlt; document.getElementById('opt-def-alt').value = data.defAlt; }

    // Update UI Labels
    document.getElementById('lbl-def-alt-unit').innerText = settings.altUnit;
    document.getElementById('lbl-global-alt-unit').innerText = settings.altUnit;

    if (data.visibleRoutes) {
        visibleRoutes = new Set(data.visibleRoutes);
        if (typeof renderBrowserList === 'function') renderBrowserList();
        if (typeof renderMapRoutes === 'function') renderMapRoutes();
    }

    // 2. Sync Base Layer
    if (data.layer && data.layer !== currentMapLayerName) {
        setMapLayer(data.layer, true);
    }

    // 3. Sync Overlays
    if (data.overlays) {
        for (const [key, isActive] of Object.entries(data.overlays)) {
            if (activeOverlays[key] !== isActive) {
                toggleOverlay(key, isActive, true);
            }
        }
    }
    // 3.1 Sync Zoom
    if (data.view) {
        const currentZoom = map.getZoom();
        const currentCenter = map.getCenter();
        const dist = map.distance(currentCenter, data.view.center);
        if (dist > 100 || currentZoom !== data.view.zoom) {
            isProgrammaticMove = true;
            map.setView(data.view.center, data.view.zoom, { animate: true });
            setTimeout(() => isProgrammaticMove = false, 1000);
        }
    }

    // 3.2 Sync Visual Filters
    if (data.visuals) {
        if (data.visuals.brightness) { document.documentElement.style.setProperty('--map-br', data.visuals.brightness); }
        if (data.visuals.contrast) { document.documentElement.style.setProperty('--map-con', data.visuals.contrast); }
        if (data.visuals.opacity) { document.documentElement.style.setProperty('--map-op', data.visuals.opacity); }

        // Update sliders if they exist
        const safeSet = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
        safeSet('sld-map-br', data.visuals.brightness);
        safeSet('sld-map-con', data.visuals.contrast);
        safeSet('sld-map-op', data.visuals.opacity);
    }

    // 4. Sync Visibility Toggles
    if (data.vis) {
        const syncChk = (id, val) => { const el = document.getElementById(id); if (el) el.checked = val; };
        syncChk('chk-vis-air', data.vis.airports);
        syncChk('chk-vis-unit', data.vis.units);
        syncChk('chk-vis-poi', data.vis.pois);
        syncChk('chk-vis-grid', data.vis.grid);
        syncChk('chk-vis-mgrs', data.vis.mgrs);
        syncChk('chk-opt-wakelock', data.vis.wakeLock);
        if (data.vis.wakeLock) requestWakeLock(); else releaseWakeLock();

        if (data.vis.ptrStyle) { document.getElementById('opt-ptr-style').value = data.vis.ptrStyle; updatePointerVisuals(); }
        if (data.vis.ptrColor) { document.getElementById('opt-ptr-color').value = data.vis.ptrColor; updatePointerVisuals(); }

        syncChk('chk-live-air', data.vis.liveAir); // Sync Live Air
        if (typeof updateAirportStatus === 'function') updateAirportStatus();

        // Sync Granular Unit Toggles
        syncChk('chk-vis-unit-static', data.vis.units_static);
        syncChk('chk-vis-unit-red', data.vis.units_red);
        syncChk('chk-vis-unit-blue', data.vis.units_blue);
        syncChk('chk-vis-unit-neutral', data.vis.units_neutral);

        if (data.vis.airports !== map.hasLayer(airportLayer)) toggleLayer(airportLayer);
        if (data.vis.units !== map.hasLayer(unitLayer)) toggleLayer(unitLayer);
        if (data.vis.pois !== map.hasLayer(poiLayer)) toggleLayer(poiLayer);
        if (data.vis.grid !== map.hasLayer(gridLayer)) toggleLayer(gridLayer);
        if (data.vis.mgrs !== map.hasLayer(mgrsGridLayer)) toggleLayer(mgrsGridLayer);
    }
    // 5. Update Grid Colors
    if (data.colors) {
        if (data.colors.latlon) document.documentElement.style.setProperty('--latlon-color', data.colors.latlon);
        if (data.colors.mgrs) document.documentElement.style.setProperty('--mgrs-color', data.colors.mgrs);
        if (data.colors.mgrsGzd) document.documentElement.style.setProperty('--mgrs-gzd-color', data.colors.mgrsGzd);
    }
});

socket.on('routes_library_update', function (data) {
    console.debug("Library Update Received");
    const firstKey = Object.keys(data)[0];
    const isOldFormat = firstKey && data[firstKey].points;
    if (isOldFormat) missions["Default Mission"].routes = data; else missions = data;
    if (activeMissionName && missions[activeMissionName]) {
        allSavedRoutes = missions[activeMissionName].routes;
        allPois = missions[activeMissionName].pois || [];
        renderBrowserList(); renderMapRoutes(); renderPois();
    } else { renderMissionList(); }
    showToast("Library Updated");
});

async function saveMapSettings() {
    try {
        const check = (id) => { const el = document.getElementById(id); return el ? el.checked : false; };
        const getVal = (id, def = "") => { const el = document.getElementById(id); return el ? el.value : def; };

        const payload = {
            coords: getVal('opt-coords', 'latlon'),
            altUnit: getVal('opt-alt-unit', 'ft'),
            distUnit: getVal('opt-dist-unit', 'nm'),
            defAlt: parseInt(getVal('opt-def-alt', '20000')) || 20000,
            layer: currentMapLayerName,
            visibleRoutes: Array.from(visibleRoutes),
            navFlyBy: check('chk-opt-flyby'), navCourseLine: check('chk-opt-courseline'),
            colors: { latlon: getVal('col-latlon', '#00ffcc'), mgrs: getVal('col-mgrs', '#733f59'), mgrsGzd: getVal('col-mgrs-gzd', '#988035') },
            overlays: activeOverlays,
            view: { zoom: map.getZoom(), center: map.getCenter() },
            threatFill: parseInt(getVal('sld-threat-fill', '20')),

            // NEW: Active State & Visuals
            activeState: { mission: activeMissionName, route: activeRouteName },
            mapFilters: (typeof filterSettings !== 'undefined' && filterSettings.map) ? filterSettings.map : {},
            visuals: {
                brightness: getComputedStyle(document.documentElement).getPropertyValue('--map-br').trim() || "1.0",
                contrast: getComputedStyle(document.documentElement).getPropertyValue('--map-con').trim() || "1.0",
                opacity: getComputedStyle(document.documentElement).getPropertyValue('--map-op').trim() || "1.0"
            },

            vis: {
                airports: check('chk-vis-air'), units: check('chk-vis-unit'),
                units_air: check('chk-vis-unit-air'), units_ground: check('chk-vis-unit-ground'),
                units_naval: check('chk-vis-unit-naval'), units_static: check('chk-vis-unit-static'),
                pois: check('chk-vis-poi'), threats: check('chk-vis-threats'),
                theaterThreats: check('chk-vis-theater-threats'), theaterOpacity: getVal('rng-theater-threat-opacity', '10'),
                grid: check('chk-vis-grid'), mgrs: check('chk-vis-mgrs'),
                alt: check('chk-vis-alt'), hdg: check('chk-vis-hdg'),
                wakeLock: check('chk-opt-wakelock'),
                units_red: check('chk-vis-unit-red'), units_blue: check('chk-vis-unit-blue'), units_neutral: check('chk-vis-unit-neutral'),
                hudMode: hudMode, liveAir: check('chk-live-air'),
                ptrStyle: getVal('opt-ptr-style', 'cross'), ptrColor: getVal('opt-ptr-color', '#00ff00')
            }
        };
        await fetch('/api/map/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    } catch (e) {
        console.error("saveMapSettings Failed:", e);
        console.error("Stack trace:", e.stack);
    }
}

async function loadMapSettings() {
    try {
        // 4. MGRS / Grid Persistence (Local First)
        if (localStorage.getItem('vis_grid') === 'true') {
            if (!map.hasLayer(gridLayer)) { map.addLayer(gridLayer); updateGrid(); }
            const chk = document.getElementById('chk-vis-grid'); if (chk) chk.checked = true;
        } else if (localStorage.getItem('vis_grid') === 'false') {
            if (map.hasLayer(gridLayer)) map.removeLayer(gridLayer);
            const chk = document.getElementById('chk-vis-grid'); if (chk) chk.checked = false;
        }
        if (localStorage.getItem('vis_mgrs') === 'true') {
            if (!map.hasLayer(mgrsGridLayer)) { map.addLayer(mgrsGridLayer); updateMgrsGrid(); }
            const chk = document.getElementById('chk-vis-mgrs'); if (chk) chk.checked = true;
        } else if (localStorage.getItem('vis_mgrs') === 'false') {
            if (map.hasLayer(mgrsGridLayer)) map.removeLayer(mgrsGridLayer);
            const chk = document.getElementById('chk-vis-mgrs'); if (chk) chk.checked = false;
        }

        const res = await fetch('/api/map/settings?t=' + Date.now()); const data = await res.json();
        console.log("Loaded Map Settings:", data); // DEBUG LOG
        if (data.visibleRoutes) { visibleRoutes = new Set(data.visibleRoutes) };
        settings = { ...settings, ...data };
        const savedNvg = data.nvgMode || localStorage.getItem('dcs_nvg_mode') || 'off'; setNightVision(savedNvg);
        document.getElementById('opt-coords').value = data.coords || 'latlon';
        document.getElementById('opt-alt-unit').value = data.altUnit || 'ft';
        document.getElementById('opt-dist-unit').value = data.distUnit || 'nm';
        document.getElementById('opt-def-alt').value = data.defAlt || 20000;
        const flyByChk = document.getElementById('chk-opt-flyby'); if (flyByChk) flyByChk.checked = (data.navFlyBy === true);
        const courseLineChk = document.getElementById('chk-opt-courseline'); if (courseLineChk) courseLineChk.checked = (data.navCourseLine === true);
        const localScale = localStorage.getItem('dcs_map_ui_scale'); if (localScale) { document.getElementById('opt-ui-scale').value = localScale; applyUiScale(localScale); }
        if (data.layer && layers[data.layer]) setMapLayer(data.layer);
        if (data.threatFill !== undefined) { document.getElementById('sld-threat-fill').value = data.threatFill; updateThreatFill(data.threatFill); }
        if (data.overlays) { for (const [key, isActive] of Object.entries(data.overlays)) { toggleOverlay(key, isActive); } }
        if (data.vis) {
            setCheckboxAndLayer('chk-vis-air', airportLayer, data.vis.airports);
            setCheckboxAndLayer('chk-vis-unit', unitLayer, data.vis.units);
            const setChk = (id, val) => {
                const el = document.getElementById(id);
                if (el) {
                    el.checked = (val !== undefined ? val : true);
                    // Sync Parent Label Class (Unit Types)
                    if (el.parentElement.classList.contains('layer-toggle-btn')) {
                        el.parentElement.classList.toggle('active', el.checked);
                    }
                }
            };
            setChk('chk-vis-unit-air', data.vis.units_air); setChk('chk-vis-unit-ground', data.vis.units_ground);
            setChk('chk-vis-unit-naval', data.vis.units_naval); setChk('chk-vis-unit-static', data.vis.units_static);
            setChk('chk-vis-unit-red', data.vis.units_red); setChk('chk-vis-unit-blue', data.vis.units_blue);
            setChk('chk-vis-unit-neutral', data.vis.units_neutral);

            // Sync Coalition Buttons (Separate IDs)
            const syncCoalitionBtn = (side) => {
                const btn = document.getElementById(`btn-vis-${side}`);
                const chk = document.getElementById(`chk-vis-unit-${side}`);
                if (btn && chk) btn.classList.toggle('active', chk.checked);
            };
            syncCoalitionBtn('red'); syncCoalitionBtn('blue'); syncCoalitionBtn('neutral');
            setChk('chk-live-air', data.vis.liveAir); // Sync Live Air
            setCheckboxAndLayer('chk-vis-poi', poiLayer, data.vis.pois !== undefined ? data.vis.pois : true);
            const threatChk = document.getElementById('chk-vis-threats'); if (threatChk) threatChk.checked = (data.vis.threats !== undefined ? data.vis.threats : true);

            // Theater Threats
            const chkTh = document.getElementById('chk-vis-theater-threats');
            if (chkTh) chkTh.checked = (data.vis.theaterThreats !== undefined ? data.vis.theaterThreats : false);
            if (data.vis.theaterOpacity !== undefined) {
                const rngThOp = document.getElementById('rng-theater-threat-opacity');
                if (rngThOp) rngThOp.value = data.vis.theaterOpacity;
            }

            // GRID: Only use Server if LocalStorage is missing (First Run)
            if (localStorage.getItem('vis_grid') === null) {
                setCheckboxAndLayer('chk-vis-grid', gridLayer, data.vis.grid);
            }
            if (localStorage.getItem('vis_mgrs') === null) {
                setCheckboxAndLayer('chk-vis-mgrs', mgrsGridLayer, data.vis.mgrs);
            }

            const altChk = document.getElementById('chk-vis-alt'); if (altChk) { altChk.checked = data.vis.alt; document.getElementById('pill-alt').classList.toggle('visible', data.vis.alt); }
            const hdgChk = document.getElementById('chk-vis-hdg'); if (hdgChk) { hdgChk.checked = data.vis.hdg; document.getElementById('pill-hdg').classList.toggle('visible', data.vis.hdg); }
            cycleHudMode(data.vis.hudMode !== undefined ? data.vis.hudMode : 0);
            if (data.vis.ptrStyle) document.getElementById('opt-ptr-style').value = data.vis.ptrStyle;
            if (data.vis.ptrColor) {
                document.getElementById('opt-ptr-color').value = data.vis.ptrColor;
                updatePointerVisuals(); // Ensure visuals update immediately
            }
            updatePointerVisuals();
            const wlChk = document.getElementById('chk-opt-wakelock'); if (wlChk && data.vis.wakeLock) { wlChk.checked = true; requestWakeLock(); }
            if (typeof updateAirportStatus === 'function') updateAirportStatus(); // Trigger Live Air Logic
        }

        // Restore Visuals
        if (data.visuals) {
            const setVar = (v, val) => document.documentElement.style.setProperty(v, val);
            if (data.visuals.brightness) setVar('--map-br', data.visuals.brightness);
            if (data.visuals.contrast) setVar('--map-con', data.visuals.contrast);
            if (data.visuals.opacity) setVar('--map-op', data.visuals.opacity);

            // Sync with local filterSettings to prevent overwrite on layer change
            if (typeof filterSettings !== 'undefined' && filterSettings.map) {
                // If the server provided a full map filters object, use it (Per-Map Persistence Fix)
                if (data.mapFilters) {
                    filterSettings.map = { ...filterSettings.map, ...data.mapFilters };
                    localStorage.setItem('map_filters', JSON.stringify(filterSettings.map));
                }

                // Ensure current layer is roughly in sync with saved 'visuals' as a fallback
                if (!filterSettings.map[currentMapLayerName]) filterSettings.map[currentMapLayerName] = { br: 1.0, con: 1.0, op: 1.0 };
                const t = filterSettings.map[currentMapLayerName];

                // HELPER: Sanitize values that might have been saved as 0-100 scales due to previous bug
                const sanitize = (val, max = 2.0) => {
                    let v = parseFloat(val);
                    if (isNaN(v)) return 1.0;
                    if (v > max && v <= 100) v = v / 100; // Auto-correct old scale
                    if (v > max) v = max; // Clamp
                    return v;
                };

                // If date.visuals is present, sync it to the current layer's memory
                if (data.visuals.brightness) t.br = sanitize(data.visuals.brightness, 2.0);
                if (data.visuals.contrast) t.con = sanitize(data.visuals.contrast, 2.0);
                if (data.visuals.opacity) t.op = sanitize(data.visuals.opacity, 1.0);

                // Also sanitize entire mapFilters if polluted
                if (filterSettings.map) {
                    for (let k in filterSettings.map) {
                        const m = filterSettings.map[k];
                        if (m.br) m.br = sanitize(m.br, 2.0);
                        if (m.con) m.con = sanitize(m.con, 2.0);
                        if (m.op) m.op = sanitize(m.op, 1.0);
                    }
                }
            }

            // Finally, Apply All Visuals (Map + NVG)
            applyVisualFilters();
        }

        // Apply Colors Immediately
        if (data.colors) {
            if (data.colors.latlon) {
                document.getElementById('col-latlon').value = data.colors.latlon;
                document.documentElement.style.setProperty('--latlon-color', data.colors.latlon);
            }
            if (data.colors.mgrs) {
                document.getElementById('col-mgrs').value = data.colors.mgrs;
                document.documentElement.style.setProperty('--mgrs-color', data.colors.mgrs);
            }
            if (data.colors.mgrsGzd) {
                document.getElementById('col-mgrs-gzd').value = data.colors.mgrsGzd;
                document.documentElement.style.setProperty('--mgrs-gzd-color', data.colors.mgrsGzd);
            }
        }

        // Restore Active State (Mission/Route)
        if (data.activeState && data.activeState.mission) {
            // Wait for missions to load? missions is global and loaded via loadSavedRoutes called AFTER loadMapSettings in init but we are async...
            // Actually map.js init calls: loadAirports(); loadMapSettings(); loadSavedRoutes(); loadSavedPois();
            // loadSavedRoutes fetches missions. We might need to wait or check.
            // BETTER STRATEGY: Store in temp var and apply in loadSavedRoutes if available OR 
            // Since loadMapSettings is async, we can just check if missions are loaded. If not, we might be early.
            // But loadSavedRoutes is also async.
            // We'll set a global 'pendingActiveState' and handle it in loadSavedRoutes/renderMissionList.
            window.pendingActiveState = data.activeState;
        }
        if (data.view) { isProgrammaticMove = true; map.setView(data.view.center, data.view.zoom); setTimeout(() => isProgrammaticMove = false, 500); }
        updateSettings();

        // Force update of grids if visible
        if (data.vis.grid && typeof updateGrid === 'function') updateGrid();
        if (data.vis.mgrs && typeof updateMgrsGrid === 'function') updateMgrsGrid();

    } catch (e) {
        console.error("loadMapSettings Failed:", e);
        console.error("Stack trace:", e.stack);
    }
}

function setCheckboxAndLayer(chkId, layer, isVisible) {
    const chk = document.getElementById(chkId);
    const shouldBeVisible = (isVisible !== false); // Default to true if undefined, but handle explicit false
    if (chk) chk.checked = shouldBeVisible;
    if (shouldBeVisible) {
        if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
        if (map.hasLayer(layer)) map.removeLayer(layer);
    }
}

function applyUiScale(val) {
    document.documentElement.style.setProperty('--ui-scale', val);
    const label = document.getElementById('lbl-ui-scale');
    if (label) label.innerText = val;
    localStorage.setItem('dcs_map_ui_scale', val);
}
function updateSettings() {
    settings.altUnit = document.getElementById('opt-alt-unit')?.value || 'ft';
    settings.coords = document.getElementById('opt-coords')?.value || 'latlon';
    settings.distUnit = document.getElementById('opt-dist-unit')?.value || 'nm';
    settings.defAlt = parseInt(document.getElementById('opt-def-alt')?.value) || 20000;
    settings.uiScale = document.getElementById('opt-ui-scale')?.value || 1.0;

    // Update labels with null checks
    const defAltLabel = document.getElementById('lbl-def-alt-unit');
    if (defAltLabel) defAltLabel.innerText = settings.altUnit;
    const globalAltLabel = document.getElementById('lbl-global-alt-unit');
    if (globalAltLabel) globalAltLabel.innerText = settings.altUnit;

    const latlonBox = document.getElementById('inp-latlon-box');
    if (latlonBox) latlonBox.style.display = (settings.coords === 'latlon') ? 'block' : 'none';
    const mgrsBox = document.getElementById('inp-mgrs-box');
    if (mgrsBox) mgrsBox.style.display = (settings.coords === 'mgrs') ? 'block' : 'none';

    const globalAltInput = document.getElementById('global-alt');
    if (globalAltInput) globalAltInput.value = settings.defAlt;

    // Update CSS variables with null checks
    const latlonColor = document.getElementById('col-latlon');
    if (latlonColor) document.documentElement.style.setProperty('--latlon-color', latlonColor.value);
    const mgrsColor = document.getElementById('col-mgrs');
    if (mgrsColor) document.documentElement.style.setProperty('--mgrs-color', mgrsColor.value);
    const mgrsGzdColor = document.getElementById('col-mgrs-gzd');
    if (mgrsGzdColor) document.documentElement.style.setProperty('--mgrs-gzd-color', mgrsGzdColor.value);
    renderEditorPoints(); renderMapRoutes(); saveMapSettings();
}

// --- ROUTE & MISSION LOGIC ---
async function getGroundElevation(lat, lon) { try { const resp = await fetch(`https://api.open-meteo.com/v1/elevation?latitude=${lat}&longitude=${lon}`); const data = await resp.json(); if (data && data.elevation) return data.elevation[0]; } catch (e) { } return 0; }
function toggleSeq() { const chk = document.getElementById('chk-opt-autoseq'); if (chk) { autoSeq = chk.checked; socket.emit('toggle_seq', { state: autoSeq }); } }
function switchToEditor() { document.getElementById('view-browser').style.display = 'none'; document.getElementById('view-editor').style.display = 'flex'; }
function createNewRoute() { editingRouteName = ""; editingRouteData = []; activeWpIndex = -1; wpCounter = 1; document.getElementById('save-color').value = "#78aabc"; document.getElementById('route-title').innerText = "New Route"; document.getElementById('save-name').value = ""; switchToEditor(); renderEditorPoints(); }
function setClickMode(mode) { clickMode = (clickMode === mode) ? 'none' : mode; document.getElementById('btn-mode-wp').classList.toggle('active', clickMode === 'wp'); document.getElementById('btn-mode-tgt').classList.toggle('active', clickMode === 'tgt'); document.getElementById('btn-mode-poi').classList.toggle('active', clickMode === 'poi'); document.getElementById('map').style.cursor = (clickMode !== 'none') ? 'crosshair' : 'default'; if (clickMode != 'none') distMode = false; }
function toggleManualInput() { const f = document.getElementById('manual-form'); f.style.display = (f.style.display === 'none') ? 'block' : 'none'; }
function updateServerNav() { socket.emit('set_active_wp', { index: activeWpIndex, route: activeRouteData, name: activeRouteName }); }
function autoRenameWaypoints() { let w = 1, t = 1; editingRouteData.forEach(p => { if (p.type === 'tgt') p.name = `TGT ${t++}`; else p.name = `WP ${w++}`; }); renderEditorPoints(); renderEditorMap(); }
async function loadSavedRoutes() {
    try {
        const res = await fetch(`/api/routes?t=${Date.now()}`); const data = await res.json();
        const firstKey = Object.keys(data)[0]; const isOldFormat = firstKey && data[firstKey].points;
        if (isOldFormat) missions = { "Legacy Mission": { imported: "L", map: null, routes: data, pois: [] } }; else missions = data;

        // Handle Pending Active State from loadMapSettings
        if (window.pendingActiveState && window.pendingActiveState.mission && missions[window.pendingActiveState.mission]) {
            activeMissionName = window.pendingActiveState.mission;
            // We don't use localStorage for this anymore if server sync is authoritative
        } else {
            const lastMission = localStorage.getItem('last_active_mission');
            if (lastMission && missions[lastMission]) activeMissionName = lastMission;
        }

        if (activeMissionName && missions[activeMissionName]) {
            selectMission(activeMissionName);
            // If route also pending
            if (window.pendingActiveState && window.pendingActiveState.route) {
                // Try activating route
                const rName = window.pendingActiveState.route;
                if (missions[activeMissionName].routes && missions[activeMissionName].routes[rName]) {
                    activateRoute(rName);
                }
            }
        } else { renderMissionList(); }
    } catch (e) { console.error("Load failed", e); }
}
async function saveCurrentRoute() {
    if (!activeMissionName) { showToast("No Active Mission"); return; }
    const name = document.getElementById('save-name').value || "Unnamed Route"; const color = document.getElementById('save-color').value; editingRouteName = name;
    const newRouteObj = { color: color, points: editingRouteData };
    if (!missions[activeMissionName]) return; if (!missions[activeMissionName].routes) missions[activeMissionName].routes = {};
    missions[activeMissionName].routes[name] = newRouteObj;
    allSavedRoutes = missions[activeMissionName].routes;
    if (activeRouteName === name || activeRouteName === "New Route") { activeRouteName = name; activeRouteData = editingRouteData; updateServerNav(); }
    renderMapRoutes(); await saveAllMissions(); showToast("Route Saved"); showBrowser();
}

// --- MISSION UI ---
function createNewMission() {
    if (document.getElementById('new-mission-row')) { document.getElementById('new-mission-name').focus(); return; }
    const list = document.getElementById('mission-list');
    if (Object.keys(missions).length === 0) list.innerHTML = "";
    const div = document.createElement('div'); div.id = 'new-mission-row'; div.className = 'saved-route-item'; div.style.display = 'flex'; div.style.alignItems = 'center'; div.style.padding = '5px'; div.style.gap = '10px'; div.style.borderLeft = '3px solid #78aabc'; div.style.background = 'rgba(120, 170, 188, 0.1)';
    div.innerHTML = `<div style="flex-grow:1; display:flex; align-items:center;"><div class="input-with-kb" style="width:100%;"><input type="text" id="new-mission-name" placeholder="Enter Mission Name..." style="width:100%; border:1px solid #78aabc; background:#111; color:#fff; padding:5px; font-weight:bold;" onkeydown="if(event.key==='Enter') saveNewMission()"><div class="kb-trigger" onclick="openKeyboard('new-mission-name', 'text')">⌨</div></div></div><button class="list-btn" onclick="saveNewMission()" title="Save"><i class="fa-solid fa-check" style="color:#2ecc71;"></i></button><button class="list-btn delete" onclick="cancelNewMission()" title="Cancel"><i class="fa-solid fa-xmark"></i></button>`;
    list.prepend(div); setTimeout(() => document.getElementById('new-mission-name').focus(), 50);
}
function exitToMissionSelector() { activeMissionName = null; localStorage.removeItem('last_active_mission'); activeRouteName = null; routeLayer.clearLayers(); activeLegLayer.clearLayers(); document.getElementById('mini-route-panel').classList.remove('visible'); showMissionList(); }
async function saveNewMission() {
    const input = document.getElementById('new-mission-name'); const name = input.value.trim();
    if (!name) { showToast("Name required"); input.focus(); return; }
    if (missions[name]) { alert("Mission name already exists!"); input.focus(); return; }
    missions[name] = { imported: "L", map: "Caucasus", routes: {}, pois: [] };
    cancelNewMission(); await saveAllMissions(); renderMissionList();
}
function cancelNewMission() { const row = document.getElementById('new-mission-row'); if (row) row.remove(); if (Object.keys(missions).length === 0) renderMissionList(); }
function selectMission(name) {
    if (!missions[name]) return;
    activeMissionName = name; localStorage.setItem('last_active_mission', name);
    document.getElementById('browser-title').innerText = `Route Manager: ${name}`;
    document.getElementById('lbl-active-map').innerText = "Map: " + (missions[name].map || "None");
    const statusSpan = document.getElementById('lbl-mission-status'); statusSpan.innerText = (missions[name].imported === 'I') ? "IMPORTED" : "LOCAL"; statusSpan.style.color = (missions[name].imported === 'I') ? "#e67e22" : "#78aabc";
    allSavedRoutes = missions[name].routes || {}; allPois = missions[name].pois || [];
    document.getElementById('view-missions').style.display = 'none'; document.getElementById('view-editor').style.display = 'none'; document.getElementById('view-browser').style.display = 'flex';
    renderBrowserList(); renderMapRoutes(); renderPois();
    saveMapSettings(); // Persist active mission
}
function showMissionList() { document.getElementById('view-browser').style.display = 'none'; document.getElementById('view-editor').style.display = 'none'; document.getElementById('view-missions').style.display = 'flex'; renderMissionList(); }
function renderMissionList() {
    const list = document.getElementById('mission-list'); list.innerHTML = "";
    const missionKeys = Object.keys(missions); if (missionKeys.length === 0) { list.innerHTML = `<div style="padding:10px; color:#555; text-align:center;">No Missions Created</div>`; return; }
    missionKeys.forEach(key => {
        const data = missions[key]; const div = document.createElement('div'); div.className = 'saved-route-item draggable-mission'; div.draggable = true; div.dataset.missionName = key; div.style.display = 'flex'; div.style.alignItems = 'center'; div.style.padding = '5px'; div.style.gap = '10px'; div.onclick = () => selectMission(key);
        div.innerHTML = `<div class="drag-handle" style="color:#555; padding:0 5px;"><i class="fa-solid fa-grip-vertical"></i></div><div style="flex-grow:1;"><div style="font-weight:bold; color:#d1e3ea; font-size:13px;">${key}</div><div style="font-size:10px; color:#888;">${Object.keys(data.routes || {}).length} Routes | ${(data.pois || []).length} POIs</div></div><div style="margin-right:5px;" onmousedown="event.stopPropagation()" onclick="event.stopPropagation()"><select class="map-selector" onchange="updateMissionMap('${key}', this.value)" style="width:80px; padding:2px; font-size:10px; background:#111; color:#aaa; border:1px solid #444; cursor:pointer;"><option value="None" ${!data.map ? 'selected' : ''}>-- Map --</option>${dcsMaps.map(m => `<option value="${m}" ${data.map === m ? 'selected' : ''}>${m}</option>`).join('')}</select></div><button class="list-btn delete" onmousedown="event.stopPropagation()" onclick="event.stopPropagation(); deleteMission('${key}')"><i class="fa-solid fa-trash"></i></button>`;
        div.addEventListener('dragstart', handleMissionDragStart); div.addEventListener('dragend', handleMissionDragEnd); list.appendChild(div);
    });
}
function updateMissionMap(name, mapVal) { if (missions[name]) { missions[name].map = (mapVal === "None") ? null : mapVal; saveAllMissions(); } }
async function deleteMission(name) { if (confirm(`Delete mission "${name}"?`)) { delete missions[name]; await saveAllMissions(); renderMissionList(); } }
function handleMissionDragStart(e) { this.classList.add('dragging'); }
function handleMissionDragEnd(e) { this.classList.remove('dragging'); const newMissions = {}; document.querySelectorAll('#mission-list .draggable-mission').forEach(el => { const key = el.dataset.missionName; if (missions[key]) newMissions[key] = missions[key]; }); missions = newMissions; saveAllMissions(); }
const missionContainer = document.getElementById('mission-list'); missionContainer.addEventListener('dragover', e => { e.preventDefault(); const afterElement = getDragAfterElement(missionContainer, e.clientY, '.draggable-mission'); const draggable = document.querySelector('.dragging'); if (draggable) { if (afterElement == null) missionContainer.appendChild(draggable); else missionContainer.insertBefore(draggable, afterElement); } });
async function saveAllMissions() { await fetch('/api/routes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(missions) }); }
async function saveActiveMission() { if (!activeMissionName || !missions[activeMissionName]) return; missions[activeMissionName].routes = allSavedRoutes; missions[activeMissionName].pois = allPois; await saveAllMissions(); }

async function loadSavedPois() { if (activeMissionName && missions[activeMissionName]) { allPois = missions[activeMissionName].pois || []; renderPois(); if (typeof renderPoiList === 'function') renderPoiList(); } }
function activateRoute(name) { if (allSavedRoutes[name]) { activeRouteName = name; activeRouteData = allSavedRoutes[name].points || allSavedRoutes[name]; activeWpIndex = 0; visibleRoutes.add(name); updateServerNav(); renderMapRoutes(); document.getElementById('route-drawer').classList.remove('open'); updateMiniPanel(); document.getElementById('mini-route-panel').classList.add('visible'); showToast(`Route Active: ${name}`); saveMapSettings(); } }
function stopRoute() { activeRouteName = null; activeRouteData = []; activeWpIndex = -1; updateServerNav(); document.getElementById('mini-route-panel').classList.remove('visible'); document.getElementById('route-drawer').classList.add('open'); activeLegLayer.clearLayers(); renderMapRoutes(); renderBrowserList(); showToast("Route Stopped"); saveMapSettings(); }

function updateMiniPanel() { if (!activeRouteName) return; document.getElementById('mini-route-name').innerText = activeRouteName; let wpName = "N/A"; if (activeRouteData[activeWpIndex]) wpName = activeRouteData[activeWpIndex].name || `WP ${activeWpIndex + 1}`; document.getElementById('mini-wp-name').innerText = wpName; }
function cycleWp(dir) { socket.emit('cycle_wp', { dir: dir }); }
function activateVisualRoute() { if (allPois.length === 0) { showToast("No Visual Targets to Follow"); return; } activatePoiFromModal(0); }

let dragSrcEl = null; function handleDragStart(e) { dragSrcEl = this; e.dataTransfer.effectAllowed = 'move'; setTimeout(() => this.classList.add('dragging'), 0); }
function handleDragEnd(e) { this.classList.remove('dragging'); document.querySelectorAll('.draggable-row').forEach(row => { row.classList.remove('over'); }); }
function getDragAfterElement(container, y, selector) { const draggableElements = [...container.querySelectorAll(`${selector}:not(.dragging)`)]; return draggableElements.reduce((closest, child) => { const box = child.getBoundingClientRect(); const offset = y - box.top - box.height / 2; if (offset < 0 && offset > closest.offset) { return { offset: offset, element: child }; } else { return closest; } }, { offset: Number.NEGATIVE_INFINITY }).element; }

// --- ROUTE & EDITOR UI ---
function renderBrowserList() {
    const list = document.getElementById('saved-list'); list.innerHTML = "";
    const poiCount = allPois.length; const isPoiActive = (activeRouteName === "Visual Targets"); const isPoiVisible = map.hasLayer(poiLayer);
    const poiDiv = document.createElement('div'); poiDiv.className = `saved-route-item ${isPoiActive ? 'is-active' : ''}`; poiDiv.style.borderLeftColor = "#f1c40f"; poiDiv.style.display = 'flex'; poiDiv.style.alignItems = 'center'; poiDiv.style.padding = '5px'; poiDiv.style.gap = '0px'; poiDiv.draggable = true; poiDiv.dataset.routeName = "Visual Targets";
    poiDiv.addEventListener('dragstart', handleDragStart); poiDiv.addEventListener('dragend', handleDragEnd);
    poiDiv.innerHTML = `<button id="btn-vis-poi-list" class="list-btn ${isPoiVisible ? 'active' : ''}" style="width:30px; margin-right:5px;" onclick="event.stopPropagation(); toggleLayer(poiLayer, null); saveMapSettings();" title="Toggle POI Visibility"><i class="fa-solid fa-eye"></i></button><div style="flex-grow:1; width:0; display:flex; align-items:center; justify-content:space-between; padding:0 5px; pointer-events:none;"><span style="font-weight:bold; font-size:13px; color:#d1e3ea; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">Visual Targets</span><span style="font-size:10px; color:#aaa; background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px; white-space:nowrap;">${poiCount} POI</span></div><button class="list-btn ${isPoiActive ? 'active' : ''}" style="width:30px;" onclick="event.stopPropagation(); activateVisualRoute()" title="Navigate Visual Targets"><i class="fa-solid fa-crosshairs"></i></button><button class="list-btn" style="width:30px;" onclick="event.stopPropagation(); toggleDrawer('poi')" title="Open Target List"><i class="fa-solid fa-list-ul"></i></button>`;
    list.appendChild(poiDiv);

    if (Object.keys(allSavedRoutes).length === 0) { if (poiCount === 0) { const empty = document.createElement('div'); empty.innerHTML = `<div style="text-align:center; padding:10px; color:#555; font-size:11px;">No Saved Routes</div>`; list.appendChild(empty); return; } }
    Object.entries(allSavedRoutes).forEach(([name, rData]) => {
        const rColor = rData.color || "#78aabc"; const isActive = (name === activeRouteName); const isVisible = visibleRoutes.has(name) || isActive;
        const div = document.createElement('div'); div.className = `saved-route-item ${isActive ? 'is-active' : ''}`; div.draggable = true; div.dataset.routeName = name; div.style.display = 'flex'; div.style.alignItems = 'center'; div.style.padding = '5px'; div.style.gap = '0px';
        div.addEventListener('dragstart', handleDragStart); div.addEventListener('dragend', handleDragEnd); div.onclick = () => openEditor(name);
        div.innerHTML = `<button class="list-btn ${isVisible ? 'active' : ''}" style="width:30px; margin-right:5px;" onclick="event.stopPropagation(); toggleRouteVis('${name}')"><i class="fa-solid fa-eye"></i></button><div style="flex-grow:1; width:0; display:flex; align-items:center; justify-content:space-between; padding:0 5px; pointer-events:none;"><span style="font-weight:bold; font-size:13px; color:#d1e3ea; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${name}</span><input type="color" class="color-picker-mini" value="${rColor}" onclick="event.stopPropagation()" onchange="updateRouteColor('${name}', this.value)" style="pointer-events:auto;"></div><button class="list-btn ${isActive ? 'active' : ''}" style="width:30px;" onclick="event.stopPropagation(); activateRoute('${name}')"><i class="fa-solid fa-crosshairs"></i></button><button class="list-btn delete" style="width:30px;" onclick="event.stopPropagation(); deleteRoute('${name}')"><i class="fa-solid fa-trash"></i></button>`;
        list.appendChild(div);
    });
}
function toggleRouteVis(name) { if (visibleRoutes.has(name)) visibleRoutes.delete(name); else visibleRoutes.add(name); renderBrowserList(); renderMapRoutes(); saveMapSettings(); }
async function updateRouteColor(name, color) { if (allSavedRoutes[name]) { allSavedRoutes[name].color = color; } renderMapRoutes(); await saveActiveMission(); }
async function deleteRoute(name) { if (confirm(`Delete route "${name}"?`)) { delete allSavedRoutes[name]; await saveAllMissions(); if (activeRouteName === name) stopRoute(); renderBrowserList(); renderMapRoutes(); } }
function handleRouteListDrop(e) { if (e.stopPropagation) e.stopPropagation(); const container = document.getElementById('saved-list'); const newOrderObj = {};[...container.querySelectorAll('.saved-route-item')].forEach(row => { const name = row.dataset.routeName; if (name && allSavedRoutes[name]) { newOrderObj[name] = allSavedRoutes[name]; } }); allSavedRoutes = newOrderObj; saveActiveMission(); }
function openEditor(name) { editingRouteName = name; const rawData = allSavedRoutes[name].points || allSavedRoutes[name]; editingRouteData = JSON.parse(JSON.stringify(rawData)); document.getElementById('save-name').value = name; document.getElementById('save-color').value = allSavedRoutes[name].color || "#78aabc"; document.getElementById('route-title').innerText = "Edit: " + name; let maxWp = 0; editingRouteData.forEach(p => { if (p.name && p.name.startsWith('WP ')) { let num = parseInt(p.name.split(' ')[1]); if (num > maxWp) maxWp = num; } }); wpCounter = maxWp + 1; if (visibleRoutes.has(name)) { visibleRoutes.delete(name); renderMapRoutes(); } switchToEditor(); renderEditorPoints(); renderEditorMap(); }
function showBrowser() { document.getElementById('view-browser').style.display = 'flex'; document.getElementById('view-editor').style.display = 'none'; document.getElementById('manual-form').style.display = 'none'; setClickMode('none'); activeEditIndex = -1; editorLayer.clearLayers(); if (editingRouteName && allSavedRoutes[editingRouteName]) visibleRoutes.add(editingRouteName); renderBrowserList(); renderMapRoutes(); }

function renderMapRoutes() {
    routeLayer.clearLayers(); activeLegLayer.clearLayers();
    for (const [name, rData] of Object.entries(allSavedRoutes)) {
        const isActive = (name === activeRouteName); if (!visibleRoutes.has(name) && !isActive) continue; const pts = rData.points || rData; const color = rData.color || "#78aabc"; if (!pts || pts.length === 0) continue;
        if (isActive) {
            pts.forEach((pt, i) => {
                const isTgt = pt.type === 'tgt'; const isNext = (i === activeWpIndex); const htmlColor = isNext ? '#fff' : color;
                const iconHtml = isTgt ? `<div style="color:${htmlColor}; font-size:20px; filter:drop-shadow(0 0 3px black);">🎯</div>` : `<div style="color:${htmlColor}; font-size:20px; filter:drop-shadow(0 0 3px black);"><i class="fa-solid fa-location-dot"></i></div>`;
                const icon = L.divIcon({ className: 'rt-icon', html: iconHtml, iconSize: [20, 20], iconAnchor: [10, 20] });
                const m = L.marker([pt.lat, pt.lon], { icon: icon }).addTo(routeLayer);
                m.on('click', () => { const coordStr = formatCoordDisplay(pt.lat, pt.lon); const displayAlt = toDisplayAlt(pt.alt); const detailHtml = `<div style="font-weight:bold; color:#333; margin-bottom:4px;">${pt.name}</div><div style="font-size:11px; color:#555;">${displayAlt} ${pt.altType || settings.altUnit}</div><div style="font-family:monospace; margin-top:5px; font-size:10px; color:#000;">${coordStr.replace('\n', '<br>')}</div>`; L.popup().setLatLng([pt.lat, pt.lon]).setContent(detailHtml).openOn(map); });
                const labelAlt = toDisplayAlt(pt.alt); if (showWpLabels) m.bindTooltip(`${pt.name} | ${labelAlt}`, { permanent: true, direction: 'right', className: 'airport-label' }); else m.bindTooltip(pt.name, { permanent: false, direction: 'top' });
            });
            if (activeWpIndex > 0) { const pastPts = pts.slice(0, activeWpIndex + 1).map(p => [p.lat, p.lon]); if (pastPts.length > 1) L.polyline(pastPts, { color: '#555', weight: 2 }).addTo(routeLayer); }
            if (activeWpIndex >= 0 && activeWpIndex < pts.length) { const futurePts = pts.slice(activeWpIndex).map(p => [p.lat, p.lon]); if (futurePts.length > 1) L.polyline(futurePts, { color: color, weight: 3, dashArray: '10, 10' }).addTo(routeLayer); }
            if (activeWpIndex > 0 && activeWpIndex < pts.length) { const prev = pts[activeWpIndex - 1]; const curr = pts[activeWpIndex]; L.polyline([[prev.lat, prev.lon], [curr.lat, curr.lon]], { color: '#0f0', weight: 4, opacity: 0.3 }).addTo(routeLayer); }
        } else {
            const latlngs = pts.map(p => [p.lat, p.lon]); L.polyline(latlngs, { color: color, weight: 2, dashArray: '3, 6', opacity: 0.8 }).addTo(routeLayer);
            pts.forEach(pt => { const cm = L.circleMarker([pt.lat, pt.lon], { radius: 3, color: color, fillOpacity: 1 }).addTo(routeLayer); if (showWpLabels) { cm.bindTooltip(`${pt.name}`, { permanent: true, direction: 'right', className: 'airport-label' }); } });
        }
    }
}
function renderEditorPoints() {
    const list = document.getElementById('active-route-list'); list.innerHTML = ""; let totalMeters = 0;
    if (editingRouteData.length > 1) { const pts = editingRouteData.map(p => L.latLng(p.lat, p.lon)); for (let i = 0; i < pts.length - 1; i++) { totalMeters += pts[i].distanceTo(pts[i + 1]); } }
    let totalStr = (settings.distUnit === 'nm') ? (totalMeters * 0.000539957).toFixed(1) + " nm" : (totalMeters / 1000).toFixed(1) + " km";
    document.getElementById('route-footer').innerText = "Total: " + totalStr;
    editingRouteData.forEach((pt, i) => {
        const div = document.createElement('div'); div.className = `route-item`; div.draggable = true; div.dataset.index = i;
        if (activeEditIndex === i) { div.style.background = "rgba(46, 204, 113, 0.15)"; div.style.borderLeft = "3px solid #2ecc71"; }
        div.addEventListener('dragstart', handleDragStart); div.addEventListener('dragend', handleDragEnd);
        const displayAlt = toDisplayAlt(pt.alt);
        div.innerHTML = `<div style="flex-grow:1; display:flex; flex-direction:column;"><div style="font-weight:bold; font-size:12px; color:#fff;">${pt.name} <span style="color:#aaa; font-weight:normal;">| ${displayAlt} ${pt.altType || settings.altUnit}</span></div><div style="font-family:monospace; font-size:11px; color:#888;">${formatCoordDisplay(pt.lat, pt.lon).replace('\n', ' ')}</div></div><div style="display:flex; gap: 5px;"><button onclick="startManualEdit(${i})" title="Edit" style="background:none; border:none; color:#f1c40f; cursor:pointer;"><i class="fa-solid fa-pencil"></i></button><button onclick="deleteEditorPoint(${i})" title="Delete" style="background:none; border:none; color:#e74c3c; cursor:pointer;"><i class="fa-solid fa-xmark"></i></button></div>`;
        list.appendChild(div);
    });
}
function handleWpDrop(e) {
    if (e.stopPropagation) e.stopPropagation(); const container = document.getElementById('active-route-list'); const rows = [...container.querySelectorAll('.route-item')]; const newArray = []; let newEditIndex = -1;
    rows.forEach((row, newIndex) => { const oldIndex = parseInt(row.dataset.index); newArray.push(editingRouteData[oldIndex]); if (activeEditIndex === oldIndex) { newEditIndex = newIndex; } });
    editingRouteData = newArray; activeEditIndex = newEditIndex; renderEditorPoints(); renderEditorMap();
}
function renderEditorMap() {
    editorLayer.clearLayers(); if (editingRouteData.length === 0) return; const latlngs = editingRouteData.map(p => [p.lat, p.lon]); const color = document.getElementById('save-color').value || "#78aabc"; if (latlngs.length > 1) L.polyline(latlngs, { color: color, weight: 3, dashArray: '5, 5' }).addTo(editorLayer);
    editingRouteData.forEach((pt, i) => {
        const isTgt = pt.type === 'tgt'; const isEditing = (activeEditIndex === i); const markerColor = isEditing ? '#00ff00' : (isTgt ? '#e74c3c' : '#ffffff'); const iconHtml = isTgt ? `<div style="color:${markerColor}; font-size:24px; filter:drop-shadow(0 0 3px black);">🎯</div>` : `<div style="color:${markerColor}; font-size:24px; filter:drop-shadow(0 0 3px black);"><i class="fa-solid fa-location-dot"></i></div>`; const icon = L.divIcon({ className: 'edit-icon', html: iconHtml, iconSize: [24, 24], iconAnchor: [12, 24] });
        const m = L.marker([pt.lat, pt.lon], { icon: icon, draggable: true }).addTo(editorLayer); if (showWpLabels) { m.bindTooltip(`${pt.name}`, { permanent: true, direction: 'right', className: 'airport-label' }); }
        m.on('dragstart', () => { clearTimeout(pressTimer); });
        m.on('dragend', function (event) { const newPos = event.target.getLatLng(); editingRouteData[i].lat = newPos.lat; editingRouteData[i].lon = newPos.lng; renderEditorMap(); renderEditorPoints(); if (activeEditIndex === i) fillManualForm(i); }); m.on('click', () => startManualEdit(i));
    });
}
async function calculateDualAltitudes(lat, lon, val, type) { const elevM = await getGroundElevation(lat, lon); const inputMeters = parseFloat(val); let msl = 0, agl = 0; if (type === 'AGL') { agl = inputMeters; msl = inputMeters + elevM; } else { msl = inputMeters; agl = inputMeters - elevM; } return { msl: Math.round(msl), agl: Math.round(agl) }; }
async function addPoint(lat, lon, alt, altType, type) { let name = (type === 'wp') ? `WP ${wpCounter++}` : `TGT`; const alts = await calculateDualAltitudes(lat, lon, alt, altType); editingRouteData.push({ lat: lat, lon: lon, alt: alt, altType: altType, type: type, name: name, alt_msl: alts.msl, alt_agl: alts.agl }); renderEditorPoints(); renderEditorMap(); }
function addManualPoint() {
    const type = document.getElementById('inp-type').value; const rawAlt = parseFloat(document.getElementById('global-alt').value) || 0; const altMeters = fromDisplayAlt(rawAlt); const altType = document.getElementById('global-alt-type').value; let lat = 0, lon = 0;
    if (settings.coords === 'mgrs') { let val = document.getElementById('inp-mgrs').value.trim().toUpperCase(); const rawMatch = val.match(/^(\d{1,2}[C-X])([A-Z]{2})(\d{5})(\d{5})$/); if (rawMatch) { val = `${rawMatch[1]} ${rawMatch[2]} ${rawMatch[3]} ${rawMatch[4]}`; } const result = LatLongFromMGRSstring(val); if (result && result[0]) { lat = result[1]; lon = result[2]; } else { alert("Invalid MGRS format"); return; } } else { lat = parseDMS(document.getElementById('inp-lat').value); lon = parseDMS(document.getElementById('inp-lon').value); }
    if (lat && lon) addPoint(lat, lon, altMeters, altType, type);
}
function updateManualPoint(index) {
    const type = document.getElementById('inp-type').value; const rawAlt = parseFloat(document.getElementById('global-alt').value) || 0; const altMeters = fromDisplayAlt(rawAlt); const altType = document.getElementById('global-alt-type').value; const newName = document.getElementById('inp-name').value; let newLat = 0, newLon = 0;
    if (settings.coords === 'mgrs') { let val = document.getElementById('inp-mgrs').value.trim().toUpperCase(); const rawMatch = val.match(/^(\d{1,2}[C-X])([A-Z]{2})(\d{5})(\d{5})$/); if (rawMatch) val = `${rawMatch[1]} ${rawMatch[2]} ${rawMatch[3]} ${rawMatch[4]}`; const result = LatLongFromMGRSstring(val); if (result && result[0]) { newLat = result[1]; newLon = result[2]; } else { alert("Invalid MGRS format"); return; } } else { newLat = parseDMS(document.getElementById('inp-lat').value); newLon = parseDMS(document.getElementById('inp-lon').value); }
    if (!newLat || !newLon) { alert("Invalid Coordinates"); return; } editingRouteData[index] = { name: newName, lat: newLat, lon: newLon, alt: altMeters, altType: altType, type: type }; closeManualInput();
}
function startManualEdit(index) { activeEditIndex = index; const pt = editingRouteData[index]; document.getElementById('manual-form').style.display = 'block'; document.getElementById('inp-name').value = pt.name; document.getElementById('inp-type').value = pt.type; document.getElementById('global-alt').value = pt.alt; document.getElementById('global-alt-type').value = pt.altType || 'MSL'; fillManualForm(index); const btn = document.getElementById('btn-add-point'); btn.innerText = "Update Point"; btn.onclick = () => updateManualPoint(index); renderEditorMap(); }
function fillManualForm(index) { const pt = editingRouteData[index]; const displayVal = toDisplayAlt(pt.alt); document.getElementById('global-alt').value = displayVal; if (settings.coords === 'mgrs') { try { document.getElementById('inp-mgrs').value = MGRSString(pt.lat, pt.lon); } catch (e) { } } else { document.getElementById('inp-lat').value = toDmsInput(pt.lat, true); document.getElementById('inp-lon').value = toDmsInput(pt.lon, false); } }
function closeManualInput() { activeEditIndex = -1; document.getElementById('manual-form').style.display = 'none'; if (typeof closeKeyboard === 'function') closeKeyboard(); const btn = document.getElementById('btn-add-point'); if (btn) { btn.innerText = "Add Point"; btn.onclick = addManualPoint; } renderEditorMap(); renderEditorPoints(); }
function deleteEditorPoint(i) { editingRouteData.splice(i, 1); renderEditorPoints(); }
function toggleMeasureTool() { distMode = !distMode; document.getElementById('btn-measure').classList.toggle('active', distMode); if (distMode) { document.getElementById('map').style.cursor = 'crosshair'; setClickMode('none'); } else { document.getElementById('map').style.cursor = 'default'; measureLayer.clearLayers(); distStart = null; } }
function drawMeasureLine(start, end, isFinal, isRemote = false) {
    if (!isFinal) measureLayer.clearLayers();
    L.circleMarker(start, { radius: 4, color: '#6C0E42' }).addTo(measureLayer); if (isFinal) L.circleMarker(end, { radius: 4, color: '#6C0E42' }).addTo(measureLayer); L.polyline([start, end], { color: '#6C0E42', weight: 1, dashArray: isFinal ? null : '5, 5' }).addTo(measureLayer);
    const distMeters = map.distance(start, end); let distStr = (settings.distUnit === 'nm') ? (distMeters * 0.000539957).toFixed(2) + " nm" : (distMeters / 1000).toFixed(2) + " km";
    L.marker(end, { icon: L.divIcon({ className: 'measure-label', html: distStr, iconSize: [60, 20] }) }).addTo(measureLayer);
    const lat1 = start.lat * Math.PI / 180; const lat2 = end.lat * Math.PI / 180; const dLon = (end.lng - start.lng) * Math.PI / 180;
    const y = Math.sin(dLon) * Math.cos(lat2); const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon); let brng = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
    L.marker(start, { icon: L.divIcon({ className: 'bearing-label', html: Math.round(brng) + "°T", iconSize: [40, 20], iconAnchor: [40, 0] }) }).addTo(measureLayer);
    if (!isRemote) { socket.emit('sync_measurement', { start: start, end: end, isFinal: isFinal }); }
}

// --- POI LOGIC ---
function createPoi(lat, lon, name, isUserPos) {
    if (!activeMissionName && !isUserPos) { showToast("Select Mission First"); return; }
    const color = isUserPos ? '#00ff00' : '#ffff00'; const label = isUserPos ? "My Pos" : (name || "Mark"); const sidc = isUserPos ? "SFGPU-------" : "SHGPU-------";
    allPois.push({ lat, lon, name: label, color: color, sidc: sidc }); renderPois(); setClickMode('none'); if (!isUserPos) saveActiveMission(); if (activeMissionName) renderBrowserList(); renderPoiList();
}
function renderPois() {
    poiLayer.clearLayers(); threatLayer.clearLayers();
    const showThreats = document.getElementById('chk-vis-threats') ? document.getElementById('chk-vis-threats').checked : true; const unitMult = (settings.distUnit === 'km') ? 1000 : 1852; const showPois = document.getElementById('chk-vis-poi') ? document.getElementById('chk-vis-poi').checked : true;
    const zoom = map.getZoom();
    let showAsDot = false;
    let iconSize = 28;

    // Sizing Logic (Match Ground Units)
    if (zoom <= 9) {
        showAsDot = true;
        iconSize = 28;
    } else if (zoom <= 11) {
        iconSize = Math.round(28 * 0.6); // ~17px
    } else if (zoom === 12) {
        iconSize = 28; // 100%
    } else {
        iconSize = 36; // Big (Match POI default)
    }

    allPois.forEach((poi, i) => {
        if (!showPois) return; const color = poi.color || '#ffff00'; const center = [poi.lat, poi.lon];
        if (showThreats && poi.threatVisible !== false) {
            if (poi.threatDetectEnabled && poi.threatDetect > 0) { L.circle(center, { radius: poi.threatDetect * unitMult, color: color, weight: 1, fill: false, dashArray: '10, 5, 2, 5', opacity: 0.8, interactive: false }).addTo(threatLayer); }
            if (poi.threatDeadlyEnabled && poi.threatDeadly > 0) { L.circle(center, { radius: poi.threatDeadly * unitMult, color: color, weight: 1, fill: true, fillColor: color, fillOpacity: threatFillOpacity, dashArray: '10, 10', opacity: 0.8, interactive: false }).addTo(threatLayer); }
        }
        let icon;

        if (showAsDot) {
            icon = L.divIcon({ className: 'poi-dot', html: `<div style="width:6px; height:6px; background:${color}; border-radius:50%; border:1px solid #000; box-shadow: 0 0 6px #cb6500;"></div>`, iconSize: [6, 6], iconAnchor: [3, 3] });
        } else {
            if (!poi.sidc || poi.sidc === 'PIN') {
                // Scale Pin? - Let's keep Pin readable but maybe smaller at lower zooms if not dot.
                // For now, keep pin somewhat standard or scale it slightly?
                // User asked for "same zoom level sizes", implies 17px at zoom 10.
                let pinSize = (iconSize < 28) ? 24 : 32;
                icon = L.divIcon({ className: 'poi-icon', html: `<i class="fa-solid fa-map-pin" style="color:${poi.color}; font-size:${pinSize}px; filter:drop-shadow(0 3px 2px rgba(0,0,0,0.5)) drop-shadow(0 0 6px #cb6500);"></i>`, iconSize: [pinSize, pinSize], iconAnchor: [pinSize / 2, pinSize] });
            }
            else {
                try {
                    if (typeof ms !== 'undefined') {
                        const symb = new ms.Symbol(poi.sidc, { size: iconSize, colorMode: "Light" }).asCanvas();
                        icon = L.divIcon({ className: 'poi-icon', html: `<img src="${symb.toDataURL()}" style="width:100%; height:100%; filter: drop-shadow(0 0 6px #cb6500);">`, iconSize: [iconSize, iconSize], iconAnchor: [iconSize / 2, iconSize / 2] });
                    } else { throw new Error("No Lib"); }
                } catch (e) { icon = L.divIcon({ className: 'poi-icon', html: '📌', iconSize: [24, 24] }); }
            }
        }
        const m = L.marker(center, { icon: icon, draggable: true }).addTo(poiLayer); m.bindTooltip(poi.name, { direction: 'top', offset: [0, -35], permanent: showWpLabels, className: 'airport-label' });
        m.on('dragstart', () => { clearTimeout(pressTimer); }); // Prevent long-press trigger
        m.on('dragend', (e) => { const pos = e.target.getLatLng(); allPois[i].lat = pos.lat; allPois[i].lon = pos.lng; renderPois(); saveActiveMission(); }); m.on('click', () => openPoiModal(i));
    });
}
function markCurrentPosition() { if (lastTelemetry && lastTelemetry.lat) createPoi(lastTelemetry.lat, lastTelemetry.lon, "My Pos", true); else showToast("No GPS Data"); }
async function openPoiModal(index) {
    activePoiIndex = index; const poi = allPois[index];
    document.getElementById('poi-name').value = poi.name; document.getElementById('poi-color').value = poi.color || '#ffff00';
    document.getElementById('chk-poi-threat-detect').checked = (poi.threatDetectEnabled !== undefined) ? poi.threatDetectEnabled : false; document.getElementById('chk-poi-threat-deadly').checked = (poi.threatDeadlyEnabled !== undefined) ? poi.threatDeadlyEnabled : false; updatePoiThreatVisBtn(poi.threatVisible !== false);
    let currentCode = poi.sidc || "PIN"; let affil = 'F'; if (currentCode.length > 10) affil = currentCode.charAt(1); document.getElementById('poi-affil').value = affil; renderPoiSelector();
    let partialToMatch = (currentCode === 'PIN') ? 'PIN' : currentCode.substring(4, 11); document.querySelectorAll('.icon-opt').forEach(d => { d.classList.remove('selected'); d.style.background = ""; d.style.borderColor = ""; d.style.color = ""; });
    const targetBtn = document.querySelector(`.icon-opt[data-code="${partialToMatch}"]`); selectPoiIcon(partialToMatch, targetBtn, 0, 0);
    const savedDetect = poi.threatDetect || lastThreatDetect || 0; const savedDeadly = poi.threatDeadly || lastThreatDeadly || 0; document.getElementById('poi-threat-detect').value = savedDetect; document.getElementById('poi-threat-deadly').value = savedDeadly;
    const coordStr = formatCoordDisplay(poi.lat, poi.lon); document.getElementById('poi-info-coord').innerText = coordStr.replace('\n', ', '); const elBox = document.getElementById('poi-info-alt'); elBox.innerText = "Fetching...";
    const elevM = await getGroundElevation(poi.lat, poi.lon); let finalAlt = elevM; let unitStr = "m"; if (settings.altUnit === 'ft') { finalAlt = elevM * 3.28084; unitStr = "ft"; } elBox.innerText = `${Math.round(finalAlt)} ${unitStr}`;
    document.getElementById('poi-btn-container').innerHTML = `<button class="btn-full" onclick="activatePoiFromModal(${index})" style="background:#18611c; color:#aaa;">Navigate To</button><button class="btn-full" onclick="savePoiEdit()" style="color:#aaa">Save</button><button class="btn-full" onclick="deletePoi()" style="background:#5c2121; color:#aaa;">Delete</button><button class="btn-full" onclick="closePoiModal()" style="background:#555; color:#aaa;">Cancel</button>`;
    document.getElementById('poi-modal').style.display = 'flex';
}
function activatePoiFromModal(index) { socket.emit('activate_poi_route', { index: index }); activeRouteName = "Visual Targets"; activeRouteData = JSON.parse(JSON.stringify(allPois)); activeRouteData.forEach((p, i) => { p.name = `T${i + 1}`; p.type = 'poi'; }); activeWpIndex = index; updateMiniPanel(); renderMapRoutes(); closePoiModal(); showToast(`Tracking T${index + 1}`); }
function renderPoiList() {
    const list = document.getElementById('poi-list-container'); list.innerHTML = ""; if (allPois.length === 0) { list.innerHTML = `<div style="text-align:center; padding:20px; color:#555;">No Visual Targets</div>`; return; }
    allPois.forEach((poi, i) => {
        const isActiveTarget = (activeRouteName === "Visual Targets" && activeWpIndex === i); const rawName = poi.name || "Mark"; const div = document.createElement('div'); div.className = `saved-route-item ${isActiveTarget ? 'is-active' : ''}`; div.setAttribute('draggable', 'true'); div.dataset.originId = i; div.style.display = 'flex'; div.style.alignItems = 'center'; div.style.padding = '5px'; div.style.gap = '0px';
        div.addEventListener('dragstart', () => div.classList.add('dragging')); div.addEventListener('dragend', () => { div.classList.remove('dragging'); finishPoiSort(); });
        const coordStr = formatCoordDisplay(poi.lat, poi.lon).replace(/\n/g, ' ');
        div.innerHTML = `<div style="width:20px; min-width:20px; text-align:center; font-weight:bold; color:${isActiveTarget ? '#0f0' : '#78aabc'}; font-size:11px; pointer-events:none;">T${i + 1}</div><div style="flex-grow:1; width:0; display:flex; align-items:center; justify-content:space-between; padding:0 5px; pointer-events:none; overflow:hidden;"><span style="font-weight:bold; font-size:13px; color:#d1e3ea; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-right:5px;">${rawName}</span><span style="font-family:'Consolas', monospace; color:#aaa; font-size:11px; white-space:nowrap; flex-shrink:0;">${coordStr}</span></div><button class="list-btn" style="width:30px;" onclick="activatePoiFromModal(${i})" title="Set Active"><i class="fa-solid fa-crosshairs"></i></button><button class="list-btn delete" style="width:30px;" onclick="activePoiIndex=${i}; deletePoi();" title="Delete"><i class="fa-solid fa-trash"></i></button>`;
        list.appendChild(div);
    });
}
const poiContainer = document.getElementById('poi-list-container'); poiContainer.addEventListener('dragover', e => { e.preventDefault(); const afterElement = getDragAfterElement(poiContainer, e.clientY, '.saved-route-item'); const draggable = document.querySelector('.dragging'); if (!draggable) return; if (afterElement == null) poiContainer.appendChild(draggable); else poiContainer.insertBefore(draggable, afterElement); });
function finishPoiSort() { const listItems = document.querySelectorAll('#poi-list-container .saved-route-item'); const newPois = []; let newActiveIndex = -1; listItems.forEach((item, newIndex) => { const originalIndex = parseInt(item.dataset.originId); newPois.push(allPois[originalIndex]); if (activeWpIndex === originalIndex) newActiveIndex = newIndex; }); allPois = newPois; if (activeRouteName === "Visual Targets") { activeRouteData = JSON.parse(JSON.stringify(allPois)); activeRouteData.forEach((p, i) => { p.name = `T${i + 1}`; p.type = 'poi'; }); activeWpIndex = newActiveIndex; updateServerNav(); } saveActiveMission(); renderPoiList(); renderMapRoutes(); }
function savePoiEdit() {
    if (activePoiIndex === -1) return; const name = document.getElementById('poi-name').value; let finalSidc = 'PIN'; let color = document.getElementById('poi-color').value; const tDetect = parseFloat(document.getElementById('poi-threat-detect').value) || 0; const tDeadly = parseFloat(document.getElementById('poi-threat-deadly').value) || 0;
    allPois[activePoiIndex].threatDetect = tDetect; allPois[activePoiIndex].threatDeadly = tDeadly; allPois[activePoiIndex].threatDetectEnabled = document.getElementById('chk-poi-threat-detect').checked; allPois[activePoiIndex].threatDeadlyEnabled = document.getElementById('chk-poi-threat-deadly').checked;
    if (tDetect > 0) lastThreatDetect = tDetect; if (tDeadly > 0) lastThreatDeadly = tDeadly;
    if (selectedPoiSidcPartial !== 'PIN') { const aff = document.getElementById('poi-affil').value; let dim = 'G'; if (selectedPoiSidcPartial.startsWith('M')) dim = 'A'; if (selectedPoiSidcPartial.startsWith('N')) dim = 'S'; finalSidc = `S${aff}${dim}P${selectedPoiSidcPartial}`; if (aff === 'H') color = '#e74c3c'; else if (aff === 'F') color = '#3498db'; else if (aff === 'N') color = '#2ecc71'; else color = '#f1c40f'; }
    allPois[activePoiIndex].name = name; allPois[activePoiIndex].color = color; allPois[activePoiIndex].sidc = finalSidc; closePoiModal(); renderPois(); saveActiveMission(); renderBrowserList(); renderPoiList();
}
function deletePoi() { if (activePoiIndex === -1) return; allPois.splice(activePoiIndex, 1); closePoiModal(); renderPois(); saveActiveMission(); renderBrowserList(); renderPoiList(); }
function closePoiModal() { document.getElementById('poi-modal').style.display = 'none'; if (typeof closeKeyboard === 'function') closeKeyboard(); activePoiIndex = -1; }

const poiPresets = [{ label: "SAM-L", code: "UCDS--", det: 45, dead: 30, desc: "Long Range SAM" }, { label: "SAM-M", code: "UCDM--", det: 25, dead: 18, desc: "Med Range SAM" }, { label: "SAM-S", code: "UCDT--", det: 8, dead: 5, desc: "Short Range SAM" }, { label: "AAA", code: "UCDG--", det: 4, dead: 2, desc: "AAA" }, { label: "MANPAD", code: "UCIM--", det: 4, dead: 2.5, desc: "Manpad" }, { label: "Armor", code: "UCA---", det: 0, dead: 2, desc: "Tank" }, { label: "Recon", code: "UCR---", det: 0, dead: 0, desc: "Recon" }, { label: "Arty", code: "UCF---", det: 0, dead: 15, desc: "Arty" }, { label: "SCUD", code: "UCFM--", det: 0, dead: 60, desc: "SCUD" }, { label: "Inf", code: "UCI---", det: 0, dead: 0.5, desc: "Inf" }, { label: "Ship", code: "IBN---", det: 60, dead: 30, desc: "Naval" }, { label: "Util", code: "UCV---", det: 0, dead: 0, desc: "Utility" }, { label: "Fighter", code: "MF----", det: 40, dead: 20, desc: "Fighter" }, { label: "Helo", code: "MH----", det: 10, dead: 5, desc: "Helis" }, { label: "Pin", code: "PIN", det: 0, dead: 0, desc: "Marker" }];

function renderPoiSelector() { const container = document.querySelector('.icon-grid'); container.innerHTML = ""; const affilEl = document.getElementById('poi-affil'); const affil = affilEl ? affilEl.value : 'H'; poiPresets.forEach(p => { const div = document.createElement('div'); div.className = "icon-opt"; div.title = p.desc || p.label; div.dataset.code = p.code; div.onclick = function () { selectPoiIcon(p.code, this, p.det, p.dead); }; if (p.code === 'PIN') { div.innerHTML = `<div style="font-size: 24px; line-height:24px; margin-bottom:-2px;">📍</div><div>${p.label}</div>`; } else { let base = "S" + affil; if (p.code.startsWith('M')) base += "A"; else if (p.code.startsWith('N')) base += "S"; else base += "G"; const fullSidc = base + "P" + p.code; try { const sym = new ms.Symbol(fullSidc, { size: 30, frame: false, icon: true }).asCanvas(); div.appendChild(sym); const lbl = document.createElement('div'); lbl.innerText = p.label; lbl.style.marginTop = "0px"; div.appendChild(lbl); } catch (e) { div.innerText = p.label; } } container.appendChild(div); }); }
function selectPoiIcon(sidcPartial, el, defaultDetect, defaultDeadly) { selectedPoiSidcPartial = sidcPartial; document.querySelectorAll('.icon-opt').forEach(d => { d.classList.remove('selected'); d.style.background = ""; d.style.borderColor = ""; d.style.color = ""; }); if (el) { el.classList.add('selected'); el.style.background = "rgba(120, 170, 188, 0.15)"; el.style.borderColor = "#78aabc"; el.style.color = "#d1e3ea"; } const isPin = (sidcPartial === 'PIN'); const affilBox = document.getElementById('box-affil-select'); const colorBox = document.getElementById('box-color-picker'); if (affilBox) affilBox.style.display = isPin ? 'none' : 'block'; if (colorBox) colorBox.style.display = isPin ? 'block' : 'none'; const detInput = document.getElementById('poi-threat-detect'); const deadInput = document.getElementById('poi-threat-deadly'); const detChk = document.getElementById('chk-poi-threat-detect'); const deadChk = document.getElementById('chk-poi-threat-deadly'); if (detInput && deadInput) { if (defaultDetect !== undefined) detInput.value = defaultDetect; if (defaultDeadly !== undefined) deadInput.value = defaultDeadly; if (detChk) detChk.checked = (defaultDetect > 0); if (deadChk) deadChk.checked = (defaultDeadly > 0); if (typeof lastThreatDetect !== 'undefined') lastThreatDetect = defaultDetect; if (typeof lastThreatDeadly !== 'undefined') lastThreatDeadly = defaultDeadly; } }

// --- MAP EVENTS ---
function toggleFollow() { followMode = !followMode; document.getElementById('btn-follow').classList.toggle('active', followMode); }
function toggleHeadingUp() { headingUp = !headingUp; document.getElementById('btn-hdg-up').classList.toggle('active', headingUp); if (!headingUp) document.getElementById('map').style.transform = 'translate(0,0) rotate(0deg)'; }
map.on('mousedown', function (e) { pressTimer = setTimeout(() => { createPoi(e.latlng.lat, e.latlng.lng, "Mark", false); }, 800); }); map.on('mouseup', function (e) { clearTimeout(pressTimer); }); map.on('dragstart', () => { clearTimeout(pressTimer); if (followMode) toggleFollow(); });
map.on('mousemove', function (e) { if (distMode && distStart) { drawMeasureLine(distStart, e.latlng, false); } const pill = document.getElementById('val-cursor'); if (settings.coords === 'mgrs') { try { pill.innerText = MGRSString(e.latlng.lat, e.latlng.lng); } catch (err) { pill.innerText = "Err"; } } else { const toDms = (val, isLat) => { const dir = val >= 0 ? (isLat ? 'N' : 'E') : (isLat ? 'S' : 'W'); const abs = Math.abs(val); const d = Math.floor(abs); const m = Math.floor((abs - d) * 60); const s = ((abs - d - m / 60) * 3600).toFixed(2); return `${dir} ${String(d).padStart(isLat ? 2 : 3, '0')}° ${String(m).padStart(2, '0')}' ${s}"`; }; pill.innerText = `${toDms(e.latlng.lat, true)}  ${toDms(e.latlng.lng, false)}`; } });
map.on('click', async function (e) { if (distMode) { if (!distStart) { distStart = e.latlng; measureLayer.clearLayers(); L.circleMarker(distStart, { radius: 4, color: '#6C0E42' }).addTo(measureLayer); } else { drawMeasureLine(distStart, e.latlng, true); distStart = null; } return; } if (clickMode === 'poi') { createPoi(e.latlng.lat, e.latlng.lng, "Mark", false); return; } if (clickMode === 'wp' || clickMode === 'tgt') { let userInput = parseFloat(document.getElementById('global-alt').value) || 0; let altMeters = fromDisplayAlt(userInput); let altType = document.getElementById('global-alt-type').value; if (clickMode === 'tgt') { const groundMeters = await getGroundElevation(e.latlng.lat, e.latlng.lng); altMeters = Math.round(groundMeters); altType = 'MSL'; } addPoint(e.latlng.lat, e.latlng.lng, altMeters, altType, clickMode); } });
function scheduleViewSave() { if (isProgrammaticMove) return; if (mapMoveTimer) clearTimeout(mapMoveTimer); mapMoveTimer = setTimeout(() => { saveMapSettings(); }, 1000); }
map.on('moveend', () => { scheduleViewSave(); updateGrid(); updateMgrsGrid(); });
map.on('zoomend', () => {
    scheduleViewSave();
    updateGrid();
    scheduleViewSave();
    updateGrid();
    updateMgrsGrid();
    renderPois(); // Re-render POIs for dynamic sizing
    // Re-render theater units with new zoom-dependent sizing
    if (theaterUnits && Object.keys(theaterUnits).length > 0) {
        const zoom = map.getZoom();
        for (let id in theaterUnits) {
            const unitData = theaterUnits[id];
            if (unitData && unitData.marker) {
                // Trigger re-render by removing and recreating markers
                // This will be handled by the next theater_state update
                // For now, just mark for update
                unitData.needsUpdate = true;
            }
        }
    }
});

// --- AIRPORTS & SOCKETS ---
map.createPane('stationPane'); map.getPane('stationPane').style.zIndex = 550;
function renderAirports() {
    airportLayer.clearLayers(); airportMarkers = {}; if (!allAirportsData) return;
    const neutralColor = document.getElementById('col-air-neutral') ? document.getElementById('col-air-neutral').value : '#aaaaaa'; const altUnit = document.getElementById('opt-alt-unit') ? document.getElementById('opt-alt-unit').value : 'ft';
    Object.keys(allAirportsData).forEach(region => {
        const list = allAirportsData[region]; list.forEach(ap => {
            const icon = L.divIcon({ className: 'airport-icon', html: `<i class="fa-solid fa-chess-rook" style="color:${neutralColor};"></i>`, iconSize: [20, 20], iconAnchor: [10, 10] });
            const mk = L.marker([ap.lat, ap.lon], { icon: icon, pane: 'stationPane' });
            let dispAlt = ap.alt; if (altUnit === 'ft') dispAlt = Math.round(ap.alt * 3.28084);
            const detailHtml = `<div style="min-width:200px;"><div style="font-weight:bold; color:#78aabc; border-bottom:1px solid #444; margin-bottom:5px;">${ap.name}</div><div style="font-size:11px; display:grid; grid-template-columns: 1fr 1fr; gap:5px;"><span><i class="fa-solid fa-road"></i> ${ap.runway}</span><span><i class="fa-solid fa-compass"></i> ${ap.rwyHeading}°</span><span><i class="fa-solid fa-wifi"></i> ${ap.atc} MHz</span><span><i class="fa-solid fa-tower-broadcast"></i> ${ap.tacan}</span><span style="color:#aaa;">ALT: ${dispAlt} ${altUnit}</span><span style="color:#aaa;">WP (FC3): ${ap.id}</span></div></div>`;
            mk.bindPopup(detailHtml); mk.bindTooltip(ap.name, { permanent: showWpLabels, direction: 'right', className: 'airport-label', offset: [10, 0] }); mk.addTo(airportLayer); airportMarkers[ap.name] = mk;
        });
    });
}
function updateAirportStatus() {
    const isLive = document.getElementById('chk-live-air').checked; const neutralColor = document.getElementById('col-air-neutral') ? document.getElementById('col-air-neutral').value : '#aaaaaa';
    if (!isLive) { for (let name in airportMarkers) { const mk = airportMarkers[name]; const iconHtml = `<i class="fa-solid fa-chess-rook" style="color:${neutralColor};"></i>`; mk.setIcon(L.divIcon({ className: 'airport-icon', html: iconHtml, iconSize: [20, 20], iconAnchor: [10, 10] })); } }
}
async function loadAirports() { try { const res = await fetch('/api/airports'); allAirportsData = await res.json(); renderAirports(); } catch (e) { console.log("Airport load failed:", e); } }

// --- SOCKET EVENT HANDLERS ---

// Metadata: Player context (ID, Name)
socket.on('metadata', function (data) {
    if (data && data.unit_id) {
        myUnitId = String(data.unit_id);
        console.log("👤 Identity Confirmed. Unit ID:", myUnitId);
    }
});

// Phonebook: Player roster updates (Unit ID → Player Name)
socket.on('phonebook', function (data) {
    console.log("📞 PHONEBOOK UPDATE:");
    console.log("  Player count:", Object.keys(data).length);

    phonebook = data;

    // Log each player
    for (let unitId in data) {
        console.log(`  Unit ${unitId}: ${data[unitId]}`);
    }
});

// Theater State: Position/status updates for all units
socket.on('theater_state', function (data) {
    if (!data) return;

    // Debug logging with separation
    console.log("=".repeat(60));
    console.log("🎭 THEATER STATE UPDATE:");
    console.log("  Unit count:", data.length);
    if (data.length > 0) {
        console.log("  Sample unit:", data[0]);
        console.log("  Fields:", Object.keys(data[0]));
    }

    // Debug: Check for human players
    const humanUnits = data.filter(u => phonebook.hasOwnProperty(u.id));
    if (humanUnits.length > 0) {
        console.log("  Human players detected:", humanUnits.length);
        humanUnits.forEach(u => {
            console.log(`    Unit ${u.id} (${phonebook[u.id]}): type_level2=${u.type_level2}`);
        });
    }
    console.log("=".repeat(60));

    const isLiveAirports = document.getElementById('chk-live-air') ? document.getElementById('chk-live-air').checked : false;
    const zoom = map.getZoom();

    // Mark all existing units as not updated
    for (let id in theaterUnits) {
        theaterUnits[id].updated = false;
    }

    data.forEach(u => {
        // Filter Owner (Avoid Duplicate with PlaneMarker)
        if (myUnitId && String(u.id) === myUnitId) return;

        // Coalition filtering
        const isRed = (u.coalition === 1);
        const isBlue = (u.coalition === 2);
        const isNeutral = (!isRed && !isBlue);

        const showRed = document.getElementById('chk-vis-unit-red') ? document.getElementById('chk-vis-unit-red').checked : true;
        const showBlue = document.getElementById('chk-vis-unit-blue') ? document.getElementById('chk-vis-unit-blue').checked : true;
        const showNeutral = document.getElementById('chk-vis-unit-neutral') ? document.getElementById('chk-vis-unit-neutral').checked : true;

        if (isRed && !showRed) return;
        if (isBlue && !showBlue) return;
        if (isNeutral && !showNeutral) return;

        // Determine coalition color
        let color = '#aaaaaa';
        if (isRed) color = '#e74c3c';
        else if (isBlue) color = '#3498db';

        // Handle airports separately (live airport coloring)
        if (airportMarkers[u.name]) {
            if (isLiveAirports) {
                const mk = airportMarkers[u.name];
                const iconHtml = `<i class="fa-solid fa-chess-rook" style="color:${color}; text-shadow:0 0 5px ${color};"></i>`;
                mk.setIcon(L.divIcon({ className: 'airport-icon', html: iconHtml, iconSize: [20, 20], iconAnchor: [10, 10] }));
            }
            return;
        }

        if (!u.lat || !u.long) return;

        // Determine unit category based on type_level1
        // Level 1: 1=Air, 2=Ground, 3=Navy, 5=Static (4=Weapon, 6=Destroyed - ignored)
        let category = 'unknown';
        if (u.type_level1 === 1) {
            category = 'air';
        } else if (u.type_level1 === 2) {
            category = 'ground';
        } else if (u.type_level1 === 3) {
            category = 'naval';
        } else if (u.type_level1 === 5) {
            category = 'static';
        }

        // Unit type filtering
        const showAir = document.getElementById('chk-vis-unit-air') ? document.getElementById('chk-vis-unit-air').checked : true;
        const showGround = document.getElementById('chk-vis-unit-ground') ? document.getElementById('chk-vis-unit-ground').checked : true;
        const showNaval = document.getElementById('chk-vis-unit-naval') ? document.getElementById('chk-vis-unit-naval').checked : true;
        const showStatic = document.getElementById('chk-vis-unit-static') ? document.getElementById('chk-vis-unit-static').checked : true;

        if (category === 'air' && !showAir) return;
        if (category === 'ground' && !showGround) return;
        if (category === 'naval' && !showNaval) return;
        if (category === 'static' && !showStatic) return;

        // Check if this is a player (ensure ID is string to match phonebook keys)
        const unitIdStr = String(u.id);
        const isPlayer = phonebook.hasOwnProperty(unitIdStr);
        const playerName = isPlayer ? phonebook[unitIdStr] : null;

        // Determine rendering parameters based on zoom and category
        let showAsDot = false;
        let iconSize = 32; // Base size for player icons

        if (isPlayer) {
            // Player units: zoom 0-6 dots, 7-9 80%, 10+ 100% (32px base)
            if (zoom <= 6) {
                showAsDot = true;
            } else if (zoom <= 9) {
                iconSize = Math.round(32 * 0.8); // ~26px
            } else {
                iconSize = 32; // 100%
            }
        } else if (category === 'air' || category === 'naval') {
            // AI Air/Naval:
            // Zoom 0-6: Dots
            // Zoom 7-9: 60% (~17px)
            // Zoom 10-11: 80% (~22px)
            // Zoom 12+: 36px
            if (zoom <= 6) {
                showAsDot = true;
                iconSize = 28;
            } else if (zoom <= 9) {
                iconSize = Math.round(28 * 0.6); // ~17px
            } else if (zoom <= 11) {
                iconSize = Math.round(28 * 0.8); // ~22px
            } else {
                iconSize = 36;
            }
        } else {
            // AI Ground/Static: 
            // Zoom 0-9: Dots
            // Zoom 10-11: 60% (17px)
            // Zoom 12: 100% (28px) 
            // Zoom 13+: Match POI (36px)
            if (zoom <= 9) {
                showAsDot = true;
                iconSize = 28;
            } else if (zoom <= 11) {
                iconSize = Math.round(28 * 0.6); // ~17px
            } else if (zoom === 12) {
                iconSize = 28; // 100%
            } else {
                iconSize = 36; // Big (Match POI)
            }
        }

        // Update or create marker
        if (theaterUnits[u.id]) {
            // Unit already exists, update position
            theaterUnits[u.id].marker.setLatLng([u.lat, u.long]);
            theaterUnits[u.id].updated = true;
            theaterUnits[u.id].data = u; // Store latest data

            // ROTATION UPDATE (Air Units)
            if (category === 'air' || isPlayer) {
                const el = theaterUnits[u.id].marker.getElement();
                if (el) {
                    const rotatable = el.querySelector('.rotatable-icon');
                    if (rotatable) {
                        const hdgDeg = (u.heading || 0) * (180 / Math.PI);
                        rotatable.style.transform = `rotate(${hdgDeg}deg)`;
                    }
                }
            }

            // Update icon if zoom level changed (check if current marker type matches required type)
            const currentIsDot = theaterUnits[u.id].isDot;
            if (currentIsDot !== showAsDot || theaterUnits[u.id].iconSize !== iconSize) {
                // Need to recreate marker with new style
                unitLayer.removeLayer(theaterUnits[u.id].marker);
                theaterUnits[u.id].marker = createUnitMarker(u, color, category, showAsDot, iconSize, isPlayer, playerName);
                theaterUnits[u.id].isDot = showAsDot;
                theaterUnits[u.id].iconSize = iconSize;
            }
        } else {
            // New unit, create marker
            const marker = createUnitMarker(u, color, category, showAsDot, iconSize, isPlayer, playerName);
            theaterUnits[u.id] = { marker: marker, updated: true, isDot: showAsDot, iconSize: iconSize, data: u };
        }
    });

    // Remove units that were not updated (no longer in data)
    for (let id in theaterUnits) {
        if (!theaterUnits[id].updated) {
            if (unitLayer.hasLayer(theaterUnits[id].marker)) {
                unitLayer.removeLayer(theaterUnits[id].marker);
            }
            delete theaterUnits[id];
        }
    }

    // Refresh threats if enabled
    renderTheaterThreats();
});

// Helper to determine threat ranges based on unit type
function getUnitRanges(unit) {
    // Default: No threat
    let ranges = { det: 0, dead: 0 };

    // Only Ground (2) and Navy (3) usually have fixed ranges we care about here
    // Air (1) is too dynamic, Static (5) is usually benign unless AAA
    if (unit.type_level1 === 2) { // Ground
        if (unit.type_level2 === 16) { // SAM
            if (unit.type_level3 === 102) { ranges = { det: 100, dead: 75 }; } // Long Range (S-300 etc) - approx
            else if (unit.type_level3 === 27) { ranges = { det: 45, dead: 35 }; } // Med Range
            else if (unit.type_level3 === 26) { ranges = { det: 25, dead: 15 }; } // Med/Short
            else { ranges = { det: 30, dead: 20 }; } // Generic
        }
        else if (unit.type_level2 === 8) { // Vehicles
            if (unit.type_level3 === 27) { ranges = { det: 10, dead: 5 }; } // SR SAM / Avenger
            else if (unit.type_level3 === 26) { ranges = { det: 5, dead: 3 }; } // SPAAG
        }
        else if (unit.type_level2 === 20 && unit.type_level3 === 27) { // MANPADS
            ranges = { det: 6, dead: 4 };
        }
        else if (unit.type_level2 === 17) { // Tanks - visual range
            ranges = { det: 0, dead: 2.5 };
        }
    }
    else if (unit.type_level1 === 3) { // Navy
        // Ships - varied
        ranges = { det: 50, dead: 30 };
    }

    return ranges;
}

// Theater Threat Ring Rendering
let theaterThreatLayer = L.layerGroup().addTo(map);

function renderTheaterThreats() {
    theaterThreatLayer.clearLayers();

    const show = document.getElementById('chk-vis-theater-threats') ? document.getElementById('chk-vis-theater-threats').checked : false;
    if (!show) return;

    const rng = document.getElementById('rng-theater-threat-opacity');
    let rawOpacity = rng ? parseFloat(rng.value) : 10;
    if (isNaN(rawOpacity)) rawOpacity = 10;
    const opacity = rawOpacity / 100.0;
    const unitMult = (settings.distUnit === 'km') ? 1000 : 1852;

    for (let id in theaterUnits) {
        const u = theaterUnits[id].data;
        if (!u) continue;

        // Determine ranges
        const ranges = getUnitRanges(u);
        if (ranges.det === 0 && ranges.dead === 0) continue;

        // Color match
        let color = '#aaaaaa';
        if (u.coalition === 1) color = '#e74c3c';
        else if (u.coalition === 2) color = '#3498db';

        const center = [u.lat, u.long];

        // Draw Detection (Dashed lines, no fill)
        if (ranges.det > 0) {
            L.circle(center, {
                radius: ranges.det * unitMult,
                color: color,
                weight: 1,
                fill: false,
                dashArray: '10, 5',
                opacity: 0.6,
                interactive: false
            }).addTo(theaterThreatLayer);
        }

        // Draw Deadly (Solid lines, fill based on opacity)
        if (ranges.dead > 0) {
            L.circle(center, {
                radius: ranges.dead * unitMult,
                color: color,
                weight: 1,
                fill: (opacity > 0.05),
                fillColor: color,
                fillOpacity: opacity,
                dashArray: null,
                opacity: 0.8,
                interactive: false
            }).addTo(theaterThreatLayer);
        }
    }
}
// Helper to clean unit labels (User Request: Replace _ with space)
function cleanUnitLabel(text) {
    if (!text) return "";
    return String(text).replace(/_/g, ' ');
}

// Helper function to create unit marker based on rendering parameters
function createUnitMarker(unit, color, category, showAsDot, iconSize, isPlayer, playerName) {
    // PREPARE LABELS
    // 1. Get raw string (Player Name or Unit Type)
    // User Update: AI = unit.name, Player = username
    let rawLabel;
    if (isPlayer) {
        rawLabel = playerName;
    } else {
        // Use unit.name, fallback to Unknown if missing
        rawLabel = unit.name || "Unknown";
    }

    // 2. Cleanup using helper
    let cleanLabel = cleanUnitLabel(rawLabel);

    if (showAsDot) {
        // Render as simple dot
        const m = L.circleMarker([unit.lat, unit.long], {
            radius: 2,
            color: color,
            fillColor: color,
            fillOpacity: 0.8,
            weight: 1
        }).addTo(unitLayer);

        m.bindTooltip(cleanLabel, {
            direction: 'top',
            offset: [0, -5],
            className: 'active-leg-label',
            permanent: showWpLabels // Respect global toggle
        });

        return m;
    } else {
        // Render as icon using milsymbol
        let icon;
        try {
            if (typeof ms !== 'undefined') {
                // Determine affiliation
                let affiliation = 'N'; // Neutral
                if (unit.coalition === 1) affiliation = 'H'; // Hostile
                else if (unit.coalition === 2) affiliation = 'F'; // Friendly

                // Determine SIDC using type levels
                let sidc = buildSIDC(affiliation, unit.type_level1, unit.type_level2, unit.type_level3);

                const sym = new ms.Symbol(sidc, { size: iconSize, colorMode: "Light" }).asCanvas();

                // Rotation Style (Air units only)
                let rotStyle = "";
                let rotClass = "";
                if (category === 'air' || isPlayer) {
                    rotStyle = `transform: rotate(${unit.heading}deg); transition: transform 0.5s linear; transform-origin: center;`;
                    rotClass = "rotatable-icon";
                }

                icon = L.divIcon({
                    className: 'theater-unit-icon',
                    html: `<div class="${rotClass}" style="width:100%; height:100%; ${rotStyle}"><img src="${sym.toDataURL()}" style="width:100%; height:100%;"></div>`,
                    iconSize: [iconSize, iconSize],
                    iconAnchor: [iconSize / 2, iconSize / 2]
                });
            } else {
                throw new Error("Milsymbol not available");
            }
        } catch (e) {
            // Fallback to generic milsymbol (Unknown unit)
            // console.warn("Milsymbol error, using fallback:", e);
            try {
                const fallbackSidc = buildSIDC('N', unit.type_level1, 0, 0); // Generic unknown for the category
                const sym = new ms.Symbol(fallbackSidc, { size: iconSize, colorMode: "Light" }).asCanvas();
                // Rotation Style (Air units only)
                let rotStyle = "";
                let rotClass = "";
                if (category === 'air' || isPlayer) {
                    const hdgDeg = (unit.heading || 0) * (180 / Math.PI);
                    rotStyle = `transform: rotate(${hdgDeg}deg); transition: transform 0.5s linear; transform-origin: center;`;
                    rotClass = "rotatable-icon";
                }

                icon = L.divIcon({
                    className: 'theater-unit-icon',
                    html: `<div class="${rotClass}" style="width:100%; height:100%; ${rotStyle}"><img src="${sym.toDataURL()}" style="width:100%; height:100%;"></div>`,
                    iconSize: [iconSize, iconSize],
                    iconAnchor: [iconSize / 2, iconSize / 2]
                });
            } catch (e2) {
                // Final fallback: Use standard marker
                // Rotation Style (Air units only)
                let rotStyle = "";
                let rotClass = "";
                if (category === 'air' || isPlayer) {
                    const hdgDeg = (unit.heading || 0) * (180 / Math.PI);
                    rotStyle = `transform: rotate(${hdgDeg}deg); transition: transform 0.5s linear; transform-origin: center;`;
                    rotClass = "rotatable-icon";
                }

                icon = L.divIcon({
                    className: 'theater-unit-icon',
                    html: `<div class="${rotClass}" style="width:${iconSize}px; height:${iconSize}px; background:${color}; opacity:0.6; border:2px solid ${color}; border-radius:3px; ${rotStyle}"></div>`,
                    iconSize: [iconSize, iconSize],
                    iconAnchor: [iconSize / 2, iconSize / 2]
                });
            }
        }

        const m = L.marker([unit.lat, unit.long], { icon: icon, zIndexOffset: 100 }).addTo(unitLayer);

        m.bindTooltip(cleanLabel, {
            direction: 'top',
            offset: [0, -iconSize / 2 - 5],
            className: 'active-leg-label',
            permanent: showWpLabels // Respect global toggle
        });

        // Detailed popup on click
        m.on('click', () => {
            // Retrieve latest unit data if available to ensure live Alt/Hdg
            let currentUnit = unit;
            if (theaterUnits[unit.id] && theaterUnits[unit.id].data) {
                currentUnit = theaterUnits[unit.id].data;
            }

            // ALTITUDE FORMATTING
            const altUnit = settings.altUnit || 'ft';
            const altVal = toDisplayAlt(currentUnit.alt);

            // HEADING FORMATTING (Radians -> Degrees)
            const hdgDeg = (currentUnit.heading || 0) * (180 / Math.PI);
            const hdgDisplay = Math.round(hdgDeg);

            // SIMPLIFIED POPUP CONTENT
            // Safety checks for display values
            const safeAlt = (!isNaN(altVal)) ? `${altVal} ${altUnit} MSL` : "N/A";
            const safeHdg = (!isNaN(hdgDisplay)) ? `${String(hdgDisplay).padStart(3, '0')}°` : "N/A";

            const popupContent = `<div style="min-width:120px; text-align: left;">
                <div style="font-weight:bold; color:#78aabc; font-size:13px; margin-bottom:5px; border-bottom:1px solid rgba(120,170,188,0.3); padding-bottom:2px;">
                    ${cleanLabel}
                </div>
                <div style="font-size:12px; margin-bottom:2px;">
                    <span style="color:#aaa;">Altitude:</span> <span style="font-weight:bold; color:#fff;">${safeAlt}</span>
                </div>
                <div style="font-size:12px;">
                    <span style="color:#aaa;">Heading:</span> <span style="font-weight:bold; color:#fff;">${safeHdg}</span>
                </div>
            </div>`;

            L.popup()
                .setLatLng([currentUnit.lat, currentUnit.long])
                .setContent(popupContent)
                .openOn(map);
        });

        return m;
    }
}

// Helper function to build SIDC from type levels
function buildSIDC(affiliation, level1, level2, level3) {
    // SIDC format: S + Affiliation + Dimension + P + SymbolSet
    // Based on actual DCS wsTypes.lua

    // DEBUG: Log type levels for troubleshooting
    console.log(`buildSIDC: affiliation=${affiliation}, L1=${level1}, L2=${level2}, L3=${level3}`);

    let dimension = 'G'; // Ground default
    let symbolSet = 'U-------'; // Unknown default

    if (level1 === 1) {
        // AIR - Keep it simple, use generic symbols
        dimension = 'A';
        if (level2 === 1) {
            // Airplane
            if (level3 === 1 || level3 === 2 || level3 === 3) {
                // Group 1: Fighter / Fighter Bomber / Interceptor
                symbolSet = 'MFF-------';
            } else if (level3 === 4 || level3 === 6) {
                // Group 2: Intruder / Battleplane (Attack)
                symbolSet = 'MFA-------';
            } else if (level3 === 5) {
                // Group 3: Cruiser (Strategic Bomber)
                symbolSet = 'MFB-------';
            } else {
                // Generic Fixed Wing
                symbolSet = 'MF---------';
            }
        } else if (level2 === 2) {
            // Helicopter
            symbolSet = 'MH---------';
        } else {
            // Unknown air
            symbolSet = 'M----------';
        }
    } else if (level1 === 2) {
        // GROUND (Corrected with actual wsTypes values)
        dimension = 'G';

        if (level2 === 17) {
            // Tank
            symbolSet = 'UCA--------'; // Armor/Tank (15 chars)
        } else if (level2 === 16) {
            // SAM - Specific by range/capability
            if (level3 === 102) {
                // Radar + Missile (S-300, Patriot = long range)
                symbolSet = 'UCDL-------'; // LR SAM (15 chars)
            } else if (level3 === 27) {
                // Missile only (Hawk, Kub = medium range)
                symbolSet = 'UCDM-------'; // MR SAM (15 chars)
            } else if (level3 === 26) {
                // Gun + Missile integrated (SA-6/Shilka, SA-8 = medium range)
                symbolSet = 'UCDM-------'; // MR SAM (15 chars)
            } else if (level3 === 101) {
                // Radar only (EWR)
                symbolSet = 'UUSR-------'; // Sensor/Radar (15 chars)
            } else {
                symbolSet = 'UCD--------'; // Generic AD (15 chars)
            }
        } else if (level2 === 8) {
            // Moving vehicles
            if (level3 === 27) {
                // Mobile missiles (Avenger, Stinger)
                symbolSet = 'UCDS-------'; // SR SAM (mobile, 15 chars)
            } else if (level3 === 26) {
                // Self-propelled guns (Shilka, Gepard)
                symbolSet = 'UCDG-------'; // AAA (SP, 15 chars)
            } else {
                // Other vehicles (trucks, APCs)
                symbolSet = 'UCV--------'; // Utility vehicle (15 chars)
            }
        } else if (level2 === 9) {
            // Stationary structures  
            if (level3 === 27) {
                // Fixed missile site
                symbolSet = 'UCDM-------'; // MR SAM (fixed, 15 chars)
            } else if (level3 === 26) {
                // Fixed gun
                symbolSet = 'UCDG-------'; // AAA (fixed, 15 chars)
            } else if (level3 === 101 || level3 === 105) {
                // Radar
                symbolSet = 'UUSR-------'; // Sensor/Radar (15 chars)
            } else {
                symbolSet = 'U----------'; // Generic static (15 chars)
            }
        } else if (level2 === 20) {
            // Infantry - Check if MANPADS
            if (level3 === 27) {
                // Infantry with missiles (MANPADS: Stinger, Igla teams)
                symbolSet = 'UCDS-------'; // SR SAM (MANPADS, 15 chars)
            } else {
                // Regular infantry
                symbolSet = 'UCI--------'; // Infantry (15 chars)
            }
        } else {
            symbolSet = 'U----------'; // Unknown ground (15 chars)
        }
    } else if (level1 === 3) {
        // NAVY
        dimension = 'S';
        if (level2 === 12) {
            // Ship
            symbolSet = 'C----------'; // Combatant (15 chars)
        } else {
            symbolSet = 'C----------'; // Default combatant
        }
    } else if (level1 === 5) {
        // STATIC
        dimension = 'G';
        symbolSet = 'I-------'; // Installation
    } else {
        // Unknown category
        dimension = 'G';
        symbolSet = 'U-------';
    }

    const sidc = `S${affiliation}${dimension}P${symbolSet}`;
    console.debug(`  → Generated SIDC: ${sidc}`);
    return sidc;
}
// --- TELEMETRY LOOP ---
let telemetryLoopRunning = false;
let latestTelemetryCheck = null;

function updateTelemetryVisuals() {
    if (!lastTelemetry) return;
    const data = lastTelemetry;

    // Update Text Values (Throttled)
    let altVal = (settings.altUnit === 'ft') ? data.alt * 3.28084 : data.alt;
    const elAlt = document.getElementById('val-alt');
    const elHdg = document.getElementById('val-hdg');
    if (elAlt) elAlt.innerText = Math.round(altVal);
    if (elHdg) elHdg.innerText = String(Math.round(data.hdg)).padStart(3, '0');

    // Update Route Steer
    if (data.steer && typeof data.steer.index !== 'undefined') {
        if (activeRouteName && activeWpIndex !== data.steer.index) {
            activeWpIndex = data.steer.index;
            updateMiniPanel();
            renderMapRoutes();
        }
    }

    // Update Map & Marker
    if (data.lat && data.lon) {
        if (!planeMarker) {
            // Create plane marker if doesn't exist (assuming socket sends data before init?)
            let iconHtml = '<i class="fa-solid fa-plane" id="my-jet"></i>';
            try {
                if (typeof ms !== 'undefined') {
                    // SIDC: S=Standard, F=Friend, A=Air, P=Plane, MF=Fixed Wing Fighter
                    const sym = new ms.Symbol("SFAPMF----", { size: 24, colorMode: "Light" }).asCanvas();
                    iconHtml = `<img src="${sym.toDataURL()}" id="my-jet" style="width:100%; height:100%;">`;
                }
            } catch (e) { console.error("Error creating ownship symbol", e); }

            var planeIcon = L.divIcon({ className: 'plane-icon', html: iconHtml, iconSize: [32, 32], iconAnchor: [16, 16] });
            planeMarker = L.marker([data.lat, data.lon], { icon: planeIcon, zIndexOffset: 1000 }).addTo(map);
        }

        // Batch Marker & Map Updates
        planeMarker.setLatLng([data.lat, data.lon]);

        const jet = document.getElementById('my-jet');
        if (headingUp) {
            document.getElementById('map').style.transform = `rotate(${-data.hdg}deg)`;
            if (jet) jet.style.transform = `rotate(0deg)`;
            map.panTo([data.lat, data.lon], { animate: false });
        } else {
            if (jet) jet.style.transform = `rotate(${data.hdg}deg)`;
            if (followMode) {
                map.panTo([data.lat, data.lon], { animate: true, duration: 0.5 });
            }
        }

        // Active Leg Line
        activeLegLayer.clearLayers();
        if (activeRouteName && activeWpIndex >= 0 && activeWpIndex < activeRouteData.length) {
            const wp = activeRouteData[activeWpIndex];
            L.polyline([[data.lat, data.lon], [wp.lat, wp.lon]], { color: '#0f0', weight: 4 }).addTo(activeLegLayer);
        }
    }
}

function telemetryLoop() {
    if (lastTelemetry !== latestTelemetryCheck) {
        updateTelemetryVisuals();
        latestTelemetryCheck = lastTelemetry;
    }
    requestAnimationFrame(telemetryLoop);
}

// Start the loop
requestAnimationFrame(telemetryLoop);

socket.on('telemetry', function (data) {
    lastTelemetry = data;
});

const pointerSvgs = { cross: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16 4V12M16 20V28M4 16H12M20 16H28" stroke="${c}" stroke-width="2" stroke-linecap="round"/><circle cx="16" cy="16" r="2" fill="${c}"/></svg>`, dot: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="5" fill="${c}" stroke="none" stroke-width="1"/></svg>`, chevron: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M8 20L16 12L24 20" stroke="${c}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`, circle: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="8" stroke="${c}" stroke-width="2" fill="none"/></svg>`, x: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M10 10L22 22M22 10L10 22" stroke="${c}" stroke-width="3" stroke-linecap="round"/></svg>`, arrow: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 8L22 26L16 22L10 26L16 8Z" fill="${c}" stroke="none" stroke-width="1" stroke-linejoin="round"/></svg>`, diamond: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="16" y="6" width="12" height="12" transform="rotate(45 16 6)" fill="none" stroke="${c}" stroke-width="2"/></svg>`, square: (c) => `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="11" y="11" width="10" height="10" stroke="${c}" stroke-width="2" fill="none"/></svg>`, };
function updatePointerVisuals() { const style = document.getElementById('opt-ptr-style').value || 'cross'; const color = document.getElementById('opt-ptr-color').value || '#00ff00'; const svgGen = pointerSvgs[style] || pointerSvgs['cross']; const svgString = svgGen(color); const encoded = encodeURIComponent(svgString); const cursor = document.getElementById('virtual-cursor'); if (cursor) { cursor.style.backgroundImage = `url("data:image/svg+xml;charset=utf-8,${encoded}")`; } }

// --- VIRTUAL POINTER SYSTEM ---
const VirtualPointer = {
    active: false,
    x: 0,
    y: 0,
    state: 'IDLE', // IDLE, HOVER, DRAG
    target: null,
    dragStartPos: null,
    dragStartLatLng: null,
    pressTime: 0,
    _cursorElement: null,
    DETECTION_RADIUS: 20, // Configurable hit detection radius (pixels)

    toggle: function (isActive) {
        this.active = isActive;
        const cursor = this._getCursor();
        if (cursor) {
            if (isActive) {
                // Initialize cursor visual if not already set
                if (!cursor.style.backgroundImage || cursor.style.backgroundImage === 'none') {
                    updatePointerVisuals(); // Set default crosshair
                }
                // Center cursor on screen if this is first activation
                if (this.x === 0 && this.y === 0) {
                    this.x = window.innerWidth / 2;
                    this.y = window.innerHeight / 2;
                    cursor.style.left = this.x + 'px';
                    cursor.style.top = this.y + 'px';
                }
                cursor.style.display = 'block';
                console.log('🖱️ Virtual Pointer ACTIVATED at', this.x, this.y);
            } else {
                cursor.style.display = 'none';
                console.log('🖱️ Virtual Pointer DEACTIVATED');
            }
        } else {
            console.error('❌ virtual-cursor element not found!');
        }

        if (!isActive) {
            // Cancel any active drag operation
            if (this.state === 'DRAG' && this.target) {
                if (this.target.marker && this.target.marker.fire) {
                    this.target.marker.fire('dragend');
                }
            }
            // Reset all state
            this.state = 'IDLE';
            this.target = null;
            this.dragStartPos = null;
            this.dragStartLatLng = null;
        }
    },

    _getCursor: function () {
        if (!this._cursorElement) {
            this._cursorElement = document.getElementById('virtual-cursor');
        }
        return this._cursorElement;
    },

    update: function (x, y, norm) {
        if (!this.active) return;
        this.x = x;
        this.y = y;

        const cursor = this._getCursor();
        if (cursor) {
            cursor.style.left = x + 'px';
            cursor.style.top = y + 'px';
        }

        // If mouse is pressed (dragging), simulate mousemove
        if (this.state === 'PRESSED' && this.target) {
            // Hide cursor to detect element underneath
            const originalDisplay = cursor ? cursor.style.display : null;
            if (cursor) cursor.style.display = 'none';

            const element = document.elementFromPoint(x, y);

            // Restore cursor
            if (cursor) cursor.style.display = originalDisplay;

            if (element) {
                const mouseMoveEvent = new MouseEvent('mousemove', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: x,
                    clientY: y,
                    button: 0,
                    buttons: 1 // Left button is pressed
                });
                element.dispatchEvent(mouseMoveEvent);
            }
        }
    },

    press: function (x, y, norm) {
        if (!this.active) {
            console.warn('❌ VirtualPointer.press() called but pointer not active');
            return;
        }

        console.log('🔽 VirtualPointer.press() at', x, y);
        this.pressTime = Date.now();
        this.pressPos = { x: x, y: y };

        // CRITICAL: Hide cursor to get element underneath
        const cursor = this._getCursor();
        const cursorDisplay = cursor ? cursor.style.display : null;
        if (cursor) cursor.style.display = 'none';

        // Get element at cursor position
        const element = document.elementFromPoint(x, y);

        // Restore cursor
        if (cursor) cursor.style.display = cursorDisplay;

        console.log('🎯 Element at position:', element);

        if (element) {
            // Simulate mousedown event
            const mouseDownEvent = new MouseEvent('mousedown', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: x,
                clientY: y,
                button: 0 // Left button
            });

            element.dispatchEvent(mouseDownEvent);
            console.log('📤 Dispatched mousedown to', element.tagName, element.className);

            this.target = element;
            this.state = 'PRESSED';
        } else {
            console.log('⭕ No element at this position');
        }
    },

    release: function (x, y, norm) {
        if (!this.active) return;

        console.log('🔼 VirtualPointer.release() at', x, y);
        const pressDuration = Date.now() - this.pressTime;
        console.log('⏱️ Press duration:', pressDuration, 'ms');

        // CRITICAL: Hide cursor to get element underneath
        const cursor = this._getCursor();
        const cursorDisplay = cursor ? cursor.style.display : null;
        if (cursor) cursor.style.display = 'none';

        // Get element at release position
        const element = document.elementFromPoint(x, y);

        // Restore cursor
        if (cursor) cursor.style.display = cursorDisplay;

        if (element) {
            // Simulate mouseup event
            const mouseUpEvent = new MouseEvent('mouseup', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: x,
                clientY: y,
                button: 0
            });

            element.dispatchEvent(mouseUpEvent);
            console.log('📤 Dispatched mouseup to', element.tagName);

            // If released on same element as pressed, simulate click
            if (this.target === element && pressDuration < 500) {
                console.log('🖱️ Simulating click on', element.tagName);

                const clickEvent = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: x,
                    clientY: y,
                    button: 0
                });

                element.dispatchEvent(clickEvent);
                console.log('✅ Click dispatched');
            } else if (pressDuration >= 500) {
                console.log('🚀 Long press - might be a drag');
                // Drag would be handled by mousemove events during press
            }
        }

        this.state = 'IDLE';
        this.target = null;
    },

    performHitTest: function (x, y) {
        // Use Leaflet's built-in hit detection
        const point = map.containerPointToLatLng([x, y]);

        // Check route waypoints first (highest priority)
        if (activeRouteName && activeRouteData.length > 0) {
            for (let i = 0; i < activeRouteData.length; i++) {
                const wp = activeRouteData[i];
                if (wp.marker) {
                    const markerPos = map.latLngToContainerPoint(wp.marker.getLatLng());
                    const dist = Math.sqrt(Math.pow(markerPos.x - x, 2) + Math.pow(markerPos.y - y, 2));
                    if (dist < 20) {
                        return { type: 'waypoint', marker: wp.marker, index: i };
                    }
                }
            }
        }

        // Check POIs
        for (let i = 0; i < allPois.length; i++) {
            const poi = allPois[i];
            if (poi.marker) {
                const markerPos = map.latLngToContainerPoint(poi.marker.getLatLng());
                const dist = Math.sqrt(Math.pow(markerPos.x - x, 2) + Math.pow(markerPos.y - y, 2));
                if (dist < this.DETECTION_RADIUS) {
                    return { type: 'poi', marker: poi.marker, index: i };
                }
            }
        }

        // Check theater units
        for (let id in theaterUnits) {
            const unit = theaterUnits[id];
            if (unit && unit.marker) {
                const markerPos = map.latLngToContainerPoint(unit.marker.getLatLng());
                const dist = Math.sqrt(Math.pow(markerPos.x - x, 2) + Math.pow(markerPos.y - y, 2));
                if (dist < this.DETECTION_RADIUS) {
                    return { type: 'unit', marker: unit.marker, id: id };
                }
            }
        }

        // Check player marker
        if (planeMarker) {
            const markerPos = map.latLngToContainerPoint(planeMarker.getLatLng());
            const dist = Math.sqrt(Math.pow(markerPos.x - x, 2) + Math.pow(markerPos.y - y, 2));
            if (dist < this.DETECTION_RADIUS) {
                return { type: 'player', marker: planeMarker };
            }
        }

        return null;
    },

    isDraggable: function (hit) {
        if (!hit) return false;
        // Only waypoints are draggable in this implementation
        return hit.type === 'waypoint';
    },

    updateDragTarget: function (latLng) {
        if (!this.target || !this.target.marker) return;

        if (this.target.type === 'waypoint') {
            // Update waypoint position
            this.target.marker.setLatLng(latLng);
            activeRouteData[this.target.index].lat = latLng.lat;
            activeRouteData[this.target.index].lon = latLng.lng;

            // Redraw route
            if (typeof renderMapRoutes === 'function') {
                renderMapRoutes();
            }
        }
    },

    simulateClick: function (hit) {
        if (!hit || !hit.marker) return;

        // Visual feedback
        this.showClickAnimation(this.x, this.y);

        // Fire click event on the marker
        if (hit.marker.fire) {
            hit.marker.fire('click');
        }

        // Type-specific actions
        if (hit.type === 'waypoint') {
            if (typeof selectWaypoint === 'function') {
                selectWaypoint(hit.index);
            }
        } else if (hit.type === 'poi') {
            if (typeof selectPoi === 'function') {
                selectPoi(hit.index);
            }
        }
    },

    showClickAnimation: function (x, y) {
        const anim = document.createElement('div');
        anim.className = 'pointer-click-anim';
        anim.style.left = x + 'px';
        anim.style.top = y + 'px';
        document.body.appendChild(anim);
        setTimeout(() => anim.remove(), 500);
    }
};
const blockRealMouse = (e) => { if (VirtualPointer.active && e.isTrusted) { e.preventDefault(); e.stopPropagation(); } }; const eventsToBlock = ['mousedown', 'mouseup', 'mousemove', 'click', 'dblclick', 'pointerdown', 'pointerup', 'pointermove', 'contextmenu'];
if (typeof eventsToBlock !== 'undefined') { eventsToBlock.forEach(evt => { window.addEventListener(evt, blockRealMouse, true); }); }

// Virtual Pointer Socket Events (matching server.py API)
socket.on('pointer_mode_changed', function (data) {
    VirtualPointer.toggle(data.active);
});

socket.on('pointer_update', function (data) {
    // Server sends full state: { active, x, y, mode }
    if (data.active !== undefined) {
        VirtualPointer.toggle(data.active);
    }
    if (data.x !== undefined && data.y !== undefined) {
        let px = data.x;
        let py = data.y;

        if (data.mode === 'pct') {
            px = data.x * window.innerWidth;
            py = data.y * window.innerHeight;
            // Ensure within bounds?
            // VirtualPointer.update logic might clamp, but let's pass calculated pixels
        }

        VirtualPointer.update(px, py, false);
    }
});

socket.on('pointer_click_event', function (data) {
    console.log('📥 Frontend received click event:', data);
    // Server sends: { action: 'click' | 'down' | 'up' }
    // Capture position to avoid race conditions if cursor moves during timeout
    const x = VirtualPointer.x;
    const y = VirtualPointer.y;
    console.log('📍 Pointer position:', x, y, 'Active:', VirtualPointer.active);

    if (data.action === 'down') {
        console.log('⬇️ Calling VirtualPointer.press()');
        VirtualPointer.press(x, y, false);
    } else if (data.action === 'up') {
        console.log('⬆️ Calling VirtualPointer.release()');
        VirtualPointer.release(x, y, false);
    } else if (data.action === 'click') {
        // Capture coordinates to prevent race condition during timeout
        const clickX = x;
        const clickY = y;
        console.log('🖱️ Simulating click at', clickX, clickY);
        VirtualPointer.press(clickX, clickY, false);
        setTimeout(() => VirtualPointer.release(clickX, clickY, false), 50);
    }
});
// DEPRECATED: 'tactical' event caused duplicate markers. 
// Logic now centralized in 'theater_state' above.
// socket.on('tactical', function (packet) {});
socket.on('visual_target_added', function (poi) {
    if (!poi) return;
    allPois.push(poi);
    renderPois();
    if (activeMissionName) {
        saveActiveMission();
        renderBrowserList();
        renderPoiList();
    }
    showToast("Visual Target Added: " + poi.name);
});
socket.on('apply_settings', (data) => { });

function openKeyboard(inputId, type) { activeInputId = inputId; const kb = document.getElementById('virtual-keyboard'); const container = document.getElementById('kb-keys-container'); container.innerHTML = ''; const numericKeys = [['7', '8', '9'], ['4', '5', '6'], ['1', '2', '3'], ['0', '.', 'BS']]; const fullKeys = [['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'], ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'], ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'], ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '.', 'BS']]; const layout = (type === 'number') ? numericKeys : fullKeys; layout.forEach(row => { const rowDiv = document.createElement('div'); rowDiv.className = 'kb-row'; row.forEach(key => { const btn = document.createElement('button'); btn.className = 'kb-key'; if (key === 'BS') { btn.innerHTML = '<i class="fa-solid fa-delete-left"></i>'; btn.className += ' action'; btn.onclick = () => handleKey('BACKSPACE'); } else { btn.innerText = key; btn.onclick = () => handleKey(key); } rowDiv.appendChild(btn); }); container.appendChild(rowDiv); }); const actionRow = document.createElement('div'); actionRow.className = 'kb-row'; actionRow.style.marginTop = "5px"; const spaceBtn = document.createElement('button'); spaceBtn.className = 'kb-key wide'; spaceBtn.innerText = "SPACE"; spaceBtn.onclick = () => handleKey('SPACE'); if (type !== 'number') actionRow.appendChild(spaceBtn); const entBtn = document.createElement('button'); entBtn.className = 'kb-key enter wide'; entBtn.innerText = "DONE"; entBtn.onclick = closeKeyboard; actionRow.appendChild(entBtn); container.appendChild(actionRow); kb.classList.add('visible'); }
function closeKeyboard() { document.getElementById('virtual-keyboard').classList.remove('visible'); activeInputId = null; }
function handleKey(val) { if (!activeInputId) return; const input = document.getElementById(activeInputId); if (val === 'BACKSPACE') input.value = input.value.slice(0, -1); else if (val === 'SPACE') input.value += " "; else input.value += val; input.dispatchEvent(new Event('input')); input.dispatchEvent(new Event('change')); }
const layoutObserver = new ResizeObserver(entries => { for (let entry of entries) { const totalHeight = entry.target.offsetHeight; document.documentElement.style.setProperty('--bottom-bar-height', `${totalHeight}px`); } });
const bottomBarEl = document.getElementById('bottom-bar'); if (bottomBarEl) layoutObserver.observe(bottomBarEl);

// --- DATA CARTRIDGE ---
function closeModal(type) { document.getElementById(`modal-${type}`).style.display = 'none'; if (type === 'import' && html5QrCode && html5QrCode.isScanning) { html5QrCode.stop().then(() => { html5QrCode.clear(); }).catch(err => console.error("Stop failed", err)); } }
function openShareModal() { const select = document.getElementById('share-mission-select'); select.innerHTML = ""; Object.keys(missions).forEach(key => { const opt = document.createElement('option'); opt.value = key; opt.innerText = key; if (key === activeMissionName) opt.selected = true; select.appendChild(opt); }); document.getElementById('modal-share').style.display = 'flex'; document.getElementById('qr-result-area').style.display = 'none'; updateShareList(); }
function updateShareList() { const missionName = document.getElementById('share-mission-select').value; const list = document.getElementById('share-routes-list'); list.innerHTML = ''; if (!missions[missionName]) return; const mRoutes = missions[missionName].routes || {}; const mPois = missions[missionName].pois || []; if (Object.keys(mRoutes).length === 0) { list.innerHTML = '<div style="padding:10px; color:#777; font-style:italic;">No routes in this mission.</div>'; } else { Object.keys(mRoutes).forEach(name => { const row = document.createElement('label'); row.className = 'chk-item'; row.innerHTML = `<input type="checkbox" value="${name}"> <span>${name}</span>`; list.appendChild(row); }); } const poiLbl = document.getElementById('share-pois').nextElementSibling; if (poiLbl) poiLbl.innerText = `Include POI List (${mPois.length} Targets)`; }
function generateMissionQR() { const missionName = document.getElementById('share-mission-select').value; const targetMission = missions[missionName]; if (!targetMission) return; const selectedRoutes = {}; document.querySelectorAll('#share-routes-list input:checked').forEach(chk => { selectedRoutes[chk.value] = targetMission.routes[chk.value]; }); const includePois = document.getElementById('share-pois').checked; const sender = document.getElementById('share-sender').value || "Commander"; const briefing = document.getElementById('share-briefing').value || ""; const payload = { protocol: "dcs-mission-v1", meta: { sender: sender, info: missionName, briefing: briefing, ts: Date.now() }, payload: { routes: selectedRoutes, pois: includePois ? (targetMission.pois || []) : [] } }; const jsonStr = JSON.stringify(payload); if (jsonStr.length > 2500) { alert("Data too large for QR."); return; } document.getElementById('qr-result-area').style.display = 'block'; document.getElementById('qr-output').innerHTML = ''; new QRCode(document.getElementById("qr-output"), { text: jsonStr, width: 256, height: 256, colorDark: "#000000", colorLight: "#ffffff", correctLevel: QRCode.CorrectLevel.L }); }
function downloadQR() { const qrContainer = document.getElementById("qr-output"); let img = qrContainer.querySelector("img"); let url = ""; if (img) { url = img.src; } else { const canvas = qrContainer.querySelector("canvas"); if (canvas) { url = canvas.toDataURL("image/png"); } } if (url) { const link = document.createElement("a"); link.href = url; link.download = "dcs_mission_qr.png"; document.body.appendChild(link); link.click(); document.body.removeChild(link); } else { alert("QR Code not generated yet."); } }

// --- IMPORT ---
function openImportModal() {
    document.getElementById('modal-import').style.display = 'flex'; document.getElementById('import-step-1').style.display = 'block'; document.getElementById('import-step-2').style.display = 'none'; if (!html5QrCode) { html5QrCode = new Html5Qrcode("reader"); } const config = { fps: 10, qrbox: { width: 250, height: 250 } }; html5QrCode.start({ facingMode: "environment" }, config, onScanSuccess).catch(err => { console.error("Camera Start Error:", err); document.getElementById('reader').innerHTML = `<div style="padding:20px; color:#e74c3c; font-size:12px;"><i class="fa-solid fa-video-slash" style="font-size:24px; margin-bottom:10px;"></i><br>CAMERA NOT FOUND OR DENIED<br><span style="color:#777;">Use Drop Zone below</span></div>`; });
    document.getElementById('qr-file-input').onchange = e => { if (e.target.files.length == 0) return; html5QrCode.scanFile(e.target.files[0], true).then(onScanSuccess).catch(err => alert(`Error scanning file: ${err}`)); };
}
function onScanSuccess(decodedText, decodedResult) { try { const data = JSON.parse(decodedText); if (data.protocol !== "dcs-mission-v1") throw new Error("Invalid Protocol"); if (html5QrCode && html5QrCode.isScanning) { html5QrCode.stop().then(() => html5QrCode.clear()); } processImportData(data); } catch (e) { console.error(e); alert("Invalid QR Code. Must be a DCS Mission v1 code."); } }
function processImportData(data) { pendingImportData = data; const missionName = data.meta.info || "Imported Mission"; if (missions[missionName]) { showImportConflict(missionName); } else { finalizeImport('new', missionName); } }
function showImportConflict(name) { document.getElementById('import-step-2').style.display = 'block'; document.getElementById('import-step-1').style.display = 'none'; document.getElementById('import-meta-sender').innerText = `CONFLICT: Mission "${name}" exists.`; document.getElementById('import-meta-info').innerText = "Select merge or replace strategy:"; const manifest = document.getElementById('import-manifest'); manifest.innerHTML = `<li style="color:var(--accent)"><b>MERGE:</b> Combine new data with existing file.</li><li style="color:var(--red-for)"><b>REPLACE:</b> Overwrite existing mission entirely.</li><li style="color:#2ecc71"><b>NEW:</b> Save as "${name} [COPY]".</li>`; const container = document.querySelector('#import-step-2'); container.querySelectorAll('.dynamic-import-btn').forEach(b => b.remove()); const btnHtml = `<button class="btn-full btn-action dynamic-import-btn" style="margin-top:10px;" onclick="finalizeImport('merge', '${name}')">MERGE INTO EXISTING</button><button class="btn-full btn-danger dynamic-import-btn" style="margin-top:5px;" onclick="finalizeImport('replace', '${name}')">REPLACE EXISTING</button><button class="btn-full btn-success dynamic-import-btn" style="margin-top:5px;" onclick="finalizeImport('new', '${name}')">IMPORT AS NEW (COPY)</button>`; const discardBtn = container.querySelector('.btn-danger:not(.dynamic-import-btn)'); discardBtn.insertAdjacentHTML('beforebegin', btnHtml); }
function finalizeImport(mode, name) { if (!pendingImportData) return; let targetName = name; if (mode === 'new') { const suffix = " [COPY " + Date.now().toString().slice(-4) + "]"; targetName = name + suffix; } if (mode === 'replace' || mode === 'new') { missions[targetName] = { imported: "I", map: pendingImportData.meta.map || null, routes: pendingImportData.payload.routes || {}, pois: pendingImportData.payload.pois || [] }; } else if (mode === 'merge') { if (!missions[targetName].routes) missions[targetName].routes = {}; Object.assign(missions[targetName].routes, pendingImportData.payload.routes); if (!missions[targetName].pois) missions[targetName].pois = []; const existingPois = missions[targetName].pois; pendingImportData.payload.pois.forEach(newP => { const exists = existingPois.some(ep => ep.lat === newP.lat && ep.lon === newP.lon); if (!exists) existingPois.push(newP); }); missions[targetName].pois = existingPois; } saveAllMissions().then(() => { showToast(`Import Success: ${targetName}`); selectMission(targetName); closeModal('import'); document.querySelectorAll('.dynamic-import-btn').forEach(b => b.remove()); }); }

// --- FINAL UTILS & LISTENERS ---
const savedListContainer = document.getElementById('saved-list'); savedListContainer.addEventListener('dragover', (e) => { e.preventDefault(); const afterElement = getDragAfterElement(savedListContainer, e.clientY, '.saved-route-item'); const draggable = document.querySelector('.dragging'); if (!draggable || !draggable.classList.contains('saved-route-item')) return; if (afterElement == null) savedListContainer.appendChild(draggable); else savedListContainer.insertBefore(draggable, afterElement); }); savedListContainer.addEventListener('drop', handleRouteListDrop);
const wpListContainer = document.getElementById('active-route-list'); wpListContainer.addEventListener('dragover', (e) => { e.preventDefault(); const afterElement = getDragAfterElement(wpListContainer, e.clientY, '.route-item'); const draggable = document.querySelector('.dragging'); if (!draggable || !draggable.classList.contains('route-item')) return; if (afterElement == null) wpListContainer.appendChild(draggable); else wpListContainer.insertBefore(draggable, afterElement); }); wpListContainer.addEventListener('drop', handleWpDrop);
const dropArea = document.getElementById('drop-area');['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => { dropArea.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false); });['dragenter', 'dragover'].forEach(eventName => { dropArea.addEventListener(eventName, () => dropArea.classList.add('dragover'), false); });['dragleave', 'drop'].forEach(eventName => { dropArea.addEventListener(eventName, () => dropArea.classList.remove('dragover'), false); }); dropArea.addEventListener('drop', (e) => { const dt = e.dataTransfer; const files = dt.files; if (files.length > 0) { const file = files[0]; if (file.type === "application/json" || file.name.endsWith('.json')) { const reader = new FileReader(); reader.onload = (event) => { try { const data = JSON.parse(event.target.result); if (data.protocol === "dcs-mission-v1") { processImportData(data); } else { alert("Not a valid DCS Mission file."); } } catch (e) { alert("Error reading JSON file."); } }; reader.readAsText(file); } else { const html5QrCode = new Html5Qrcode("reader"); html5QrCode.scanFile(file, true).then(decodedText => { const data = JSON.parse(decodedText); processImportData(data); }).catch(err => alert(`Error scanning image: ${err}`)); } } }, false);
const TouchGestures = { active: false, startTime: 0, timer: null, holdTriggered: false, init: function () { document.body.addEventListener('touchstart', this.handleStart.bind(this), { passive: true }); document.body.addEventListener('touchend', this.handleEnd.bind(this)); document.body.addEventListener('touchcancel', this.reset.bind(this)); }, handleStart: function (e) { if (e.touches.length === 3) { this.active = true; this.holdTriggered = false; this.startTime = Date.now(); this.timer = setTimeout(() => { if (this.active) { this.holdTriggered = true; toggleFullScreen(); if (navigator.vibrate) navigator.vibrate(50); } }, 800); } else { if (e.touches.length > 3) this.reset(); } }, handleEnd: function (e) { if (!this.active) return; const duration = Date.now() - this.startTime; if (e.touches.length < 3) { clearTimeout(this.timer); if (duration < 400 && !this.holdTriggered) { toggleDrawer('settings'); } this.active = false; } }, reset: function () { this.active = false; this.holdTriggered = false; clearTimeout(this.timer); } }; TouchGestures.init();
map.on('layeradd', function (e) { if (e.layer === poiLayer) { const chk = document.getElementById('chk-vis-poi'); if (chk) chk.checked = true; const btn = document.getElementById('btn-vis-poi-list'); if (btn) btn.classList.add('active'); } }); map.on('layerremove', function (e) { if (e.layer === poiLayer) { const chk = document.getElementById('chk-vis-poi'); if (chk) chk.checked = false; const btn = document.getElementById('btn-vis-poi-list'); if (btn) btn.classList.remove('active'); } });
function exportMissionToFile() { const missionName = document.getElementById('share-mission-select').value; const targetMission = missions[missionName]; if (!targetMission) return; const payload = { protocol: "dcs-mission-v1", meta: { sender: document.getElementById('share-sender').value || "Commander", info: missionName, briefing: document.getElementById('share-briefing').value || "", ts: Date.now(), is_file: true }, payload: { routes: targetMission.routes || {}, pois: targetMission.pois || [] } }; const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(payload)); const downloadAnchorNode = document.createElement('a'); downloadAnchorNode.setAttribute("href", dataStr); downloadAnchorNode.setAttribute("download", missionName.replace(/\s+/g, '_') + ".json"); document.body.appendChild(downloadAnchorNode); downloadAnchorNode.click(); downloadAnchorNode.remove(); showToast("File Exported"); }
function togglePoiThreatVis() { if (activePoiIndex === -1) return; const current = (allPois[activePoiIndex].threatVisible !== false); allPois[activePoiIndex].threatVisible = !current; updatePoiThreatVisBtn(!current); }
function toggleCoalition(side) { const btn = document.getElementById(`btn-vis-${side}`); const chk = document.getElementById(`chk-vis-unit-${side}`); if (btn && chk) { chk.checked = !chk.checked; btn.classList.toggle('active', chk.checked); saveMapSettings(); renderPois(); } }
function updatePoiThreatVisBtn(isVisible) { const btn = document.getElementById('btn-poi-threat-vis'); if (isVisible) { btn.classList.add('active'); btn.innerHTML = '<i class="fa-solid fa-eye"></i>'; btn.style.color = "#78aabc"; } else { btn.classList.remove('active'); btn.innerHTML = '<i class="fa-solid fa-eye-slash"></i>'; btn.style.color = "#555"; } }
function updateThreatFill(val) { threatFillOpacity = val / 100; renderPois(); }
// Wait for DOM to be ready before initializing
window.addEventListener('DOMContentLoaded', async () => {
    await loadAirports();
    await loadMapSettings();
    await loadSavedRoutes();
    await loadSavedPois();
});
