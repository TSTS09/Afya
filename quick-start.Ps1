# Afya Medical EHR - Quick Start Script (PowerShell)
# This script sets up the entire Firebase + Node.js system in one go

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🏥 Afya Medical EHR - Firebase Migration Quick Start" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# Colors for output
function Write-Step($message) {
    Write-Host "[STEP] $message" -ForegroundColor Magenta
}

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

# Check prerequisites
function Test-Prerequisites {
    Write-Step "Checking prerequisites..."
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        $versionNumber = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
        
        if ($versionNumber -lt 18) {
            Write-Error "Node.js version 18 or higher is required. Current version: $nodeVersion"
            exit 1
        }
        
        Write-Success "Node.js $nodeVersion is installed"
    }
    catch {
        Write-Error "Node.js is not installed! Please install Node.js 18+ first."
        exit 1
    }
    
    # Check npm
    try {
        $npmVersion = npm --version
        Write-Success "npm $npmVersion is installed"
    }
    catch {
        Write-Error "npm is not installed!"
        exit 1
    }
}

# Install Firebase CLI
function Install-FirebaseCLI {
    Write-Step "Installing Firebase CLI..."
    
    try {
        $firebaseVersion = firebase --version
        Write-Info "Firebase CLI already installed: $firebaseVersion"
    }
    catch {
        Write-Info "Installing Firebase CLI globally..."
        npm install -g firebase-tools
        Write-Success "Firebase CLI installed"
    }
}

# Setup project structure
function New-ProjectStructure {
    Write-Step "Setting up project structure..."
    
    # Create directories if they don't exist
    $directories = @(
        "functions",
        "public\src\views",
        "public\src\components", 
        "public\src\services",
        "public\src\router",
        "public\public"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Project structure created"
}

# Install dependencies
function Install-Dependencies {
    Write-Step "Installing dependencies..."
    
    # Root dependencies
    Write-Info "Installing root dependencies..."
    if (Test-Path "package.json") {
        npm install
    }
    else {
        Write-Warning "No root package.json found, skipping root dependencies"
    }
    
    # Functions dependencies
    Write-Info "Installing functions dependencies..."
    if (Test-Path "functions\package.json") {
        Push-Location functions
        npm install
        Pop-Location
        Write-Success "Functions dependencies installed"
    }
    else {
        Write-Warning "No functions\package.json found"
    }
    
    # Web dependencies
    Write-Info "Installing web dependencies..."
    if (Test-Path "public\package.json") {
        Push-Location public
        npm install
        Pop-Location
        Write-Success "Web dependencies installed"
    }
    else {
        Write-Warning "No public\package.json found"
    }
}

# Setup environment files
function New-EnvironmentFiles {
    Write-Step "Setting up environment files..."
    
    # Functions environment
    if (!(Test-Path "functions\.env")) {
        Write-Info "Creating functions\.env from template..."
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" "functions\.env"
            Write-Warning "Please edit functions\.env with your actual values"
        }
        else {
            $envContent = @"
# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id

# Africa's Talking
AFRICASTALKING_API_KEY=your-africastalking-api-key
AFRICASTALKING_USERNAME=your-africastalking-username

# Application
NODE_ENV=development
SECRET_KEY=your-secret-key-change-in-production
"@
            Set-Content -Path "functions\.env" -Value $envContent
            Write-Warning "Created basic functions\.env - please update with your values"
        }
    }
    else {
        Write-Info "functions\.env already exists"
    }
    
    # Web environment
    if (!(Test-Path "public\.env.local")) {
        Write-Info "Creating public\.env.local..."
        $webEnvContent = @"
# Vue.js Configuration
VUE_APP_API_BASE_URL=http://localhost:5001/your-project-id/us-central1/api
VUE_APP_FIREBASE_PROJECT_ID=your-firebase-project-id
"@
        Set-Content -Path "public\.env.local" -Value $webEnvContent
        Write-Warning "Created public\.env.local - please update with your project ID"
    }
    else {
        Write-Info "public\.env.local already exists"
    }
}

# Initialize Firebase
function Initialize-Firebase {
    Write-Step "Initializing Firebase..."
    
    if (!(Test-Path "firebase.json")) {
        Write-Info "Firebase not initialized. Please run the following commands manually:"
        Write-Host ""
        Write-Host "1. firebase login" -ForegroundColor Yellow
        Write-Host "2. firebase init" -ForegroundColor Yellow
        Write-Host "   - Select: Functions, Firestore, Hosting" -ForegroundColor Yellow
        Write-Host "   - Choose your Firebase project" -ForegroundColor Yellow
        Write-Host "   - Set functions source to 'functions'" -ForegroundColor Yellow
        Write-Host "   - Set hosting public directory to 'public/dist'" -ForegroundColor Yellow
        Write-Host ""
        Write-Warning "Then run this script again"
        exit 1
    }
    else {
        Write-Success "Firebase configuration found"
    }
}

