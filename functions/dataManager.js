/**
 * Data Manager - Handles all database operations for Afya Medical EHR
 * Provides centralized data access layer for Firebase Firestore
 */

const { getFirestore, FieldValue } = require('firebase-admin/firestore');
const { logger } = require('firebase-functions');

class DataManager {
  constructor() {
    this.db = getFirestore();
    this.collections = {
      facilities: 'facilities',
      providers: 'providers',
      patients: 'patients',
      medical_records: 'medical_records',
      system_logs: 'system_logs',
      ussd_sessions: 'ussd_sessions'
    };
  }

  // ============== UTILITY METHODS ==============

  /**
   * Generate unique ID
   * @param {string} prefix - ID prefix
   * @returns {string} Unique ID
   */
  generateId(prefix = '') {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 8);
    return `${prefix}${timestamp}${random}`.toLowerCase();
  }

  /**
   * Validate Ghana phone number
   * @param {string} phone - Phone number
   * @returns {Object} Validation result
   */
  validateGhanaPhone(phone) {
    if (!phone) return { valid: false, message: 'Phone number required' };

    const cleaned = phone.replace(/[\s-]/g, '');

    if (cleaned.startsWith('0') && cleaned.length === 10) {
      return { valid: true, phone: cleaned };
    } else if (cleaned.startsWith('+233') && cleaned.length === 13) {
      return { valid: true, phone: '0' + cleaned.substring(4) };
    } else if (cleaned.startsWith('233') && cleaned.length === 12) {
      return { valid: true, phone: '0' + cleaned.substring(3) };
    } else {
      return { valid: false, message: 'Invalid Ghana phone number format' };
    }
  }

  /**
   * Log system activity
   * @param {Object} logData - Log information
   */
  async logActivity(logData) {
    try {
      const logEntry = {
        ...logData,
        timestamp: FieldValue.serverTimestamp(),
        id: this.generateId('log_')
      };

      await this.db.collection(this.collections.system_logs).add(logEntry);
    } catch (error) {
      logger.error('Failed to log activity:', error);
    }
  }

  // ============== FACILITIES ==============

  /**
   * Create a new facility
   * @param {Object} facilityData - Facility information
   * @returns {Promise<Object>} Created facility
   */
  async createFacility(facilityData) {
    try {
      // Validate required fields
      const required = ['name', 'facility_type', 'location', 'phone'];
      for (const field of required) {
        if (!facilityData[field]) {
          throw new Error(`${field} is required`);
        }
      }

      // Validate phone number
      const phoneValidation = this.validateGhanaPhone(facilityData.phone);
      if (!phoneValidation.valid) {
        throw new Error(phoneValidation.message);
      }

      // Check if facility with same phone exists
      const existingFacility = await this.db.collection(this.collections.facilities)
        .where('phone', '==', phoneValidation.phone)
        .get();

      if (!existingFacility.empty) {
        throw new Error('A facility with this phone number already exists');
      }

      const facility = {
        id: this.generateId('fac_'),
        name: facilityData.name.trim(),
        facility_type: facilityData.facility_type,
        location: facilityData.location.trim(),
        phone: phoneValidation.phone,
        description: facilityData.description?.trim() || '',
        is_active: true,
        registration_date: FieldValue.serverTimestamp(),
        providers_count: 0,
        records_count: 0
      };

      await this.db.collection(this.collections.facilities).doc(facility.id).set(facility);

      // Log activity
      await this.logActivity({
        action: 'Facility_Registration',
        details: `Facility registered: ${facility.name}`,
        facility_id: facility.id
      });

      return { success: true, facility, message: 'Facility created successfully' };
    } catch (error) {
      logger.error('Error creating facility:', error);
      throw error;
    }
  }

  /**
   * Get all facilities
   * @returns {Promise<Array>} List of facilities
   */
  async getFacilities() {
    try {
      const snapshot = await this.db.collection(this.collections.facilities)
        .where('is_active', '!=', null) // Only get real records
        .orderBy('is_active', 'desc')
        .orderBy('registration_date', 'desc')
        .get();

      const facilities = [];
      snapshot.forEach(doc => {
        const data = doc.data();
        // Only include records with valid data
        if (data.name && data.name.trim() && data.facility_type) {
          facilities.push({
            id: doc.id,
            ...data,
            // Convert Firestore timestamps to readable format
            registration_date: data.registration_date?.toDate?.()?.toISOString() || data.registration_date
          });
        }
      });

      return facilities;
    } catch (error) {
      logger.error('Error getting facilities:', error);
      return []; // Return empty array instead of throwing
    }
  }

  /**
   * Get facility by ID
   * @param {string} facilityId - Facility ID
   * @returns {Promise<Object>} Facility data
   */
  async getFacility(facilityId) {
    try {
      const doc = await this.db.collection(this.collections.facilities).doc(facilityId).get();

      if (!doc.exists) {
        throw new Error('Facility not found');
      }

      return { id: doc.id, ...doc.data() };
    } catch (error) {
      logger.error('Error getting facility:', error);
      throw error;
    }
  }

  /**
   * Toggle facility status
   * @param {string} facilityId - Facility ID
   * @returns {Promise<Object>} Update result
   */
  async toggleFacilityStatus(facilityId) {
    try {
      const facilityRef = this.db.collection(this.collections.facilities).doc(facilityId);
      const facility = await facilityRef.get();

      if (!facility.exists) {
        throw new Error('Facility not found');
      }

      const currentStatus = facility.data().is_active;
      const newStatus = !currentStatus;

      await facilityRef.update({
        is_active: newStatus,
        updated_at: FieldValue.serverTimestamp()
      });

      // Log activity
      await this.logActivity({
        action: 'Status_Toggle',
        details: `Facility ${newStatus ? 'activated' : 'deactivated'}: ${facility.data().name}`,
        facility_id: facilityId
      });

      return { success: true, is_active: newStatus };
    } catch (error) {
      logger.error('Error toggling facility status:', error);
      throw error;
    }
  }

  // ============== PROVIDERS ==============

  /**
   * Create a new provider
   * @param {Object} providerData - Provider information
   * @returns {Promise<Object>} Created provider
   */
  async createProvider(providerData) {
    try {
      // Validate required fields
      const required = ['name', 'phone', 'specialization', 'facility_id', 'pin'];
      for (const field of required) {
        if (!providerData[field]) {
          throw new Error(`${field} is required`);
        }
      }

      // Validate phone number
      const phoneValidation = this.validateGhanaPhone(providerData.phone);
      if (!phoneValidation.valid) {
        throw new Error(phoneValidation.message);
      }

      // Validate PIN
      if (!/^\d{4}$/.test(providerData.pin)) {
        throw new Error('PIN must be exactly 4 digits');
      }

      // Check if provider with same phone exists
      const existingProvider = await this.db.collection(this.collections.providers)
        .where('phone', '==', phoneValidation.phone)
        .get();

      if (!existingProvider.empty) {
        throw new Error('A provider with this phone number already exists');
      }

      // Verify facility exists
      const facility = await this.getFacility(providerData.facility_id);

      const provider = {
        id: this.generateId('prov_'),
        name: providerData.name.trim(),
        phone: phoneValidation.phone,
        specialization: providerData.specialization,
        facility_id: providerData.facility_id,
        pin: providerData.pin, // In production, hash this
        is_active: true,
        registration_date: FieldValue.serverTimestamp(),
        facility: {
          id: facility.id,
          name: facility.name,
          location: facility.location
        }
      };

      await this.db.collection(this.collections.providers).doc(provider.id).set(provider);

      // Update facility provider count
      await this.db.collection(this.collections.facilities).doc(providerData.facility_id).update({
        providers_count: FieldValue.increment(1)
      });

      // Log activity
      await this.logActivity({
        action: 'Provider_Registration',
        details: `Provider registered: ${provider.name}`,
        provider_id: provider.id,
        facility_id: providerData.facility_id
      });

      return { success: true, provider, message: 'Provider created successfully' };
    } catch (error) {
      logger.error('Error creating provider:', error);
      throw error;
    }
  }

  /**
   * Get all providers
   * @returns {Promise<Array>} List of providers
   */
  async getProviders() {
    try {
      const snapshot = await this.db.collection(this.collections.providers)
        .where('is_active', '!=', null) // Only get real records
        .orderBy('is_active', 'desc')
        .orderBy('registration_date', 'desc')
        .get();

      const providers = [];
      snapshot.forEach(doc => {
        const data = doc.data();
        // Only include records with valid data
        if (data.name && data.name.trim() && data.phone) {
          // Don't expose PIN in listings
          const { pin, ...providerData } = data;
          providers.push({
            id: doc.id,
            ...providerData,
            // Convert Firestore timestamps
            registration_date: data.registration_date?.toDate?.()?.toISOString() || data.registration_date
          });
        }
      });

      return providers;
    } catch (error) {
      logger.error('Error getting providers:', error);
      return []; // Return empty array instead of throwing
    }
  }

  /**
   * Get provider by phone and PIN
   * @param {string} phone - Provider phone
   * @param {string} pin - Provider PIN
   * @returns {Promise<Object>} Provider data
   */
  async authenticateProvider(phone, pin) {
    try {
      const phoneValidation = this.validateGhanaPhone(phone);
      if (!phoneValidation.valid) {
        throw new Error('Invalid phone number format');
      }

      const snapshot = await this.db.collection(this.collections.providers)
        .where('phone', '==', phoneValidation.phone)
        .where('pin', '==', pin)
        .where('is_active', '==', true)
        .get();

      if (snapshot.empty) {
        throw new Error('Invalid credentials or inactive provider');
      }

      const provider = snapshot.docs[0];
      const providerData = { id: provider.id, ...provider.data() };

      // Don't return PIN
      delete providerData.pin;

      return providerData;
    } catch (error) {
      logger.error('Error authenticating provider:', error);
      throw error;
    }
  }

  /**
   * Reset provider PIN
   * @param {string} providerId - Provider ID
   * @returns {Promise<Object>} New PIN
   */
  async resetProviderPin(providerId) {
    try {
      const newPin = Math.floor(1000 + Math.random() * 9000).toString();

      await this.db.collection(this.collections.providers).doc(providerId).update({
        pin: newPin,
        updated_at: FieldValue.serverTimestamp()
      });

      // Log activity
      await this.logActivity({
        action: 'PIN_Reset',
        details: `PIN reset for provider`,
        provider_id: providerId
      });

      return { success: true, new_pin: newPin };
    } catch (error) {
      logger.error('Error resetting provider PIN:', error);
      throw error;
    }
  }

  /**
   * Toggle provider status
   * @param {string} providerId - Provider ID
   * @returns {Promise<Object>} Update result
   */
  async toggleProviderStatus(providerId) {
    try {
      const providerRef = this.db.collection(this.collections.providers).doc(providerId);
      const provider = await providerRef.get();

      if (!provider.exists) {
        throw new Error('Provider not found');
      }

      const currentStatus = provider.data().is_active;
      const newStatus = !currentStatus;

      await providerRef.update({
        is_active: newStatus,
        updated_at: FieldValue.serverTimestamp()
      });

      // Log activity
      await this.logActivity({
        action: 'Status_Toggle',
        details: `Provider ${newStatus ? 'activated' : 'deactivated'}: ${provider.data().name}`,
        provider_id: providerId
      });

      return { success: true, is_active: newStatus };
    } catch (error) {
      logger.error('Error toggling provider status:', error);
      throw error;
    }
  }

  // ============== PATIENTS ==============

  /**
   * Create a new patient
   * @param {Object} patientData - Patient information
   * @returns {Promise<Object>} Created patient
   */
  async createPatient(patientData) {
    try {
      // Validate required fields
      const required = ['name', 'phone'];
      for (const field of required) {
        if (!patientData[field]) {
          throw new Error(`${field} is required`);
        }
      }

      // Validate phone number
      const phoneValidation = this.validateGhanaPhone(patientData.phone);
      if (!phoneValidation.valid) {
        throw new Error(phoneValidation.message);
      }

      // Check if patient with same phone exists
      const existingPatient = await this.db.collection(this.collections.patients)
        .where('phone', '==', phoneValidation.phone)
        .get();

      if (!existingPatient.empty) {
        throw new Error('A patient with this phone number already exists');
      }

      const patient = {
        id: this.generateId('pat_'),
        name: patientData.name.trim(),
        phone: phoneValidation.phone,
        date_of_birth: patientData.date_of_birth || '',
        gender: patientData.gender || '',
        blood_type: patientData.blood_type || '',
        allergies: patientData.allergies || '',
        emergency_contact: patientData.emergency_contact || '',
        registration_date: FieldValue.serverTimestamp(),
        last_visit: null,
        is_active: true
      };

      await this.db.collection(this.collections.patients).doc(patient.id).set(patient);

      // Log activity
      await this.logActivity({
        action: 'Patient_Registration',
        details: `Patient registered: ${patient.name}`,
        patient_id: patient.id,
        user_phone: patientData.registered_by_phone
      });

      return { success: true, patient, message: 'Patient registered successfully' };
    } catch (error) {
      logger.error('Error creating patient:', error);
      throw error;
    }
  }

  /**
   * Get all patients
   * @returns {Promise<Array>} List of patients
   */
  async getPatients() {
    try {
      const snapshot = await this.db.collection(this.collections.patients)
        .where('is_active', '!=', null) // Only get real records
        .orderBy('is_active', 'desc')
        .orderBy('registration_date', 'desc')
        .get();

      const patients = [];
      snapshot.forEach(doc => {
        const data = doc.data();
        // Only include records with valid data
        if (data.name && data.name.trim() && data.phone) {
          patients.push({
            id: doc.id,
            ...data,
            // Convert Firestore timestamps
            registration_date: data.registration_date?.toDate?.()?.toISOString() || data.registration_date,
            last_visit: data.last_visit?.toDate?.()?.toISOString() || data.last_visit
          });
        }
      });

      return patients;
    } catch (error) {
      logger.error('Error getting patients:', error);
      return []; // Return empty array instead of throwing
    }
  }

  /**
   * Get patient by phone
   * @param {string} phone - Patient phone
   * @returns {Promise<Object>} Patient data
   */
  async getPatientByPhone(phone) {
    try {
      const phoneValidation = this.validateGhanaPhone(phone);
      if (!phoneValidation.valid) {
        throw new Error('Invalid phone number format');
      }

      const snapshot = await this.db.collection(this.collections.patients)
        .where('phone', '==', phoneValidation.phone)
        .get();

      if (snapshot.empty) {
        throw new Error('Patient not found');
      }

      const patient = snapshot.docs[0];
      return { id: patient.id, ...patient.data() };
    } catch (error) {
      logger.error('Error getting patient by phone:', error);
      throw error;
    }
  }

  /**
   * Search patients
   * @param {string} query - Search query
   * @returns {Promise<Array>} Matching patients
   */
  async searchPatients(query) {
    try {
      const patients = await this.getPatients();
      const searchTerm = query.toLowerCase();

      return patients.filter(patient =>
        patient.name?.toLowerCase().includes(searchTerm) ||
        patient.phone?.includes(searchTerm) ||
        patient.id?.toLowerCase().includes(searchTerm)
      );
    } catch (error) {
      logger.error('Error searching patients:', error);
      throw error;
    }
  }

  // ============== MEDICAL RECORDS ==============

  /**
   * Create a new medical record
   * @param {Object} recordData - Medical record information
   * @returns {Promise<Object>} Created record
   */
  async createMedicalRecord(recordData) {
    try {
      // Validate required fields
      const required = ['patient_id', 'provider_id', 'facility_id', 'chief_complaint'];
      for (const field of required) {
        if (!recordData[field]) {
          throw new Error(`${field} is required`);
        }
      }

      // Verify patient, provider, and facility exist
      const [patient, provider, facility] = await Promise.all([
        this.db.collection(this.collections.patients).doc(recordData.patient_id).get(),
        this.db.collection(this.collections.providers).doc(recordData.provider_id).get(),
        this.db.collection(this.collections.facilities).doc(recordData.facility_id).get()
      ]);

      if (!patient.exists) throw new Error('Patient not found');
      if (!provider.exists) throw new Error('Provider not found');
      if (!facility.exists) throw new Error('Facility not found');

      const record = {
        id: this.generateId('rec_'),
        patient_id: recordData.patient_id,
        provider_id: recordData.provider_id,
        facility_id: recordData.facility_id,
        visit_date: recordData.visit_date || new Date().toISOString().split('T')[0],
        chief_complaint: recordData.chief_complaint.trim(),
        history: recordData.history?.trim() || '',
        physical_examination: recordData.physical_examination?.trim() || '',
        diagnosis: recordData.diagnosis?.trim() || '',
        treatment: recordData.treatment?.trim() || '',
        prescription: recordData.prescription?.trim() || '',
        follow_up: recordData.follow_up?.trim() || '',
        notes: recordData.notes?.trim() || '',
        created_at: FieldValue.serverTimestamp(),
        patient: {
          id: patient.id,
          name: patient.data().name,
          phone: patient.data().phone
        },
        provider: {
          id: provider.id,
          name: provider.data().name,
          specialization: provider.data().specialization
        },
        facility: {
          id: facility.id,
          name: facility.data().name,
          location: facility.data().location
        }
      };

      await this.db.collection(this.collections.medical_records).doc(record.id).set(record);

      // Update patient last visit
      await this.db.collection(this.collections.patients).doc(recordData.patient_id).update({
        last_visit: FieldValue.serverTimestamp()
      });

      // Update facility records count
      await this.db.collection(this.collections.facilities).doc(recordData.facility_id).update({
        records_count: FieldValue.increment(1)
      });

      // Log activity
      await this.logActivity({
        action: 'Medical_Record_Created',
        details: `Medical record created for ${patient.data().name}`,
        patient_id: recordData.patient_id,
        provider_id: recordData.provider_id,
        facility_id: recordData.facility_id,
        record_id: record.id
      });

      return { success: true, record, message: 'Medical record created successfully' };
    } catch (error) {
      logger.error('Error creating medical record:', error);
      throw error;
    }
  }

  /**
   * Get medical records for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Array>} Patient's medical records
   */
  async getPatientRecords(patientId) {
    try {
      const snapshot = await this.db.collection(this.collections.medical_records)
        .where('patient_id', '==', patientId)
        .orderBy('visit_date', 'desc')
        .get();

      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } catch (error) {
      logger.error('Error getting patient records:', error);
      throw error;
    }
  }

  /**
   * Get recent medical records
   * @param {number} limit - Number of records to fetch
   * @returns {Promise<Array>} Recent medical records
   */
  async getRecentRecords(limit = 10) {
    try {
      const snapshot = await this.db.collection(this.collections.medical_records)
        .orderBy('created_at', 'desc')
        .limit(limit)
        .get();

      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } catch (error) {
      logger.error('Error getting recent records:', error);
      throw error;
    }
  }

  // ============== SYSTEM LOGS ==============

  /**
   * Get system logs
   * @param {number} limit - Number of logs to fetch
   * @returns {Promise<Array>} System logs
   */
  async getLogs(limit = 100) {
    try {
      const snapshot = await this.db.collection(this.collections.system_logs)
        .orderBy('timestamp', 'desc')
        .limit(limit)
        .get();

      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } catch (error) {
      logger.error('Error getting logs:', error);
      throw error;
    }
  }

  // ============== DASHBOARD STATS ==============

  /**
   * Get dashboard statistics
   * @returns {Promise<Object>} Dashboard stats
   */
  async getDashboardStats() {
    try {
      const [facilities, providers, patients, recentRecords] = await Promise.all([
        this.getFacilities(),
        this.getProviders(),
        this.getPatients(),
        this.getRecentRecords(5)
      ]);

      return {
        total_facilities: facilities.length,
        total_providers: providers.length,
        total_patients: patients.length,
        active_facilities: facilities.filter(f => f.is_active).length,
        active_providers: providers.filter(p => p.is_active).length,
        recent_records: recentRecords
      };
    } catch (error) {
      logger.error('Error getting dashboard stats:', error);
      throw error;
    }
  }

  // ============== USSD SESSION MANAGEMENT ==============

  /**
   * Create or update USSD session
   * @param {string} sessionId - Session ID
   * @param {Object} sessionData - Session data
   * @returns {Promise<void>}
   */
  async updateUssdSession(sessionId, sessionData) {
    try {
      await this.db.collection(this.collections.ussd_sessions).doc(sessionId).set({
        ...sessionData,
        updated_at: FieldValue.serverTimestamp()
      }, { merge: true });
    } catch (error) {
      logger.error('Error updating USSD session:', error);
      throw error;
    }
  }

  /**
   * Get USSD session
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} Session data
   */
  async getUssdSession(sessionId) {
    try {
      const doc = await this.db.collection(this.collections.ussd_sessions).doc(sessionId).get();
      return doc.exists ? doc.data() : null;
    } catch (error) {
      logger.error('Error getting USSD session:', error);
      throw error;
    }
  }

  /**
   * Delete USSD session
   * @param {string} sessionId - Session ID
   * @returns {Promise<void>}
   */
  async deleteUssdSession(sessionId) {
    try {
      await this.db.collection(this.collections.ussd_sessions).doc(sessionId).delete();
    } catch (error) {
      logger.error('Error deleting USSD session:', error);
      throw error;
    }
  }

  /**
   * Clean up invalid records
   */
  async cleanupInvalidRecords() {
    try {
      let cleaned = 0;

      // Clean facilities
      const facilitiesSnapshot = await this.db.collection(this.collections.facilities).get();
      const batch1 = this.db.batch();
      
      facilitiesSnapshot.forEach(doc => {
        const data = doc.data();
        if (!data.name || !data.name.toString().trim() || !data.facility_type) {
          batch1.delete(doc.ref);
          cleaned++;
        }
      });
      
      if (cleaned > 0) await batch1.commit();

      // Clean providers
      const providersSnapshot = await this.db.collection(this.collections.providers).get();
      const batch2 = this.db.batch();
      
      providersSnapshot.forEach(doc => {
        const data = doc.data();
        if (!data.name || !data.name.toString().trim() || !data.phone) {
          batch2.delete(doc.ref);
          cleaned++;
        }
      });
      
      if (cleaned > 0) await batch2.commit();

      // Clean patients
      const patientsSnapshot = await this.db.collection(this.collections.patients).get();
      const batch3 = this.db.batch();
      
      patientsSnapshot.forEach(doc => {
        const data = doc.data();
        if (!data.name || !data.name.toString().trim() || !data.phone) {
          batch3.delete(doc.ref);
          cleaned++;
        }
      });
      
      if (cleaned > 0) await batch3.commit();

      logger.info(`Cleaned up ${cleaned} invalid records`);
      return cleaned;
    } catch (error) {
      logger.error('Error cleaning up records:', error);
      return 0;
    }
  }
}

module.exports = new DataManager();