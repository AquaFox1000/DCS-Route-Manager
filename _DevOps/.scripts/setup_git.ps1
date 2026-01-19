# Initialize git in this folder
git init

# Create a .gitignore file to prevent junk files from being backed up
echo "bad backups/" >> .gitignore
echo "local backups/" >> .gitignore
echo "node_modules/" >> .gitignore
echo ".DS_Store" >> .gitignore
echo "*.log" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "RouteManagerExport backup.lua" >> .gitignore
echo "Literature/" >> .gitignore

# Copy external Lua files
# Create target directories if they don't exist
New-Item -ItemType Directory -Force -Path "Scripts"
New-Item -ItemType Directory -Force -Path "Scripts\Hooks"

# Copy RouteManagerExport.lua
Copy-Item -Path "$env:USERPROFILE\Saved Games\DCS.openbeta\Scripts\RouteManagerExport.lua" -Destination "Scripts\RouteManagerExport.lua" -Force

# Copy RouteManagerHook.lua
Copy-Item -Path "$env:USERPROFILE\Saved Games\DCS.openbeta\Scripts\Hooks\RouteManagerHook.lua" -Destination "Scripts\Hooks\RouteManagerHook.lua" -Force

# Copy Raycast.lua
Copy-Item -Path "$env:USERPROFILE\Saved Games\DCS.openbeta\Scripts\Raycast.lua" -Destination "Scripts\Raycast.lua" -Force

# Stage all your current files
git add .

# Commit them (save this snapshot)
git commit -m "Initial backup RouteManager mod"

# Link to the already set up (empty github project)
git remote add origin https://github.com/AquaFox1000/DCS-Route-Manager.git

# Rename the branch to main (standard practice)
git branch -M main

# Push your files to GitHub
git push -u origin main
