import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production'
    ? '/api'  // In production, requests go through Firebase Hosting rewrites
    : 'http://localhost:5001/afya-a1006/us-central1/api', // Development - update with your project ID
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`)
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('Response error:', error)

    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.error || error.response.data?.message || 'Server error'
      throw new Error(message)
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Network error - please check your connection')
    } else {
      // Something else happened
      throw new Error(error.message || 'An unexpected error occurred')
    }
  }
)

class ApiService {
  // ============== DASHBOARD ==============

  /**
  * Get dashboard statistics - FIXED VERSION
  * @returns {Promise<Object>} Dashboard stats
  */
  async getDashboardStats() {
    try {
      const response = await api.get('/dashboard/stats')
      // Ensure recent_records is always an array
      if (response && !Array.isArray(response.recent_records)) {
        response.recent_records = []
      }
      return response || {
        total_facilities: 0,
        total_providers: 0,
        total_patients: 0,
        recent_records: []
      }
    } catch (error) {
      console.error('Failed to get dashboard stats:', error)
      return {
        total_facilities: 0,
        total_providers: 0,
        total_patients: 0,
        recent_records: []
      }
    }
  }

  // ============== FACILITIES ==============

  /**
  * Get all facilities - FIXED VERSION
  * @returns {Promise<Array>} List of facilities
  */
  async getFacilities() {
    try {
      const response = await api.get('/facilities')
      // Ensure we always return an array
      return Array.isArray(response) ? response : []
    } catch (error) {
      console.error('Failed to get facilities:', error)
      return [] // Return empty array on error
    }
  }

  /**
   * Create a new facility
   * @param {Object} facilityData - Facility information
   * @returns {Promise<Object>} Created facility
   */
  async createFacility(facilityData) {
    return await api.post('/facilities', facilityData)
  }

  /**
   * Update facility
   * @param {string} facilityId - Facility ID
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Updated facility
   */
  async updateFacility(facilityId, updateData) {
    return await api.put(`/facilities/${facilityId}`, updateData)
  }

  /**
   * Toggle facility status
   * @param {string} facilityId - Facility ID
   * @returns {Promise<Object>} Response
   */
  async toggleFacilityStatus(facilityId) {
    return await api.post(`/facility/${facilityId}/toggle-status`)
  }

  // ============== PROVIDERS ==============

  /**
  * Get all providers - FIXED VERSION
  * @returns {Promise<Array>} List of providers
  */
  async getProviders() {
    try {
      const response = await api.get('/providers')
      // Ensure we always return an array
      return Array.isArray(response) ? response : []
    } catch (error) {
      console.error('Failed to get providers:', error)
      return [] // Return empty array on error
    }
  }

  /**
   * Create a new provider
   * @param {Object} providerData - Provider information
   * @returns {Promise<Object>} Created provider
   */
  async createProvider(providerData) {
    return await api.post('/providers', providerData)
  }

  /**
   * Toggle provider status
   * @param {string} providerId - Provider ID
   * @returns {Promise<Object>} Response
   */
  async toggleProviderStatus(providerId) {
    return await api.post(`/provider/${providerId}/toggle-status`)
  }

  /**
   * Reset provider PIN
   * @param {string} providerId - Provider ID
   * @returns {Promise<Object>} Response with new PIN
   */
  async resetProviderPin(providerId) {
    return await api.post(`/provider/${providerId}/reset-pin`)
  }

  // ============== PATIENTS ==============
  /**
   * Get all patients - FIXED VERSION
   * @returns {Promise<Array>} List of patients
   */
  async getPatients() {
    try {
      const response = await api.get('/patients')
      // Ensure we always return an array
      return Array.isArray(response) ? response : []
    } catch (error) {
      console.error('Failed to get patients:', error)
      return [] // Return empty array on error
    }
  }


  /**
   * Search patients
   * @param {string} query - Search query
   * @returns {Promise<Array>} Matching patients
   */
  async searchPatients(query) {
    return await api.get(`/patients/search?q=${encodeURIComponent(query)}`)
  }

  /**
   * Get patient by ID
   * @param {string} patientId - Patient ID
   * @returns {Promise<Object>} Patient details
   */
  async getPatient(patientId) {
    return await api.get(`/patients/${patientId}`)
  }

  /**
   * Create a new patient
   * @param {Object} patientData - Patient information
   * @returns {Promise<Object>} Created patient
   */
  async createPatient(patientData) {
    return await api.post('/patients', patientData)
  }

  /**
   * Update patient
   * @param {string} patientId - Patient ID
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Updated patient
   */
  async updatePatient(patientId, updateData) {
    return await api.put(`/patients/${patientId}`, updateData)
  }

  // ============== MEDICAL RECORDS ==============

  /**
   * Get medical records for a patient
   * @param {string} patientId - Patient ID
   * @returns {Promise<Array>} Patient's medical records
   */
  async getPatientRecords(patientId) {
    return await api.get(`/patients/${patientId}/records`)
  }

  /**
   * Create a new medical record
   * @param {Object} recordData - Medical record data
   * @returns {Promise<Object>} Created record
   */
  async createMedicalRecord(recordData) {
    return await api.post('/medical-records', recordData)
  }

  /**
   * Get medical record by ID
   * @param {string} recordId - Record ID
   * @returns {Promise<Object>} Medical record
   */
  async getMedicalRecord(recordId) {
    return await api.get(`/medical-records/${recordId}`)
  }

  /**
   * Update medical record
   * @param {string} recordId - Record ID
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Updated record
   */
  async updateMedicalRecord(recordId, updateData) {
    return await api.put(`/medical-records/${recordId}`, updateData)
  }

  // ============== USSD ==============

  /**
   * Send USSD request (for testing)
   * @param {Object} ussdData - USSD request data
   * @returns {Promise<string>} USSD response
   */
  async sendUssdRequest(ussdData) {
    const response = await api.post('/ussd/callback', ussdData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      transformRequest: [(data) => {
        const params = new URLSearchParams()
        Object.keys(data).forEach(key => {
          params.append(key, data[key])
        })
        return params
      }]
    })
    return response
  }

  // ============== SYSTEM ==============

  /**
   * Get system logs
   * @param {number} limit - Number of logs to retrieve
   * @returns {Promise<Array>} System logs
   */
  async getLogs(limit = 100) {
    return await api.get(`/logs?limit=${limit}`)
  }

  /**
   * Get system health status
   * @returns {Promise<Object>} Health status
   */
  async getHealth() {
    return await api.get('/health')
  }

  /**
   * Initialize sample data
   * @returns {Promise<Object>} Initialization result
   */
  async initializeSampleData() {
    return await api.post('/initialize-data')
  }

  // ============== UTILITY METHODS ==============

  /**
   * Upload file (if needed for future features)
   * @param {File} file - File to upload
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} Upload result
   */
  async uploadFile(file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)

    return await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      }
    })
  }

  /**
   * Generic GET request
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   * @returns {Promise<any>} Response data
   */
  async get(endpoint, params = {}) {
    return await api.get(endpoint, { params })
  }

  /**
   * Generic POST request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise<any>} Response data
   */
  async post(endpoint, data = {}) {
    return await api.post(endpoint, data)
  }

  /**
   * Generic PUT request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise<any>} Response data
   */
  async put(endpoint, data = {}) {
    return await api.put(endpoint, data)
  }

  /**
   * Generic DELETE request
   * @param {string} endpoint - API endpoint
   * @returns {Promise<any>} Response data
   */
  async delete(endpoint) {
    return await api.delete(endpoint)
  }

  // ============== VALIDATION HELPERS ==============

  /**
   * Validate Ghana phone number
   * @param {string} phone - Phone number
   * @returns {Object} Validation result
   */
  validateGhanaPhone(phone) {
    if (!phone) return { valid: false, message: 'Phone number required' }

    const cleaned = phone.replace(/[\s-]/g, '')

    if (cleaned.startsWith('0') && cleaned.length === 10) {
      return { valid: true, phone: cleaned }
    } else if (cleaned.startsWith('+233') && cleaned.length === 13) {
      return { valid: true, phone: '0' + cleaned.substring(4) }
    } else if (cleaned.startsWith('233') && cleaned.length === 12) {
      return { valid: true, phone: '0' + cleaned.substring(3) }
    } else {
      return { valid: false, message: 'Invalid Ghana phone number format' }
    }
  }

  /**
   * Validate PIN format
   * @param {string} pin - PIN to validate
   * @returns {Object} Validation result
   */
  validatePin(pin) {
    if (!pin) return { valid: false, message: 'PIN is required' }
    if (pin.length !== 4) return { valid: false, message: 'PIN must be exactly 4 digits' }
    if (!/^\d{4}$/.test(pin)) return { valid: false, message: 'PIN must contain only numbers' }
    return { valid: true }
  }

  /**
   * Format date for display
   * @param {string} dateString - Date string
   * @returns {string} Formatted date
   */
  formatDate(dateString) {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit'
      })
    } catch (error) {
      return dateString
    }
  }

  /**
   * Format phone number for display
   * @param {string} phone - Phone number
   * @returns {string} Formatted phone
   */
  formatPhone(phone) {
    if (!phone) return ''

    // Ghana phone format: 0XX XXX XXXX
    if (phone.length === 10 && phone.startsWith('0')) {
      return `${phone.substring(0, 3)} ${phone.substring(3, 6)} ${phone.substring(6)}`
    }

    return phone
  }

  /**
   * Sanitize phone number
   * @param {string} phone - Phone number
   * @returns {string} Sanitized phone
   */
  sanitizePhone(phone) {
    if (!phone) return ''

    let cleaned = phone.replace(/[\s-]/g, '')

    if (cleaned.startsWith('+233')) {
      cleaned = '0' + cleaned.substring(4)
    } else if (cleaned.startsWith('233')) {
      cleaned = '0' + cleaned.substring(3)
    } else if (!cleaned.startsWith('0') && cleaned.length === 9) {
      cleaned = '0' + cleaned
    }

    return cleaned
  }
}

// Create and export singleton instance
const apiService = new ApiService()
export default apiService