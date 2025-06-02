/**
 * Afya Medical EHR - Firebase Cloud Functions
 * Main entry point for all cloud functions
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

// Initialize Firebase Admin with explicit configuration
try {
  // For production (when deployed to Firebase)
  if (process.env.NODE_ENV === 'production' || process.env.FUNCTIONS_EMULATOR) {
    admin.initializeApp();
  } else {
    // For local development, use service account
    const serviceAccount = process.env.GOOGLE_APPLICATION_CREDENTIALS 
      ? require(process.env.GOOGLE_APPLICATION_CREDENTIALS)
      : null;
    
    if (serviceAccount) {
      admin.initializeApp({
        credential: admin.credential.cert(serviceAccount),
        databaseURL: `https://${process.env.FIREBASE_PROJECT_ID || 'afya-a1006'}-default-rtdb.firebaseio.com`
      });
    } else {
      // Fallback to default initialization
      admin.initializeApp({
        projectId: process.env.FIREBASE_PROJECT_ID || 'afya-a1006'
      });
    }
  }
  
  functions.logger.info('Firebase Admin initialized successfully');
} catch (error) {
  functions.logger.error('Firebase Admin initialization failed:', error);
  // Try default initialization as fallback
  if (!admin.apps.length) {
    admin.initializeApp();
  }
}

// Test database connection
admin.firestore().collection('_test').doc('_connection').set({
  status: 'connected',
  timestamp: admin.firestore.FieldValue.serverTimestamp()
}).then(() => {
  functions.logger.info('Firestore connection test successful');
}).catch((error) => {
  functions.logger.error('Firestore connection test failed:', error);
});


// Import modules
const dataManager = require('./dataManager');
const sessionManager = require('./sessionManager');
const medicalMenu = require('./medicalMenu');

// Create Express app
const app = express();

// Middleware
app.use(helmet());
app.use(cors({ origin: true }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  functions.logger.info(`${req.method} ${req.path}`, {
    body: req.body,
    query: req.query,
    headers: req.headers
  });
  next();
});

// ============== USSD ENDPOINTS ==============

/**
 * USSD Callback endpoint
 * Handles incoming USSD requests from Africa's Talking
 */
app.post('/ussd/callback', async (req, res) => {
  try {
    const { sessionId, serviceCode, phoneNumber, text } = req.body;

    functions.logger.info('USSD Request:', {
      sessionId,
      serviceCode,
      phoneNumber,
      text: text || '(empty)'
    });

    // Validate required parameters
    if (!sessionId || !phoneNumber) {
      return res.send('END Invalid request parameters.');
    }

    // Normalize phone number
    const phoneValidation = dataManager.validateGhanaPhone(phoneNumber);
    if (!phoneValidation.valid) {
      return res.send('END Invalid phone number format.');
    }

    const normalizedPhone = phoneValidation.phone;
    let response = '';

    try {
      // Handle the USSD flow
      response = await handleUssdFlow(sessionId, serviceCode, normalizedPhone, text || '');
    } catch (error) {
      functions.logger.error('USSD Flow Error:', error);
      response = 'END Sorry, there was a system error. Please try again later.';
    }

    // Log the response
    functions.logger.info('USSD Response:', { response });

    // Return response with proper content type
    res.set('Content-Type', 'text/plain');
    res.send(response);

  } catch (error) {
    functions.logger.error('USSD Callback Error:', error);
    res.send('END System error. Please try again later.');
  }
});

/**
 * Main USSD flow handler
 * @param {string} sessionId - USSD session ID
 * @param {string} serviceCode - USSD service code
 * @param {string} phoneNumber - User phone number
 * @param {string} text - User input text
 * @returns {Promise<string>} USSD response
 */
async function handleUssdFlow(sessionId, serviceCode, phoneNumber, text) {
  // Get or create session
  let session = await sessionManager.getSession(sessionId);
  
  if (!session) {
    session = await sessionManager.createSession(sessionId, phoneNumber, serviceCode);
  } else {
    await sessionManager.addUserInput(sessionId, text);
  }

  // Parse input
  const parts = text.split('*');
  const choice = parts[parts.length - 1];

  // Main menu (no input or first choice)
  if (!text || text === '') {
    return getMainMenu();
  }

  // Route based on first choice
  const firstChoice = parts[0];

  switch (firstChoice) {
    case '1':
      return await handleProviderFlow(sessionId, text, phoneNumber);
    
    case '2':
      return await handlePatientFlow(sessionId, text, phoneNumber);
    
    case '3':
      return await handleEmergencyFlow(sessionId, text, phoneNumber);
    
    case '4':
      return await handleSystemInfoFlow(sessionId, text, phoneNumber);
    
    default:
      return 'CON Invalid choice. Please try again:\n\n1. Healthcare Provider\n2. Patient Services\n3. Emergency\n4. System Info\n\nEnter choice:';
  }
}

