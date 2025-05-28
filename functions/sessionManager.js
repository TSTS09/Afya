/**
 * Session Manager - Handles USSD session state management
 * Manages user sessions, state persistence, and session cleanup
 */

const dataManager = require('./dataManager');
const { logger } = require('firebase-functions');

class SessionManager {
  constructor() {
    this.sessionTimeout = 300000; // 5 minutes in milliseconds
    this.cleanupInterval = 600000; // 10 minutes
    this.startCleanupSchedule();
  }

  /**
   * Create new session
   * @param {string} sessionId - Unique session identifier
   * @param {string} phoneNumber - User phone number
   * @param {string} serviceCode - USSD service code
   * @returns {Promise<Object>} Session data
   */
  async createSession(sessionId, phoneNumber, serviceCode) {
    try {
      const session = {
        sessionId,
        phoneNumber: dataManager.validateGhanaPhone(phoneNumber).phone,
        serviceCode,
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        state: 'active',
        menu_level: 0,
        menu_path: [],
        user_input: [],
        provider: null,
        patient: null,
        medical_record: null,
        temp_data: {},
        attempt_count: 0,
        menu_step: null,
        search_results: null,
        context: null
      };

      await dataManager.updateUssdSession(sessionId, session);
      
      // Log session creation
      await dataManager.logActivity({
        action: 'USSD_Session_Start',
        user_phone: session.phoneNumber,
        session_id: sessionId,
        details: `USSD session started with ${serviceCode}`
      });

      return session;
    } catch (error) {
      logger.error('Error creating session:', error);
      throw error;
    }
  }

  /**
   * Get existing session
   * @param {string} sessionId - Session identifier
   * @returns {Promise<Object|null>} Session data or null
   */
  async getSession(sessionId) {
    try {
      const session = await dataManager.getUssdSession(sessionId);
      
      if (!session) {
        return null;
      }

      // Check if session has expired
      const lastActivity = new Date(session.lastActivity);
      const now = new Date();
      const timeDiff = now.getTime() - lastActivity.getTime();

      if (timeDiff > this.sessionTimeout) {
        await this.endSession(sessionId, 'timeout');
        return null;
      }

      return session;
    } catch (error) {
      logger.error('Error getting session:', error);
      return null;
    }
  }

  /**
   * Update session data
   * @param {string} sessionId - Session identifier
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Updated session
   */
  async updateSession(sessionId, updateData) {
    try {
      const session = await this.getSession(sessionId);
      
      if (!session) {
        throw new Error('Session not found or expired');
      }

      const updatedSession = {
        ...session,
        ...updateData,
        lastActivity: new Date().toISOString()
      };

      await dataManager.updateUssdSession(sessionId, updatedSession);
      return updatedSession;
    } catch (error) {
      logger.error('Error updating session:', error);
      throw error;
    }
  }

  /**
   * Add user input to session history
   * @param {string} sessionId - Session identifier
   * @param {string} input - User input
   * @returns {Promise<void>}
   */
  async addUserInput(sessionId, input) {
    try {
      const session = await this.getSession(sessionId);
      
      if (session) {
        const userInput = session.user_input || [];
        userInput.push({
          input,
          timestamp: new Date().toISOString()
        });

        await this.updateSession(sessionId, { user_input: userInput });
      }
    } catch (error) {
      logger.error('Error adding user input:', error);
    }
  }

  /**
   * Set menu path for navigation tracking
   * @param {string} sessionId - Session identifier
   * @param {string} menuItem - Current menu item
   * @returns {Promise<void>}
   */
  async setMenuPath(sessionId, menuItem) {
    try {
      const session = await this.getSession(sessionId);
      
      if (session) {
        const menuPath = session.menu_path || [];
        menuPath.push({
          menu: menuItem,
          timestamp: new Date().toISOString()
        });

        await this.updateSession(sessionId, { 
          menu_path: menuPath,
          current_menu: menuItem
        });
      }
    } catch (error) {
      logger.error('Error setting menu path:', error);
    }
  }

  /**
   * Set authenticated provider for session
   * @param {string} sessionId - Session identifier
   * @param {Object} provider - Provider data
   * @returns {Promise<void>}
   */
  async setProvider(sessionId, provider) {
    try {
      await this.updateSession(sessionId, { 
        provider: provider,
        user_type: 'provider',
        authenticated: true
      });

      // Log provider authentication
      await dataManager.logActivity({
        action: 'Provider_USSD_Login',
        user_phone: provider.phone,
        provider_id: provider.id,
        session_id: sessionId,
        details: `Provider ${provider.name} authenticated via USSD`
      });
    } catch (error) {
      logger.error('Error setting provider:', error);
      throw error;
    }
  }

