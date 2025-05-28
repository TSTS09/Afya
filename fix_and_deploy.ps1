# Afya Medical EHR - Basic Build Fix and Deploy
Write-Host "Afya Medical EHR - Build and Deploy"
Write-Host "==================================="

# Check current directory
if (-not (Test-Path "firebase.json")) {
    Write-Host "Error: firebase.json not found. Run from project root directory."
    exit 1
}

# Go to public directory
if (-not (Test-Path "public")) {
    Write-Host "Error: public directory not found."
    exit 1
}

Set-Location public

# Clean up
Write-Host "Cleaning up..."
if (Test-Path "node_modules") { Remove-Item -Recurse -Force node_modules }
if (Test-Path "package-lock.json") { Remove-Item -Force package-lock.json }
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }

# Clear cache
Write-Host "Clearing npm cache..."
npm cache clean --force

# Create vue.config.js
Write-Host "Creating vue.config.js..."
$config = "const { defineConfig } = require('@vue/cli-service')" + [Environment]::NewLine
$config += "module.exports = defineConfig({" + [Environment]::NewLine
$config += "  transpileDependencies: true," + [Environment]::NewLine
$config += "  publicPath: '/'," + [Environment]::NewLine
$config += "  productionSourceMap: false" + [Environment]::NewLine
$config += "})"

$config | Out-File -FilePath "vue.config.js" -Encoding UTF8

# Install dependencies
Write-Host "Installing dependencies..."
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies"
    Set-Location ..
    exit 1
}

# Build application
Write-Host "Building application..."
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed, trying alternative..."
    npx vue-cli-service build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed completely"
        Set-Location ..
        exit 1
    }
}

# Check if build succeeded
if (-not (Test-Path "dist")) {
    Write-Host "Build failed - no dist directory"
    Set-Location ..
    exit 1
}

Write-Host "Build successful!"

# Go back and deploy
Set-Location ..

Write-Host "Deploying to Firebase..."
firebase deploy

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed"
    exit 1
}

Write-Host ""
Write-Host "SUCCESS! Deployment complete!"
Write-Host "Web Dashboard: https://afya-a1006.web.app"
Write-Host "USSD Access: Dial *714# from mobile phone"
Write-Host ""
Write-Host "Test Credentials:"
Write-Host "Provider PIN: 1234"
Write-Host "Test Patient: 0200123456"