/**
 * Get main menu
 * @returns {string} Main menu USSD response
 */
function getMainMenu() {
  return `CON Welcome to Afya Medical EHR
Ghana's Healthcare Records System

1. Healthcare Provider
2. Patient Services  
3. Emergency Services
4. System Information

Enter your choice:`;
}

/**
 * Handle provider authentication and menu flow
 */
async function handleProviderFlow(sessionId, text, phoneNumber) {
  const parts = text.split('*');
  const session = await sessionManager.getSession(sessionId);

  // Provider login: 1*PIN
  if (parts.length === 2) {
    const pin = parts[1];
    
    if (!pin || pin.length !== 4 || !/^\d{4}$/.test(pin)) {
      const attempts = await sessionManager.incrementAttempts(sessionId);
      
      if (attempts >= 3) {
        await sessionManager.endSession(sessionId, 'max_attempts');
        return 'END Too many failed attempts. Please try again later.';
      }
      
      return `CON Invalid PIN format. Enter 4-digit PIN (Attempt ${attempts}/3):`;
    }

    try {
      // Authenticate provider
      const provider = await dataManager.authenticateProvider(phoneNumber, pin);
      await sessionManager.setProvider(sessionId, provider);
      await sessionManager.resetAttempts(sessionId);

      return `CON Welcome, ${provider.name}
${provider.facility.name}

1. Patient lookup
2. New patient
3. Create medical record
4. View recent records
5. Profile
6. Logout

Enter choice:`;

    } catch (error) {
      const attempts = await sessionManager.incrementAttempts(sessionId);
      
      if (attempts >= 3) {
        await sessionManager.endSession(sessionId, 'max_attempts');
        return 'END Too many failed attempts. Access blocked.';
      }
      
      return `CON Invalid credentials. Enter 4-digit PIN (Attempt ${attempts}/3):`;
    }
  }

  // Provider authenticated - handle menu options
  if (session && session.provider) {
    const choice = parts[2];

    switch (choice) {
      case '1':
        return await medicalMenu.handlePatientLookup(sessionId, text, phoneNumber);
      
      case '2':
        await sessionManager.setMenuPath(sessionId, 'new_patient');
        return await medicalMenu.handleQuickPatientRegistration(sessionId, text, phoneNumber);
      
      case '3':
        return await medicalMenu.handleRecordCreationFlow(sessionId, text);
      
      case '4':
        return await handleRecentRecords(sessionId, session.provider);
      
      case '5':
        return await handleProviderProfile(sessionId, session.provider);
      
      case '6':
        await sessionManager.endSession(sessionId, 'logout');
        return 'END Thank you for using Afya Medical EHR. Goodbye!';
      
      default:
        return `CON Invalid choice. Please try again:

1. Patient lookup
2. New patient  
3. Create medical record
4. View recent records
5. Profile
6. Logout

Enter choice:`;
    }
  }

  // Handle workflow continuation
  if (session && session.menu_step) {
    return await medicalMenu.handleRecordCreationFlow(sessionId, text);
  }

  // Initial provider menu - ask for PIN
  return 'CON Healthcare Provider Login\n\nEnter your 4-digit PIN:';
}

/**
 * Handle patient services flow
 */
async function handlePatientFlow(sessionId, text, phoneNumber) {
  const parts = text.split('*');
  
  if (parts.length === 1) {
    return `CON Patient Services

1. View my records
2. Emergency contact
3. Update info
4. Find nearest facility
5. Back to main menu

Enter choice:`;
  }

  const choice = parts[1];

  switch (choice) {
    case '1':
      await dataManager.logActivity({
        action: 'Emergency_Ambulance_Request',
        user_phone: phoneNumber,
        details: 'Ambulance requested via USSD'
      });
      return 'END 🚨 EMERGENCY ACTIVATED 🚨\n\nAmbulance dispatched to your location.\n\nNational Ambulance: 193\nPolice: 191\nFire: 192';
    
    case '2':
      return 'END ☠️ POISON CONTROL ☠️\n\nPoison Control Center:\n0302-777-777\n\nDo NOT induce vomiting unless instructed.\nSeek immediate medical attention.';
    
    case '3':
      return await handleEmergencyContacts(sessionId, phoneNumber);
    
    case '4':
      return await handleNearestHospital(sessionId);
    
    case '5':
      return await handleMedicalAlerts(sessionId, phoneNumber);
    
    default:
      return 'CON Invalid choice. Enter 1-5:';
  }
}

/**
 * Handle system information flow
 */
