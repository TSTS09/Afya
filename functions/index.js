/**
 * Afya Medical EMR - Firebase Cloud Functions (PWA Version)
 * Main entry point for all cloud functions - USSD components removed
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const jwt = require('jsonwebtoken');

// Initialize Firebase Admin
try {
  if (process.env.NODE_ENV === 'production' || process.env.FUNCTIONS_EMULATOR) {
    admin.initializeApp();
  } else {
    admin.initializeApp({
      projectId: process.env.FIREBASE_PROJECT_ID || 'afya-a1006'
    });
  }
  functions.logger.info('Firebase Admin initialized successfully');
} catch (error) {
  functions.logger.error('Firebase Admin initialization failed:', error);
  if (!admin.apps.length) {
    admin.initializeApp();
  }
}

// Create Express app
const app = express();

// Security and CORS middleware
app.use(helmet());
app.use(cors({ 
  origin: true,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging middleware
app.use((req, res, next) => {
  functions.logger.info(`${req.method} ${req.path}`, {
    body: req.method !== 'GET' ? req.body : undefined,
    query: Object.keys(req.query).length > 0 ? req.query : undefined
  });
  next();
});

// JWT Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'afya-medical-emr-secret-key-2024';
const JWT_EXPIRES_IN = '24h';

// ============== AUTHENTICATION MIDDLEWARE ==============

/**
 * JWT Authentication middleware
 * Verifies JWT token in Authorization header
 */
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({ 
      success: false, 
      message: 'Access token required' 
    });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      functions.logger.warn('Invalid token:', err.message);
      return res.status(403).json({ 
        success: false, 
        message: 'Invalid or expired token' 
      });
    }
    req.user = user;
    next();
  });
};

/**
 * Generate JWT token for authenticated user
 */
const generateJWT = (provider) => {
  return jwt.sign(
    { 
      id: provider.id,
      email: provider.email,
      name: provider.name,
      facilityId: provider.facilityId,
      role: provider.role || 'provider'
    },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES_IN }
  );
};

// ============== AUTHENTICATION ENDPOINTS ==============

/**
 * POST /api/auth/login
 * Authenticate provider with email/password or PIN
 */
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password, pin } = req.body;

    if (!email && !pin) {
      return res.status(400).json({
        success: false,
        message: 'Email or PIN is required'
      });
    }

    const db = admin.firestore();
    let providerQuery;

    // Query by email or PIN
    if (email) {
      providerQuery = db.collection('providers')
        .where('email', '==', email.toLowerCase())
        .limit(1);
    } else {
      providerQuery = db.collection('providers')
        .where('pin', '==', pin)
        .limit(1);
    }

    const snapshot = await providerQuery.get();

    if (snapshot.empty) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    const providerDoc = snapshot.docs[0];
    const provider = { id: providerDoc.id, ...providerDoc.data() };

    // For email login, verify password (implement password hashing in production)
    if (email && password !== provider.password) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Generate JWT token
    const token = generateJWT(provider);

    // Remove sensitive data before sending response
    delete provider.password;
    delete provider.pin;

    // Log successful authentication
    await db.collection('audit_logs').add({
      action: 'LOGIN',
      providerId: provider.id,
      providerName: provider.name,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      ip: req.ip,
      userAgent: req.headers['user-agent']
    });

    res.json({
      success: true,
      message: 'Login successful',
      provider: provider,
      token: token
    });

  } catch (error) {
    functions.logger.error('Login error:', error);
    res.status(500).json({
      success: false,
      message: 'Authentication failed'
    });
  }
});

/**
 * POST /api/auth/logout
 * Logout user (mainly for audit logging)
 */
app.post('/api/auth/logout', authenticateToken, async (req, res) => {
  try {
    const db = admin.firestore();
    
    // Log logout action
    await db.collection('audit_logs').add({
      action: 'LOGOUT',
      providerId: req.user.id,
      providerName: req.user.name,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      ip: req.ip
    });

    res.json({
      success: true,
      message: 'Logged out successfully'
    });

  } catch (error) {
    functions.logger.error('Logout error:', error);
    res.status(500).json({
      success: false,
      message: 'Logout failed'
    });
  }
});

// ============== PATIENT MANAGEMENT ENDPOINTS ==============

/**
 * GET /api/patients
 * Get patients list with search and pagination
 */