# Build web application
function Build-WebApp {
    Write-Step "Building web application..."
    
    if (Test-Path "public\package.json") {
        Push-Location public
        Write-Info "Building Vue.js application..."
        npm run build
        Pop-Location
        Write-Success "Web application built"
    }
    else {
        Write-Warning "No web application to build"
    }
}

# Start development environment
function Start-Development {
    Write-Step "Starting development environment..."
    
    Write-Info "Starting Firebase emulators..."
    Write-Info "This will start:"
    Write-Info "  - Functions: http://localhost:5001"
    Write-Info "  - Firestore: http://localhost:8080"
    Write-Info "  - Hosting: http://localhost:5000"
    Write-Info "  - Emulator UI: http://localhost:4000"
    Write-Host ""
    Write-Info "Press Ctrl+C to stop the emulators"
    Write-Host ""
    
    # Run emulators
    firebase emulators:start
}

# Create sample data
function New-SampleData {
    Write-Step "Creating sample data..."
    
    Write-Info "Waiting for functions to be ready..."
    Start-Sleep -Seconds 5
    
    # Try to initialize sample data
    try {
        $projectId = firebase use --show
    }
    catch {
        $projectId = "your-project-id"
    }
    
    $functionUrl = "http://localhost:5001/$projectId/us-central1/api/initialize-data"
    
    Write-Info "Calling initialization endpoint: $functionUrl"
    
    try {
        $response = Invoke-RestMethod -Uri $functionUrl -Method Post -ContentType "application/json" -Body "{}" -TimeoutSec 30
        Write-Success "Sample data created successfully"
    }
    catch {
        Write-Warning "Sample data creation may have failed (this is optional)"
    }
}

# Display helpful information
function Show-Info {
    Write-Host ""
    Write-Success "🎉 Setup completed!"
    Write-Host ""
    Write-Host "📱 USSD Testing:" -ForegroundColor Cyan
    Write-Host "   Local Test: http://localhost:5000/ussd-test"
    Write-Host "   USSD Code: *714# (configure in Africa's Talking)"
    Write-Host ""
    Write-Host "🌐 Web Dashboard:" -ForegroundColor Cyan
    Write-Host "   Local: http://localhost:5000"
    Write-Host "   Emulator UI: http://localhost:4000"
    Write-Host ""
    Write-Host "🔧 Development Commands:" -ForegroundColor Cyan
    Write-Host "   Start emulators: firebase emulators:start"
    Write-Host "   Deploy: .\deploy.ps1"
    Write-Host "   View logs: firebase functions:log"
    Write-Host ""
    Write-Host "📋 Demo Credentials:" -ForegroundColor Cyan
    Write-Host "   Provider PINs: 1234, 5678, 9012"
    Write-Host "   Test Phones: 0200123456, 0240234567"
    Write-Host ""
    Write-Host "⚠️  Important:" -ForegroundColor Yellow
    Write-Host "   1. Update functions\.env with your actual API keys"
    Write-Host "   2. Update public\.env.local with your Firebase project ID"
    Write-Host "   3. Configure Africa's Talking webhook when deploying"
    Write-Host ""
}

# Main execution
function Main {
    Write-Info "Starting Afya Medical EHR Firebase setup..."
    Write-Host ""
    
    try {
        # Run setup steps
        Test-Prerequisites
        Install-FirebaseCLI
        New-ProjectStructure
        Install-Dependencies
        New-EnvironmentFiles
        Initialize-Firebase
        
        # Ask user what to do next
        Write-Host ""
        Write-Host "What would you like to do?" -ForegroundColor Cyan
        Write-Host "1. Start development environment (recommended)"
        Write-Host "2. Build and deploy to Firebase"
        Write-Host "3. Just show info and exit"
        Write-Host ""
        $choice = Read-Host "Enter your choice (1-3)"
        
        switch ($choice) {
            "1" {
                Write-Info "Starting development environment..."
                if (Test-Path "public\package.json") {
                    Build-WebApp
                }
                Show-Info
                Start-Development
            }
            "2" {
                Write-Info "Building and deploying..."
                if (Test-Path "public\package.json") {
                    Build-WebApp
                }
                firebase deploy
                Show-Info
            }
            "3" {
                Show-Info
            }
            default {
                Write-Error "Invalid choice"
                exit 1
            }
        }
    }
    catch {
        Write-Error "Setup failed! Error: $_"
        exit 1
    }
}

# Handle script interruption
trap {
    Write-Warning "Setup interrupted by user"
}

# Run main function
Main