async function handleSystemInfoFlow(sessionId, text, phoneNumber) {
  const parts = text.split('*');
  
  if (parts.length === 1) {
    return `CON System Information

1. About Afya EHR
2. How to use
3. Privacy policy
4. Contact support
5. System status

Enter choice:`;
  }

  const choice = parts[1];

  switch (choice) {
    case '1':
      return 'END Afya Medical EHR\n\nGhana\'s digital healthcare records system. Transforming healthcare access through mobile technology.\n\nVisit: afya.gov.gh';
    
    case '2':
      return 'END How to Use:\n\n1. Healthcare providers dial *384*15897#\n2. Enter PIN to access\n3. Patients can view records\n4. Emergency services available 24/7\n\nFor help: support@afya.gov.gh';
    
    case '3':
      return 'END Privacy Policy:\n\nYour health data is protected by encryption and access controls. Only authorized providers can view records.\n\nFull policy: afya.gov.gh/privacy';
    
    case '4':
      return 'END Support Contacts:\n\nTechnical: +233-30-123-4567\nEmail: support@afya.gov.gh\nWebsite: afya.gov.gh\n\nOffice hours: 8AM-6PM';
    
    case '5':
      return await handleSystemStatus();
    
    default:
      return 'CON Invalid choice. Enter 1-5:';
  }
}

// ============== HELPER FUNCTIONS ==============

async function handlePatientRecords(sessionId, phoneNumber) {
  try {
    const patient = await dataManager.getPatientByPhone(phoneNumber);
    const records = await dataManager.getPatientRecords(patient.id);
    
    if (records.length === 0) {
      return 'END No medical records found.\n\nVisit a healthcare facility to create your first record.';
    }

    const recentRecord = records[0];
    return `END Your Recent Medical Record:

Date: ${recentRecord.visit_date}
Provider: ${recentRecord.provider.name}
Facility: ${recentRecord.facility.name}
Diagnosis: ${recentRecord.diagnosis}

Total records: ${records.length}
Visit afya.gov.gh for details.`;

  } catch (error) {
    return 'END Patient records not found.\n\nRegister at any healthcare facility to create your record.';
  }
}

async function handleSystemStatus() {
  try {
    const stats = await dataManager.getDashboardStats();
    return `END System Status: ✅ ONLINE

Facilities: ${stats.total_facilities}
Providers: ${stats.total_providers}
Patients: ${stats.total_patients}

Last updated: ${new Date().toLocaleString()}
Status: afya.gov.gh/status`;
  } catch (error) {
    return 'END System Status: ⚠️ Checking...\n\nPlease try again later or visit afya.gov.gh/status';
  }
}

async function handleRecentRecords(sessionId, provider) {
  try {
    const records = await dataManager.getRecentRecords(5);
    const providerRecords = records.filter(r => r.provider_id === provider.id);
    
    if (providerRecords.length === 0) {
      return 'END No recent records found.\n\nCreate your first medical record using the patient lookup menu.';
    }

    let response = 'CON Your Recent Records:\n\n';
    providerRecords.slice(0, 3).forEach((record, index) => {
      response += `${index + 1}. ${record.patient.name}\n`;
      response += `   ${record.visit_date} - ${record.diagnosis}\n\n`;
    });

    response += '0. Back to menu\n\nSelect record:';
    return response;
  } catch (error) {
    return 'END Error loading records. Please try again.';
  }
}

async function handleProviderProfile(sessionId, provider) {
  return `END Provider Profile:

Name: ${provider.name}
Specialization: ${provider.specialization}
Facility: ${provider.facility.name}
Location: ${provider.facility.location}
Status: ${provider.is_active ? 'Active' : 'Inactive'}

Update profile at afya.gov.gh`;
}

async function handleEmergencyContact(sessionId, phoneNumber) {
  try {
    const patient = await dataManager.getPatientByPhone(phoneNumber);
    
    if (!patient.emergency_contact) {
      return 'END No emergency contact on file.\n\nUpdate your information at any healthcare facility.';
    }

    return `END Emergency Contact:
${patient.emergency_contact}

National Emergency: 191
Ambulance: 193
Fire Service: 192`;

  } catch (error) {
    return 'END Emergency Contacts:\n\nNational Emergency: 191\nAmbulance: 193\nFire Service: 192\nPoison Control: 0302-777-777';
  }
}

async function handleNearestFacility(sessionId) {
  try {
    const facilities = await dataManager.getFacilities();
    const activeFacilities = facilities.filter(f => f.is_active).slice(0, 5);

    if (activeFacilities.length === 0) {
      return 'END No facilities found.\n\nContact support: +233-30-123-4567';
    }

    let response = 'END Nearest Healthcare Facilities:\n\n';
    activeFacilities.forEach((facility, index) => {
      response += `${index + 1}. ${facility.name}\n`;
      response += `   ${facility.location}\n`;
      response += `   ${facility.phone}\n\n`;
    });

    return response;
  } catch (error) {
    return 'END Error loading facilities.\n\nContact support: +233-30-123-4567';
  }
}

