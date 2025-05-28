#!/bin/bash

# Afya Medical EHR - Quick Start Script for Firebase Migration
# This script sets up the entire Firebase + Node.js system in one go

set -e  # Exit on any error

echo "🏥 Afya Medical EHR - Firebase Migration Quick Start"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed! Please install Node.js 18+ first."
        exit 1
    fi
    
    node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$node_version" -lt 18 ]; then
        print_error "Node.js version 18 or higher is required. Current version: $(node --version)"
        exit 1
    fi
    
    print_success "Node.js $(node --version) is installed"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed!"
        exit 1
    fi
    
    print_success "npm $(npm --version) is installed"
}

# Install Firebase CLI
install_firebase_cli() {
    print_step "Installing Firebase CLI..."
    
    if command -v firebase &> /dev/null; then
        print_status "Firebase CLI already installed: $(firebase --version)"
    else
        print_status "Installing Firebase CLI globally..."
        npm install -g firebase-tools
        print_success "Firebase CLI installed"
    fi
}

# Setup project structure
setup_project_structure() {
    print_step "Setting up project structure..."
    
    # Create directories if they don't exist
    mkdir -p functions
    mkdir -p web/src/{views,components,services,router}
    mkdir -p web/public
    
    print_success "Project structure created"
}

# Install dependencies
install_dependencies() {
    print_step "Installing dependencies..."
    
    # Root dependencies
    print_status "Installing root dependencies..."
    if [ -f "package.json" ]; then
        npm install
    else
        print_warning "No root package.json found, skipping root dependencies"
    fi
    
    # Functions dependencies
    print_status "Installing functions dependencies..."
    if [ -f "functions/package.json" ]; then
        cd functions
        npm install
        cd ..
        print_success "Functions dependencies installed"
    else
        print_warning "No functions/package.json found"
    fi
    
    # Web dependencies
    print_status "Installing web dependencies..."
    if [ -f "web/package.json" ]; then
        cd web
        npm install
        cd ..
        print_success "Web dependencies installed"
    else
        print_warning "No web/package.json found"
    fi
}

# Setup environment files
setup_environment() {
    print_step "Setting up environment files..."
    
    # Functions environment
    if [ ! -f "functions/.env" ]; then
        print_status "Creating functions/.env from template..."
        if [ -f ".env.example" ]; then
            cp .env.example functions/.env
            print_warning "Please edit functions/.env with your actual values"
        else
            cat > functions/.env << EOF
# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id

# Africa's Talking
AFRICASTALKING_API_KEY=your-africastalking-api-key
AFRICASTALKING_USERNAME=your-africastalking-username

# Application
NODE_ENV=development
SECRET_KEY=your-secret-key-change-in-production
EOF
            print_warning "Created basic functions/.env - please update with your values"
        fi
    else
        print_status "functions/.env already exists"
    fi
    
    # Web environment
    if [ ! -f "web/.env.local" ]; then
        print_status "Creating web/.env.local..."
        cat > web/.env.local << EOF
# Vue.js Configuration
VUE_APP_API_BASE_URL=http://localhost:5001/your-project-id/us-central1/api
VUE_APP_FIREBASE_PROJECT_ID=your-firebase-project-id
EOF
        print_warning "Created web/.env.local - please update with your project ID"
    else
        print_status "web/.env.local already exists"
    fi
}

# Initialize Firebase
initialize_firebase() {
    print_step "Initializing Firebase..."
    
    if [ ! -f "firebase.json" ]; then
        print_status "Firebase not initialized. Please run the following commands manually:"
        echo ""
        echo "1. firebase login"
        echo "2. firebase init"
        echo "   - Select: Functions, Firestore, Hosting"
        echo "   - Choose your Firebase project"
        echo "   - Set functions source to 'functions'"
        echo "   - Set hosting public directory to 'web/dist'"
        echo ""
        print_warning "Then run this script again"
        exit 1
    else
        print_success "Firebase configuration found"
    fi
}

# Build web application
build_web() {
    print_step "Building web application..."
    
    if [ -f "web/package.json" ]; then
        cd web
        print_status "Building Vue.js application..."
        npm run build
        cd ..
        print_success "Web application built"
    else
        print_warning "No web application to build"
    fi
}

# Start development environment
start_development() {
    print_step "Starting development environment..."
    
    print_status "Starting Firebase emulators..."
    print_status "This will start:"
    print_status "  - Functions: http://localhost:5001"
    print_status "  - Firestore: http://localhost:8080"
    print_status "  - Hosting: http://localhost:5000"
    print_status "  - Emulator UI: http://localhost:4000"
    echo ""
    print_status "Press Ctrl+C to stop the emulators"
    echo ""
    
    # Run emulators
    firebase emulators:start
}

# Create sample data
create_sample_data() {
    print_step "Creating sample data..."
    
    print_status "Waiting for functions to be ready..."
    sleep 5
    
    # Try to initialize sample data
    PROJECT_ID=$(firebase use --show 2>/dev/null || echo "your-project-id")
    FUNCTION_URL="http://localhost:5001/${PROJECT_ID}/us-central1/api/initialize-data"
    
    print_status "Calling initialization endpoint: $FUNCTION_URL"
    
    curl -X POST "$FUNCTION_URL" \
         -H "Content-Type: application/json" \
         -d '{}' \
         --max-time 30 \
         --connect-timeout 10 || print_warning "Sample data creation may have failed (this is optional)"
    
    print_success "Sample data creation attempted"
}

# Display helpful information
show_info() {
    echo ""
    print_success "🎉 Setup completed!"
    echo ""
    echo "📱 USSD Testing:"
    echo "   Local Test: http://localhost:5000/ussd-test"
    echo "   USSD Code: *384*15897# (configure in Africa's Talking)"
    echo ""
    echo "🌐 Web Dashboard:"
    echo "   Local: http://localhost:5000"
    echo "   Emulator UI: http://localhost:4000"
    echo ""
    echo "🔧 Development Commands:"
    echo "   Start emulators: npm run dev"
    echo "   Deploy: npm run deploy"
    echo "   View logs: firebase functions:log"
    echo ""
    echo "📋 Demo Credentials:"
    echo "   Provider PINs: 1234, 5678, 9012"
    echo "   Test Phones: 0200123456, 0240234567"
    echo ""
    echo "⚠️  Important:"
    echo "   1. Update functions/.env with your actual API keys"
    echo "   2. Update web/.env.local with your Firebase project ID"
    echo "   3. Configure Africa's Talking webhook when deploying"
    echo ""
}

# Main execution
main() {
    print_status "Starting Afya Medical EHR Firebase setup..."
    echo ""
    
    # Run setup steps
    check_prerequisites
    install_firebase_cli
    setup_project_structure
    install_dependencies
    setup_environment
    initialize_firebase
    
    # Ask user what to do next
    echo ""
    echo "What would you like to do?"
    echo "1. Start development environment (recommended)"
    echo "2. Build and deploy to Firebase"
    echo "3. Just show info and exit"
    echo ""
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            print_status "Starting development environment..."
            if [ -f "web/package.json" ]; then
                build_web
            fi
            show_info
            start_development
            ;;
        2)
            print_status "Building and deploying..."
            if [ -f "web/package.json" ]; then
                build_web
            fi
            firebase deploy
            show_info
            ;;
        3)
            show_info
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'print_warning "Setup interrupted by user"' INT

# Run main function
main "$@"