  /**
   * Set patient for current session
   * @param {string} sessionId - Session identifier
   * @param {Object} patient - Patient data
   * @returns {Promise<void>}
   */
  async setPatient(sessionId, patient) {
    try {
      await this.updateSession(sessionId, { 
        patient: patient,
        current_patient: patient.id
      });

      // Log patient selection
      await dataManager.logActivity({
        action: 'Patient_Selected',
        user_phone: patient.phone,
        patient_id: patient.id,
        session_id: sessionId,
        details: `Patient ${patient.name} selected for medical record`
      });
    } catch (error) {
      logger.error('Error setting patient:', error);
      throw error;
    }
  }

  /**
   * Store temporary data in session
   * @param {string} sessionId - Session identifier
   * @param {string} key - Data key
   * @param {any} value - Data value
   * @returns {Promise<void>}
   */
  async setTempData(sessionId, key, value) {
    try {
      const session = await this.getSession(sessionId);
      
      if (session) {
        const tempData = session.temp_data || {};
        tempData[key] = value;

        await this.updateSession(sessionId, { temp_data: tempData });
      }
    } catch (error) {
      logger.error('Error setting temp data:', error);
    }
  }

  /**
   * Get temporary data from session
   * @param {string} sessionId - Session identifier
   * @param {string} key - Data key
   * @returns {Promise<any>} Data value
   */
  async getTempData(sessionId, key) {
    try {
      const session = await this.getSession(sessionId);
      
      if (session && session.temp_data) {
        return session.temp_data[key];
      }
      
      return null;
    } catch (error) {
      logger.error('Error getting temp data:', error);
      return null;
    }
  }

  /**
   * Clear temporary data
   * @param {string} sessionId - Session identifier
   * @param {string} key - Specific key to clear (optional)
   * @returns {Promise<void>}
   */
  async clearTempData(sessionId, key = null) {
    try {
      const session = await this.getSession(sessionId);
      
      if (session) {
        if (key) {
          const tempData = session.temp_data || {};
          delete tempData[key];
          await this.updateSession(sessionId, { temp_data: tempData });
        } else {
          await this.updateSession(sessionId, { temp_data: {} });
        }
      }
    } catch (error) {
      logger.error('Error clearing temp data:', error);
    }
  }

  /**
   * Increment attempt counter for failed operations
   * @param {string} sessionId - Session identifier
   * @returns {Promise<number>} Current attempt count
   */
  async incrementAttempts(sessionId) {
    try {
      const session = await this.getSession(sessionId);
      
      if (session) {
        const attemptCount = (session.attempt_count || 0) + 1;
        await this.updateSession(sessionId, { attempt_count: attemptCount });
        return attemptCount;
      }
      
      return 0;
    } catch (error) {
      logger.error('Error incrementing attempts:', error);
      return 0;
    }
  }

  /**
   * Reset attempt counter
   * @param {string} sessionId - Session identifier
   * @returns {Promise<void>}
   */
  async resetAttempts(sessionId) {
    try {
      await this.updateSession(sessionId, { attempt_count: 0 });
    } catch (error) {
      logger.error('Error resetting attempts:', error);
    }
  }

  /**
   * Check if maximum attempts reached
   * @param {string} sessionId - Session identifier
   * @param {number} maxAttempts - Maximum allowed attempts
   * @returns {Promise<boolean>} True if max attempts reached
   */
  async isMaxAttemptsReached(sessionId, maxAttempts = 3) {
    try {
      const session = await this.getSession(sessionId);
      return session ? (session.attempt_count || 0) >= maxAttempts : false;
    } catch (error) {
      logger.error('Error checking max attempts:', error);
      return false;
    }
  }

  /**
   * End session
   * @param {string} sessionId - Session identifier
   * @param {string} reason - Reason for ending session
   * @returns {Promise<void>}
   */
  async endSession(sessionId, reason = 'normal') {
    try {
      const session = await this.getSession(sessionId);
      
      if (session) {
        const endTime = new Date().toISOString();
        const duration = new Date(endTime).getTime() - new Date(session.startTime).getTime();

        // Log session end
        await dataManager.logActivity({
          action: 'USSD_Session_End',
          user_phone: session.phoneNumber,
          session_id: sessionId,
          details: `Session ended: ${reason}, Duration: ${Math.round(duration / 1000)}s`
        });

        // Update session with end info
        await this.updateSession(sessionId, {
          state: 'ended',
          endTime: endTime,
          endReason: reason,
          duration: duration
        });

        // Clean up session after delay
        setTimeout(async () => {
          await dataManager.deleteUssdSession(sessionId);
        }, 60000); // Keep for 1 minute for debugging
      }
    } catch (error) {
      logger.error('Error ending session:', error);
    }
  }

