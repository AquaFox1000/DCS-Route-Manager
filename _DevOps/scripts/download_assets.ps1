# download_assets.ps1
$vendorDir = "static/vendor"
$imagesDir = "$vendorDir/images"
$fontsDir = "$vendorDir/webfonts"

# Ensure directories exist
New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null
New-Item -ItemType Directory -Force -Path $imagesDir | Out-Null
New-Item -ItemType Directory -Force -Path $fontsDir | Out-Null

# Function to download file
function Download-File {
    param ($url, $dest)
    Write-Host "Downloading $url -> $dest"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    } catch {
        Write-Error "Failed to download $url : $_"
    }
}

# --- JS Core ---
Download-File "https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js" "$vendorDir/socket.io.js"
Download-File "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" "$vendorDir/leaflet.js"
Download-File "https://unpkg.com/leaflet.vectorgrid@latest/dist/Leaflet.VectorGrid.bundled.js" "$vendorDir/Leaflet.VectorGrid.bundled.js"
Download-File "https://unpkg.com/@joergdietrich/leaflet.terminator/L.Terminator.js" "$vendorDir/L.Terminator.js"
Download-File "https://unpkg.com/milsymbol@2.0.0/dist/milsymbol.js" "$vendorDir/milsymbol.js"
Download-File "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" "$vendorDir/qrcode.min.js"
Download-File "https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js" "$vendorDir/html5-qrcode.min.js"

# --- CSS ---
Download-File "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" "$vendorDir/leaflet.css"
Download-File "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" "$vendorDir/all.min.css"

# --- Images (Leaflet) ---
Download-File "https://unpkg.com/leaflet@1.9.4/dist/images/layers.png" "$imagesDir/layers.png"
Download-File "https://unpkg.com/leaflet@1.9.4/dist/images/layers-2x.png" "$imagesDir/layers-2x.png"
Download-File "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png" "$imagesDir/marker-icon.png"
Download-File "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png" "$imagesDir/marker-icon-2x.png"
Download-File "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png" "$imagesDir/marker-shadow.png"

# --- Fonts (FontAwesome) ---
# We generally need the solid-900 woff2 for standard icons
Download-File "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2" "$fontsDir/fa-solid-900.woff2"
Download-File "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.ttf" "$fontsDir/fa-solid-900.ttf"

Write-Host "Download Complete." -ForegroundColor Green
