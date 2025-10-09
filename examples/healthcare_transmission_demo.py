#!/usr/bin/env python3
"""
Healthcare Transmission System Example
=====================================

Comprehensive example demonstrating the healthcare data transmission
system with proper architecture, SMS API integration, and real-world scenarios.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from src.core.factory import create_development_system
from src.core.models import OpenHIMMessage, DataType, HealthcarePatient, LabResult
from src.adapters.openhim_adapter import create_lab_result_message, create_prescription_message
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HealthcareDataProcessor:
    """Process healthcare data for transmission"""
    
    def __init__(self, transmission_service):
        self.transmission_service = transmission_service
        self.logger = get_logger(f"{__name__}.HealthcareDataProcessor")
    
    async def process_lab_result(self, lab_data: Dict[str, Any]) -> bool:
        """Process and queue lab result for transmission"""
        try:
            # Extract patient and lab information
            patient_data = lab_data.get('patient', {})
            test_data = lab_data.get('test', {})
            
            # Determine priority based on test type
            priority = 3  # Normal
            data_type = DataType.LAB_RESULT
            
            if test_data.get('test_type') == 'hiv_test':
                priority = 1  # Critical
                data_type = DataType.LAB_HIV_RESULT
            
            # Create OpenHIM message
            message = OpenHIMMessage(
                source=lab_data.get('facility_id', 'unknown_facility'),
                destination=lab_data.get('destination', 'central_hie'),
                message_type="LabResult",
                data_type=data_type,
                priority=priority,
                patient_id=patient_data.get('patient_id'),
                facility_id=lab_data.get('facility_id'),
                payload=create_lab_result_message(patient_data, test_data)
            )
            
            # Queue message
            success = await self.transmission_service.queue_message(message)
            
            if success:
                self.logger.info(f"Lab result queued: {message.message_id}")
            else:
                self.logger.error(f"Failed to queue lab result: {message.message_id}")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error processing lab result: {str(e)}")
            return False
    
    async def process_prescription(self, prescription_data: Dict[str, Any]) -> bool:
        """Process and queue prescription for transmission"""
        try:
            patient_data = prescription_data.get('patient', {})
            rx_data = prescription_data.get('prescription', {})
            
            # Create OpenHIM message
            message = OpenHIMMessage(
                source=prescription_data.get('clinic_id', 'unknown_clinic'),
                destination=prescription_data.get('pharmacy_id', 'default_pharmacy'),
                message_type="Prescription",
                data_type=DataType.PRESCRIPTION,
                priority=2,  # High priority
                patient_id=patient_data.get('patient_id'),
                facility_id=prescription_data.get('clinic_id'),
                payload=create_prescription_message(patient_data, rx_data)
            )
            
            # Queue message
            success = await self.transmission_service.queue_message(message)
            
            if success:
                self.logger.info(f"Prescription queued: {message.message_id}")
            else:
                self.logger.error(f"Failed to queue prescription: {message.message_id}")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error processing prescription: {str(e)}")
            return False
    
    async def process_emergency_alert(self, emergency_data: Dict[str, Any]) -> bool:
        """Process and queue emergency alert for immediate transmission"""
        try:
            # Create emergency message
            message = OpenHIMMessage(
                source=emergency_data.get('source', 'emergency_system'),
                destination=emergency_data.get('destination', 'emergency_response'),
                message_type="Emergency",
                data_type=DataType.EMERGENCY,
                priority=1,  # Critical
                patient_id=emergency_data.get('patient_id'),
                facility_id=emergency_data.get('facility_id'),
                payload={
                    'emergency_type': emergency_data.get('emergency_type'),
                    'severity': emergency_data.get('severity', 'high'),
                    'location': emergency_data.get('location'),
                    'description': emergency_data.get('description'),
                    'vital_signs': emergency_data.get('vital_signs', {}),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Queue message with high priority
            success = await self.transmission_service.queue_message(message)
            
            if success:
                self.logger.info(f"Emergency alert queued: {message.message_id}")
            else:
                self.logger.error(f"Failed to queue emergency alert: {message.message_id}")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error processing emergency alert: {str(e)}")
            return False


async def demonstrate_healthcare_transmission():
    """Demonstrate comprehensive healthcare data transmission"""
    
    logger.info("Starting Healthcare Data Transmission System Demo")
    
    # Create transmission system
    transmission_system = create_development_system()
    
    # Initialize the system
    if not await transmission_system.initialize():
        logger.error("Failed to initialize transmission system")
        return
    
    # Create data processor
    data_processor = HealthcareDataProcessor(transmission_system)
    
    try:
        # Example 1: Process HIV test result (high priority)
        logger.info("Processing HIV test result...")
        hiv_test_data = {
            'patient': {
                'patient_id': 'PAT001',
                'first_name': 'John',
                'last_name': 'Doe',
                'date_of_birth': '1985-03-15',
                'gender': 'male',
                'phone_number': '+254712345678',
                'national_id': '12345678'
            },
            'test': {
                'test_id': 'HIV001',
                'test_type': 'hiv_test',
                'test_name': 'HIV Rapid Test',
                'result_value': 'NEGATIVE',
                'reference_range': 'NEGATIVE',
                'performed_date': datetime.now().isoformat()
            },
            'facility_id': 'FAC001',
            'destination': 'national_hiv_registry'
        }
        
        await data_processor.process_lab_result(hiv_test_data)
        
        # Example 2: Process regular lab result
        logger.info("Processing regular lab result...")
        lab_data = {
            'patient': {
                'patient_id': 'PAT002',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'date_of_birth': '1990-07-22',
                'gender': 'female',
                'phone_number': '+254723456789'
            },
            'test': {
                'test_id': 'LAB002',
                'test_type': 'blood_glucose',
                'test_name': 'Random Blood Glucose',
                'result_value': '95',
                'units': 'mg/dL',
                'reference_range': '70-140',
                'performed_date': datetime.now().isoformat()
            },
            'facility_id': 'FAC001',
            'destination': 'central_lab_system'
        }
        
        await data_processor.process_lab_result(lab_data)
        
        # Example 3: Process prescription
        logger.info("Processing prescription...")
        prescription_data = {
            'patient': {
                'patient_id': 'PAT003',
                'first_name': 'Bob',
                'last_name': 'Johnson',
                'date_of_birth': '1975-12-10',
                'gender': 'male',
                'phone_number': '+254734567890'
            },
            'prescription': {
                'prescription_id': 'RX003',
                'medication_name': 'Amoxicillin',
                'dosage': '500mg',
                'frequency': 'three times daily',
                'duration': '7 days',
                'prescriber_id': 'DR001',
                'instructions': 'Take with food'
            },
            'clinic_id': 'CLI001',
            'pharmacy_id': 'PHA001'
        }
        
        await data_processor.process_prescription(prescription_data)
        
        # Example 4: Process emergency alert
        logger.info("Processing emergency alert...")
        emergency_data = {
            'patient_id': 'PAT004',
            'emergency_type': 'cardiac_arrest',
            'severity': 'critical',
            'location': 'Emergency Room - Bed 3',
            'description': 'Patient collapsed, CPR in progress',
            'vital_signs': {
                'heart_rate': 0,
                'blood_pressure': '0/0',
                'respiratory_rate': 0,
                'temperature': 36.5
            },
            'source': 'emergency_department',
            'destination': 'trauma_team',
            'facility_id': 'HOSP001'
        }
        
        await data_processor.process_emergency_alert(emergency_data)
        
        # Process queued messages
        logger.info("Processing message queue...")
        await asyncio.sleep(2)  # Allow messages to be queued
        
        stats = await transmission_system.process_queue(batch_size=20)
        logger.info(f"Queue processing results: {stats}")
        
        # Get transmission statistics
        transmission_stats = await transmission_system.get_transmission_stats()
        logger.info(f"Transmission statistics: {transmission_stats}")
        
    except Exception as e:
        logger.error(f"Error in demonstration: {str(e)}")
    
    finally:
        # Close the system
        await transmission_system.close()
        logger.info("Healthcare transmission system demonstration completed")


async def demonstrate_sms_transmission():
    """Demonstrate SMS transmission specifically"""
    logger.info("Demonstrating SMS transmission...")
    
    # This would be used when SMS is properly configured
    # For now, just show the message formatting
    
    sample_message = OpenHIMMessage(
        source="FAC001",
        destination="+254712345678",
        message_type="LabResult",
        data_type=DataType.LAB_HIV_RESULT,
        priority=1,
        patient_id="PAT001",
        facility_id="FAC001",
        payload={
            'test_type': 'HIV Rapid Test',
            'result': 'NEGATIVE',
            'date': datetime.now().isoformat()
        }
    )
    
    # Show how the message would be formatted for SMS
    from src.services.transmission_service import HealthcareTransmissionService
    
    # Create a mock service to demonstrate formatting
    mock_service = HealthcareTransmissionService(None)
    formatted_sms = mock_service._format_message_for_sms(sample_message)
    
    logger.info(f"SMS format: {formatted_sms}")


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_healthcare_transmission())
    
    # Demonstrate SMS formatting
    asyncio.run(demonstrate_sms_transmission())