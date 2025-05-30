# 🏥 Afya Medical EHR

**Ghana's Healthcare Records System - USSD + Web Dashboard**

Afya Medical EHR is an Electronic Health Records system designed for Ghana's healthcare ecosystem. It combines USSD accessibility (works on any mobile phone) with a modern web dashboard for comprehensive healthcare management.

## 🌟 Key Features

### 📱 Universal Access
- **USSD Interface**: Works on any mobile phone - dial `*384*15897#`
- **Web Dashboard**: Modern Vue.js interface for administration
- **No Internet Required**: USSD works on basic feature phones
- **Ghana-Optimized**: Built for local networks and infrastructure

### 🏥 Healthcare Management
- **Provider Registration**: Secure PIN-based authentication
- **Facility Management**: Hospitals, clinics, health centers
- **Patient Records**: Comprehensive medical history tracking
- **Medical Records**: Digital consultation notes and prescriptions

### 🔒 Security & Privacy  
- **Encrypted Data**: End-to-end encryption for medical data
- **Role-Based Access**: Providers only see authorized information
- **Audit Logging**: Complete activity tracking
- **HIPAA-Compliant**: International healthcare data standards

## 🚀 Technology Stack

- **Backend**: Firebase Cloud Functions (Node.js + Express)
- **Database**: Cloud Firestore (NoSQL)
- **Frontend**: Vue.js 3 + Vuetify (Material Design)
- **Hosting**: Firebase Hosting
- **USSD**: Africa's Talking integration

## ⚡ Quick Start

### Windows Users (PowerShell - Recommended)
```powershell
# Clone repository
git clone https://github.com/your-username/afya-medical-ehr.git
cd afya-medical-ehr

# Run setup script
.\quick-start.ps1
```

### Windows Users (Command Prompt)
```cmd
# Clone repository
git clone https://github.com/your-username/afya-medical-ehr.git
cd afya-medical-ehr

# Run setup script
deploy.cmd --help
```

### Linux/Mac Users
```bash
# Clone repository
git clone https://github.com/your-username/afya-medical-ehr.git
cd afya-medical-ehr

# Run setup script
chmod +x quick-start.sh
./quick-start.sh
```

## 🛠️ Manual Setup

### Prerequisites
- **Node.js** 18 or higher
- **Firebase CLI** (`npm install -g firebase-tools`)
- **Firebase Project** with Firestore and Functions enabled
- **Africa's Talking Account** for USSD services

### 1. Install Dependencies
```bash
# Root dependencies
npm install

# Functions dependencies
cd functions && npm install && cd ..

# Web dependencies  
cd public && npm install && cd ..
```

### 2. Firebase Configuration
```bash
# Login to Firebase
firebase login

# Initialize Firebase (select Functions, Firestore, Hosting)
firebase init

# Set your project
firebase use your-project-id
```

**Important**: When asked for hosting public directory, use `public/dist` (not `public`)

### 3. Environment Setup
```bash
# Copy and edit functions environment
cp .env.example functions/.env
# Edit functions/.env with your actual values:
# - FIREBASE_PROJECT_ID
# - AFRICASTALKING_API_KEY  
# - AFRICASTALKING_USERNAME
```

### 4. Build and Deploy
```bash
# Build web application
cd public && npm run build && cd ..

# Deploy everything
firebase deploy

# Or use deployment scripts
.\deploy.ps1          # Windows PowerShell
deploy.cmd            # Windows Command Prompt  
./deploy.sh           # Linux/Mac
```

## 📱 USSD Configuration

### Africa's Talking Setup
1. Login to your Africa's Talking account
2. Go to USSD services
3. Create new USSD code (e.g., `*384*15897#`)
4. Set webhook URL: `https://us-central1-YOUR-PROJECT-ID.cloudfunctions.net/api/ussd/callback`

