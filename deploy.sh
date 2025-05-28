#!/bin/bash

# Afya Medical EHR - Firebase Deployment Script
# This script automates the deployment process for the Firebase + Node.js system

set -e  # Exit on any error

echo "🏥 Afya Medical EHR - Firebase Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Firebase CLI is installed
check_firebase_cli() {
    print_status "Checking Firebase CLI installation..."
    if ! command -v firebase &> /dev/null; then
        print_error "Firebase CLI is not installed!"
        print_status "Installing Firebase CLI..."
        npm install -g firebase-tools
    else
        print_success "Firebase CLI is installed"
    fi
}

# Check if user is logged in to Firebase
check_firebase_auth() {
    print_status "Checking Firebase authentication..."
    if ! firebase projects:list &> /dev/null; then
        print_warning "Not logged in to Firebase"
        print_status "Please log in to Firebase..."
        firebase login
    else
        print_success "Firebase authentication verified"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Root dependencies
    print_status "Installing root dependencies..."
    npm install
    
    # Functions dependencies
    print_status "Installing functions dependencies..."
    cd functions
    npm install
    cd ..
    
    # Web dependencies
    print_status "Installing web dependencies..."
    cd public
    npm install
    cd ..
    
    print_success "All dependencies installed"
}

# Build web application
build_web() {
    print_status "Building web application..."
    cd public
    
    # Set production environment
    export NODE_ENV=production
    
    # Build the application
    npm run build
    
    if [ $? -eq 0 ]; then
        print_success "Web application built successfully"
    else
        print_error "Web application build failed"
        exit 1
    fi
    
    cd ..
}

# Deploy Firestore rules and indexes
deploy_firestore() {
    print_status "Deploying Firestore rules and indexes..."
    firebase deploy --only firestore
    
    if [ $? -eq 0 ]; then
        print_success "Firestore rules and indexes deployed"
    else
        print_error "Firestore deployment failed"
        exit 1
    fi
}

# Deploy Cloud Functions
deploy_functions() {
    print_status "Deploying Cloud Functions..."
    firebase deploy --only functions
    
    if [ $? -eq 0 ]; then
        print_success "Cloud Functions deployed"
    else
        print_error "Functions deployment failed"
        exit 1
    fi
}

# Deploy web application to Firebase Hosting
deploy_hosting() {
    print_status "Deploying web application to Firebase Hosting..."
    firebase deploy --only hosting
    
    if [ $? -eq 0 ]; then
        print_success "Web application deployed to Firebase Hosting"
    else
        print_error "Hosting deployment failed"
        exit 1
    fi
}

# Initialize sample data
initialize_data() {
    print_status "Initializing sample data..."
    
    # Get the project URL
    PROJECT_ID=$(firebase use --show)
    FUNCTION_URL="https://us-central1-${PROJECT_ID}.cloudfunctions.net/api/initialize-data"
    
    print_status "Calling initialization endpoint: $FUNCTION_URL"
    
    # Call the initialization endpoint
    curl -X POST "$FUNCTION_URL" \
         -H "Content-Type: application/json" \
         -d '{}' \
         --max-time 30
    
    if [ $? -eq 0 ]; then
        print_success "Sample data initialized"
    else
        print_warning "Sample data initialization may have failed (this is optional)"
    fi
}

# Display deployment information
show_deployment_info() {
    PROJECT_ID=$(firebase use --show)
    
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📱 USSD System Information:"
    echo "   Webhook URL: https://us-central1-${PROJECT_ID}.cloudfunctions.net/api/ussd/callback"
    echo "   Set this URL in your Africa's Talking USSD service"
    echo ""
    echo "🌐 Web Dashboard:"
    echo "   URL: https://${PROJECT_ID}.web.app"
    echo "   Alternative: https://${PROJECT_ID}.firebaseapp.com"
    echo ""
    echo "🔧 Management URLs:"
    echo "   Firebase Console: https://console.firebase.google.com/project/${PROJECT_ID}"
    echo "   Functions Logs: https://console.firebase.google.com/project/${PROJECT_ID}/functions/logs"
    echo "   Firestore Data: https://console.firebase.google.com/project/${PROJECT_ID}/firestore"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Configure Africa's Talking USSD webhook"
    echo "   2. Test USSD functionality: Dial *384*15897# (or your configured code)"
    echo "   3. Access web dashboard to manage the system"
    echo "   4. Monitor logs for any issues"
    echo ""
    print_warning "Remember to update your environment variables if needed!"
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    echo ""
    
    # Parse command line arguments
    SKIP_DEPS=false
    QUICK_DEPLOY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --quick)
                QUICK_DEPLOY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-deps    Skip dependency installation"
                echo "  --quick        Quick deployment (skip build, deploy functions and hosting only)"
                echo "  --help         Show this help message"
                echo ""
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    check_firebase_cli
    check_firebase_auth
    
    if [ "$QUICK_DEPLOY" = true ]; then
        print_status "Quick deployment mode - deploying functions and hosting only"
        deploy_functions
        deploy_hosting
    else
        # Full deployment process
        if [ "$SKIP_DEPS" = false ]; then
            install_dependencies
        else
            print_warning "Skipping dependency installation"
        fi
        
        build_web
        deploy_firestore
        deploy_functions
        deploy_hosting
        
        # Optional: Initialize sample data
        read -p "Do you want to initialize sample data? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            initialize_data
        fi
    fi
    
    show_deployment_info
}

# Error handling
trap 'print_error "Deployment failed! Check the error messages above."' ERR

# Run main function
main "$@"