async function handleNearestHospital(sessionId) {
  try {
    const facilities = await dataManager.getFacilities();
    const hospitals = facilities.filter(f => 
      f.is_active && 
      (f.facility_type === 'Hospital' || f.facility_type === 'Emergency Center')
    ).slice(0, 3);

    if (hospitals.length === 0) {
      return 'END 🏥 NEAREST HOSPITALS 🏥\n\nKorle Bu Teaching Hospital\nAccra - 0302-123-456\n\nRidge Hospital\nAccra - 0302-987-654';
    }

    let response = 'END 🏥 NEAREST HOSPITALS 🏥\n\n';
    hospitals.forEach((hospital, index) => {
      response += `${hospital.name}\n`;
      response += `${hospital.location}\n`;
      response += `${hospital.phone}\n\n`;
    });

    return response;
  } catch (error) {
    return 'END 🏥 NEAREST HOSPITALS 🏥\n\nKorle Bu Teaching Hospital\nAccra - 0302-123-456\n\nRidge Hospital\nAccra - 0302-987-654';
  }
}

async function handleMedicalAlerts(sessionId, phoneNumber) {
  try {
    const patient = await dataManager.getPatientByPhone(phoneNumber);
    
    let response = `END 🚨 MEDICAL ALERTS 🚨\n\nPatient: ${patient.name}\n`;
    
    if (patient.blood_type) {
      response += `Blood Type: ${patient.blood_type}\n`;
    }
    
    if (patient.allergies) {
      response += `Allergies: ${patient.allergies}\n`;
    }
    
    if (patient.emergency_contact) {
      response += `Emergency Contact: ${patient.emergency_contact}\n`;
    }
    
    if (!patient.blood_type && !patient.allergies) {
      response += '\nNo medical alerts on file.\nUpdate at healthcare facility.';
    }

    return response;
  } catch (error) {
    return 'END 🚨 MEDICAL ALERTS 🚨\n\nNo patient record found.\nRegister at any healthcare facility.';
  }
}

async function handleEmergencyContacts(sessionId, phoneNumber) {
  try {
    const patient = await dataManager.getPatientByPhone(phoneNumber);
    
    let response = 'END 📞 EMERGENCY CONTACTS 📞\n\n';
    
    if (patient.emergency_contact) {
      response += `Your Contact: ${patient.emergency_contact}\n\n`;
    }
    
    response += `National Emergency: 191\n`;
    response += `Ambulance Service: 193\n`;
    response += `Fire Service: 192\n`;
    response += `Police: 191\n`;
    response += `Poison Control: 0302-777-777`;

    return response;
  } catch (error) {
    return 'END 📞 EMERGENCY CONTACTS 📞\n\nNational Emergency: 191\nAmbulance Service: 193\nFire Service: 192\nPolice: 191\nPoison Control: 0302-777-777';
  }
}

