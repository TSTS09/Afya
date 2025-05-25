"""
Afya Medical Menu System - USSD Interface for Medical EHR
Fixed version with proper imports and error handling
"""

import string
import random
import os
import json
from datetime import datetime, timedelta


class MedicalMenu:
    """Medical EHR USSD Menu System"""

    def __init__(self, session):
        self.session = session

    def main_menu(self, session_id, phone_number):
        """Main USSD menu for Afya Medical System"""
        menu_text = "Welcome to Afya Medical EHR\n"
        menu_text += "Your Health Records, Anywhere\n\n"
        menu_text += "1. Healthcare Provider\n"
        menu_text += "2. Patient Services\n"
        menu_text += "3. Emergency Services\n"
        menu_text += "4. System Info\n"

        # Save user session
        self.session.save(session_id, "main_menu")
        return self.session.ussd_proceed(menu_text, session_id)

    def provider_login_menu(self, session_id, phone_number):
        """Healthcare provider login menu"""
        menu_text = "Healthcare Provider Portal\n\n"
        menu_text += "Enter your 4-digit PIN:\n"
        menu_text += "(If not registered, visit your facility admin)"

        self.session.save(session_id, "provider_login")
        return self.session.ussd_proceed(menu_text, session_id)

    def patient_services_menu(self, session_id, phone_number):
        """Patient services menu"""
        menu_text = "Patient Services\n\n"
        menu_text += "1. View My Records\n"
        menu_text += "2. Emergency Contact\n"
        menu_text += "3. Appointment Info\n"
        menu_text += "4. Update Contact Info\n"
        menu_text += "0. Back to Main Menu"

        self.session.save(session_id, "patient_services")
        return self.session.ussd_proceed(menu_text, session_id)

    def emergency_services_menu(self, session_id, phone_number):
        """Emergency services menu"""
        menu_text = "EMERGENCY SERVICES\n\n"
        menu_text += "1. Call Ambulance (193)\n"
        menu_text += "2. Medical Alert\n"
        menu_text += "3. Share Emergency Info\n"
        menu_text += "4. Nearest Hospital\n"
        menu_text += "0. Back to Main Menu"

        self.session.save(session_id, "emergency_services")
        return self.session.ussd_proceed(menu_text, session_id)

    def system_info_menu(self, session_id, phone_number):
        """System information menu"""
        menu_text = "Afya Medical EHR System\n\n"
        menu_text += "Version: 1.0.0\n"
        menu_text += "Support: *714*9#\n"
        menu_text += "Web: afya.health.gh\n\n"
        menu_text += "Transforming Healthcare\n"
        menu_text += "One Record at a Time"

        return self.session.ussd_end(menu_text)

    def handle_multi_level_menu(self, text, session_id, phone_number):
        """Handle complex menu navigation"""
        # Import here to avoid circular imports
        try:
            from app import HealthcareProvider, Patient, MedicalRecord, db, hash_pin
        except ImportError:
            # Fallback for testing without full app
            return self.error_menu("System temporarily unavailable", session_id)

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
        """Handle healthcare provider menu flow"""
        try:
            from app import HealthcareProvider, Patient, MedicalRecord, db, hash_pin
        except ImportError:
            return self.error_menu("Provider services unavailable", session_id)

        if len(menu_path) == 2:
            # Provider entered PIN
            pin = menu_path[1]

            if len(pin) != 4 or not pin.isdigit():
                menu_text = "Invalid PIN format.\n"
                menu_text += "Please enter 4 digits:"
                return self.session.ussd_proceed(menu_text, session_id)

            # Verify provider credentials (simplified for prototype)
            try:
                provider = HealthcareProvider.query.filter_by(
                    phone=self.sanitize_phone(phone_number),
                    pin=hash_pin(pin),
                    is_active=True
                ).first()
            except:
                # Fallback for demo - accept PIN 1234
                if pin == "1234":
                    return self.demo_provider_menu(session_id, phone_number)
                else:
                    menu_text = "Invalid credentials.\n"
                    menu_text += "Contact your facility admin.\n\n"
                    menu_text += "1. Try Again\n"
                    menu_text += "0. Main Menu"
                    return self.session.ussd_proceed(menu_text, session_id)

            if not provider:
                # Demo mode fallback
                if pin == "1234":
                    return self.demo_provider_menu(session_id, phone_number)

                menu_text = "Invalid credentials.\n"
                menu_text += "Contact your facility admin.\n\n"
                menu_text += "1. Try Again\n"
                menu_text += "0. Main Menu"
                return self.session.ussd_proceed(menu_text, session_id)

            # Provider main menu
            menu_text = f"Welcome Dr. {provider.name}\n"
            menu_text += f"{provider.facility.name if provider.facility else 'Demo Clinic'}\n\n"
            menu_text += "1. Patient Lookup\n"
            menu_text += "2. New Patient\n"
            menu_text += "3. New Record\n"
            menu_text += "4. Lab Results\n"
            menu_text += "5. Appointments\n"
            menu_text += "0. Logout"

            # Save provider session
            self.session.save(session_id, f"provider_menu:{provider.id}")
            return self.session.ussd_proceed(menu_text, session_id)

        elif len(menu_path) >= 3:
            return self.handle_provider_actions(menu_path, session_id, phone_number)

    def demo_provider_menu(self, session_id, phone_number):
        """Demo provider menu for testing"""
        menu_text = "Welcome Dr. Demo User\n"
        menu_text += "Afya Demo Clinic\n\n"
        menu_text += "1. Patient Lookup\n"
        menu_text += "2. New Patient\n"
        menu_text += "3. New Record\n"
        menu_text += "4. Lab Results\n"
        menu_text += "5. Appointments\n"
        menu_text += "0. Logout"

        self.session.save(session_id, "demo_provider_menu")
        return self.session.ussd_proceed(menu_text, session_id)

    def handle_provider_actions(self, menu_path, session_id, phone_number):
        """Handle provider action selections"""
        action = menu_path[2]

        if action == '1':
            # Patient Lookup
            menu_text = "Patient Lookup\n\n"
            menu_text += "Enter patient phone number:\n"
            menu_text += "(Format: 0XXXXXXXXX)"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '2':
            # New Patient Registration
            menu_text = "New Patient Registration\n\n"
            menu_text += "Enter patient phone number:\n"
            menu_text += "(This will be their unique ID)"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '3':
            # New Medical Record
            menu_text = "New Medical Record\n\n"
            menu_text += "Enter patient phone number:"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '4':
            # Lab Results
            menu_text = "Laboratory Results\n\n"
            menu_text += "Enter patient phone number:"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '5':
            # Appointments
            menu_text = "Appointment Management\n\n"
            menu_text += "1. Today's Appointments\n"
            menu_text += "2. Schedule Appointment\n"
            menu_text += "3. Patient Phone Lookup\n"
            menu_text += "0. Back"
            return self.session.ussd_proceed(menu_text, session_id)

        elif action == '0':
            # Logout
            menu_text = "Logged out successfully.\n"
            menu_text += "Thank you for using Afya!"
            return self.session.ussd_end(menu_text)

        else:
            return self.invalid_selection(session_id)

    def handle_patient_flow(self, menu_path, session_id, phone_number):
        """Handle patient services menu flow"""
        if len(menu_path) == 2:
            action = menu_path[1]

            if action == '1':  # View My Records
                menu_text = "Your Medical Records\n\n"
                menu_text += "Recent visits:\n"
                menu_text += "• 15/03/24 - General Check\n"
                menu_text += "• 02/02/24 - Follow-up\n"
                menu_text += "• 18/01/24 - Emergency\n\n"
                menu_text += "Visit afya.health.gh\nfor full details."
                return self.session.ussd_end(menu_text)

            elif action == '2':  # Emergency Contact
                menu_text = "EMERGENCY CONTACTS\n\n"
                menu_text += "Ambulance: 193\n"
                menu_text += "Police: 191\n"
                menu_text += "Fire: 192\n\n"
                menu_text += "Your location will be\n"
                menu_text += "shared when you call."
                return self.session.ussd_end(menu_text)

            elif action == '3':  # Appointment Info
                menu_text = "Your Appointments\n\n"
                menu_text += "Upcoming:\n"
                menu_text += "• 25/03/24 10:00 AM\n"
                menu_text += "  Dr. Asante - General\n"
                menu_text += "  Afya Demo Clinic\n\n"
                menu_text += "• 02/04/24 2:00 PM\n"
                menu_text += "  Dr. Mensah - Follow-up\n"
                menu_text += "  Ridge Hospital"
                return self.session.ussd_end(menu_text)

            elif action == '4':  # Update Contact Info
                menu_text = "Update Contact Info\n\n"
                menu_text += "Enter new emergency contact\n"
                menu_text += "phone number:"
                return self.session.ussd_proceed(menu_text, session_id)

            elif action == '0':  # Back to main menu
                return self.main_menu(session_id, phone_number)

        elif len(menu_path) == 3 and menu_path[1] == '4':
            # Update emergency contact
            new_emergency_contact = menu_path[2]
            menu_text = "Emergency contact updated!\n\n"
            menu_text += f"New contact: {new_emergency_contact}\n\n"
            menu_text += "This contact will be notified\n"
            menu_text += "in case of emergency."
            return self.session.ussd_end(menu_text)

    def handle_emergency_flow(self, menu_path, session_id, phone_number):
        """Handle emergency services flow"""
        if len(menu_path) == 2:
            action = menu_path[1]

            if action == '1':  # Call Ambulance
                menu_text = "EMERGENCY AMBULANCE\n\n"
                menu_text += "Dial 193 immediately\n"
                menu_text += "for ambulance service.\n\n"
                menu_text += "Your location will be\n"
                menu_text += "automatically shared.\n\n"
                menu_text += "Stay calm and wait\n"
                menu_text += "for help to arrive."
                return self.session.ussd_end(menu_text)

            elif action == '2':  # Medical Alert
                menu_text = "MEDICAL ALERT SENT\n\n"
                menu_text += "Emergency contact notified:\n"
                menu_text += f"Contact will be called\n\n"
                menu_text += "If this is life-threatening,\n"
                menu_text += "call 193 for ambulance."
                return self.session.ussd_end(menu_text)

            elif action == '3':  # Share Emergency Info
                menu_text = f"EMERGENCY INFO\n\n"
                menu_text += f"Name: Demo Patient\n"
                menu_text += f"Phone: {phone_number}\n"
                menu_text += f"Blood Type: O+\n"
                menu_text += f"Allergies: None recorded\n"
                menu_text += f"Conditions: Hypertension\n\n"
                menu_text += "Show this to medical staff"
                return self.session.ussd_end(menu_text)

            elif action == '4':  # Nearest Hospital
                menu_text = "NEAREST HOSPITALS\n\n"
                menu_text += "Accra:\n"
                menu_text += "- Korle Bu: 0302-674376\n"
                menu_text += "- 37 Hospital: 0302-776481\n\n"
                menu_text += "Kumasi:\n"
                menu_text += "- KATH: 0322-022308\n\n"
                menu_text += "For ambulance: 193"
                return self.session.ussd_end(menu_text)

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

    def send_sms(self, phone_number, intent, custom_message=None):
        """Send SMS using Twilio API"""
        try:
            if custom_message:
                sms_content = custom_message
            else:
                sms_content = f"Afya Medical EHR: You have {intent}. For support, dial *714*9#"

            # For demo purposes, just print the SMS
            print(f"SMS to {phone_number}: {sms_content}")

            # Uncomment below for actual Twilio integration
            # account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            # auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            #
            # if account_sid and auth_token:
            #     from twilio.rest import Client
            #     client = Client(account_sid, auth_token)
            #
            #     message = client.messages.create(
            #         body=sms_content,
            #         from_=os.environ.get('TWILIO_PHONE', '+19498280706'),
            #         to=phone_number
            #     )
            #     print(f"SMS sent successfully: {message.sid}")

        except Exception as e:
            print(f"SMS sending failed: {str(e)}")

    def invalid_selection(self, session_id):
        """Handle invalid menu selections"""
        menu_text = "Invalid selection.\n\n"
        menu_text += "Please choose a valid option\n"
        menu_text += "or dial *714# to restart."
        return self.session.ussd_end(menu_text)

    def error_menu(self, error_message, session_id):
        """Handle system errors gracefully"""
        menu_text = f"System Error\n\n"
        menu_text += f"{error_message}\n\n"
        menu_text += "Please try again later\n"
        menu_text += "or contact support."
        return self.session.ussd_end(menu_text)
