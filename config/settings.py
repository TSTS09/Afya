#!/usr/bin/env python3
"""
Healthcare Transmission System Configuration
===========================================

Centralized configuration management with environment variable support
and validation for production deployment.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '5432')))
    database: str = field(default_factory=lambda: os.getenv('DB_NAME', 'pg_mq_poc'))
    username: str = field(default_factory=lambda: os.getenv('DB_USER', 'postgres'))
    password: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return (f"postgresql://{self.username}:{self.password}"
                f"@{self.host}:{self.port}/{self.database}")


@dataclass
class OpenHIMConfig:
    """OpenHIM (Open Health Information Mediator) configuration"""
    base_url: str = field(default_factory=lambda: os.getenv('OPENHIM_URL', 'https://localhost:8080'))
    client_id: str = field(default_factory=lambda: os.getenv('OPENHIM_CLIENT_ID', 'healthcare_transmission'))
    client_password: str = field(default_factory=lambda: os.getenv('OPENHIM_CLIENT_PASSWORD', ''))
    verify_ssl: bool = field(default_factory=lambda: os.getenv('OPENHIM_VERIFY_SSL', 'true').lower() == 'true')
    timeout: int = field(default_factory=lambda: int(os.getenv('OPENHIM_TIMEOUT', '30')))


@dataclass
class SMSConfig:
    """SMS API configuration for testing and low-bandwidth transmission"""
    provider: str = field(default_factory=lambda: os.getenv('SMS_PROVIDER', 'twilio'))
    api_key: str = field(default_factory=lambda: os.getenv('SMS_API_KEY', ''))
    api_secret: str = field(default_factory=lambda: os.getenv('SMS_API_SECRET', ''))
    sender_number: str = field(default_factory=lambda: os.getenv('SMS_SENDER_NUMBER', ''))
    base_url: str = field(default_factory=lambda: os.getenv('SMS_API_URL', ''))
    max_message_length: int = field(default_factory=lambda: int(os.getenv('SMS_MAX_LENGTH', '160')))
    
    # Twilio-specific settings
    account_sid: str = field(default_factory=lambda: os.getenv('TWILIO_ACCOUNT_SID', ''))
    auth_token: str = field(default_factory=lambda: os.getenv('TWILIO_AUTH_TOKEN', ''))
    
    # Alternative SMS providers
    africastalking_username: str = field(default_factory=lambda: os.getenv('AFRICASTALKING_USERNAME', ''))
    africastalking_api_key: str = field(default_factory=lambda: os.getenv('AFRICASTALKING_API_KEY', ''))


@dataclass
class NetworkConfig:
    """Network monitoring and transmission configuration"""
    check_interval: int = field(default_factory=lambda: int(os.getenv('NETWORK_CHECK_INTERVAL', '60')))
    timeout: int = field(default_factory=lambda: int(os.getenv('NETWORK_TIMEOUT', '10')))
    retry_attempts: int = field(default_factory=lambda: int(os.getenv('NETWORK_RETRY_ATTEMPTS', '3')))
    low_bandwidth_threshold: float = field(default_factory=lambda: float(os.getenv('LOW_BANDWIDTH_THRESHOLD', '1.0')))
    high_latency_threshold: float = field(default_factory=lambda: float(os.getenv('HIGH_LATENCY_THRESHOLD', '500.0')))


@dataclass
class QueueConfig:
    """Message queue configuration"""
    default_exchange: str = field(default_factory=lambda: os.getenv('DEFAULT_EXCHANGE', 'healthcare_exchange'))
    default_queue: str = field(default_factory=lambda: os.getenv('DEFAULT_QUEUE', 'healthcare_queue'))
    retry_limit: int = field(default_factory=lambda: int(os.getenv('QUEUE_RETRY_LIMIT', '3')))
    retry_delay: int = field(default_factory=lambda: int(os.getenv('QUEUE_RETRY_DELAY', '5')))
    max_message_size: int = field(default_factory=lambda: int(os.getenv('MAX_MESSAGE_SIZE', '65536')))


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_path: Optional[str] = field(default_factory=lambda: os.getenv('LOG_FILE_PATH'))
    max_bytes: int = field(default_factory=lambda: int(os.getenv('LOG_MAX_BYTES', '10485760')))  # 10MB
    backup_count: int = field(default_factory=lambda: int(os.getenv('LOG_BACKUP_COUNT', '5')))


@dataclass
class HealthcareTransmissionSettings:
    """Main configuration class for the healthcare transmission system"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    openhim: OpenHIMConfig = field(default_factory=OpenHIMConfig)
    sms: SMSConfig = field(default_factory=SMSConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    queue: QueueConfig = field(default_factory=QueueConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Environment settings
    environment: str = field(default_factory=lambda: os.getenv('ENVIRONMENT', 'development'))
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return any errors"""
        errors = {}
        
        # Validate database connection
        if not self.database.password and self.environment == 'production':
            errors['database'] = 'Database password is required in production'
        
        # Validate OpenHIM configuration
        if not self.openhim.client_password and self.environment == 'production':
            errors['openhim'] = 'OpenHIM client password is required in production'
        
        # Validate SMS configuration
        if self.sms.provider == 'twilio':
            if not self.sms.account_sid or not self.sms.auth_token:
                errors['sms'] = 'Twilio Account SID and Auth Token are required'
        elif self.sms.provider == 'africastalking':
            if not self.sms.africastalking_username or not self.sms.africastalking_api_key:
                errors['sms'] = 'Africa\'s Talking username and API key are required'
        
        return errors
    
    @classmethod
    def load_from_env_file(cls, env_file_path: Optional[str] = None) -> 'HealthcareTransmissionSettings':
        """Load configuration from environment file"""
        if env_file_path is None:
            env_file_path = Path(__file__).parent / '.env'
        
        if Path(env_file_path).exists():
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        
        return cls()


# Global settings instance
settings = HealthcareTransmissionSettings()