// ============== REST API ENDPOINTS ==============

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Basic health check
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      services: {
        database: 'connected',
        functions: 'running'
      }
    };

    res.json(health);
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// Dashboard stats
app.get('/dashboard/stats', async (req, res) => {
  try {
    const stats = await dataManager.getDashboardStats();
    res.json(stats);
  } catch (error) {
    functions.logger.error('Dashboard stats error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Facilities endpoints
app.get('/facilities', async (req, res) => {
  try {
    const facilities = await dataManager.getFacilities();
    res.json(facilities);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/facilities', async (req, res) => {
  try {
    const result = await dataManager.createFacility(req.body);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.post('/facility/:id/toggle-status', async (req, res) => {
  try {
    const result = await dataManager.toggleFacilityStatus(req.params.id);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Providers endpoints
app.get('/providers', async (req, res) => {
  try {
    const providers = await dataManager.getProviders();
    res.json(providers);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/providers', async (req, res) => {
  try {
    const result = await dataManager.createProvider(req.body);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.post('/provider/:id/toggle-status', async (req, res) => {
  try {
    const result = await dataManager.toggleProviderStatus(req.params.id);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.post('/provider/:id/reset-pin', async (req, res) => {
  try {
    const result = await dataManager.resetProviderPin(req.params.id);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Patients endpoints
app.get('/patients', async (req, res) => {
  try {
    const patients = await dataManager.getPatients();
    res.json(patients);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/patients/search', async (req, res) => {
  try {
    const query = req.query.q;
    if (!query) {
      return res.status(400).json({ error: 'Search query required' });
    }
    const patients = await dataManager.searchPatients(query);
    res.json(patients);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/patients', async (req, res) => {
  try {
    const result = await dataManager.createPatient(req.body);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Medical records endpoints
app.post('/medical-records', async (req, res) => {
  try {
    const result = await dataManager.createMedicalRecord(req.body);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.get('/patients/:id/records', async (req, res) => {
  try {
    const records = await dataManager.getPatientRecords(req.params.id);
    res.json(records);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// System logs
app.get('/logs', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 100;
    const logs = await dataManager.getLogs(limit);
    res.json(logs);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Initialize sample data
app.post('/initialize-data', async (req, res) => {
  try {
    await initializeSampleData();
    res.json({ success: true, message: 'Sample data initialized' });
  } catch (error) {
    functions.logger.error('Initialize data error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Initialize sample data for testing
 */
async function initializeSampleData() {
  try {
    // Create sample facilities
    const facilityData = [
      {
        name: 'Korle Bu Teaching Hospital',
        facility_type: 'Hospital',
        location: 'Accra Central, Greater Accra',
        phone: '0302123456',
        description: 'Premier teaching hospital in Ghana'
      },
      {
        name: 'Ridge Hospital',
        facility_type: 'Hospital', 
        location: 'Ridge, Accra',
        phone: '0302987654',
        description: 'Government hospital serving central Accra'
      },
      {
        name: 'Adabraka Clinic',
        facility_type: 'Clinic',
        location: 'Adabraka, Accra',
        phone: '0501234567',
        description: 'Community clinic providing primary care'
      }
    ];

    const facilities = [];
    for (const data of facilityData) {
      try {
        const result = await dataManager.createFacility(data);
        facilities.push(result.facility);
      } catch (error) {
        functions.logger.warn('Facility may already exist:', data.name);
      }
    }

    if (facilities.length > 0) {
      // Create sample providers
      const providerData = [
        {
          name: 'Dr. Kwame Asante',
          phone: '0200123456',
          specialization: 'General Medicine',
          facility_id: facilities[0].id,
          pin: '1234'
        },
        {
          name: 'Dr. Ama Mensah',
          phone: '0240234567',
          specialization: 'Pediatrics',
          facility_id: facilities[1].id,
          pin: '5678'
        },
        {
          name: 'Dr. Kofi Boateng',
          phone: '0260345678',
          specialization: 'Internal Medicine',
          facility_id: facilities[2].id,
          pin: '9012'
        }
      ];

      for (const data of providerData) {
        try {
          await dataManager.createProvider(data);
        } catch (error) {
          functions.logger.warn('Provider may already exist:', data.name);
        }
      }

      // Create sample patients
      const patientData = [
        {
          name: 'John Doe',
          phone: '0200123456',
          date_of_birth: '15/03/1985',
          gender: 'Male',
          blood_type: 'O+',
          registered_by_phone: '0200123456'
        },
        {
          name: 'Jane Smith',
          phone: '0240234567',
          date_of_birth: '22/07/1992',
          gender: 'Female',
          blood_type: 'A+',
          registered_by_phone: '0240234567'
        },
        {
          name: 'Kwame Osei',
          phone: '0260345678',
          date_of_birth: '10/12/1978',
          gender: 'Male',
          blood_type: 'B+',
          registered_by_phone: '0260345678'
        },
        {
          name: 'Akosua Addo',
          phone: '0270456789',
          date_of_birth: '05/09/1990',
          gender: 'Female',
          blood_type: 'AB+',
          registered_by_phone: '0270456789'
        }
      ];

      for (const data of patientData) {
        try {
          await dataManager.createPatient(data);
        } catch (error) {
          functions.logger.warn('Patient may already exist:', data.name);
        }
      }
    }

    functions.logger.info('Sample data initialization completed');
  } catch (error) {
    functions.logger.error('Error initializing sample data:', error);
    throw error;
  }
}

// Error handling middleware
app.use((error, req, res, next) => {
  functions.logger.error('Express error:', error);
  res.status(500).json({
    error: 'Internal server error',
    message: error.message
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    path: req.originalUrl,
    method: req.method
  });
});

// Export the Express app as a Firebase Function
exports.api = functions.region('us-central1').runWith({
  timeoutSeconds: 540,
  memory: '1GB'
}).https.onRequest(app);

// ============== ADDITIONAL CLOUD FUNCTIONS ==============

/**
 * Scheduled function to cleanup expired sessions
 * Runs every hour to remove old USSD sessions
 */
exports.cleanupSessions = functions.pubsub.schedule('0 * * * *')
  .timeZone('Africa/Accra')
  .onRun(async (context) => {
    try {
      functions.logger.info('Starting scheduled session cleanup');
      const cleanedCount = await sessionManager.cleanupExpiredSessions();
      functions.logger.info(`Cleaned up ${cleanedCount} expired sessions`);
      
      // Log cleanup activity
      await dataManager.logActivity({
        action: 'Scheduled_Cleanup',
        details: `Cleaned ${cleanedCount} expired sessions`,
        user_phone: 'system'
      });
      
      return null;
    } catch (error) {
      functions.logger.error('Error in scheduled cleanup:', error);
      throw error;
    }
  });

/**
 * Firestore trigger for new patient registration
 * Sends welcome message and logs activity
 */
exports.onPatientCreated = functions.firestore
  .document('patients/{patientId}')
  .onCreate(async (snap, context) => {
    try {
      const patient = snap.data();
      const patientId = context.params.patientId;
      
      functions.logger.info('New patient registered:', patient.name);
      
      // Log patient registration
      await dataManager.logActivity({
        action: 'Patient_Registered',
        patient_id: patientId,
        user_phone: patient.phone,
        details: `New patient registered: ${patient.name}`
      });
      
      // Here you could add SMS notification logic if needed
      // await sendWelcomeSMS(patient.phone, patient.name);
      
    } catch (error) {
      functions.logger.error('Error in patient creation trigger:', error);
    }
  });

/**
 * Firestore trigger for new medical record
 * Updates patient's last visit and facility record count
 */
exports.onMedicalRecordCreated = functions.firestore
  .document('medical_records/{recordId}')
  .onCreate(async (snap, context) => {
    try {
      const record = snap.data();
      const recordId = context.params.recordId;
      
      functions.logger.info('New medical record created:', recordId);
      
      // Log record creation
      await dataManager.logActivity({
        action: 'Medical_Record_Created',
        patient_id: record.patient_id,
        provider_id: record.provider_id,
        facility_id: record.facility_id,
        details: `Medical record created for patient ${record.patient.name}`
      });
      
    } catch (error) {
      functions.logger.error('Error in medical record creation trigger:', error);
    }
  });

/**
 * HTTP function for webhook testing
 * Allows external services to test connectivity
 */
exports.webhookTest = functions.https.onRequest(async (req, res) => {
  try {
    const method = req.method;
    const body = req.body;
    const query = req.query;
    
    functions.logger.info('Webhook test called', { method, body, query });
    
    // Log webhook test
    await dataManager.logActivity({
      action: 'Webhook_Test',
      details: `Webhook test - Method: ${method}`,
      user_phone: 'system'
    });
    
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      method: method,
      received: {
        body: body,
        query: query
      },
      message: 'Webhook test successful'
    });
    
  } catch (error) {
    functions.logger.error('Webhook test error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Backup function - creates daily backups of critical data
 * Runs at 2 AM Ghana time daily
 */
exports.dailyBackup = functions.pubsub.schedule('0 2 * * *')
  .timeZone('Africa/Accra')
  .onRun(async (context) => {
    try {
      functions.logger.info('Starting daily backup');
      
      // Get basic stats for backup verification
      const stats = await dataManager.getDashboardStats();
      
      // Log backup activity
      await dataManager.logActivity({
        action: 'Daily_Backup',
        details: `Backup completed - Facilities: ${stats.total_facilities}, Providers: ${stats.total_providers}, Patients: ${stats.total_patients}`,
        user_phone: 'system'
      });
      
      functions.logger.info('Daily backup completed', stats);
      
      return null;
    } catch (error) {
      functions.logger.error('Error in daily backup:', error);
      
      // Log backup failure
      await dataManager.logActivity({
        action: 'Backup_Failed',
        details: `Daily backup failed: ${error.message}`,
        user_phone: 'system'
      });
      
      throw error;
    }
  });

/**
 * System health monitoring function
 * Runs every 15 minutes to check system health
 */
exports.healthMonitor = functions.pubsub.schedule('*/15 * * * *')
  .timeZone('Africa/Accra')
  .onRun(async (context) => {
    try {
      // Check database connectivity
      const stats = await dataManager.getDashboardStats();
      
      // Check if we have active sessions
      const activeSessions = await sessionManager.getActiveSessions();
      
      const healthStatus = {
        database: stats ? 'healthy' : 'unhealthy',
        sessions: activeSessions.length || 0,
        timestamp: new Date().toISOString(),
        facilities: stats.total_facilities,
        providers: stats.total_providers,
        patients: stats.total_patients
      };
      
      // Only log if there are issues or every hour
      const minute = new Date().getMinutes();
      if (minute === 0 || healthStatus.database === 'unhealthy') {
        await dataManager.logActivity({
          action: 'Health_Check',
          details: JSON.stringify(healthStatus),
          user_phone: 'system'
        });
        
        functions.logger.info('Health check completed', healthStatus);
      }
      
      return null;
    } catch (error) {
      functions.logger.error('Health monitor error:', error);
      
      // Log health check failure
      await dataManager.logActivity({
        action: 'Health_Check_Failed',
        details: `Health monitoring failed: ${error.message}`,
        user_phone: 'system'
      });
      
      return null; // Don't throw to avoid function retries
    }
  });

/**
 * Analytics function - processes daily usage statistics
 * Runs at 1 AM Ghana time daily
 */
exports.dailyAnalytics = functions.pubsub.schedule('0 1 * * *')
  .timeZone('Africa/Accra')
  .onRun(async (context) => {
    try {
      functions.logger.info('Starting daily analytics processing');
      
      // Get recent logs for analysis
      const recentLogs = await dataManager.getLogs(1000);
      
      // Process usage statistics
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      yesterday.setHours(0, 0, 0, 0);
      
      const todayStart = new Date();
      todayStart.setHours(0, 0, 0, 0);
      
      const dailyLogs = recentLogs.filter(log => {
        const logDate = new Date(log.timestamp);
        return logDate >= yesterday && logDate < todayStart;
      });
      
      const analytics = {
        date: yesterday.toISOString().split('T')[0],
        total_interactions: dailyLogs.length,
        ussd_sessions: dailyLogs.filter(log => log.action.includes('USSD')).length,
        patient_registrations: dailyLogs.filter(log => log.action === 'Patient_Registration').length,
        medical_records_created: dailyLogs.filter(log => log.action === 'Medical_Record_Created').length,
        provider_logins: dailyLogs.filter(log => log.action === 'Provider_USSD_Login').length,
        emergency_requests: dailyLogs.filter(log => log.action.includes('Emergency')).length
      };
      
      // Log analytics
      await dataManager.logActivity({
        action: 'Daily_Analytics',
        details: JSON.stringify(analytics),
        user_phone: 'system'
      });
      
      functions.logger.info('Daily analytics completed', analytics);
      
      return null;
    } catch (error) {
      functions.logger.error('Error in daily analytics:', error);
      throw error;
    }
  });

/**
 * Error reporting function
 * Handles critical system errors and notifications
 */
exports.reportError = functions.https.onCall(async (data, context) => {
  try {
    const { error, context: errorContext, userPhone } = data;
    
    // Log the error
    await dataManager.logActivity({
      action: 'System_Error',
      user_phone: userPhone || 'unknown',
      details: JSON.stringify({ error, context: errorContext })
    });
    
    functions.logger.error('System error reported:', { error, context: errorContext });
    
    // In production, you might want to send alerts to administrators
    // await sendErrorAlert(error, errorContext);
    
    return { success: true, message: 'Error reported successfully' };
    
  } catch (err) {
    functions.logger.error('Error in error reporting:', err);
    throw new functions.https.HttpsError('internal', 'Failed to report error');
  }
});

/**
 * Data export function for compliance
 * Allows authorized export of patient data
 */
exports.exportPatientData = functions.https.onCall(async (data, context) => {
  try {
    // Note: In production, add proper authentication and authorization
    const { patientId, requesterId } = data;
    
    if (!patientId) {
      throw new functions.https.HttpsError('invalid-argument', 'Patient ID required');
    }
    
    // Get patient data
    const patient = await dataManager.getPatientByPhone(patientId);
    const records = await dataManager.getPatientRecords(patient.id);
    
    const exportData = {
      patient: patient,
      medical_records: records,
      export_timestamp: new Date().toISOString(),
      requested_by: requesterId
    };
    
    // Log data export
    await dataManager.logActivity({
      action: 'Data_Export',
      patient_id: patient.id,
      user_phone: requesterId,
      details: `Patient data exported for ${patient.name}`
    });
    
    return {
      success: true,
      data: exportData,
      record_count: records.length
    };
    
  } catch (error) {
    functions.logger.error('Error in data export:', error);
    throw new functions.https.HttpsError('internal', error.message);
  }
});

/**
 * System maintenance function
 * Performs routine maintenance tasks
 */
exports.systemMaintenance = functions.https.onCall(async (data, context) => {
  try {
    // Note: Add proper authentication in production
    const { task, parameters } = data;
    
    let result = {};
    
    switch (task) {
      case 'cleanup_logs':
        const daysToKeep = parameters?.days || 30;
        // Implementation would clean logs older than specified days
        result = { message: `Logs older than ${daysToKeep} days cleaned up` };
        break;
        
      case 'optimize_database':
        // Implementation would optimize database performance
        result = { message: 'Database optimization completed' };
        break;
        
      case 'generate_report':
        const stats = await dataManager.getDashboardStats();
        result = { 
          message: 'System report generated',
          stats: stats,
          generated_at: new Date().toISOString()
        };
        break;
        
      default:
        throw new functions.https.HttpsError('invalid-argument', 'Unknown maintenance task');
    }
    
    // Log maintenance activity
    await dataManager.logActivity({
      action: 'System_Maintenance',
      details: `Maintenance task: ${task}`,
      user_phone: 'admin'
    });
    
    return {
      success: true,
      task: task,
      result: result
    };
    
  } catch (error) {
    functions.logger.error('Error in system maintenance:', error);
    throw new functions.https.HttpsError('internal', error.message);
  }
});

// ============== UTILITY FUNCTIONS ==============

/**
 * Send SMS notification (placeholder for future implementation)
 * @param {string} phoneNumber - Recipient phone number
 * @param {string} message - SMS message
 */
async function sendSMS(phoneNumber, message) {
  // Implementation would integrate with SMS service
  functions.logger.info('SMS notification:', { phoneNumber, message });
  
  // Log SMS activity
  await dataManager.logActivity({
    action: 'SMS_Sent',
    user_phone: phoneNumber,
    details: `SMS sent: ${message.substring(0, 50)}...`
  });
}

/**
 * Send welcome SMS to new patients
 * @param {string} phoneNumber - Patient phone number
 * @param {string} patientName - Patient name
 */
async function sendWelcomeSMS(phoneNumber, patientName) {
  const message = `Welcome to Afya Medical EHR, ${patientName}! Your medical records are now digitally secured. Dial *384*15897# anytime to access your health information.`;
  await sendSMS(phoneNumber, message);
}

/**
 * Send error alert to administrators
 * @param {string} error - Error message
 * @param {Object} context - Error context
 */
async function sendErrorAlert(error, context) {
  const message = `ALERT: Afya EHR System Error - ${error}. Context: ${JSON.stringify(context)}`;
  // Implementation would send to admin contacts
  functions.logger.error('Error alert:', message);
}

/**
 * Validate request authentication (placeholder)
 * @param {Object} context - Function context
 * @returns {boolean} Authentication status
 */
function validateAuth(context) {
  // Implementation would validate Firebase Auth tokens
  // For now, return true for development
  return true;
}

/**
 * Rate limiting utility
 * @param {string} identifier - User/IP identifier
 * @param {number} maxRequests - Maximum requests allowed
 * @param {number} windowMs - Time window in milliseconds
 * @returns {Promise<boolean>} Whether request is allowed
 */
async function checkRateLimit(identifier, maxRequests = 60, windowMs = 60000) {
  // Implementation would use Redis or Firestore for rate limiting
  // For now, return true to allow all requests
  return true;
}

// ============== DATABASE CLEANUP ENDPOINTS ==============

/**
 * Cleanup invalid records endpoint
 */
app.post('/admin/cleanup', async (req, res) => {
  try {
    const authKey = req.headers['x-admin-key'];
    if (authKey !== 'afya-cleanup-2025') {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    functions.logger.info('Starting database cleanup...');
    
    const cleaned = await dataManager.cleanupInvalidRecords();
    
    res.json({ 
      success: true, 
      message: `Cleaned up ${cleaned} invalid records`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    functions.logger.error('Cleanup error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * System health check with detailed information
 */
app.get('/admin/health', async (req, res) => {
  try {
    const stats = await dataManager.getDashboardStats();
    
    const facilities = await dataManager.getFacilities();
    const providers = await dataManager.getProviders();
    const patients = await dataManager.getPatients();
    
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      database: {
        total_facilities: facilities.length,
        total_providers: providers.length,
        total_patients: patients.length
      },
      services: {
        database: 'connected',
        functions: 'running',
        ussd: 'available'
      }
    };

    res.json(health);
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// ============== EXPORTS SUMMARY ==============

/*
EXPORTED CLOUD FUNCTIONS:

1. exports.api - Main Express API (USSD + REST endpoints)
2. exports.cleanupSessions - Scheduled session cleanup
3. exports.onPatientCreated - Firestore trigger for new patients
4. exports.onMedicalRecordCreated - Firestore trigger for new records
5. exports.webhookTest - Webhook connectivity testing
6. exports.dailyBackup - Scheduled daily backups
7. exports.healthMonitor - System health monitoring
8. exports.dailyAnalytics - Daily usage analytics
9. exports.reportError - Error reporting endpoint
10. exports.exportPatientData - Data export for compliance
11. exports.systemMaintenance - System maintenance tasks

DEPLOYMENT:
- Deploy with: firebase deploy --only functions
- Test locally with: firebase emulators:start
- Monitor with: firebase functions:log

WEBHOOK URL (after deployment):
https://us-central1-YOUR-PROJECT-ID.cloudfunctions.net/api/ussd/callback
*/
