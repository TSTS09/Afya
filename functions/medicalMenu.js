/**
 * Medical Menu - Handles medical record creation workflow for USSD
 * Provides step-by-step guided medical record entry
 */

const dataManager = require('./dataManager');
const sessionManager = require('./sessionManager');
const { logger } = require('firebase-functions');

class MedicalMenu {
  constructor() {
    this.steps = {
      PATIENT_LOOKUP: 'patient_lookup',
      PATIENT_PHONE: 'patient_phone',
      PATIENT_NOT_FOUND: 'patient_not_found',
      NEW_PATIENT_NAME: 'new_patient_name',
      NEW_PATIENT_DOB: 'new_patient_dob',
      NEW_PATIENT_GENDER: 'new_patient_gender',
      NEW_PATIENT_CONFIRM: 'new_patient_confirm',
      CHIEF_COMPLAINT: 'chief_complaint',
      HISTORY: 'history',
      EXAMINATION: 'examination',
      DIAGNOSIS: 'diagnosis',
      TREATMENT: 'treatment',
      PRESCRIPTION: 'prescription',
      FOLLOW_UP: 'follow_up',
      RECORD_CONFIRM: 'record_confirm',
      PATIENT_SEARCH: 'patient_search',
      PATIENT_SELECTION: 'patient_selection'
    };
  }

