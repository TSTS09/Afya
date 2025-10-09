"""
Healthcare Transmission System Configuration
===========================================

Configuration settings for the healthcare data transmission system
supporting OpenHIM integration and multiple transmission protocols.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = "localhost"
    database: str = "pg_mq_poc"
    user: str = "postgres"
    password: str = "Christelle09123"
    port: int = 5432
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'host': self.host,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'port': self.port
        }


@dataclass
class OpenHIMConfig:
    """OpenHIM server configuration"""
    base_url: str = "https://openhim.example.com"
    username: str = "root@openhim.org"
    password: str = "your-openhim-password"
    auth_token: str = ""
    client_id: str = "afya_client"
    
    # OpenHIM channel configurations
    channels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = {
                'emergency': 'emergency-channel',
                'lab_results': 'lab-results-channel',
                'prescriptions': 'prescription-channel',
                'administrative': 'admin-channel'
            }


@dataclass
class SMSConfig:
    """SMS gateway configuration"""
    provider: str = "generic"  # Options: twilio, africas_talking, generic
    api_key: str = "your-sms-api-key"
    api_secret: str = "your-sms-api-secret"
    sender_id: str = "AFYA"
    base_url: str = "https://api.smsgateway.com/v1"
    webhook_secret: str = "your-webhook-secret"
    
    # Provider-specific settings
    twilio_account_sid: str = ""
    africas_talking_username: str = ""
    
    # SMS limits and settings
    max_message_length: int = 160
    enable_delivery_reports: bool = True
    retry_failed_messages: bool = True


@dataclass
class USSDConfig:
    """USSD configuration"""
    service_code: str = "*714#"
    session_timeout: int = 300  # seconds
    max_menu_levels: int = 5
    enable_session_logging: bool = True


@dataclass
class NetworkConfig:
    """Network monitoring and thresholds configuration"""
    # Bandwidth thresholds (kbps)
    excellent_bandwidth_threshold: int = 1000
    good_bandwidth_threshold: int = 256
    poor_bandwidth_threshold: int = 64
    
    # Latency thresholds (ms)
    excellent_latency_threshold: int = 100
    good_latency_threshold: int = 500
    poor_latency_threshold: int = 2000
    
    # Packet loss thresholds (%)
    excellent_packet_loss_threshold: float = 1.0
    good_packet_loss_threshold: float = 5.0
    poor_packet_loss_threshold: float = 15.0
    
    # Monitoring intervals
    network_check_interval: int = 60  # seconds
    status_update_interval: int = 300  # seconds


@dataclass
class SecurityConfig:
    """Security and encryption configuration"""
    encryption_key: str = "your-encryption-key-here"
    enable_message_encryption: bool = True
    enable_audit_logging: bool = True
    
    # Data type specific encryption requirements
    force_encryption_for_types: list = None
    
    def __post_init__(self):
        if self.force_encryption_for_types is None:
            self.force_encryption_for_types = [
                'lab_hiv_result',
                'emergency',
                'prescription'
            ]


@dataclass
class RetryConfig:
    """Message retry configuration"""
    max_retries: int = 5
    initial_retry_delay: int = 60  # seconds
    max_retry_delay: int = 3600  # 1 hour
    exponential_backoff_multiplier: float = 2.0
    
    # Protocol-specific retry settings
    sms_max_retries: int = 3
    http_max_retries: int = 10
    ussd_max_retries: int = 2


@dataclass
class HealthcareDataConfig:
    """Healthcare data type configurations"""
    priority_mappings: Dict[str, int] = None
    ttl_mappings: Dict[str, int] = None  # Time to live in seconds
    size_limits: Dict[str, int] = None  # Size limits in bytes
    
    def __post_init__(self):
        if self.priority_mappings is None:
            self.priority_mappings = {
                'emergency': 1,
                'lab_hiv_result': 1,
                'prescription': 2,
                'vitals': 3,
                'lab_routine': 3,
                'patient_registration': 4,
                'appointment': 4,
                'administrative': 5
            }
        
        if self.ttl_mappings is None:
            self.ttl_mappings = {
                'emergency': 3600,      # 1 hour
                'lab_hiv_result': 3600, # 1 hour
                'prescription': 14400,   # 4 hours
                'vitals': 86400,        # 24 hours
                'lab_routine': 86400,   # 24 hours
                'patient_registration': 604800,  # 7 days
                'appointment': 86400,   # 24 hours
                'administrative': 604800  # 7 days
            }
        
        if self.size_limits is None:
            self.size_limits = {
                'emergency': 1024,          # 1KB
                'lab_hiv_result': 1024,     # 1KB
                'prescription': 2048,       # 2KB
                'vitals': 512,              # 512B
                'lab_routine': 10240,       # 10KB
                'patient_registration': 2048,  # 2KB
                'appointment': 1024,        # 1KB
                'administrative': 10240     # 10KB
            }


class HealthcareTransmissionConfig:
    """Main configuration class combining all settings"""
    
    def __init__(self, config_file: str = None):
        # Load from environment variables or defaults
        self.database = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'pg_mq_poc'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'Christelle09123'),
            port=int(os.getenv('DB_PORT', '5432'))
        )
        
        self.openhim = OpenHIMConfig(
            base_url=os.getenv('OPENHIM_URL', 'https://openhim.example.com'),
            username=os.getenv('OPENHIM_USER', 'root@openhim.org'),
            password=os.getenv('OPENHIM_PASSWORD', 'your-openhim-password'),
            auth_token=os.getenv('OPENHIM_TOKEN', ''),
            client_id=os.getenv('OPENHIM_CLIENT_ID', 'afya_client')
        )
        
        self.sms = SMSConfig(
            provider=os.getenv('SMS_PROVIDER', 'generic'),
            api_key=os.getenv('SMS_API_KEY', 'your-sms-api-key'),
            api_secret=os.getenv('SMS_API_SECRET', 'your-sms-api-secret'),
            sender_id=os.getenv('SMS_SENDER_ID', 'AFYA'),
            base_url=os.getenv('SMS_BASE_URL', 'https://api.smsgateway.com/v1'),
            webhook_secret=os.getenv('SMS_WEBHOOK_SECRET', 'your-webhook-secret'),
            twilio_account_sid=os.getenv('TWILIO_ACCOUNT_SID', ''),
            africas_talking_username=os.getenv('AT_USERNAME', '')
        )
        
        self.ussd = USSDConfig(
            service_code=os.getenv('USSD_SERVICE_CODE', '*714#'),
            session_timeout=int(os.getenv('USSD_SESSION_TIMEOUT', '300')),
            max_menu_levels=int(os.getenv('USSD_MAX_MENU_LEVELS', '5'))
        )
        
        self.network = NetworkConfig()
        self.security = SecurityConfig(
            encryption_key=os.getenv('ENCRYPTION_KEY', 'your-encryption-key-here'),
            enable_message_encryption=os.getenv('ENABLE_ENCRYPTION', 'true').lower() == 'true',
            enable_audit_logging=os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true'
        )
        
        self.retry = RetryConfig()
        self.healthcare_data = HealthcareDataConfig()
        
        # Load from config file if provided
        if config_file:
            self._load_from_file(config_file)
    
    def _load_from_file(self, config_file: str):
        """Load configuration from file (JSON/YAML)"""
        # Implementation for loading from config file
        # This could support JSON, YAML, or TOML formats
        pass
    
    def get_protocol_config(self, protocol: str) -> Dict[str, Any]:
        """Get configuration for specific protocol"""
        configs = {
            'http': {
                'timeout': 30,
                'max_retries': self.retry.http_max_retries,
                'auth_token': self.openhim.auth_token
            },
            'https': {
                'timeout': 30,
                'max_retries': self.retry.http_max_retries,
                'auth_token': self.openhim.auth_token,
                'verify_ssl': True
            },
            'sms': {
                'provider': self.sms.provider,
                'api_key': self.sms.api_key,
                'api_secret': self.sms.api_secret,
                'sender_id': self.sms.sender_id,
                'base_url': self.sms.base_url,
                'max_retries': self.retry.sms_max_retries,
                'max_length': self.sms.max_message_length
            },
            'ussd': {
                'service_code': self.ussd.service_code,
                'session_timeout': self.ussd.session_timeout,
                'max_retries': self.retry.ussd_max_retries
            }
        }
        
        return configs.get(protocol, {})
    
    def get_data_type_config(self, data_type: str) -> Dict[str, Any]:
        """Get configuration for specific healthcare data type"""
        return {
            'priority': self.healthcare_data.priority_mappings.get(data_type, 5),
            'ttl': self.healthcare_data.ttl_mappings.get(data_type, 86400),
            'size_limit': self.healthcare_data.size_limits.get(data_type, 10240),
            'requires_encryption': data_type in self.security.force_encryption_for_types
        }
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Validate database config
        if not all([self.database.host, self.database.database, 
                   self.database.user, self.database.password]):
            errors.append("Database configuration incomplete")
        
        # Validate SMS config
        if not all([self.sms.api_key, self.sms.sender_id]):
            errors.append("SMS configuration incomplete")
        
        # Validate encryption key
        if self.security.enable_message_encryption and not self.security.encryption_key:
            errors.append("Encryption key required when encryption is enabled")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


# Default configuration instance
default_config = HealthcareTransmissionConfig()


# Example environment variable setup for production
def setup_production_environment():
    """
    Example of how to set up environment variables for production deployment
    """
    example_env_vars = {
        # Database
        'DB_HOST': 'your-postgres-server.com',
        'DB_NAME': 'afya_production',
        'DB_USER': 'afya_user',
        'DB_PASSWORD': 'secure-database-password',
        'DB_PORT': '5432',
        
        # OpenHIM
        'OPENHIM_URL': 'https://openhim.yourhealth.gov.gh',
        'OPENHIM_USER': 'afya_system@health.gov.gh',
        'OPENHIM_PASSWORD': 'secure-openhim-password',
        'OPENHIM_TOKEN': 'your-openhim-auth-token',
        'OPENHIM_CLIENT_ID': 'afya_ghana_client',
        
        # SMS Configuration (Example for Africa's Talking)
        'SMS_PROVIDER': 'africas_talking',
        'SMS_API_KEY': 'your-africas-talking-api-key',
        'SMS_SENDER_ID': 'AFYA_GH',
        'AT_USERNAME': 'your-africas-talking-username',
        
        # Security
        'ENCRYPTION_KEY': 'your-256-bit-encryption-key',
        'ENABLE_ENCRYPTION': 'true',
        'ENABLE_AUDIT_LOG': 'true',
        
        # USSD
        'USSD_SERVICE_CODE': '*714#',
        'USSD_SESSION_TIMEOUT': '300',
    }
    
    print("Set these environment variables for production:")
    for key, value in example_env_vars.items():
        print(f"export {key}='{value}'")


if __name__ == "__main__":
    # Test configuration
    config = HealthcareTransmissionConfig()
    
    if config.validate_config():
        print("Configuration validation passed!")
        print(f"Database: {config.database.host}:{config.database.port}/{config.database.database}")
        print(f"SMS Provider: {config.sms.provider}")
        print(f"USSD Service Code: {config.ussd.service_code}")
        print(f"Encryption Enabled: {config.security.enable_message_encryption}")
    else:
        print("Configuration validation failed!")
    
    # Show example for production setup
    print("\n" + "="*50)
    setup_production_environment()