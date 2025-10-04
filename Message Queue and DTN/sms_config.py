# SMS Gateway Configuration for Healthcare Message Queue System
# Contains database settings, gateway provider configurations,
# healthcare-specific priority rules, and security parameters.

# Database Configuration
DATABASE = {
    'host': 'localhost',
    'database': 'afya_prototype', 
    'user': 'postgres',
    'password': 'your_database_password'
}

# SMS Gateway API Configuration
# Example configurations for popular SMS gateways:

# Twilio Configuration
TWILIO_CONFIG = {
    'api_key': 'your_twilio_account_sid',
    'api_secret': 'your_twilio_auth_token',
    'send_url': (
        'https://api.twilio.com/2010-04-01/Accounts/'
        '{account_sid}/Messages.json'
    ),
    'sender_id': '+1234567890',  # Your Twilio phone number
    'webhook_auth_token': 'your_webhook_auth_token'
}

# AfricasTalking Configuration  
AFRICAS_TALKING_CONFIG = {
    'api_key': 'your_africas_talking_api_key',
    'username': 'your_africas_talking_username',
    'send_url': 'https://api.africastalking.com/version1/messaging',
    'sender_id': 'HealthSys',
    'webhook_secret': 'your_webhook_secret'
}

# Generic SMS Gateway Configuration
GENERIC_SMS_CONFIG = {
    'api_key': 'your_sms_gateway_api_key',
    'send_url': 'https://api.yourgateway.com/v1/sms/send',
    'webhook_url': 'https://your-domain.com/sms/webhook',
    'sender_id': 'HealthSystem',
    'auth_header': 'Bearer',  # or 'X-API-Key', etc.
    'webhook_auth_token': 'your_webhook_verification_token'
}

# Choose your SMS gateway provider
# Change to TWILIO_CONFIG or AFRICAS_TALKING_CONFIG
SMS_GATEWAY = GENERIC_SMS_CONFIG

# Encryption Configuration
ENCRYPTION = {
    'password': 'your_strong_encryption_password_here_2025',
    'salt': 'healthcare_sms_salt_2025'
}

# Webhook Server Configuration
WEBHOOK_SERVER = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'ssl_cert': None,  # Path to SSL certificate for HTTPS
    'ssl_key': None    # Path to SSL private key for HTTPS
}

# Healthcare Facility Phone Number Mapping
# Maps phone numbers to healthcare facility identifiers for routing
FACILITY_MAPPING = {
    '+233201234567': 'ACCRA_GENERAL_001',
    '+233501234568': 'KUMASI_HEALTH_002', 
    '+233301234569': 'CAPE_COAST_003',
    '+233241234570': 'TAMALE_HOSPITAL_004',
    '+233551234571': 'TAKORADI_CLINIC_005'
}

# Healthcare Data Priority Configuration
# Defines priority levels, TTL values, and protocol constraints
# for medical data types
HEALTHCARE_PRIORITIES = {
    'hiv': {
        'priority': 1,
        'ttl_hours': 1,
        'protocols': ['sms', 'ussd'],
        'encryption_required': True
    },
    'prescription': {
        'priority': 2,
        'ttl_hours': 4,
        'protocols': ['sms', 'http', 'ussd'],
        'encryption_required': True
    },
    'lab_results': {
        'priority': 3,
        'ttl_hours': 24,
        'protocols': ['sms', 'http', 'email'],
        'encryption_required': True
    },
    'appointment': {
        'priority': 4,
        'ttl_hours': 72,
        'protocols': ['sms', 'email'],
        'encryption_required': False
    },
    'insurance': {
        'priority': 5,
        'ttl_hours': 168,  # 7 days
        'protocols': ['sms', 'email', 'http'],
        'encryption_required': False
    }
}

# Logging Configuration
LOGGING = {
    'level': 'INFO',
    'file': 'sms_healthcare.log',
    'max_size_mb': 10,
    'backup_count': 5
}

# Rate Limiting Configuration
RATE_LIMITING = {
    'max_sms_per_minute': 60,
    'max_sms_per_hour': 1000,
    'burst_limit': 10
}

# Network Protocol Selection Rules
PROTOCOL_RULES = {
    'offline': 'store_and_forward',
    '2g': 'sms',
    'edge': 'ussd',
    '3g': 'http_compressed',
    '4g': 'https',
    'wifi': 'https'
}

# Message Fragmentation Limits
FRAGMENTATION_LIMITS = {
    'sms': 140,      # Standard SMS limit
    'ussd': 150,     # USSD session limit
    'lorawan': 200,  # LoRaWAN payload limit
    'http': 65536    # HTTP payload limit (64KB)
}

# Retry Configuration
RETRY_CONFIG = {
    'max_retries': 10,
    'initial_delay_seconds': 30,
    'max_delay_minutes': 60,
    'exponential_base': 2
}

# Monitoring and Alerting
MONITORING = {
    'health_check_interval_seconds': 60,
    'alert_on_queue_size': 100,
    'alert_on_failed_deliveries': 10,
    'metrics_retention_days': 30
}

# Security Configuration
SECURITY = {
    'require_https_webhooks': True,
    'validate_webhook_signatures': True,
    'ip_whitelist': [],  # Add your SMS gateway IPs
    'max_message_size_kb': 64
}