  /**
   * Handle patient lookup menu
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @param {string} phoneNumber - User phone number
   * @returns {Promise<string>} USSD response
   */
  async handlePatientLookup(sessionId, text, phoneNumber) {
    try {
      const session = await sessionManager.getSession(sessionId);
      
      if (!session || !session.provider) {
        return 'END Session expired. Please dial *384*15897# again.';
      }

      const parts = text.split('*');
      
      // If just entering this menu (1*PIN*1)
      if (parts.length === 3) {
        await sessionManager.updateSession(sessionId, {
          menu_step: this.steps.PATIENT_LOOKUP
        });

        return `CON Patient Lookup - ${session.provider.name}
        
1. Enter patient phone number
2. Search by name
3. Create new patient
4. Back to main menu

Enter choice:`;
      }

      const choice = parts[3];

      switch (choice) {
        case '1':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.PATIENT_PHONE
          });
          return 'CON Enter patient phone number (0XXXXXXXXX):';

        case '2':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.PATIENT_SEARCH
          });
          return 'CON Enter patient name to search:';

        case '3':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.NEW_PATIENT_NAME
          });
          return 'CON New Patient Registration\n\nEnter patient full name:';

        case '4':
          return await this.backToProviderMenu(sessionId, session.provider);

        default:
          return 'CON Invalid choice. Please try again:\n\n1. Phone number\n2. Search name\n3. New patient\n4. Back';
      }
    } catch (error) {
      logger.error('Error in patient lookup:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Handle patient phone number input
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handlePatientPhone(sessionId, text) {
    try {
      const parts = text.split('*');
      const patientPhone = parts[parts.length - 1];

      // Validate phone number format
      const phoneValidation = dataManager.validateGhanaPhone(patientPhone);
      if (!phoneValidation.valid) {
        return 'CON Invalid phone format. Enter 10-digit phone number (0XXXXXXXXX):';
      }

      try {
        // Look up patient
        const patient = await dataManager.getPatientByPhone(phoneValidation.phone);
        
        await sessionManager.updateSession(sessionId, {
          patient: patient,
          menu_step: this.steps.CHIEF_COMPLAINT
        });

        return `CON Patient Found:
Name: ${patient.name}
Phone: ${patient.phone}
${patient.date_of_birth ? `DOB: ${patient.date_of_birth}` : ''}

Enter chief complaint:`;

      } catch (error) {
        // Patient not found
        await sessionManager.updateSession(sessionId, {
          temp_patient_phone: phoneValidation.phone,
          menu_step: this.steps.PATIENT_NOT_FOUND
        });

        return `CON Patient not found: ${phoneValidation.phone}

1. Register new patient
2. Try different number
3. Back to patient lookup

Enter choice:`;
      }
    } catch (error) {
      logger.error('Error handling patient phone:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Handle patient not found menu
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handlePatientNotFound(sessionId, text) {
    try {
      const parts = text.split('*');
      const choice = parts[parts.length - 1];
      const session = await sessionManager.getSession(sessionId);

      switch (choice) {
        case '1':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.NEW_PATIENT_NAME
          });
          return `CON New Patient Registration
Phone: ${session.temp_patient_phone}

Enter patient full name:`;

        case '2':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.PATIENT_PHONE
          });
          return 'CON Enter patient phone number (0XXXXXXXXX):';

        case '3':
          return await this.handlePatientLookup(sessionId, text.split('*').slice(0, -1).join('*'), session.provider.phone);

        default:
          return 'CON Invalid choice. Please try again:\n\n1. Register new\n2. Try different number\n3. Back';
      }
    } catch (error) {
      logger.error('Error handling patient not found:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Handle new patient registration
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handleNewPatient(sessionId, text) {
    try {
      const session = await sessionManager.getSession(sessionId);
      const parts = text.split('*');
      const input = parts[parts.length - 1];

      switch (session.menu_step) {
        case this.steps.NEW_PATIENT_NAME:
          if (!input || input.trim().length < 2) {
            return 'CON Name too short. Enter patient full name:';
          }

          await sessionManager.updateSession(sessionId, {
            temp_patient_name: input.trim(),
            menu_step: this.steps.NEW_PATIENT_DOB
          });

          return 'CON Enter date of birth (DD/MM/YYYY) or 0 to skip:';

        case this.steps.NEW_PATIENT_DOB:
          let dob = '';
          if (input !== '0') {
            // Basic date validation
            if (!/^\d{2}\/\d{2}\/\d{4}$/.test(input)) {
              return 'CON Invalid date format. Use DD/MM/YYYY or 0 to skip:';
            }
            dob = input;
          }

          await sessionManager.updateSession(sessionId, {
            temp_patient_dob: dob,
            menu_step: this.steps.NEW_PATIENT_GENDER
          });

          return 'CON Select gender:\n\n1. Male\n2. Female\n3. Other\n4. Skip\n\nEnter choice:';

        case this.steps.NEW_PATIENT_GENDER:
          const genderMap = { '1': 'Male', '2': 'Female', '3': 'Other', '4': '' };
          const gender = genderMap[input] || '';

          await sessionManager.updateSession(sessionId, {
            temp_patient_gender: gender,
            menu_step: this.steps.NEW_PATIENT_CONFIRM
          });

          return `CON Confirm new patient:
Name: ${session.temp_patient_name}
Phone: ${session.temp_patient_phone}
DOB: ${session.temp_patient_dob || 'Not provided'}
Gender: ${gender || 'Not provided'}

1. Register patient
2. Cancel

Enter choice:`;

        case this.steps.NEW_PATIENT_CONFIRM:
          if (input === '1') {
            // Register the patient
            const patientData = {
              name: session.temp_patient_name,
              phone: session.temp_patient_phone,
              date_of_birth: session.temp_patient_dob || '',
              gender: session.temp_patient_gender || '',
              registered_by_phone: session.provider.phone
            };

            try {
              const result = await dataManager.createPatient(patientData);
              
              await sessionManager.updateSession(sessionId, {
                patient: result.patient,
                menu_step: this.steps.CHIEF_COMPLAINT,
                // Clear temp data
                temp_patient_name: null,
                temp_patient_phone: null,
                temp_patient_dob: null,
                temp_patient_gender: null
              });

              return `CON Patient registered successfully!
Name: ${result.patient.name}

Now enter chief complaint:`;

            } catch (error) {
              return `CON Registration failed: ${error.message}

1. Try again
2. Back to menu

Enter choice:`;
            }
          } else if (input === '2') {
            return await this.handlePatientLookup(sessionId, text.split('*').slice(0, -4).join('*'), session.provider.phone);
          } else {
            return 'CON Invalid choice:\n\n1. Register patient\n2. Cancel';
          }

        default:
          return 'END Session error. Please dial *384*15897# again.';
      }
    } catch (error) {
      logger.error('Error handling new patient:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Handle medical record creation
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handleMedicalRecord(sessionId, text) {
    try {
      const session = await sessionManager.getSession(sessionId);
      const parts = text.split('*');
      const input = parts[parts.length - 1];

      if (!session.patient) {
        return 'END Session error. Please start over.';
      }

      switch (session.menu_step) {
        case this.steps.CHIEF_COMPLAINT:
          if (!input || input.trim().length < 3) {
            return 'CON Chief complaint too short. Enter patient\'s main concern:';
          }

          await sessionManager.updateSession(sessionId, {
            medical_record: { chief_complaint: input.trim() },
            menu_step: this.steps.HISTORY
          });

          return 'CON Enter history of present illness (or 0 to skip):';

        case this.steps.HISTORY:
          const history = input === '0' ? '' : input.trim();
          
          await sessionManager.updateSession(sessionId, {
            medical_record: { 
              ...session.medical_record, 
              history 
            },
            menu_step: this.steps.EXAMINATION
          });

          return 'CON Enter physical examination findings (or 0 to skip):';

        case this.steps.EXAMINATION:
          const examination = input === '0' ? '' : input.trim();
          
          await sessionManager.updateSession(sessionId, {
            medical_record: { 
              ...session.medical_record, 
              physical_examination: examination 
            },
            menu_step: this.steps.DIAGNOSIS
          });

          return 'CON Enter diagnosis:';

        case this.steps.DIAGNOSIS:
          if (!input || input.trim().length < 2) {
            return 'CON Diagnosis required. Enter diagnosis:';
          }

          await sessionManager.updateSession(sessionId, {
            medical_record: { 
              ...session.medical_record, 
              diagnosis: input.trim() 
            },
            menu_step: this.steps.TREATMENT
          });

          return 'CON Enter treatment given (or 0 to skip):';

        case this.steps.TREATMENT:
          const treatment = input === '0' ? '' : input.trim();
          
          await sessionManager.updateSession(sessionId, {
            medical_record: { 
              ...session.medical_record, 
              treatment 
            },
            menu_step: this.steps.PRESCRIPTION
          });

          return 'CON Enter prescription (or 0 to skip):';

        case this.steps.PRESCRIPTION:
          const prescription = input === '0' ? '' : input.trim();
          
          await sessionManager.updateSession(sessionId, {
            medical_record: { 
              ...session.medical_record, 
              prescription 
            },
            menu_step: this.steps.FOLLOW_UP
          });

          return 'CON Enter follow-up instructions (or 0 to skip):';

        case this.steps.FOLLOW_UP:
          const followUp = input === '0' ? '' : input.trim();
          
          await sessionManager.updateSession(sessionId, {
            medical_record: { 
              ...session.medical_record, 
              follow_up: followUp 
            },
            menu_step: this.steps.RECORD_CONFIRM
          });

          const record = session.medical_record;
          return `CON Review Medical Record:
Patient: ${session.patient.name}
Complaint: ${record.chief_complaint}
Diagnosis: ${record.diagnosis}
Treatment: ${record.treatment || 'None'}
Prescription: ${record.prescription || 'None'}

1. Save record
2. Edit
3. Cancel

Enter choice:`;

        case this.steps.RECORD_CONFIRM:
          if (input === '1') {
            // Save the medical record
            const recordData = {
              patient_id: session.patient.id,
              provider_id: session.provider.id,
              facility_id: session.provider.facility_id,
              ...session.medical_record
            };

            try {
              const result = await dataManager.createMedicalRecord(recordData);
              
              // Clear session medical record data
              await sessionManager.updateSession(sessionId, {
                medical_record: null,
                patient: null,
                menu_step: null
              });

              return `END Medical record saved successfully!

Record ID: ${result.record.id.substring(0, 8)}
Patient: ${session.patient.name}
Date: ${new Date().toLocaleDateString()}

Thank you for using Afya Medical EHR.`;

            } catch (error) {
              return `END Failed to save record: ${error.message}

Please try again by dialing *384*15897#.`;
            }
          } else if (input === '2') {
            return 'CON Edit options:\n\n1. Chief complaint\n2. Diagnosis\n3. Treatment\n4. Prescription\n\nEnter choice:';
          } else if (input === '3') {
            await sessionManager.updateSession(sessionId, {
              medical_record: null,
              patient: null,
              menu_step: null
            });
            return await this.backToProviderMenu(sessionId, session.provider);
          } else {
            return 'CON Invalid choice:\n\n1. Save record\n2. Edit\n3. Cancel';
          }

        default:
          return 'END Session error. Please dial *384*15897# again.';
      }
    } catch (error) {
      logger.error('Error handling medical record:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Handle patient search by name
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handlePatientSearch(sessionId, text) {
    try {
      const parts = text.split('*');
      const searchQuery = parts[parts.length - 1];

      if (!searchQuery || searchQuery.trim().length < 2) {
        return 'CON Search term too short. Enter patient name:';
      }

      const patients = await dataManager.searchPatients(searchQuery.trim());

      if (patients.length === 0) {
        return `CON No patients found for "${searchQuery}"

1. Try different name
2. Enter phone number
3. Register new patient
4. Back to menu

Enter choice:`;
      }

      if (patients.length === 1) {
        // Only one patient found, select automatically
        await sessionManager.updateSession(sessionId, {
          patient: patients[0],
          menu_step: this.steps.CHIEF_COMPLAINT
        });

        return `CON Patient Found:
Name: ${patients[0].name}
Phone: ${patients[0].phone}

Enter chief complaint:`;
      }

      // Multiple patients found, show list
      let response = `CON Found ${patients.length} patients:\n\n`;
      patients.slice(0, 8).forEach((patient, index) => {
        response += `${index + 1}. ${patient.name} (${patient.phone})\n`;
      });

      if (patients.length > 8) {
        response += `\nShowing first 8 results.`;
      }

      response += '\n9. Search again\n0. Back\n\nSelect patient:';

      // Store search results in session
      await sessionManager.updateSession(sessionId, {
        search_results: patients.slice(0, 8),
        menu_step: this.steps.PATIENT_SELECTION
      });

      return response;
    } catch (error) {
      logger.error('Error handling patient search:', error);
      return 'END Sorry, there was an error searching. Please try again.';
    }
  }

  /**
   * Handle patient selection from search results
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handlePatientSelection(sessionId, text) {
    try {
      const session = await sessionManager.getSession(sessionId);
      const parts = text.split('*');
      const choice = parts[parts.length - 1];

      if (!session.search_results || session.search_results.length === 0) {
        return 'END Session expired. Please dial *384*15897# again.';
      }

      if (choice === '9') {
        await sessionManager.updateSession(sessionId, {
          menu_step: this.steps.PATIENT_SEARCH,
          search_results: null
        });
        return 'CON Enter patient name to search:';
      }

      if (choice === '0') {
        return await this.handlePatientLookup(sessionId, text.split('*').slice(0, -2).join('*'), session.provider.phone);
      }

      const patientIndex = parseInt(choice) - 1;
      
      if (patientIndex >= 0 && patientIndex < session.search_results.length) {
        const selectedPatient = session.search_results[patientIndex];
        
        await sessionManager.updateSession(sessionId, {
          patient: selectedPatient,
          search_results: null,
          menu_step: this.steps.CHIEF_COMPLAINT
        });

        return `CON Patient Selected:
Name: ${selectedPatient.name}
Phone: ${selectedPatient.phone}

Enter chief complaint:`;
      } else {
        return 'CON Invalid selection. Choose patient number (1-8), 9 to search again, or 0 to go back:';
      }
    } catch (error) {
      logger.error('Error handling patient selection:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Back to provider main menu
   * @param {string} sessionId - Session ID
   * @param {Object} provider - Provider data
   * @returns {Promise<string>} USSD response
   */
  async backToProviderMenu(sessionId, provider) {
    await sessionManager.updateSession(sessionId, {
      menu_step: null,
      patient: null,
      medical_record: null,
      search_results: null,
      temp_patient_name: null,
      temp_patient_phone: null,
      temp_patient_dob: null,
      temp_patient_gender: null
    });

    return `CON Dr. ${provider.name}
${provider.facility.name}

1. Patient lookup
2. New patient
3. View recent records
4. Profile
5. Logout

Enter choice:`;
  }

  /**
   * Handle record editing
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handleRecordEdit(sessionId, text) {
    try {
      const session = await sessionManager.getSession(sessionId);
      const parts = text.split('*');
      const choice = parts[parts.length - 1];

      switch (choice) {
        case '1':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.CHIEF_COMPLAINT
          });
          return 'CON Enter new chief complaint:';

        case '2':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.DIAGNOSIS
          });
          return 'CON Enter new diagnosis:';

        case '3':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.TREATMENT
          });
          return 'CON Enter new treatment:';

        case '4':
          await sessionManager.updateSession(sessionId, {
            menu_step: this.steps.PRESCRIPTION
          });
          return 'CON Enter new prescription:';

        default:
          return 'CON Invalid choice. Select field to edit:\n\n1. Chief complaint\n2. Diagnosis\n3. Treatment\n4. Prescription';
      }
    } catch (error) {
      logger.error('Error handling record edit:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Handle step-by-step record creation workflow
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @returns {Promise<string>} USSD response
   */
  async handleRecordCreationFlow(sessionId, text) {
    try {
      const session = await sessionManager.getSession(sessionId);
      
      if (!session || !session.provider) {
        return 'END Session expired. Please dial *384*15897# again.';
      }

      // Route based on current menu step
      switch (session.menu_step) {
        case this.steps.PATIENT_LOOKUP:
          return await this.handlePatientLookup(sessionId, text, session.provider.phone);
        
        case this.steps.PATIENT_PHONE:
          return await this.handlePatientPhone(sessionId, text);
        
        case this.steps.PATIENT_NOT_FOUND:
          return await this.handlePatientNotFound(sessionId, text);
        
        case this.steps.NEW_PATIENT_NAME:
        case this.steps.NEW_PATIENT_DOB:
        case this.steps.NEW_PATIENT_GENDER:
        case this.steps.NEW_PATIENT_CONFIRM:
          return await this.handleNewPatient(sessionId, text);
        
        case this.steps.PATIENT_SEARCH:
          return await this.handlePatientSearch(sessionId, text);
        
        case this.steps.PATIENT_SELECTION:
          return await this.handlePatientSelection(sessionId, text);
        
        case this.steps.CHIEF_COMPLAINT:
        case this.steps.HISTORY:
        case this.steps.EXAMINATION:
        case this.steps.DIAGNOSIS:
        case this.steps.TREATMENT:
        case this.steps.PRESCRIPTION:
        case this.steps.FOLLOW_UP:
        case this.steps.RECORD_CONFIRM:
          return await this.handleMedicalRecord(sessionId, text);
        
        default:
          return await this.handlePatientLookup(sessionId, text, session.provider.phone);
      }
    } catch (error) {
      logger.error('Error in record creation flow:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Handle quick patient registration
   * @param {string} sessionId - USSD session ID
   * @param {string} text - User input
   * @param {string} phoneNumber - User phone number
   * @returns {Promise<string>} USSD response
   */
  async handleQuickPatientRegistration(sessionId, text, phoneNumber) {
    try {
      const session = await sessionManager.getSession(sessionId);
      const parts = text.split('*');
      
      if (parts.length === 3) {
        // Just entered new patient menu
        await sessionManager.updateSession(sessionId, {
          menu_step: this.steps.NEW_PATIENT_NAME
        });
        return 'CON Quick Patient Registration\n\nEnter patient full name:';
      }
      
      return await this.handleNewPatient(sessionId, text);
    } catch (error) {
      logger.error('Error in quick patient registration:', error);
      return 'END Sorry, there was an error. Please try again.';
    }
  }

  /**
   * Get current step description
   * @param {string} step - Current step
   * @returns {string} Step description
   */
  getStepDescription(step) {
    const descriptions = {
      [this.steps.PATIENT_LOOKUP]: 'Patient Lookup Menu',
      [this.steps.PATIENT_PHONE]: 'Enter Patient Phone',
      [this.steps.PATIENT_NOT_FOUND]: 'Patient Not Found Options',
      [this.steps.NEW_PATIENT_NAME]: 'Enter Patient Name',
      [this.steps.NEW_PATIENT_DOB]: 'Enter Date of Birth',
      [this.steps.NEW_PATIENT_GENDER]: 'Select Gender',
      [this.steps.NEW_PATIENT_CONFIRM]: 'Confirm Patient Registration',
      [this.steps.CHIEF_COMPLAINT]: 'Enter Chief Complaint',
      [this.steps.HISTORY]: 'Enter History',
      [this.steps.EXAMINATION]: 'Enter Examination',
      [this.steps.DIAGNOSIS]: 'Enter Diagnosis',
      [this.steps.TREATMENT]: 'Enter Treatment',
      [this.steps.PRESCRIPTION]: 'Enter Prescription',
      [this.steps.FOLLOW_UP]: 'Enter Follow-up',
      [this.steps.RECORD_CONFIRM]: 'Confirm Medical Record',
      [this.steps.PATIENT_SEARCH]: 'Search Patient by Name',
      [this.steps.PATIENT_SELECTION]: 'Select Patient from Results'
    };
    
    return descriptions[step] || 'Unknown Step';
  }

  /**
   * Validate medical record data
   * @param {Object} recordData - Medical record data
   * @returns {Object} Validation result
   */
  validateMedicalRecord(recordData) {
    const errors = [];
    
    if (!recordData.chief_complaint || recordData.chief_complaint.trim().length < 3) {
      errors.push('Chief complaint is required (minimum 3 characters)');
    }
    
    if (!recordData.diagnosis || recordData.diagnosis.trim().length < 2) {
      errors.push('Diagnosis is required (minimum 2 characters)');
    }
    
    return {
      valid: errors.length === 0,
      errors: errors
    };
  }

  /**
   * Format medical record for display
   * @param {Object} record - Medical record
   * @param {Object} patient - Patient data
   * @returns {string} Formatted record
   */
  formatMedicalRecordSummary(record, patient) {
    let summary = `Medical Record Summary:\n\n`;
    summary += `Patient: ${patient.name}\n`;
    summary += `Phone: ${patient.phone}\n`;
    summary += `Date: ${new Date().toLocaleDateString()}\n\n`;
    summary += `Chief Complaint: ${record.chief_complaint}\n`;
    
    if (record.history) {
      summary += `History: ${record.history}\n`;
    }
    
    if (record.physical_examination) {
      summary += `Examination: ${record.physical_examination}\n`;
    }
    
    summary += `Diagnosis: ${record.diagnosis}\n`;
    
    if (record.treatment) {
      summary += `Treatment: ${record.treatment}\n`;
    }
    
    if (record.prescription) {
      summary += `Prescription: ${record.prescription}\n`;
    }
    
    if (record.follow_up) {
      summary += `Follow-up: ${record.follow_up}\n`;
    }
    
    return summary;
  }
}

module.exports = new MedicalMenu();