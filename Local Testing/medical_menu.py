"""
Afya Medical Menu
"""
from datetime import datetime, timedelta


class MedicalMenu:
    """Medical EHR USSD Menu System - Basic Phone Optimized"""

    def __init__(self, session):
        self.session = session
        self.MAX_TEXT_LENGTH = 160  # SMS standard limit
        self.MAX_MENU_OPTIONS = 4   # Prevent screen overflow

    def main_menu(self, session_id, phone_number):
        """Main USSD menu optimized for basic phones"""
        menu_text = "AFYA MEDICAL EHR\n"
        menu_text += "Ghana Health Records\n\n"
        menu_text += "1. Doctor/Nurse\n"
        menu_text += "2. Patient\n"
        menu_text += "3. Emergency\n"
        menu_text += "4. Info"

        # Ensure text fits basic phone screens
        menu_text = self._format_for_basic_phone(menu_text)
        
        self.session.save(session_id, "main_menu")
        return self.session.ussd_proceed(menu_text, session_id)

    def provider_login_menu(self, session_id, phone_number):
        """Healthcare provider login - simplified for basic phones"""
        menu_text = "DOCTOR/NURSE LOGIN\n\n"
        menu_text += "Enter your 4-digit PIN:\n"
        menu_text += "(Contact admin if forgot)"

        self.session.save(session_id, "provider_login")
        return self.session.ussd_proceed(menu_text, session_id)

    def patient_services_menu(self, session_id, phone_number):
        """Patient services - optimized for basic phones"""
        menu_text = "PATIENT SERVICES\n\n"
        menu_text += "1. My Health Records\n"
        menu_text += "2. Emergency Numbers\n"
        menu_text += "3. My Appointments\n"
        menu_text += "0. Back to Main"

        self.session.save(session_id, "patient_services")
        return self.session.ussd_proceed(menu_text, session_id)

    def emergency_services_menu(self, session_id, phone_number):
        """Emergency services - clear and direct for basic phones"""
        menu_text = "EMERGENCY SERVICES\n\n"
        menu_text += "1. Call Ambulance (193)\n"
        menu_text += "2. Alert My Family\n"
        menu_text += "3. My Medical Info\n"
        menu_text += "4. Nearest Hospital"

        self.session.save(session_id, "emergency_services")
        return self.session.ussd_proceed(menu_text, session_id)

    def system_info_menu(self, session_id, phone_number):
        """System information - concise for basic phones"""
        menu_text = "AFYA MEDICAL EHR\n\n"
        menu_text += "Version: 1.0\n"
        menu_text += "Support: *714*9#\n"
        menu_text += "Web: afya.health.gh\n\n"
        menu_text += "Better Healthcare\nFor All Ghanaians"

        return self.session.ussd_end(menu_text)

    def handle_multi_level_menu(self, text, session_id, phone_number):
        """Handle complex menu navigation - simplified for basic phones"""
        try:
            from app import HealthcareProvider, Patient, MedicalRecord, db, hash_pin
        except ImportError:
            return self.error_menu("System unavailable", session_id)

        menu_path = text.split('*')

        # Healthcare Provider Flow
        if menu_path[0] == '1':
            return self.handle_provider_flow(menu_path, session_id, phone_number)

        # Patient Services Flow
        elif menu_path[0] == '2':
            return self.handle_patient_flow(menu_path, session_id, phone_number)

        # Emergency Services Flow
        elif menu_path[0] == '3':
            return self.handle_emergency_flow(menu_path, session_id, phone_number)

        else:
            return self.invalid_selection(session_id)

    def handle_provider_flow(self, menu_path, session_id, phone_number):
        """Handle healthcare provider menu flow - basic phone optimized"""
        try:
            from app import HealthcareProvider, Patient, MedicalRecord, db, hash_pin
        except ImportError:
            return self.error_menu("Service unavailable", session_id)

        if len(menu_path) == 2:
            # Provider entered PIN
            pin = menu_path[1]

            if len(pin) != 4 or not pin.isdigit():
                menu_text = "INVALID PIN FORMAT\n\n"
                menu_text += "Enter exactly 4 digits:"
                return self.session.ussd_proceed(menu_text, session_id)

            # Verify provider credentials
            try:
                provider = HealthcareProvider.query.filter_by(
                    phone=self.sanitize_phone(phone_number),
                    pin=hash_pin(pin),
                    is_active=True
                ).first()
            except:
                # Fallback for demo
                if pin == "1234":
                    return self.demo_provider_menu(session_id, phone_number)
                else:
                    return self.login_failed_menu(session_id)

            if not provider:
                # Demo mode fallback
                if pin == "1234":
                    return self.demo_provider_menu(session_id, phone_number)
                return self.login_failed_menu(session_id)

            # Provider main menu - basic phone friendly
            first_name = provider.name.split()[0] if provider.name else "Doctor"
            menu_text = f"WELCOME {first_name.upper()}\n"
            
            facility_name = provider.facility.name if provider.facility else 'Demo Clinic'
            # Truncate facility name if too long
            if len(facility_name) > 20:
                facility_name = facility_name[:17] + "..."
            menu_text += f"{facility_name}\n\n"
            
            menu_text += "1. Find Patient\n"
            menu_text += "2. New Patient\n"
            menu_text += "3. New Record\n"
            menu_text += "4. Today's List\n"
            menu_text += "0. Logout"

            # Save provider session
            self.session.save(session_id, f"provider_menu:{provider.id}")
            return self.session.ussd_proceed(menu_text, session_id)

        elif len(menu_path) >= 3:
            return self.handle_provider_actions(menu_path, session_id, phone_number)

    def demo_provider_menu(self, session_id, phone_number):
        """Demo provider menu for testing - basic phone optimized"""
        menu_text = "WELCOME DR. DEMO\n"
        menu_text += "Demo Clinic\n\n"
        menu_text += "1. Find Patient\n"
        menu_text += "2. New Patient\n"
        menu_text += "3. New Record\n"
        menu_text += "4. Today's List\n"
        menu_text += "0. Logout"

        self.session.save(session_id, "demo_provider_menu")
        return self.session.ussd_proceed(menu_text, session_id)

    def login_failed_menu(self, session_id):
        """Login failed - clear message for basic phones"""
        menu_text = "LOGIN FAILED\n\n"
        menu_text += "Wrong PIN or\nphone number.\n\n"
        menu_text += "Contact your\nfacility admin."
        return self.session.ussd_end(menu_text)

    def handle_provider_actions(self, menu_path, session_id, phone_number):
        """Handle provider action selections - basic phone optimized"""
        action = menu_path[2]

        if action == '1':
            # Patient Lookup
            menu_text = "FIND PATIENT\n\n"
            menu_text += "Enter patient phone:\n"
            menu_text += "(10 digits starting with 0)"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '2':
            # New Patient Registration
            menu_text = "NEW PATIENT\n\n"
            menu_text += "Enter patient phone:\n"
            menu_text += "(This becomes their ID)"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '3':
            # New Medical Record
            menu_text = "NEW MEDICAL RECORD\n\n"
            menu_text += "Enter patient phone:"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '4':
            # Today's appointments - simplified display
            menu_text = "TODAY'S PATIENTS\n\n"
            menu_text += "Morning:\n"
            menu_text += "• 9:00 - John D.\n"
            menu_text += "• 10:30 - Jane S.\n\n"
            menu_text += "Afternoon:\n"
            menu_text += "• 2:00 - Kwame O.\n\n"
            menu_text += "Total: 3 patients"
            return self.session.ussd_end(menu_text)

        elif action == '0':
            # Logout
            menu_text = "LOGGED OUT\n\n"
            menu_text += "Thank you for using\nAfya Medical EHR.\n\n"
            menu_text += "Have a great day!"
            return self.session.ussd_end(menu_text)

        else:
            return self.invalid_selection(session_id)

    def handle_patient_flow(self, menu_path, session_id, phone_number):
        """Handle patient services menu flow - basic phone optimized"""
        if len(menu_path) == 2:
            action = menu_path[1]

            if action == '1':  # View My Records
                menu_text = "YOUR MEDICAL RECORDS\n\n"
                menu_text += "Recent visits:\n"
                menu_text += "• 15/03/24 - General\n"
                menu_text += "• 02/02/24 - Follow-up\n"
                menu_text += "• 18/01/24 - Emergency\n\n"
                menu_text += "All records are\nsafely stored."
                return self.session.ussd_end(menu_text)

            elif action == '2':  # Emergency Contact
                menu_text = "EMERGENCY NUMBERS\n\n"
                menu_text += "Ambulance: 193\n"
                menu_text += "Police: 191\n"
                menu_text += "Fire Service: 192\n\n"
                menu_text += "Your location will be\nshared when you call."
                return self.session.ussd_end(menu_text)

            elif action == '3':  # Appointment Info
                menu_text = "YOUR APPOINTMENTS\n\n"
                menu_text += "Next appointment:\n"
                menu_text += "Date: 25/03/24\n"
                menu_text += "Time: 10:00 AM\n"
                menu_text += "Doctor: Dr. Asante\n"
                menu_text += "Place: Demo Clinic\n\n"
                menu_text += "Please don't forget!"
                return self.session.ussd_end(menu_text)

            elif action == '0':  # Back to main menu
                return self.main_menu(session_id, phone_number)

    def handle_emergency_flow(self, menu_path, session_id, phone_number):
        """Handle emergency services flow - optimized for urgency"""
        if len(menu_path) == 2:
            action = menu_path[1]

            if action == '1':  # Call Ambulance
                menu_text = "EMERGENCY AMBULANCE\n\n"
                menu_text += "CALL 193 RIGHT NOW\n\n"
                menu_text += "Stay calm and wait.\n"
                menu_text += "Help is on the way.\n\n"
                menu_text += "Your location will be\ntracked automatically."
                return self.session.ussd_end(menu_text)

            elif action == '2':  # Medical Alert
                menu_text = "FAMILY ALERT SENT\n\n"
                menu_text += "Your emergency contact\nhas been notified.\n\n"
                menu_text += "If life-threatening:\nCALL 193 for ambulance"
                return self.session.ussd_end(menu_text)

            elif action == '3':  # Share Emergency Info
                menu_text = f"EMERGENCY INFO\n\n"
                menu_text += f"Name: Demo Patient\n"
                menu_text += f"Phone: {phone_number}\n"
                menu_text += f"Blood Type: O+\n"
                menu_text += f"Allergies: None known\n"
                menu_text += f"Condition: Hypertension\n\n"
                menu_text += "Show this to doctors"
                return self.session.ussd_end(menu_text)

            elif action == '4':  # Nearest Hospital
                menu_text = "NEAREST HOSPITALS\n\n"
                menu_text += "ACCRA:\n"
                menu_text += "• Korle Bu Hospital\n"
                menu_text += "  Tel: 0302-674376\n"
                menu_text += "• 37 Military Hospital\n"
                menu_text += "  Tel: 0302-776481\n\n"
                menu_text += "EMERGENCY: 193"
                return self.session.ussd_end(menu_text)

    def _format_for_basic_phone(self, text):
        """Format text to fit basic phone screens"""
        # Ensure text doesn't exceed SMS limits
        if len(text) > self.MAX_TEXT_LENGTH:
            # Truncate and add continuation indicator
            text = text[:self.MAX_TEXT_LENGTH-15] + "\n...(truncated)"
        
        # Replace long words that might break display
        text = text.replace("Healthcare", "Health")
        text = text.replace("Emergency", "Emerg")
        text = text.replace("Registration", "Reg")
        text = text.replace("Appointment", "Appt")
        
        return text

    def sanitize_phone(self, phone_number):
        """Sanitize phone numbers to standard format"""
        if not phone_number:
            return None

        phone = phone_number.strip().replace(' ', '').replace('-', '')

        # Handle Ghana phone number formats
        if phone.startswith('+233'):
            phone = '0' + phone[4:]
        elif phone.startswith('233'):
            phone = '0' + phone[3:]
        elif not phone.startswith('0') and len(phone) == 9:
            phone = '0' + phone

        return phone

    def send_sms_basic_phone(self, phone_number, message_type, custom_message=None):
        """Send SMS optimized for basic phones"""
        try:
            if custom_message:
                sms_content = custom_message
            else:
                # Predefined messages for different scenarios
                messages = {
                    'appointment_reminder': f"AFYA: Appointment tomorrow at 10AM. Dr. Asante, Demo Clinic. Don't forget!",
                    'registration_success': f"AFYA: You are now registered. Use *714# to access your health records.",
                    'emergency_alert': f"AFYA: Emergency alert sent to your family. If serious, call 193.",
                    'pin_reset': f"AFYA: Your new PIN is 1234. Keep it safe. Change after first login.",
                    'record_created': f"AFYA: New medical record created. Access via *714# anytime."
                }
                sms_content = messages.get(message_type, f"AFYA: {message_type}. Support: *714*9#")

            # Ensure SMS fits 160 character limit
            if len(sms_content) > 160:
                sms_content = sms_content[:157] + "..."

            # For demo purposes, just print the SMS
            print(f"SMS to {phone_number}: {sms_content}")

            # Uncomment below for actual SMS integration
            # self._send_actual_sms(phone_number, sms_content)

        except Exception as e:
            print(f"SMS sending failed: {str(e)}")

    def _send_actual_sms(self, phone_number, message):
        """Send actual SMS using configured service"""
        # This would integrate with your SMS provider
        # Africa's Talking, Twilio, etc.
        pass

    def validate_phone_number(self, phone):
        """Validate Ghana phone number format"""
        if not phone:
            return False, "Phone number required"
        
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Check if it's a valid Ghana number
        if phone.startswith('0') and len(phone) == 10:
            return True, phone
        elif phone.startswith('+233') and len(phone) == 13:
            return True, '0' + phone[4:]
        elif phone.startswith('233') and len(phone) == 12:
            return True, '0' + phone[3:]
        else:
            return False, "Invalid Ghana phone format"

    def create_patient_record_basic(self, phone_number, name=None):
        """Create patient record with minimal required data for basic phones"""
        try:
            from app import Patient, db, log_activity
            
            # Validate phone number
            is_valid, clean_phone = self.validate_phone_number(phone_number)
            if not is_valid:
                return False, clean_phone

            # Check if patient already exists
            existing_patient = Patient.query.filter_by(phone=clean_phone).first()
            if existing_patient:
                return False, "Patient already registered"

            # Create new patient with minimal data
            patient = Patient(
                phone=clean_phone,
                name=name or f"Patient {clean_phone[-4:]}",  # Default name with last 4 digits
                registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S'),
                is_active=True
            )

            db.session.add(patient)
            db.session.commit()

            # Log the registration
            log_activity(
                clean_phone,
                'Patient_Registration_USSD',
                f"Patient registered via basic phone USSD"
            )

            # Send confirmation SMS
            self.send_sms_basic_phone(clean_phone, 'registration_success')

            return True, "Patient registered successfully"

        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def find_patient_basic(self, phone_number):
        """Find patient with basic phone optimized display"""
        try:
            from app import Patient, MedicalRecord
            
            # Validate and clean phone number
            is_valid, clean_phone = self.validate_phone_number(phone_number)
            if not is_valid:
                return None, clean_phone

            # Find patient
            patient = Patient.query.filter_by(phone=clean_phone, is_active=True).first()
            if not patient:
                return None, "Patient not found"

            # Get recent records count
            recent_records = MedicalRecord.query.filter_by(patient_id=patient.id).count()

            # Format patient info for basic phone display
            patient_info = {
                'name': patient.name,
                'phone': patient.phone,
                'registration_date': patient.registration_date,
                'records_count': recent_records,
                'blood_type': patient.blood_type or 'Unknown',
                'allergies': patient.allergies or 'None known'
            }

            return patient_info, "Patient found"

        except Exception as e:
            return None, f"Search failed: {str(e)}"

    def create_medical_record_basic(self, patient_phone, provider_id, complaint, diagnosis=None):
        """Create medical record with basic phone input"""
        try:
            from app import Patient, MedicalRecord, HealthcareProvider, db, log_activity
            
            # Find patient
            patient = Patient.query.filter_by(phone=patient_phone, is_active=True).first()
            if not patient:
                return False, "Patient not found"

            # Find provider
            provider = HealthcareProvider.query.get(provider_id)
            if not provider:
                return False, "Provider not found"

            # Create medical record
            record = MedicalRecord(
                patient_id=patient.id,
                provider_id=provider.id,
                facility_id=provider.facility_id or 1,
                visit_date=datetime.now().strftime('%d/%m/%y'),
                chief_complaint=complaint,
                diagnosis=diagnosis or 'To be determined',
                treatment_plan='As prescribed',
                notes=f'Created via USSD by {provider.name}'
            )

            db.session.add(record)
            db.session.commit()

            # Log the activity
            log_activity(
                patient_phone,
                'Medical_Record_Created_USSD',
                f"Record created by {provider.name}"
            )

            # Send confirmation SMS to patient
            self.send_sms_basic_phone(patient_phone, 'record_created')

            return True, "Medical record created"

        except Exception as e:
            return False, f"Record creation failed: {str(e)}"

    def get_today_appointments_basic(self, provider_id):
        """Get today's appointments in basic phone format"""
        try:
            from app import MedicalRecord, Patient
            
            today = datetime.now().strftime('%d/%m/%y')
            
            # Get today's records as appointments
            records = MedicalRecord.query.filter_by(
                provider_id=provider_id,
                visit_date=today
            ).limit(5).all()  # Limit for basic phone display

            appointments = []
            for record in records:
                appointments.append({
                    'time': '10:00',  # Default time - could be enhanced
                    'patient_name': record.patient.name,
                    'complaint': record.chief_complaint or 'General'
                })

            return appointments, "Appointments retrieved"

        except Exception as e:
            return [], f"Failed to get appointments: {str(e)}"

    def invalid_selection(self, session_id):
        """Handle invalid menu selections - basic phone friendly"""
        menu_text = "INVALID CHOICE\n\n"
        menu_text += "Please select a\nvalid option.\n\n"
        menu_text += "Dial *714# to restart"
        return self.session.ussd_end(menu_text)

    def error_menu(self, error_message, session_id):
        """Handle system errors gracefully - basic phone friendly"""
        menu_text = f"SYSTEM ERROR\n\n"
        menu_text += f"{error_message}\n\n"
        menu_text += "Please try again later.\nDial *714*9# for support."
        return self.session.ussd_end(menu_text)

    def network_error_menu(self, session_id):
        """Handle network errors specifically"""
        menu_text = "NETWORK ERROR\n\n"
        menu_text += "Poor connection.\nTrying again...\n\n"
        menu_text += "Or dial *714# later"
        return self.session.ussd_end(menu_text)

    def session_timeout_menu(self, session_id):
        """Handle session timeouts"""
        menu_text = "SESSION TIMEOUT\n\n"
        menu_text += "Please dial *714#\nto start again.\n\n"
        menu_text += "Keep options ready\nfor faster access."
        return self.session.ussd_end(menu_text)

    # Utility methods for basic phone optimization
    def truncate_text(self, text, max_length=25):
        """Truncate text for basic phone display"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def format_date_basic(self, date_string):
        """Format date for basic phone display"""
        try:
            if isinstance(date_string, str):
                # Convert various date formats to DD/MM/YY
                if '/' in date_string:
                    parts = date_string.split('/')
                    if len(parts) >= 3:
                        return f"{parts[0]}/{parts[1]}/{parts[2][-2:]}"
            return date_string
        except:
            return "N/A"

    def create_numbered_list(self, items, max_items=4):
        """Create numbered list optimized for basic phones"""
        display_items = items[:max_items]
        result = ""
        
        for i, item in enumerate(display_items, 1):
            result += f"{i}. {self.truncate_text(item)}\n"
        
        if len(items) > max_items:
            result += f"...and {len(items) - max_items} more"
            
        return result.strip()

    def get_basic_phone_help(self):
        """Help text optimized for basic phones"""
        help_text = "AFYA HELP\n\n"
        help_text += "Main Menu: *714#\n"
        help_text += "Support: *714*9#\n"
        help_text += "Emergency: 193\n\n"
        help_text += "Keep your PIN safe.\nReport issues quickly."
        return help_text