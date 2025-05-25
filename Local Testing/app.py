"""
Afya Medical EHR System - Local Deployment Version
Updated with proper environment variable handling
"""

import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv  
from session_manager import SessionManager
from medical_menu import MedicalMenu
from flask import Flask, make_response, request, flash, url_for, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration for local deployment


def configure_app():
    """Configure app for local deployment with environment variables"""

    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = os.environ.get('DEBUG', 'True').lower() == 'true'

    # Database configuration
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Handle PostgreSQL URL formats
        if database_url.startswith('postgres://'):
            database_url = database_url.replace(
                'postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"🐘 Using PostgreSQL database")
    else:
        # Fallback to SQLite for development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///afya_medical.sqlite3'
        print("🗃️ Using SQLite database (fallback)")

    # Environment detection
    env = os.environ.get('FLASK_ENV', 'development')
    port = int(os.environ.get('PORT', 5000))

    print(f"🚀 Running in {env} mode on port {port}")

    # Print loaded environment variables (safely)
    print("📋 Environment variables loaded:")
    print(
        f"   - SECRET_KEY: {'✓ Set' if app.config['SECRET_KEY'] != 'dev-secret-key-change-in-production' else '⚠️ Using default'}")
    print(
        f"   - DATABASE_URL: {'✓ Set' if database_url else '⚠️ Using SQLite'}")
    print(
        f"   - REDIS_URL: {'✓ Set' if os.environ.get('REDIS_URL') else '⚠️ Not set'}")
    print(
        f"   - AFRICASTALKING_API_KEY: {'✓ Set' if os.environ.get('AFRICASTALKING_API_KEY') else '⚠️ Not set'}")
    print(
        f"   - TWILIO_ACCOUNT_SID: {'✓ Set' if os.environ.get('TWILIO_ACCOUNT_SID') else '⚠️ Not set'}")


# Configure the app
configure_app()

db = SQLAlchemy(app)
session = SessionManager()
medical_menu = MedicalMenu(session)

# Database Models (Same as before)


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
    """Initialize database with comprehensive sample data"""
    try:
        db.create_all()
        print("✅ Database tables created successfully!")

        # Create sample data if none exists
        if HealthcareFacility.query.count() == 0:
            print("📝 Creating sample data...")

            # Sample facilities
            facilities = [
                HealthcareFacility(
                    name="Afya Demo Clinic",
                    facility_type="Health Center",
                    location="Accra Central",
                    phone="0501234567",
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                ),
                HealthcareFacility(
                    name="Ridge Hospital",
                    facility_type="Hospital",
                    location="Ridge, Accra",
                    phone="0302776481",
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                ),
                HealthcareFacility(
                    name="Kumasi Health Center",
                    facility_type="Health Center",
                    location="Kumasi Central",
                    phone="0322022308",
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                )
            ]

            for facility in facilities:
                db.session.add(facility)

            db.session.commit()

            # Sample providers
            providers = [
                HealthcareProvider(
                    name="Dr. Kwame Asante",
                    phone="0501234568",
                    specialization="General Medicine",
                    facility_id=1,
                    pin=hash_pin("1234"),
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                ),
                HealthcareProvider(
                    name="Dr. Ama Mensah",
                    phone="0201234569",
                    specialization="Pediatrics",
                    facility_id=2,
                    pin=hash_pin("5678"),
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                ),
                HealthcareProvider(
                    name="Dr. Kofi Boateng",
                    phone="0241234570",
                    specialization="Internal Medicine",
                    facility_id=3,
                    pin=hash_pin("9012"),
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                )
            ]

            for provider in providers:
                db.session.add(provider)

            db.session.commit()

            # Sample patients
            patients = [
                Patient(
                    phone="0200123456",
                    name="John Doe",
                    date_of_birth="01/01/1990",
                    gender="Male",
                    blood_type="O+",
                    allergies="None known",
                    emergency_contact="0200987654",
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                ),
                Patient(
                    phone="0240234567",
                    name="Jane Smith",
                    date_of_birth="15/05/1985",
                    gender="Female",
                    blood_type="A+",
                    allergies="Penicillin",
                    emergency_contact="0240876543",
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                ),
                Patient(
                    phone="0260345678",
                    name="Kwame Osei",
                    date_of_birth="20/12/1992",
                    gender="Male",
                    blood_type="B+",
                    allergies="None known",
                    emergency_contact="0260765432",
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                ),
                Patient(
                    phone="0270456789",
                    name="Akosua Addo",
                    date_of_birth="10/03/1988",
                    gender="Female",
                    blood_type="AB+",
                    allergies="Shellfish",
                    emergency_contact="0270654321",
                    registration_date=datetime.now().strftime('%d/%m/%y %H:%M:%S')
                )
            ]

            for patient in patients:
                db.session.add(patient)

            db.session.commit()

            # Sample medical records
            medical_records = [
                MedicalRecord(
                    patient_id=1,
                    provider_id=1,
                    facility_id=1,
                    visit_date=datetime.now().strftime('%d/%m/%y'),
                    chief_complaint="General checkup",
                    diagnosis="Healthy - routine examination",
                    treatment_plan="Continue healthy lifestyle",
                    notes="Patient appears in good health"
                ),
                MedicalRecord(
                    patient_id=2,
                    provider_id=2,
                    facility_id=2,
                    visit_date=datetime.now().strftime('%d/%m/%y'),
                    chief_complaint="Headache and fever",
                    diagnosis="Viral infection",
                    treatment_plan="Rest, fluids, paracetamol",
                    notes="Symptoms should resolve in 3-5 days"
                ),
                MedicalRecord(
                    patient_id=3,
                    provider_id=3,
                    facility_id=3,
                    visit_date=datetime.now().strftime('%d/%m/%y'),
                    chief_complaint="Follow-up for hypertension",
                    diagnosis="Hypertension - controlled",
                    treatment_plan="Continue current medication",
                    notes="Blood pressure well controlled"
                )
            ]

            for record in medical_records:
                db.session.add(record)

            db.session.commit()

            print("✅ Sample data created successfully!")
            print("📋 Created:")
            print(f"   - {len(facilities)} healthcare facilities")
            print(f"   - {len(providers)} healthcare providers")
            print(f"   - {len(patients)} patients")
            print(f"   - {len(medical_records)} medical records")
            print("🔑 Demo provider PINs: 1234, 5678, 9012")

    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

    return True

# Routes


@app.route('/', methods=['GET'])
def index():
    """Main dashboard with error handling"""
    try:
        return render_template('dashboard.html',
                               total_patients=Patient.query.count(),
                               total_providers=HealthcareProvider.query.count(),
                               total_facilities=HealthcareFacility.query.count(),
                               recent_records=MedicalRecord.query.order_by(MedicalRecord.id.desc()).limit(5).all())
    except Exception as e:
        print(f"Dashboard error: {e}")
        return f"""
        <div style="font-family: Arial; padding: 20px; background: #f8f9fa; min-height: 100vh;">
            <h2>🏥 Afya Medical EHR</h2>
            <div style="background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #28a745;">
                <h3>System Initializing...</h3>
                <p>The database is being set up. Please refresh the page in a moment.</p>
                <p><strong>Error details:</strong> {str(e)}</p>
                <hr>
                <p><strong>Quick Actions:</strong></p>
                <ul>
                    <li><a href="/test-ussd">Test USSD Interface</a></li>
                    <li><a href="/health">Check System Health</a></li>
                    <li><a href="/register-facility">Register Facility</a></li>
                </ul>
            </div>
        </div>
        """


@app.route('/ussd/callback', methods=['POST', 'GET'])
def ussd_callback():
    """Main USSD callback function for Africa's Talking"""
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
        print(f"❌ USSD callback error: {e}")
        return make_response(
            f"END System temporarily unavailable.\nPlease try again later.\nError: {str(e)[:50]}",
            200,
            {'Content-Type': 'text/plain'}
        )

# Web Dashboard Routes


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
            log_activity(
                request.form['phone'], 'Facility_Registration', f"Facility: {request.form['name']}")
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
            log_activity(
                request.form['phone'], 'Provider_Registration', f"Provider: {request.form['name']}")
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
        logs = SystemLog.query.order_by(SystemLog.id.desc()).limit(100).all()
    except:
        logs = []
    return render_template('system_logs.html', logs=logs)


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')

        # Test Redis connection if configured
        redis_status = "not_configured"
        if os.environ.get('REDIS_URL'):
            try:
                from redis import Redis
                r = Redis.from_url(os.environ.get('REDIS_URL'))
                r.ping()
                redis_status = "connected"
            except:
                redis_status = "error"

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected',
            'redis': redis_status,
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'total_patients': Patient.query.count(),
            'total_providers': HealthcareProvider.query.count(),
            'total_facilities': HealthcareFacility.query.count()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/test-ussd', methods=['GET', 'POST'])
def test_ussd():
    """Test USSD functionality locally"""
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>🧪 USSD Test Interface - Afya Medical EHR</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background: #f8f9fa; }
                .test-container { max-width: 600px; margin: 50px auto; }
                .ussd-code { background: #212529; color: #ffc107; padding: 10px; border-radius: 5px; font-family: monospace; }
            </style>
        </head>
        <body>
            <div class="container test-container">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">
                        <h2 class="mb-0">🧪 USSD Test Interface</h2>
                        <small>Test the Afya Medical EHR USSD system locally</small>
                    </div>
                    <div class="card-body">
                        <form method="post">
                            <div class="mb-3">
                                <label class="form-label"><strong>Session ID:</strong></label>
                                <input name="sessionId" value="test_session_''' + str(datetime.now().timestamp()) + '''" class="form-control">
                            </div>
                            <div class="mb-3">
                                <label class="form-label"><strong>Service Code:</strong></label>
                                <input name="serviceCode" value="*384*15879#" class="form-control">
                            </div>
                            <div class="mb-3">
                                <label class="form-label"><strong>Phone Number:</strong></label>
                                <input name="phoneNumber" value="+233200000000" class="form-control">
                            </div>
                            <div class="mb-3">
                                <label class="form-label"><strong>Text (Menu Input):</strong></label>
                                <input name="text" placeholder="e.g., 1*1234" class="form-control">
                                <div class="form-text">Leave empty for main menu</div>
                            </div>
                            <button type="submit" class="btn btn-success btn-lg w-100">
                                📱 Send USSD Request
                            </button>
                        </form>
                    </div>
                    <div class="card-footer bg-light">
                        <h5>🔧 Test Sequences:</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <ul class="list-unstyled small">
                                    <li><strong>Main Menu:</strong> <code>(empty)</code></li>
                                    <li><strong>Provider Login:</strong> <code>1</code></li>
                                    <li><strong>Provider + PIN:</strong> <code>1*1234</code></li>
                                    <li><strong>Patient Services:</strong> <code>2</code></li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <ul class="list-unstyled small">
                                    <li><strong>Emergency:</strong> <code>3</code></li>
                                    <li><strong>System Info:</strong> <code>4</code></li>
                                    <li><strong>Patient Records:</strong> <code>2*1</code></li>
                                    <li><strong>Provider Menu:</strong> <code>1*1234*1</code></li>
                                </ul>
                            </div>
                        </div>
                        <div class="alert alert-info mt-3">
                            <strong>Demo PINs:</strong> 1234, 5678, 9012
                        </div>
                    </div>
                </div>
                <div class="text-center mt-3">
                    <a href="/" class="btn btn-outline-primary">← Back to Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        '''
    else:
        return ussd_callback()


# Initialize database on startup
with app.app_context():
    db_initialized = init_db()
    if not db_initialized:
        print("❌ Failed to initialize database!")
    else:
        print("✅ Database initialized successfully!")

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))

    print(f"\n🏥 Afya Medical EHR System Starting...")
    print(f"🌐 Web Interface: http://localhost:{port}")
    print(f"🧪 USSD Test: http://localhost:{port}/test-ussd")
    print(f"❤️ Health Check: http://localhost:{port}/health")
    print(f"📱 USSD Code: *384*15879#")
    print("=" * 60)

    # Run the application
    app.run(
        host="0.0.0.0",
        port=port,
        debug=app.config.get('DEBUG', False)
    )
