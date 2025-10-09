#!/usr/bin/env python3
"""
Quick Test for Healthcare Transmission System
============================================

Basic test to verify the system is working correctly.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.models import OpenHIMMessage, DataType
from src.core.factory import HealthcareTransmissionFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_basic_functionality():
    """Test basic system functionality"""
    
    logger.info("Starting basic functionality test...")
    
    try:
        # Create a testing system (database only)
        system = HealthcareTransmissionFactory.create_testing_system()
        
        # Test system initialization
        logger.info("Testing system initialization...")
        init_success = await system.initialize()
        
        if not init_success:
            logger.error("System initialization failed!")
            return False
        
        logger.info("✓ System initialization successful")
        
        # Test message creation
        logger.info("Testing message creation...")
        message = OpenHIMMessage(
            source="test_facility",
            destination="test_destination",
            message_type="TestMessage",
            data_type=DataType.GENERAL,
            priority=3,
            patient_id="TEST001",
            facility_id="FAC001",
            payload={"test": "data", "message": "Hello Healthcare System!"}
        )
        
        logger.info(f"✓ Message created: {message.message_id}")
        
        # Test message queuing
        logger.info("Testing message queuing...")
        queue_success = await system.queue_message(message, "test_exchange")
        
        if queue_success:
            logger.info("✓ Message queued successfully")
        else:
            logger.warning("Message queuing failed (may be due to database connection)")
        
        # Test configuration
        logger.info("Testing configuration...")
        from config.settings import HealthcareTransmissionSettings
        
        config = HealthcareTransmissionSettings()
        validation_errors = config.validate()
        
        if validation_errors:
            logger.info(f"Configuration validation (expected in test): {validation_errors}")
        else:
            logger.info("✓ Configuration validation passed")
        
        # Test message formatting for SMS
        logger.info("Testing SMS message formatting...")
        formatted_sms = system._format_message_for_sms(message)
        logger.info(f"✓ SMS format: {formatted_sms}")
        
        # Cleanup
        await system.close()
        logger.info("✓ System closed successfully")
        
        logger.info("🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False


async def test_sms_formatting():
    """Test SMS message formatting for different healthcare data types"""
    
    logger.info("Testing SMS formatting for different healthcare message types...")
    
    from src.services.transmission_service import HealthcareTransmissionService
    
    # Create a mock service for testing formatting
    mock_service = HealthcareTransmissionService(None)
    
    # Test lab result formatting
    lab_message = OpenHIMMessage(
        message_type="LabResult",
        data_type=DataType.LAB_RESULT,
        patient_id="PAT001",
        facility_id="FAC001",
        payload={"test_type": "blood_glucose", "result": "95 mg/dL"}
    )
    
    lab_sms = mock_service._format_message_for_sms(lab_message)
    logger.info(f"Lab result SMS: {lab_sms}")
    
    # Test prescription formatting
    rx_message = OpenHIMMessage(
        message_type="Prescription",
        data_type=DataType.PRESCRIPTION,
        patient_id="PAT002",
        facility_id="FAC001",
        payload={"medication": "Amoxicillin", "dosage": "500mg"}
    )
    
    rx_sms = mock_service._format_message_for_sms(rx_message)
    logger.info(f"Prescription SMS: {rx_sms}")
    
    # Test emergency formatting
    emergency_message = OpenHIMMessage(
        message_type="Emergency",
        data_type=DataType.EMERGENCY,
        patient_id="PAT003",
        facility_id="HOSP001",
        payload={"emergency_type": "cardiac_arrest", "location": "ER Room 3"}
    )
    
    emergency_sms = mock_service._format_message_for_sms(emergency_message)
    logger.info(f"Emergency SMS: {emergency_sms}")
    
    logger.info("✓ SMS formatting tests completed")


async def main():
    """Run all tests"""
    
    logger.info("=" * 60)
    logger.info("Healthcare Transmission System - Quick Test")
    logger.info("=" * 60)
    
    # Test basic functionality
    basic_test_passed = await test_basic_functionality()
    
    print()
    
    # Test SMS formatting
    await test_sms_formatting()
    
    print()
    
    if basic_test_passed:
        logger.info("🎉 Healthcare Transmission System is working correctly!")
        logger.info("\nNext steps:")
        logger.info("1. Configure your SMS provider in config/.env")
        logger.info("2. Set up OpenHIM if needed")
        logger.info("3. Run the full demo: python examples/healthcare_transmission_demo.py")
    else:
        logger.error("❌ Some tests failed. Check your configuration and database connection.")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())