  /**
   * Get session statistics
   * @param {string} sessionId - Session identifier
   * @returns {Promise<Object>} Session stats
   */
  async getSessionStats(sessionId) {
    try {
      const session = await this.getSession(sessionId);
      
      if (!session) {
        return null;
      }

      const now = new Date();
      const startTime = new Date(session.startTime);
      const duration = now.getTime() - startTime.getTime();

      return {
        sessionId,
        phoneNumber: session.phoneNumber,
        duration: Math.round(duration / 1000), // in seconds
        menuInteractions: session.user_input ? session.user_input.length : 0,
        currentMenu: session.current_menu,
        userType: session.user_type,
        authenticated: session.authenticated || false,
        state: session.state
      };
    } catch (error) {
      logger.error('Error getting session stats:', error);
      return null;
    }
  }

  /**
   * Validate session state for specific operations
   * @param {string} sessionId - Session identifier
   * @param {string} requiredState - Required session state
   * @returns {Promise<boolean>} True if session is valid
   */
  async validateSessionState(sessionId, requiredState) {
    try {
      const session = await this.getSession(sessionId);
      
      if (!session) {
        return false;
      }

      switch (requiredState) {
        case 'authenticated':
          return session.authenticated === true;
        
        case 'provider':
          return session.user_type === 'provider' && session.provider !== null;
        
        case 'patient':
          return session.user_type === 'patient' && session.patient !== null;
        
        case 'medical_record':
          return session.provider !== null && session.patient !== null;
        
        default:
          return session.state === 'active';
      }
    } catch (error) {
      logger.error('Error validating session state:', error);
      return false;
    }
  }

  /**
   * Get all active sessions (for monitoring)
   * @returns {Promise<Array>} List of active sessions
   */
  async getActiveSessions() {
    try {
      // This would need to be implemented with a query if using Firestore
      // For now, return empty array as we don't have a direct query method
      return [];
    } catch (error) {
      logger.error('Error getting active sessions:', error);
      return [];
    }
  }

  /**
   * Clean up expired sessions
   * @returns {Promise<number>} Number of sessions cleaned
   */
  async cleanupExpiredSessions() {
    try {
      let cleanedCount = 0;
      
      // Note: In a production environment, you would want to implement
      // a more efficient cleanup using Firestore queries with timestamps
      // For now, this is a placeholder implementation
      
      logger.info(`Cleanup completed: ${cleanedCount} expired sessions removed`);
      return cleanedCount;
    } catch (error) {
      logger.error('Error cleaning up sessions:', error);
      return 0;
    }
  }

  /**
   * Start periodic cleanup of expired sessions
   * @returns {void}
   */
  startCleanupSchedule() {
    setInterval(async () => {
      try {
        await this.cleanupExpiredSessions();
      } catch (error) {
        logger.error('Error in scheduled cleanup:', error);
      }
    }, this.cleanupInterval);
  }

  /**
   * Export session data for debugging
   * @param {string} sessionId - Session identifier
   * @returns {Promise<Object>} Complete session data
   */
  async exportSessionData(sessionId) {
    try {
      const session = await dataManager.getUssdSession(sessionId);
      
      if (!session) {
        return null;
      }

      return {
        ...session,
        exported_at: new Date().toISOString(),
        session_stats: await this.getSessionStats(sessionId)
      };
    } catch (error) {
      logger.error('Error exporting session data:', error);
      return null;
    }
  }

  /**
   * Restore session from backup data
   * @param {string} sessionId - Session identifier
   * @param {Object} sessionData - Session data to restore
   * @returns {Promise<boolean>} Success status
   */
  async restoreSession(sessionId, sessionData) {
    try {
      // Remove export metadata
      const { exported_at, session_stats, ...cleanSessionData } = sessionData;
      
      await dataManager.updateUssdSession(sessionId, {
        ...cleanSessionData,
        restored_at: new Date().toISOString(),
        lastActivity: new Date().toISOString()
      });

      return true;
    } catch (error) {
      logger.error('Error restoring session:', error);
      return false;
    }
  }

  /**
   * Get session navigation history
   * @param {string} sessionId - Session identifier
   * @returns {Promise<Array>} Navigation history
   */
  async getNavigationHistory(sessionId) {
    try {
      const session = await this.getSession(sessionId);
      
      if (!session || !session.menu_path) {
        return [];
      }

      return session.menu_path.map(item => ({
        menu: item.menu,
        timestamp: item.timestamp,
        duration: null // Could calculate duration between menu changes
      }));
    } catch (error) {
      logger.error('Error getting navigation history:', error);
      return [];
    }
  }

