#!/usr/bin/env python3
"""
Healthcare Transmission System Factory
=====================================

Main application factory for creating configured healthcare
transmission system instances with proper dependency injection.
"""

from typing import Optional
import os

from config.settings import HealthcareTransmissionSettings
from src.services.database_service import DatabaseService
from src.services.sms_service import create_sms_service_from_config
from src.services.transmission_service import HealthcareTransmissionService
from src.adapters.openhim_adapter import OpenHIMAdapter
from src.utils.network_monitor import NetworkMonitor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HealthcareTransmissionFactory:
    """Factory for creating healthcare transmission system instances"""
    
    @staticmethod
    def create_system(
        config: Optional[HealthcareTransmissionSettings] = None,
        enable_sms: bool = True,
        enable_openhim: bool = True,
        enable_network_monitoring: bool = True
    ) -> HealthcareTransmissionService:
        """Create a fully configured healthcare transmission system"""
        
        if config is None:
            config = HealthcareTransmissionSettings()
        
        # Validate configuration
        validation_errors = config.validate()
        if validation_errors:
            logger.warning(f"Configuration validation issues: {validation_errors}")
        
        # Create database service
        database_service = DatabaseService(config.database.get_connection_string())
        
        # Create SMS service if enabled and configured
        sms_service = None
        if enable_sms and config.sms.api_key:
            try:
                sms_service = create_sms_service_from_config(config.sms)
                logger.info(f"SMS service configured with provider: {config.sms.provider}")
            except Exception as e:
                logger.error(f"Failed to create SMS service: {str(e)}")
        
        # Create OpenHIM adapter if enabled and configured
        openhim_adapter = None
        if enable_openhim and config.openhim.client_password:
            try:
                openhim_adapter = OpenHIMAdapter(
                    base_url=config.openhim.base_url,
                    client_id=config.openhim.client_id,
                    client_password=config.openhim.client_password,
                    verify_ssl=config.openhim.verify_ssl,
                    timeout=config.openhim.timeout
                )
                logger.info("OpenHIM adapter configured")
            except Exception as e:
                logger.error(f"Failed to create OpenHIM adapter: {str(e)}")
        
        # Create network monitor if enabled
        network_monitor = None
        if enable_network_monitoring:
            try:
                network_monitor = NetworkMonitor(timeout=config.network.timeout)
                logger.info("Network monitoring enabled")
            except Exception as e:
                logger.error(f"Failed to create network monitor: {str(e)}")
        
        # Create main transmission service
        transmission_service = HealthcareTransmissionService(
            database_service=database_service,
            sms_service=sms_service,
            openhim_adapter=openhim_adapter,
            network_monitor=network_monitor
        )
        
        logger.info("Healthcare transmission system created successfully")
        return transmission_service
    
    @staticmethod
    def create_testing_system() -> HealthcareTransmissionService:
        """Create a system configured for testing with minimal dependencies"""
        
        # Use environment variables or defaults for testing
        config = HealthcareTransmissionSettings()
        config.database.database = os.getenv('TEST_DB_NAME', 'test_pg_mq')
        config.sms.provider = 'twilio'  # Default for testing
        
        # Create with only database service for basic testing
        database_service = DatabaseService(config.database.get_connection_string())
        
        transmission_service = HealthcareTransmissionService(
            database_service=database_service,
            sms_service=None,  # SMS disabled for basic testing
            openhim_adapter=None,  # OpenHIM disabled for basic testing
            network_monitor=None   # Network monitoring disabled for basic testing
        )
        
        logger.info("Testing healthcare transmission system created")
        return transmission_service


def create_production_system() -> HealthcareTransmissionService:
    """Create a production-ready healthcare transmission system"""
    
    # Load configuration from environment
    config = HealthcareTransmissionSettings.load_from_env_file()
    config.environment = 'production'
    
    # Validate production configuration
    validation_errors = config.validate()
    if validation_errors:
        raise ValueError(f"Production configuration errors: {validation_errors}")
    
    # Create system with all features enabled
    return HealthcareTransmissionFactory.create_system(
        config=config,
        enable_sms=True,
        enable_openhim=True,
        enable_network_monitoring=True
    )


def create_development_system() -> HealthcareTransmissionService:
    """Create a development system with relaxed validation"""
    
    config = HealthcareTransmissionSettings()
    config.environment = 'development'
    config.debug = True
    
    # Create system with features that are configured
    return HealthcareTransmissionFactory.create_system(
        config=config,
        enable_sms=bool(config.sms.api_key),
        enable_openhim=bool(config.openhim.client_password),
        enable_network_monitoring=True
    )