#!/usr/bin/env python3
"""
OpenHIM Adapter for Healthcare Data Transmission
===============================================

Adapter for Open Health Information Mediator (OpenHIM) integration
with FHIR resource support and healthcare interoperability standards.
"""

import json
from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime

from ..core.models import (
    OpenHIMMessage, TransmissionResult, MessageStatus, TransmissionProtocol,
    HealthcarePatient, LabResult, Prescription
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OpenHIMAdapter:
    """OpenHIM integration adapter for healthcare data transmission"""
    
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_password: str,
        verify_ssl: bool = True,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_password = client_password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.logger = get_logger(f"{__name__}.OpenHIMAdapter")
    
    async def send_message(
        self,
        message: OpenHIMMessage,
        destination: str
    ) -> TransmissionResult:
        """Send message via OpenHIM"""
        try:
            # Prepare OpenHIM transaction
            transaction_data = {
                'request': {
                    'method': 'POST',
                    'url': f'/healthcare/{message.data_type.value}',
                    'headers': {
                        'Content-Type': 'application/fhir+json',
                        'X-OpenHIM-TransactionID': message.transaction_id,
                        'X-Forwarded-For': '127.0.0.1',
                        'Authorization': f'Custom {self.client_id}:{self.client_password}'
                    },
                    'body': json.dumps(message.to_dict()),
                    'timestamp': datetime.now().isoformat()
                },
                'clientID': self.client_id,
                'channelID': f'healthcare-{message.data_type.value}',
                'orchestrations': []
            }
            
            # Send to OpenHIM
            url = f"{self.base_url}/transactions"
            
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(
                    url,
                    json=transaction_data,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Custom {self.client_id}:{self.client_password}'
                    }
                ) as response:
                    
                    response_data = await response.text()
                    
                    if response.status in [200, 201, 202]:
                        self.logger.info(f"OpenHIM transmission successful for message {message.message_id}")
                        return TransmissionResult(
                            success=True,
                            status=MessageStatus.SENT,
                            protocol_used=TransmissionProtocol.HTTPS,
                            message_id=message.message_id,
                            response_data={'openhim_response': response_data}
                        )
                    else:
                        error_msg = f"OpenHIM returned status {response.status}: {response_data}"
                        self.logger.error(error_msg)
                        return TransmissionResult(
                            success=False,
                            status=MessageStatus.FAILED,
                            protocol_used=TransmissionProtocol.HTTPS,
                            message_id=message.message_id,
                            error_message=error_msg
                        )
        
        except Exception as e:
            error_msg = f"OpenHIM transmission failed: {str(e)}"
            self.logger.error(error_msg)
            return TransmissionResult(
                success=False,
                status=MessageStatus.FAILED,
                protocol_used=TransmissionProtocol.HTTPS,
                message_id=message.message_id,
                error_message=error_msg
            )
    
    def create_fhir_bundle(self, resources: list) -> Dict[str, Any]:
        """Create FHIR Bundle from multiple resources"""
        return {
            'resourceType': 'Bundle',
            'id': f'bundle-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'type': 'transaction',
            'timestamp': datetime.now().isoformat(),
            'entry': [
                {
                    'resource': resource,
                    'request': {
                        'method': 'POST',
                        'url': resource['resourceType']
                    }
                }
                for resource in resources
            ]
        }


def create_patient_fhir_resource(patient: HealthcarePatient) -> Dict[str, Any]:
    """Create FHIR Patient resource"""
    return patient.to_fhir_dict()


def create_lab_result_fhir_resource(lab_result: LabResult) -> Dict[str, Any]:
    """Create FHIR Observation resource for lab result"""
    return lab_result.to_fhir_dict()


def create_prescription_fhir_resource(prescription: Prescription) -> Dict[str, Any]:
    """Create FHIR MedicationRequest resource"""
    return prescription.to_fhir_dict()


def create_lab_result_message(patient_data: Dict[str, Any], lab_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create OpenHIM message for lab results"""
    try:
        # Create FHIR resources
        patient = HealthcarePatient(
            patient_id=patient_data.get('patient_id', ''),
            first_name=patient_data.get('first_name', ''),
            last_name=patient_data.get('last_name', ''),
            date_of_birth=patient_data.get('date_of_birth', ''),
            gender=patient_data.get('gender', 'unknown'),
            phone_number=patient_data.get('phone_number'),
            national_id=patient_data.get('national_id')
        )
        
        lab_result = LabResult(
            test_id=lab_data.get('test_id', ''),
            patient_id=patient_data.get('patient_id', ''),
            test_type=lab_data.get('test_type', ''),
            test_name=lab_data.get('test_name', ''),
            result_value=lab_data.get('result_value', ''),
            reference_range=lab_data.get('reference_range'),
            units=lab_data.get('units'),
            performed_date=lab_data.get('performed_date', datetime.now().isoformat()),
            facility_id=lab_data.get('facility_id')
        )
        
        # Create FHIR Bundle
        resources = [
            create_patient_fhir_resource(patient),
            create_lab_result_fhir_resource(lab_result)
        ]
        
        return {
            'fhir_bundle': {
                'resourceType': 'Bundle',
                'type': 'transaction',
                'entry': [
                    {'resource': resource, 'request': {'method': 'POST', 'url': resource['resourceType']}}
                    for resource in resources
                ]
            },
            'metadata': {
                'message_type': 'LabResult',
                'patient_id': patient.patient_id,
                'test_type': lab_result.test_type,
                'facility_id': lab_result.facility_id
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating lab result message: {str(e)}")
        return {}


def create_prescription_message(patient_data: Dict[str, Any], prescription_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create OpenHIM message for prescriptions"""
    try:
        # Create FHIR resources
        patient = HealthcarePatient(
            patient_id=patient_data.get('patient_id', ''),
            first_name=patient_data.get('first_name', ''),
            last_name=patient_data.get('last_name', ''),
            date_of_birth=patient_data.get('date_of_birth', ''),
            gender=patient_data.get('gender', 'unknown'),
            phone_number=patient_data.get('phone_number')
        )
        
        prescription = Prescription(
            prescription_id=prescription_data.get('prescription_id', ''),
            patient_id=patient_data.get('patient_id', ''),
            medication_name=prescription_data.get('medication_name', ''),
            dosage=prescription_data.get('dosage', ''),
            frequency=prescription_data.get('frequency', ''),
            duration=prescription_data.get('duration', ''),
            prescriber_id=prescription_data.get('prescriber_id', ''),
            instructions=prescription_data.get('instructions'),
            pharmacy_id=prescription_data.get('pharmacy_id')
        )
        
        # Create FHIR Bundle
        resources = [
            create_patient_fhir_resource(patient),
            create_prescription_fhir_resource(prescription)
        ]
        
        return {
            'fhir_bundle': {
                'resourceType': 'Bundle',
                'type': 'transaction',
                'entry': [
                    {'resource': resource, 'request': {'method': 'POST', 'url': resource['resourceType']}}
                    for resource in resources
                ]
            },
            'metadata': {
                'message_type': 'Prescription',
                'patient_id': patient.patient_id,
                'medication': prescription.medication_name,
                'prescriber_id': prescription.prescriber_id
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating prescription message: {str(e)}")
        return {}