### Testing USSD
- **Local Testing**: Use web interface at `/ussd-test`
- **Live Testing**: Dial your USSD code on mobile phone

## 🎯 Usage Guide

### For Healthcare Providers
1. **Get Registered**: Admin registers your facility and creates your account
2. **Access USSD**: Dial `*384*15897#` → Select "Healthcare Provider" → Enter PIN
3. **Workflows**:
   - Patient lookup by phone/name
   - Register new patients
   - Create medical records
   - View patient history

### For Patients  
1. **Get Registered**: Visit any participating healthcare facility
2. **Access Records**: Dial `*384*15897#` → Select "Patient Services"
3. **Emergency**: Dial `*384*15897#` → Select "Emergency Services"

### For Administrators
1. **Web Dashboard**: Access at your Firebase hosting URL
2. **Manage System**: Register facilities, providers, view analytics
3. **Monitor**: Check system logs and health status

## 📋 Demo Credentials

**Provider PINs**:
- `1234` - Dr. Kwame Asante (General Medicine)
- `5678` - Dr. Ama Mensah (Pediatrics) 
- `9012` - Dr. Kofi Boateng (Internal Medicine)

**Test Phone Numbers**:
- `0200123456` - John Doe
- `0240234567` - Jane Smith
- `0260345678` - Kwame Osei

## 🔧 Development Commands

```bash
# Start local development
npm run dev                    # Start Firebase emulators

# Build and deploy
npm run build                  # Build web app
npm run deploy                 # Deploy everything
npm run deploy:functions       # Deploy functions only
npm run deploy:hosting         # Deploy hosting only

# Monitoring
npm run logs                   # View function logs
firebase functions:log         # Alternative log viewing

# Testing
cd functions && npm test       # Run function tests
```

## 🏗️ Project Structure

```
afya-medical-ehr/
├── functions/                 # Firebase Cloud Functions
│   ├── index.js              # Main API endpoints
│   ├── dataManager.js        # Database operations
│   ├── sessionManager.js     # USSD session handling
│   ├── medicalMenu.js        # Medical workflow logic
│   └── package.json
├── public/                    # Vue.js Web Application
│   ├── src/
│   │   ├── views/            # Vue.js pages
│   │   ├── components/       # Reusable components
│   │   ├── services/         # API services
│   │   └── router/           # Vue Router config
│   ├── dist/                 # Built files (auto-generated)
│   └── package.json
├── firebase.json              # Firebase configuration
├── firestore.rules           # Database security rules
├── deploy.ps1                # Windows deployment script
├── quick-start.ps1           # Windows setup script
└── package.json              # Root package configuration
```

## 🔍 Troubleshooting

### Common Issues

**USSD Not Working**:
```bash
# Check webhook URL in Africa's Talking console
# Verify function deployment
firebase functions:log --only api
```

**Web App Routes Not Working**:
- Ensure `firebase.json` hosting public directory is `public/dist`
- Check that `npm run build` was run in `public/` directory
- Verify rewrites are configured for SPA routing

**Database Connection Issues**:
```bash
# Check Firestore rules
firebase firestore:rules:get

# Verify function permissions
firebase functions:log
```

## 🌍 Deployment URLs

After deployment, your system will be available at:

- **Web Dashboard**: `https://YOUR-PROJECT-ID.web.app`
- **USSD Webhook**: `https://us-central1-YOUR-PROJECT-ID.cloudfunctions.net/api/ussd/callback`  
- **Firebase Console**: `https://console.firebase.google.com/project/YOUR-PROJECT-ID`

## 📞 Support

- **Documentation**: Check inline code comments and Firebase docs
- **Issues**: Create GitHub issue for bugs
- **USSD Testing**: Use built-in web interface at `/ussd-test`

## 📄 License

MIT License - see LICENSE file for details.

---

**Built for Ghana's Healthcare Future** 🇬🇭

*Making healthcare accessible to everyone, everywhere - from basic phones to smartphones.*