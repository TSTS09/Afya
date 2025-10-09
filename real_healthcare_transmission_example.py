#!/usr/bin/env python3
"""
Healthcare Data Transmission System - Real Implementation Example
================================================================

This demonstrates a real-world implementation of the healthcare data
transmission system with proper OpenHIM integration, multiple protocol
support, and healthcare data handling.
"""

import asyncio
import logging
import time
from datetime import datetime
from healthcare_transmission_system import (
    HealthcareTransmissionSystem,
    OpenHIMMessage,
    DataType,
    NetworkStatus,
)
from transmission_config import HealthcareTransmissionConfig
from openhim_adapter import (
    OpenHIMMessageAdapter,
    create_lab_result_message,
    create_prescription_message
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthcareDataProcessor:
    """
    Processes real healthcare data and converts it to transmission-ready format
    """
    
    def __init__(self, config: HealthcareTransmissionConfig):
        self.config = config
        self.openhim_adapter = OpenHIMMessageAdapter(
            config.openhim.client_id,
            "healthcare-channel"
        )
    
    def process_lab_result(self, lab_data: dict) -> OpenHIMMessage:
        """Process laboratory result data"""
        
        # Extract patient information
        patient_data = {
            'id': lab_data.get('patient_id'),
            'name': lab_data.get('patient_name'),
            'phone': lab_data.get('patient_phone'),
            'ghana_card_number': lab_data.get('ghana_card'),
            'gender': lab_data.get('gender', 'unknown'),
            'birth_date': lab_data.get('birth_date'),
        }
        
        # Process test results
        test_results = []
        for test in lab_data.get('tests', []):
            test_result = {
                'type': test.get('test_type'),
                'display_name': test.get('test_name'),
                'value': test.get('result_value'),
                'unit': test.get('unit'),
                'reference_range': test.get('reference_range'),
                'timestamp': test.get('timestamp', datetime.now().isoformat())
            }
            test_results.append(test_result)
        
        # Create OpenHIM message structure
        openhim_data = create_lab_result_message(patient_data, {
            'test_name': lab_data.get('test_name', 'Laboratory Test'),
            'test_date': lab_data.get('test_date', datetime.now().isoformat()),
            'conclusion': lab_data.get('conclusion', ''),
            'tests': test_results
        })
        
        # Determine data type and priority based on test type
        data_type = DataType.LAB_ROUTINE
        priority = 3
        
        # Special handling for critical tests
        hiv_tests = [t for t in lab_data.get('tests', [])
                     if t.get('test_type') == 'hiv_test']
        if hiv_tests:
            data_type = DataType.LAB_HIV_RESULT
            priority = 1
        
        # Create OpenHIM message
        patient_id = lab_data.get('patient_id', 'unknown')
        message_id = f"lab_{int(time.time())}_{patient_id}"
        message = OpenHIMMessage(
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            source=lab_data.get('facility_id', 'unknown_facility'),
            destination=lab_data.get('destination', 'central_hie'),
            message_type="LabResult",
            data_type=data_type,
            priority=priority,
            client_id=self.config.openhim.client_id,
            transaction_id=f"txn_{int(time.time())}",
            patient_id=lab_data.get('patient_id'),
            facility_id=lab_data.get('facility_id'),
            provider_id=lab_data.get('provider_id'),
            payload=openhim_data
        )
        
        return message
    
    def process_prescription(self, prescription_data: dict) -> OpenHIMMessage:
        """Process prescription data"""
        
        patient_data = {
            'id': prescription_data.get('patient_id'),
            'name': prescription_data.get('patient_name'),
            'phone': prescription_data.get('patient_phone'),
        }
        
        prescription_details = {
            'medication_name': prescription_data.get('medication'),
            'dosage_instructions': prescription_data.get('instructions'),
            'frequency': prescription_data.get('frequency', 1),
            'quantity': prescription_data.get('quantity', 1),
        }
        
        openhim_data = create_prescription_message(
            patient_data, prescription_details
        )
        
        patient_id = prescription_data.get('patient_id', 'unknown')
        message_id = f"rx_{int(time.time())}_{patient_id}"
        pharmacy_id = prescription_data.get('pharmacy_id', 'default_pharmacy')
        message = OpenHIMMessage(
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            source=prescription_data.get('facility_id', 'unknown_facility'),
            destination=pharmacy_id,
            message_type="Prescription",
            data_type=DataType.PRESCRIPTION,
            priority=2,
            client_id=self.config.openhim.client_id,
            transaction_id=f"txn_{int(time.time())}",
            patient_id=prescription_data.get('patient_id'),
            facility_id=prescription_data.get('facility_id'),
            provider_id=prescription_data.get('provider_id'),
            payload=openhim_data
        )
        
        return message
    
    def process_emergency_alert(self, emergency_data: dict) -> OpenHIMMessage:
        """Process emergency alert data"""
        
        patient_id = emergency_data.get('patient_id', 'unknown')
        message_id = f"emr_{int(time.time())}_{patient_id}"
        destination = emergency_data.get('destination', 'emergency_response')
        message = OpenHIMMessage(
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            source=emergency_data.get('source', 'emergency_system'),
            destination=destination,
            message_type="Emergency",
            data_type=DataType.EMERGENCY,
            priority=1,  # Highest priority
            client_id=self.config.openhim.client_id,
            transaction_id=f"txn_{int(time.time())}",
            patient_id=emergency_data.get('patient_id'),
            facility_id=emergency_data.get('facility_id'),
            payload={
                'alert_type': emergency_data.get('alert_type'),
                'severity': emergency_data.get('severity'),
                'location': emergency_data.get('location'),
                'contact_number': emergency_data.get('contact_number'),
                'description': emergency_data.get('description'),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return message


class NetworkMonitor:
    """
    Monitors network conditions and updates status for protocol selection
    """
    
    def __init__(self, transmission_system: HealthcareTransmissionSystem):
        self.transmission_system = transmission_system
        self.facility_statuses = {}
    
    async def simulate_network_conditions(self):
        """Simulate various network conditions for different facilities"""
        
        # Simulate different facilities with varying network conditions
        facilities = [
            {
                'facility_id': 'urban_hospital_001',
                'network_type': 'fiber',
                'bandwidth_kbps': 5000,
                'latency_ms': 20,
                'packet_loss_percent': 0.1
            },
            {
                'facility_id': 'rural_clinic_002',
                'network_type': '3g',
                'bandwidth_kbps': 128,
                'latency_ms': 300,
                'packet_loss_percent': 5.0
            },
            {
                'facility_id': 'remote_outpost_003',
                'network_type': 'sms_only',
                'bandwidth_kbps': 0,
                'latency_ms': 10000,
                'packet_loss_percent': 50.0
            }
        ]
        
        for facility in facilities:
            network_status = NetworkStatus(
                facility_id=facility['facility_id'],
                network_type=facility['network_type'],
                bandwidth_kbps=facility['bandwidth_kbps'],
                latency_ms=facility['latency_ms'],
                packet_loss_percent=facility['packet_loss_percent'],
                last_updated=datetime.now(),
                is_active=True
            )
            
            await self.transmission_system.update_network_status(
                facility['facility_id'],
                network_status
            )
            
            self.facility_statuses[facility['facility_id']] = network_status
            
            facility_id = facility['facility_id']
            condition = network_status.get_condition().value
            logger.info(f"Updated network status for {facility_id}: {condition}")


async def run_comprehensive_example():
    """
    Run comprehensive example demonstrating the healthcare transmission system
    """
    
    logger.info("Starting Healthcare Data Transmission System Example")
    
    # Load configuration
    config = HealthcareTransmissionConfig()
    
    if not config.validate_config():
        logger.error("Configuration validation failed!")
        return
    
    # Initialize transmission system
    transmission_system = HealthcareTransmissionSystem(
        config.database.to_dict(),
        {
            'http': config.get_protocol_config('http'),
            'https': config.get_protocol_config('https'),
            'sms': config.get_protocol_config('sms'),
            'ussd': config.get_protocol_config('ussd')
        }
    )
    
    try:
        await transmission_system.initialize()
        logger.info("Transmission system initialized successfully")
        
        # Initialize data processor
        data_processor = HealthcareDataProcessor(config)
        
        # Initialize and run network monitoring
        network_monitor = NetworkMonitor(transmission_system)
        await network_monitor.simulate_network_conditions()
        
        # Example 1: Process a laboratory result
        logger.info("Processing laboratory result...")
        lab_data = {
            'patient_id': 'patient_001',
            'patient_name': 'Kwame Asante',
            'patient_phone': '0200123456',
            'ghana_card': 'GHA-123456789-0',
            'gender': 'male',
            'birth_date': '1985-03-15',
            'facility_id': 'urban_hospital_001',
            'provider_id': 'provider_123',
            'destination': 'central_hie',
            'test_name': 'Complete Blood Count',
            'test_date': datetime.now().isoformat(),
            'conclusion': 'All values within normal ranges',
            'tests': [
                {
                    'test_type': 'blood_glucose',
                    'test_name': 'Blood Glucose',
                    'result_value': 95,
                    'unit': 'mg/dL',
                    'reference_range': {'low': 70, 'high': 100},
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'test_type': 'heart_rate',
                    'test_name': 'Heart Rate',
                    'result_value': 72,
                    'unit': 'bpm',
                    'reference_range': {'low': 60, 'high': 100},
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        lab_message = data_processor.process_lab_result(lab_data)
        success = await transmission_system.queue_message(lab_message, 'healthcare_exchange')
        if success:
            logger.info(f"Successfully queued lab result message: {lab_message.message_id}")
        
        # Example 2: Process a prescription
        logger.info("Processing prescription...")
        prescription_data = {
            'patient_id': 'patient_002',
            'patient_name': 'Ama Mensah',
            'patient_phone': '0240234567',
            'facility_id': 'rural_clinic_002',
            'provider_id': 'provider_456',
            'pharmacy_id': 'pharmacy_001',
            'medication': 'Paracetamol 500mg',
            'instructions': 'Take 1 tablet every 6 hours as needed for pain',
            'frequency': 4,
            'quantity': 20
        }
        
        prescription_message = data_processor.process_prescription(prescription_data)
        success = await transmission_system.queue_message(prescription_message, 'healthcare_exchange')
        if success:
            logger.info(f"Successfully queued prescription message: {prescription_message.message_id}")
        
        # Example 3: Process an emergency alert
        logger.info("Processing emergency alert...")
        emergency_data = {
            'patient_id': 'patient_003',
            'source': 'remote_outpost_003',
            'destination': 'emergency_response_center',
            'facility_id': 'remote_outpost_003',
            'alert_type': 'cardiac_arrest',
            'severity': 'critical',
            'location': 'Remote Health Outpost, Northern Region',
            'contact_number': '0260345678',
            'description': 'Male patient, 45 years old, cardiac arrest, CPR in progress'
        }
        
        emergency_message = data_processor.process_emergency_alert(emergency_data)
        success = await transmission_system.queue_message(emergency_message, 'healthcare_exchange')
        if success:
            logger.info(f"Successfully queued emergency message: {emergency_message.message_id}")
        
        # Process all pending messages
        logger.info("Processing pending messages...")
        await transmission_system.process_pending_messages()
        
        # Simulate processing over time with different network conditions
        logger.info("Simulating ongoing message processing...")
        for i in range(3):
            await asyncio.sleep(2)  # Wait 2 seconds
            
            # Add another message during processing
            if i == 1:
                # Add a high-priority HIV test result
                hiv_test_data = lab_data.copy()
                hiv_test_data.update({
                    'patient_id': 'patient_004',
                    'facility_id': 'rural_clinic_002',
                    'test_name': 'HIV Test',
                    'tests': [
                        {
                            'test_type': 'hiv_test',
                            'test_name': 'HIV Antibody Test',
                            'result_value': 'Non-reactive',
                            'unit': '',
                            'timestamp': datetime.now().isoformat()
                        }
                    ]
                })
                
                hiv_message = data_processor.process_lab_result(hiv_test_data)
                await transmission_system.queue_message(hiv_message, 'healthcare_exchange')
                logger.info(f"Added high-priority HIV test result: {hiv_message.message_id}")
            
            # Process messages
            await transmission_system.process_pending_messages()
        
        logger.info("Message processing simulation completed")
        
        # Display network status summary
        logger.info("Network Status Summary:")
        for facility_id, status in network_monitor.facility_statuses.items():
            logger.info(f"  {facility_id}: {status.get_condition().value} "
                       f"({status.bandwidth_kbps} kbps, {status.latency_ms}ms latency)")
        
    except Exception as e:
        logger.error(f"Error in comprehensive example: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await transmission_system.shutdown()
        logger.info("Healthcare transmission system shutdown complete")


async def run_protocol_selection_demo():
    """
    Demonstrate protocol selection based on network conditions
    """
    
    logger.info("Running Protocol Selection Demonstration")
    
    # Test data for different scenarios
    test_scenarios = [
        {
            'name': 'Urban Hospital - High Bandwidth',
            'facility': 'urban_hospital_001',
            'expected_protocol': 'HTTPS',
            'data_type': DataType.LAB_ROUTINE
        },
        {
            'name': 'Rural Clinic - Medium Bandwidth',
            'facility': 'rural_clinic_002',
            'expected_protocol': 'SMS_MULTIPART or HTTPS',
            'data_type': DataType.PRESCRIPTION
        },
        {
            'name': 'Remote Outpost - SMS Only',
            'facility': 'remote_outpost_003',
            'expected_protocol': 'SMS',
            'data_type': DataType.EMERGENCY
        }
    ]
    
    for scenario in test_scenarios:
        logger.info(f"\nScenario: {scenario['name']}")
        logger.info(f"Expected Protocol: {scenario['expected_protocol']}")
        logger.info(f"Data Type: {scenario['data_type'].value}")
    
    logger.info("Protocol selection demonstration completed")


if __name__ == "__main__":
    """
    Main execution with different examples
    """
    
    print("Healthcare Data Transmission System - Real Implementation")
    print("=" * 60)
    print()
    print("This system demonstrates:")
    print("- Real healthcare data processing")
    print("- OpenHIM format compliance")
    print("- Multi-protocol transmission (HTTP/HTTPS, SMS, USSD)")
    print("- Network-aware protocol selection")
    print("- Healthcare data prioritization")
    print("- Message queuing and retry mechanisms")
    print()
    
    # Ask user which example to run
    print("Available examples:")
    print("1. Comprehensive system demonstration")
    print("2. Protocol selection demonstration")
    print("3. Both examples")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(run_comprehensive_example())
    elif choice == "2":
        asyncio.run(run_protocol_selection_demo())
    elif choice == "3":
        asyncio.run(run_comprehensive_example())
        print("\n" + "="*60 + "\n")
        asyncio.run(run_protocol_selection_demo())
    else:
        print("Invalid choice. Running comprehensive example...")
        asyncio.run(run_comprehensive_example())