app.get('/api/patients', authenticateToken, async (req, res) => {
  try {
    const { search, phone, limit = 20, offset = 0 } = req.query;
    const db = admin.firestore();
    
    let query = db.collection('patients');
    let patients = [];

    if (phone) {
      // Search by exact phone number
      const phoneValidation = validateGhanaPhone(phone);
      if (phoneValidation.valid) {
        const snapshot = await query
          .where('phone', '==', phoneValidation.phone)
          .limit(1)
          .get();
        patients = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      }
    } else if (search && search.length >= 2) {
      // Search by name (simple text search - consider Algolia for production)
      const snapshot = await query
        .orderBy('name')
        .startAt(search.toLowerCase())
        .endAt(search.toLowerCase() + '\uf8ff')
        .limit(parseInt(limit))
        .offset(parseInt(offset))
        .get();
      patients = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } else {
      // Get recent patients
      const snapshot = await query
        .orderBy('createdAt', 'desc')
        .limit(parseInt(limit))
        .offset(parseInt(offset))
        .get();
      patients = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    }

    res.json({
      success: true,
      patients: patients,
      total: patients.length,
      hasMore: patients.length >= parseInt(limit)
    });

  } catch (error) {
    functions.logger.error('Get patients error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch patients'
    });
  }
});

/**
 * POST /api/patients
 * Create new patient
 */
app.post('/api/patients', authenticateToken, async (req, res) => {
  try {
    const { name, phone, dateOfBirth, gender, address, emergencyContact } = req.body;

    // Validation
    if (!name || !phone) {
      return res.status(400).json({
        success: false,
        message: 'Name and phone are required'
      });
    }

    const phoneValidation = validateGhanaPhone(phone);
    if (!phoneValidation.valid) {
      return res.status(400).json({
        success: false,
        message: 'Invalid Ghana phone number format'
      });
    }

    const db = admin.firestore();

    // Check if patient already exists
    const existingPatient = await db.collection('patients')
      .where('phone', '==', phoneValidation.phone)
      .limit(1)
      .get();

    if (!existingPatient.empty) {
      return res.status(409).json({
        success: false,
        message: 'Patient with this phone number already exists',
        existingPatient: { 
          id: existingPatient.docs[0].id, 
          ...existingPatient.docs[0].data() 
        }
      });
    }

    // Create patient
    const patientData = {
      name: name.trim(),
      phone: phoneValidation.phone,
      dateOfBirth: dateOfBirth || null,
      gender: gender || null,
      address: address || null,
      emergencyContact: emergencyContact || null,
      createdBy: req.user.id,
      createdByName: req.user.name,
      facilityId: req.user.facilityId,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      updatedAt: admin.firestore.FieldValue.serverTimestamp()
    };

    const docRef = await db.collection('patients').add(patientData);
    const newPatient = { id: docRef.id, ...patientData };

    // Log patient creation
    await db.collection('audit_logs').add({
      action: 'PATIENT_CREATED',
      providerId: req.user.id,
      providerName: req.user.name,
      patientId: docRef.id,
      patientName: name,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });

    res.status(201).json({
      success: true,
      message: 'Patient created successfully',
      patient: newPatient
    });

  } catch (error) {
    functions.logger.error('Create patient error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to create patient'
    });
  }
});

/**
 * GET /api/patients/:id
 * Get specific patient details
 */
app.get('/api/patients/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const db = admin.firestore();

    const patientDoc = await db.collection('patients').doc(id).get();

    if (!patientDoc.exists) {
      return res.status(404).json({
        success: false,
        message: 'Patient not found'
      });
    }

    const patient = { id: patientDoc.id, ...patientDoc.data() };

    res.json({
      success: true,
      patient: patient
    });

  } catch (error) {
    functions.logger.error('Get patient error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch patient details'
    });
  }
});

// ============== MEDICAL RECORDS ENDPOINTS ==============

/**
 * POST /api/patients/:patientId/records
 * Create new medical record for patient
 */
app.post('/api/patients/:patientId/records', authenticateToken, async (req, res) => {
  try {
    const { patientId } = req.params;
    const { 
      chiefComplaint, 
      diagnosis, 
      treatment, 
      prescription, 
      notes,
      vitals 
    } = req.body;

    if (!chiefComplaint) {
      return res.status(400).json({
        success: false,
        message: 'Chief complaint is required'
      });
    }

    const db = admin.firestore();

    // Verify patient exists
    const patientDoc = await db.collection('patients').doc(patientId).get();
    if (!patientDoc.exists) {
      return res.status(404).json({
        success: false,
        message: 'Patient not found'
      });
    }

    const patient = patientDoc.data();

    // Create medical record
    const recordData = {
      patientId: patientId,
      patientName: patient.name,
      patientPhone: patient.phone,
      providerId: req.user.id,
      providerName: req.user.name,
      facilityId: req.user.facilityId,
      chiefComplaint: chiefComplaint.trim(),
      diagnosis: diagnosis?.trim() || null,
      treatment: treatment?.trim() || null,
      prescription: prescription?.trim() || null,
      notes: notes?.trim() || null,
      vitals: vitals || null,
      createdAt: admin.firestore.FieldValue.serverTimestamp()
    };

    const docRef = await db.collection('medical_records').add(recordData);
    const newRecord = { id: docRef.id, ...recordData };

    // Log record creation
    await db.collection('audit_logs').add({
      action: 'MEDICAL_RECORD_CREATED',
      providerId: req.user.id,
      providerName: req.user.name,
      patientId: patientId,
      patientName: patient.name,
      recordId: docRef.id,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });

    res.status(201).json({
      success: true,
      message: 'Medical record created successfully',
      record: newRecord
    });

  } catch (error) {
    functions.logger.error('Create medical record error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to create medical record'
    });
  }
});