  /**
   * Check if user can perform action based on session state
   * @param {string} sessionId - Session identifier
   * @param {string} action - Action to check
   * @returns {Promise<Object>} Permission result
   */
  async checkPermission(sessionId, action) {
    try {
      const session = await this.getSession(sessionId);
      
      if (!session) {
        return { allowed: false, reason: 'Session not found or expired' };
      }

      // Check basic session validity
      if (session.state !== 'active') {
        return { allowed: false, reason: 'Session is not active' };
      }

      // Check specific action permissions
      switch (action) {
        case 'create_patient':
        case 'create_medical_record':
        case 'view_patient_records':
          if (!session.provider) {
            return { allowed: false, reason: 'Provider authentication required' };
          }
          if (!session.provider.is_active) {
            return { allowed: false, reason: 'Provider account is inactive' };
          }
          return { allowed: true };

        case 'view_own_records':
          if (!session.patient && !session.phoneNumber) {
            return { allowed: false, reason: 'Patient identification required' };
          }
          return { allowed: true };

        case 'emergency_access':
          // Emergency access is always allowed
          return { allowed: true };

        default:
          return { allowed: true };
      }
    } catch (error) {
      logger.error('Error checking permission:', error);
      return { allowed: false, reason: 'Permission check failed' };
    }
  }

  /**
   * Set session context for complex workflows
   * @param {string} sessionId - Session identifier
   * @param {Object} context - Context data
   * @returns {Promise<void>}
   */
  async setContext(sessionId, context) {
    try {
      await this.updateSession(sessionId, {
        context: {
          ...context,
          set_at: new Date().toISOString()
        }
      });
    } catch (error) {
      logger.error('Error setting context:', error);
    }
  }

  /**
   * Get session context
   * @param {string} sessionId - Session identifier
   * @returns {Promise<Object|null>} Context data
   */
  async getContext(sessionId) {
    try {
      const session = await this.getSession(sessionId);
      return session ? session.context : null;
    } catch (error) {
      logger.error('Error getting context:', error);
      return null;
    }
  }

  /**
   * Clear session context
   * @param {string} sessionId - Session identifier
   * @returns {Promise<void>}
   */
  async clearContext(sessionId) {
    try {
      await this.updateSession(sessionId, { context: null });
    } catch (error) {
      logger.error('Error clearing context:', error);
    }
  }

  /**
   * Log session event
   * @param {string} sessionId - Session identifier
   * @param {string} event - Event type
   * @param {Object} data - Event data
   * @returns {Promise<void>}
   */
  async logEvent(sessionId, event, data = {}) {
    try {
      const session = await this.getSession(sessionId);
      
      if (session) {
        await dataManager.logActivity({
          action: `USSD_${event}`,
          user_phone: session.phoneNumber,
          session_id: sessionId,
          details: JSON.stringify(data),
          provider_id: session.provider?.id,
          patient_id: session.patient?.id,
          facility_id: session.provider?.facility_id
        });
      }
    } catch (error) {
      logger.error('Error logging session event:', error);
    }
  }

  /**
   * Get session timeout remaining
   * @param {string} sessionId - Session identifier
   * @returns {Promise<number>} Seconds remaining until timeout
   */
  async getTimeoutRemaining(sessionId) {
    try {
      const session = await this.getSession(sessionId);
      
      if (!session) {
        return 0;
      }

      const lastActivity = new Date(session.lastActivity);
      const now = new Date();
      const elapsed = now.getTime() - lastActivity.getTime();
      const remaining = Math.max(0, this.sessionTimeout - elapsed);

      return Math.round(remaining / 1000); // Return in seconds
    } catch (error) {
      logger.error('Error getting timeout remaining:', error);
      return 0;
    }
  }

  /**
   * Extend session timeout
   * @param {string} sessionId - Session identifier
   * @param {number} additionalTime - Additional time in milliseconds
   * @returns {Promise<boolean>} Success status
   */
  async extendSession(sessionId, additionalTime = 300000) {
    try {
      const session = await this.getSession(sessionId);
      
      if (!session) {
        return false;
      }

      await this.updateSession(sessionId, {
        lastActivity: new Date().toISOString(),
        extended_at: new Date().toISOString(),
        extension_duration: additionalTime
      });

      return true;
    } catch (error) {
      logger.error('Error extending session:', error);
      return false;
    }
  }
}

module.exports = new SessionManager();