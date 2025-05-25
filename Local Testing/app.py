"""
Afya Medical EHR System - Deployment Ready Version
Works with Render, Railway, Fly.io, and other free platforms
"""

import os
import hashlib
from datetime import datetime
from session_manager import SessionManager
from medical_menu import MedicalMenu
from flask import Flask, make_response, request, flash, url_for, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuration for different deployment platforms


def configure_app():
    """Configure app based on environment"""

    # Default configuration
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Database configuration - works with multiple platforms
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Fix for newer PostgreSQL URLs (Render, Railway use postgresql://)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace(
                'postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to SQLite for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///afya_medical.sqlite3'

    # Environment-specific settings
    if os.environ.get('RENDER'):
        # Render-specific configuration
        app.config['DEBUG'] = False
        print("🚀 Running on Render")
    elif os.environ.get('RAILWAY_ENVIRONMENT'):
        # Railway-specific configuration
        app.config['DEBUG'] = False
        print("🚀 Running on Railway")
    elif os.environ.get('FLY_APP_NAME'):
        # Fly.io-specific configuration
        app.config['DEBUG'] = False
        print("🚀 Running on Fly.io")
    elif os.environ.get('PYTHONANYWHERE_DOMAIN'):
        # PythonAnywhere-specific configuration
        app.config['DEBUG'] = False
        print("🚀 Running on PythonAnywhere")
    else:
        # Local development
        app.config['DEBUG'] = True
        print("🔧 Running in development mode")


# Configure the app
configure_app()

db = SQLAlchemy(app)
session = SessionManager()
medical_menu = MedicalMenu(session)

# Database Models (Same as before but with better error handling)


class HealthcareFacility(db.Model):
    """Healthcare Facility Model"""
    id = db.Column('facility_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    facility_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    registration_date = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)


class HealthcareProvider(db.Model):
    """Healthcare Provider Model"""
    id = db.Column('provider_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    specialization = db.Column(db.String(100))
    facility_id = db.Column(db.Integer, db.ForeignKey(
        'healthcare_facility.facility_id'))
    pin = db.Column(db.String(64))  # Hashed PIN
    registration_date = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

    facility = db.relationship('HealthcareFacility', backref='providers')


class Patient(db.Model):
    """Patient Model"""
    id = db.Column('patient_id', db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    emergency_contact = db.Column(db.String(15))
    registration_date = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)


class MedicalRecord(db.Model):
    """Medical Record Model"""
    id = db.Column('record_id', db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey(
        'patient.patient_id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey(
        'healthcare_provider.provider_id'), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey(
        'healthcare_facility.facility_id'), nullable=False)
    visit_date = db.Column(db.String(20), nullable=False)
    chief_complaint = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    notes = db.Column(db.Text)

    patient = db.relationship('Patient', backref='medical_records')
    provider = db.relationship('HealthcareProvider', backref='medical_records')
    facility = db.relationship('HealthcareFacility', backref='medical_records')


class SystemLog(db.Model):
    """System Activity Logs"""
    id = db.Column('log_id', db.Integer, primary_key=True)
    timestamp = db.Column(db.String(30), nullable=False)
    user_phone = db.Column(db.String(15))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)

# Helper Functions


def sanitize_phone(phone_number):
    """Sanitize phone numbers to standard format"""
    if not phone_number:
        return None

    phone = phone_number.strip().replace(' ', '').replace('-', '')

    if phone.startswith('+233'):
        phone = '0' + phone[4:]
    elif phone.startswith('233'):
        phone = '0' + phone[3:]
    elif not phone.startswith('0') and len(phone) == 9:
        phone = '0' + phone

    return phone


def hash_pin(pin):
    """Hash PIN for secure storage"""
    return hashlib.sha256(pin.encode()).hexdigest()


def log_activity(user_phone, action, details=None):
    """Log system activities with error handling"""
    try:
        log = SystemLog(
            timestamp=datetime.now().strftime('%d/%m/%y %H:%M:%S.%f'),
            user_phone=user_phone,
            action=action,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Logging error: {e}")


def init_db():
    """Initialize database with error handling"""
    try:
        db.create_all()

        # Create sample data if none exists
        if HealthcareFacility.query.count() == 0:
            # Sample facility
            facility = HealthcareFacility(
                name="Afya Demo Clinic",
                facility_type="Health Center",
                location="Accra Central",
                phone="0501234567",
                registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
            )
            db.session.add(facility)

            # Sample provider (PIN: 1234)
            provider = HealthcareProvider(
                name="Dr. Kwame Asante",
                phone="0501234568",
                specialization="General Medicine",
                facility_id=1,
                pin=hash_pin("1234"),
                registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
            )
            db.session.add(provider)

            # Sample patient
            patient = Patient(
                phone="0200123456",
                name="John Doe",
                date_of_birth="01/01/1990",
                gender="Male",
                blood_type="O+",
                registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
            )
            db.session.add(patient)

            db.session.commit()
            print("✅ Sample data created successfully!")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Routes


@app.route('/', methods=['GET'])
def index():
    """Main landing page with error handling"""
    try:
        return render_template('dashboard.html',
                               total_patients=Patient.query.count(),
                               total_providers=HealthcareProvider.query.count(),
                               total_facilities=HealthcareFacility.query.count(),
                               recent_records=MedicalRecord.query.order_by(MedicalRecord.id.desc()).limit(5).all())
    except Exception as e:
        print(f"Dashboard error: {e}")
        return f"Dashboard loading... Database might be initializing. Refresh in a moment.<br>Error: {e}"


@app.route('/ussd/callback', methods=['POST', 'GET'])
def ussd_callback():
    """
    Main USSD callback function for Africa's Talking
    Works with any USSD provider
    """
    try:
        # Get parameters from USSD provider
        session_id = request.values.get("sessionId", None)
        service_code = request.values.get("serviceCode", None)
        phone_number = sanitize_phone(request.values.get("phoneNumber", None))
        text = request.values.get("text", '')

        print(
            f"📱 USSD Request: SessionID={session_id}, Service={service_code}, Phone={phone_number}, Text='{text}'")

        # Log the USSD interaction
        log_activity(
            phone_number, f"USSD_Access: {text}", f"Service: {service_code}")

        # Handle empty text (initial USSD dial)
        if text == '':
            return medical_menu.main_menu(session_id, phone_number)

        # Route based on user selection
        if text == '1':
            return medical_menu.provider_login_menu(session_id, phone_number)
        elif text == '2':
            return medical_menu.patient_services_menu(session_id, phone_number)
        elif text == '3':
            return medical_menu.emergency_services_menu(session_id, phone_number)
        elif text == '4':
            return medical_menu.system_info_menu(session_id, phone_number)
        elif len(text.split('*')) > 1:
            return medical_menu.handle_multi_level_menu(text, session_id, phone_number)
        else:
            return medical_menu.invalid_selection(session_id)

    except Exception as e:
        print(f"USSD callback error: {e}")
        # Return error message in USSD format
        return make_response(f"END System temporarily unavailable.\nPlease try again later.\nError: {str(e)[:50]}", 200, {'Content-Type': 'text/plain'})

# Web Dashboard Routes with better error handling


@app.route('/register-facility', methods=['GET', 'POST'])
def register_facility():
    """Register new healthcare facility"""
    if request.method == 'POST':
        try:
            facility = HealthcareFacility(
                name=request.form['name'],
                facility_type=request.form.get('facility_type', 'Clinic'),
                location=request.form['location'],
                phone=sanitize_phone(request.form['phone']),
                registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
            )
            db.session.add(facility)
            db.session.commit()
            flash('Healthcare facility registered successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error registering facility: {str(e)}')

    return render_template('register_facility.html')


@app.route('/register-provider', methods=['GET', 'POST'])
def register_provider():
    """Register new healthcare provider"""
    if request.method == 'POST':
        try:
            if len(request.form['pin']) != 4:
                flash('PIN must be exactly 4 digits.')
                return redirect(url_for('register_provider'))

            provider = HealthcareProvider(
                name=request.form['name'],
                phone=sanitize_phone(request.form['phone']),
                specialization=request.form.get('specialization', 'General'),
                facility_id=request.form.get('facility_id', 1),
                pin=hash_pin(request.form['pin']),
                registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
            )
            db.session.add(provider)
            db.session.commit()
            flash('Healthcare provider registered successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error registering provider: {str(e)}')

    try:
        facilities = HealthcareFacility.query.filter_by(is_active=True).all()
    except:
        facilities = []

    return render_template('register_provider.html', facilities=facilities)


@app.route('/patients')
def list_patients():
    """List all patients"""
    try:
        patients = Patient.query.filter_by(is_active=True).all()
    except:
        patients = []
    return render_template('patients.html', patients=patients)


@app.route('/logs')
def system_logs():
    """View system activity logs"""
    try:
        logs = SystemLog.query.order_by(SystemLog.id.desc()).limit(50).all()
    except:
        logs = []
    return render_template('system_logs.html', logs=logs)


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected',
            'environment': os.environ.get('RENDER', os.environ.get('RAILWAY_ENVIRONMENT', 'development'))
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Test endpoint for development


@app.route('/test-ussd', methods=['GET', 'POST'])
def test_ussd():
    """Test USSD functionality locally"""
    if request.method == 'GET':
        return '''
        <h2>🧪 USSD Test Interface</h2>
        <form method="post" style="font-family: Arial; padding: 20px; background: #f5f5f5; border-radius: 10px; max-width: 400px;">
            <p><strong>Session ID:</strong><br><input name="sessionId" value="test_session_123" style="width: 100%; padding: 5px;"></p>
            <p><strong>Service Code:</strong><br><input name="serviceCode" value="*714#" style="width: 100%; padding: 5px;"></p>
            <p><strong>Phone Number:</strong><br><input name="phoneNumber" value="+233200000000" style="width: 100%; padding: 5px;"></p>
            <p><strong>Text (Menu Input):</strong><br><input name="text" value="" placeholder="e.g., 1*1234" style="width: 100%; padding: 5px;"></p>
            <button type="submit" style="background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">📱 Send USSD Request</button>
        </form>
        <div style="margin-top: 20px; font-size: 14px; color: #666;">
            <h3>Test Sequences:</h3>
            <ul>
                <li><strong>Main Menu:</strong> Leave text empty</li>
                <li><strong>Provider Login:</strong> Text = "1"</li>
                <li><strong>Provider with PIN:</strong> Text = "1*1234"</li>
                <li><strong>Patient Services:</strong> Text = "2"</li>
                <li><strong>Emergency Services:</strong> Text = "3"</li>
            </ul>
        </div>
        '''
    else:
        return ussd_callback()


# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))

    # Run the application
    app.run(
        host="0.0.0.0",
        port=port,
        debug=app.config.get('DEBUG', False)
    )