/**
 * GET /api/patients/:patientId/records
 * Get medical records for specific patient
 */
app.get('/api/patients/:patientId/records', authenticateToken, async (req, res) => {
  try {
    const { patientId } = req.params;
    const { limit = 10, offset = 0 } = req.query;
    const db = admin.firestore();

    const snapshot = await db.collection('medical_records')
      .where('patientId', '==', patientId)
      .orderBy('createdAt', 'desc')
      .limit(parseInt(limit))
      .offset(parseInt(offset))
      .get();

    const records = snapshot.docs.map(doc => ({ 
      id: doc.id, 
      ...doc.data(),
      createdAt: doc.data().createdAt?.toDate()?.toISOString()
    }));

    res.json({
      success: true,
      records: records,
      total: records.length,
      hasMore: records.length >= parseInt(limit)
    });

  } catch (error) {
    functions.logger.error('Get patient records error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch medical records'
    });
  }
});

// ============== DASHBOARD ENDPOINTS ==============

/**
 * GET /api/dashboard/stats
 * Get dashboard statistics for provider
 */
app.get('/api/dashboard/stats', authenticateToken, async (req, res) => {
  try {
    const db = admin.firestore();
    const providerId = req.user.id;
    const today = new Date();
    const startOfDay = new Date(today.setHours(0, 0, 0, 0));

    // Get statistics
    const [
      totalPatientsSnapshot,
      todayRecordsSnapshot,
      recentRecordsSnapshot
    ] = await Promise.all([
      db.collection('patients')
        .where('createdBy', '==', providerId)
        .get(),
      db.collection('medical_records')
        .where('providerId', '==', providerId)
        .where('createdAt', '>=', admin.firestore.Timestamp.fromDate(startOfDay))
        .get(),
      db.collection('medical_records')
        .where('providerId', '==', providerId)
        .orderBy('createdAt', 'desc')
        .limit(5)
        .get()
    ]);

    const recentRecords = recentRecordsSnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      createdAt: doc.data().createdAt?.toDate()?.toISOString()
    }));

    res.json({
      success: true,
      stats: {
        totalPatients: totalPatientsSnapshot.size,
        todayRecords: todayRecordsSnapshot.size,
        recentRecords: recentRecords
      }
    });

  } catch (error) {
    functions.logger.error('Get dashboard stats error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch dashboard statistics'
    });
  }
});

// ============== UTILITY FUNCTIONS ==============

/**
 * Validate Ghana phone number format
 * Accepts: 0XXXXXXXXX, +233XXXXXXXXX, 233XXXXXXXXX
 */
function validateGhanaPhone(phone) {
  if (!phone || typeof phone !== 'string') {
    return { valid: false, phone: null };
  }

  let cleanPhone = phone.replace(/\s+/g, '').replace(/[-()]/g, '');

  // Handle different formats
  if (cleanPhone.startsWith('+233')) {
    cleanPhone = '0' + cleanPhone.substring(4);
  } else if (cleanPhone.startsWith('233')) {
    cleanPhone = '0' + cleanPhone.substring(3);
  }

  // Validate format: 0XXXXXXXXX (10 digits starting with 0)
  const phoneRegex = /^0[2-9]\d{8}$/;
  
  if (phoneRegex.test(cleanPhone)) {
    return { valid: true, phone: cleanPhone };
  }

  return { valid: false, phone: null };
}

// ============== ERROR HANDLING ==============

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found'
  });
});

// Global error handler
app.use((error, req, res, next) => {
  functions.logger.error('Unhandled error:', error);
  res.status(500).json({
    success: false,
    message: 'Internal server error'
  });
});

// Export the Express app as a Firebase Function
exports.api = functions.https.onRequest(app);

// Health check function
exports.healthCheck = functions.https.onRequest((req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '2.0.0'
  });
});