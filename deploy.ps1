# Afya Medical EHR - Firebase Deployment Script (PowerShell)
# This script automates the deployment process for the Firebase + Node.js system

param(
    [switch]$SkipDeps,
    [switch]$Quick,
    [switch]$Help
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Blue
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Write-Step($message) {
    Write-Host "[STEP] $message" -ForegroundColor Magenta
}

# Show help
if ($Help) {
    Write-Host "Afya Medical EHR - Firebase Deployment Script"
    Write-Host "Usage: .\deploy.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipDeps     Skip dependency installation"
    Write-Host "  -Quick        Quick deployment (functions and hosting only)"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    exit 0
}

Write-Host "🏥 Afya Medical EHR - Firebase Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if Firebase CLI is installed
function Test-FirebaseCLI {
    Write-Info "Checking Firebase CLI installation..."
    try {
        $null = Get-Command firebase -ErrorAction Stop
        Write-Success "Firebase CLI is installed"
        return $true
    }
    catch {
        Write-Error "Firebase CLI is not installed!"
        Write-Info "Installing Firebase CLI..."
        npm install -g firebase-tools
        Write-Success "Firebase CLI installed"
        return $true
    }
}

# Check if user is logged in to Firebase
function Test-FirebaseAuth {
    Write-Info "Checking Firebase authentication..."
    try {
        $result = firebase projects:list 2>$null
        Write-Success "Firebase authentication verified"
        return $true
    }
    catch {
        Write-Warning "Not logged in to Firebase"
        Write-Info "Please log in to Firebase..."
        firebase login
        return $true
    }
}

# Install dependencies
function Install-Dependencies {
    Write-Step "Installing dependencies..."
    
    # Root dependencies
    Write-Info "Installing root dependencies..."
    npm install
    
    # Functions dependencies
    Write-Info "Installing functions dependencies..."
    Push-Location functions
    npm install
    Pop-Location
    
    # Web dependencies
    Write-Info "Installing web dependencies..."
    Push-Location public
    npm install
    Pop-Location
    
    Write-Success "All dependencies installed"
}

# Build web application
function Build-WebApp {
    Write-Step "Building web application..."
    Push-Location public
    
    # Set production environment
    $env:NODE_ENV = "production"
    
    # Build the application
    npm run build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Web application built successfully"
    }
    else {
        Write-Error "Web application build failed"
        Pop-Location
        exit 1
    }
    
    Pop-Location
}

# Deploy Firestore rules and indexes
function Deploy-Firestore {
    Write-Step "Deploying Firestore rules and indexes..."
    firebase deploy --only firestore
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Firestore rules and indexes deployed"
    }
    else {
        Write-Error "Firestore deployment failed"
        exit 1
    }
}

# Deploy Cloud Functions
function Deploy-Functions {
    Write-Step "Deploying Cloud Functions..."
    firebase deploy --only functions
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Cloud Functions deployed"
    }
    else {
        Write-Error "Functions deployment failed"
        exit 1
    }
}

# Deploy web application to Firebase Hosting
function Deploy-Hosting {
    Write-Step "Deploying web application to Firebase Hosting..."
    firebase deploy --only hosting
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Web application deployed to Firebase Hosting"
    }
    else {
        Write-Error "Hosting deployment failed"
        exit 1
    }
}

# Initialize sample data
function Initialize-SampleData {
    Write-Step "Initializing sample data..."
    
    # Get the project URL
    $projectId = firebase use --show
    $functionUrl = "https://us-central1-$projectId.cloudfunctions.net/api/initialize-data"
    
    Write-Info "Calling initialization endpoint: $functionUrl"
    
    try {
        # Call the initialization endpoint
        $response = Invoke-RestMethod -Uri $functionUrl -Method Post -ContentType "application/json" -Body "{}" -TimeoutSec 30
        Write-Success "Sample data initialized"
    }
    catch {
        Write-Warning "Sample data initialization may have failed (this is optional)"
    }
}

# Display deployment information
function Show-DeploymentInfo {
    $projectId = firebase use --show
    
    Write-Host ""
    Write-Success "🎉 Deployment completed successfully!"
    Write-Host ""
    Write-Host "📱 USSD System Information:" -ForegroundColor Cyan
    Write-Host "   Webhook URL: https://us-central1-$projectId.cloudfunctions.net/api/ussd/callback"
    Write-Host "   Set this URL in your Africa's Talking USSD service"
    Write-Host ""
    Write-Host "🌐 Web Dashboard:" -ForegroundColor Cyan
    Write-Host "   URL: https://$projectId.web.app"
    Write-Host "   Alternative: https://$projectId.firebaseapp.com"
    Write-Host ""
    Write-Host "🔧 Management URLs:" -ForegroundColor Cyan
    Write-Host "   Firebase Console: https://console.firebase.google.com/project/$projectId"
    Write-Host "   Functions Logs: https://console.firebase.google.com/project/$projectId/functions/logs"
    Write-Host "   Firestore Data: https://console.firebase.google.com/project/$projectId/firestore"
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Configure Africa's Talking USSD webhook"
    Write-Host "   2. Test USSD functionality: Dial *714# (or your configured code)"
    Write-Host "   3. Access web dashboard to manage the system"
    Write-Host "   4. Monitor logs for any issues"
    Write-Host ""
    Write-Warning "Remember to update your environment variables if needed!"
}

# Main deployment function
function Main {
    Write-Host "Starting deployment process..." -ForegroundColor Green
    Write-Host ""
    
    try {
        # Check prerequisites
        Test-FirebaseCLI
        Test-FirebaseAuth
        
        if ($Quick) {
            Write-Info "Quick deployment mode - deploying functions and hosting only"
            Deploy-Functions
            Deploy-Hosting
        }
        else {
            # Full deployment process
            if (-not $SkipDeps) {
                Install-Dependencies
            }
            else {
                Write-Warning "Skipping dependency installation"
            }
            
            Build-WebApp
            Deploy-Firestore
            Deploy-Functions
            Deploy-Hosting
            
            # Optional: Initialize sample data
            $initData = Read-Host "Do you want to initialize sample data? (y/N)"
            if ($initData -match "^[Yy]") {
                Initialize-SampleData
            }
        }
        
        Show-DeploymentInfo
    }
    catch {
        Write-Error "Deployment failed! Error: $_"
        exit 1
    }
}

# Run main function
Main