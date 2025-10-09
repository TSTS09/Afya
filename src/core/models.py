#!/usr/bin/env python3
"""
Core Models for Healthcare Transmission System
==============================================

Data models and enums for healthcare data transmission,
OpenHIM message format, and system state management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid


class DataType(Enum):
    """Healthcare data types for message classification"""
    LAB_RESULT = "lab_result"
    LAB_HIV_RESULT = "lab_hiv_result"
    PRESCRIPTION = "prescription" 
    PATIENT_REGISTRATION = "patient_registration"
    EMERGENCY = "emergency"
    GENERAL = "general"


class TransmissionProtocol(Enum):
    """Available transmission protocols"""
    HTTP = "http"
    HTTPS = "https"
    SMS = "sms"
    USSD = "ussd"


class NetworkCondition(Enum):
    """Network condition classifications"""
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    OFFLINE = "offline"


class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class NetworkStatus:
    """Network status information"""
    bandwidth: float  # Mbps
    latency: float    # milliseconds
    packet_loss: float  # percentage
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_condition(self) -> NetworkCondition:
        """Determine network condition based on metrics"""
        if self.bandwidth <= 0 or self.packet_loss >= 50:
            return NetworkCondition.OFFLINE
        elif self.bandwidth >= 10 and self.latency <= 100 and self.packet_loss <= 1:
            return NetworkCondition.EXCELLENT
        elif self.bandwidth >= 2 and self.latency <= 300 and self.packet_loss <= 5:
            return NetworkCondition.GOOD
        else:
            return NetworkCondition.POOR


@dataclass
class OpenHIMMessage:
    """OpenHIM-compliant message structure"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = ""
    destination: str = ""
    message_type: str = ""
    data_type: DataType = DataType.GENERAL
    priority: int = 3  # 1=critical, 2=high, 3=normal, 4=low
    client_id: str = ""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: Optional[str] = None
    facility_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'messageId': self.message_id,
            'timestamp': self.timestamp,
            'source': self.source,
            'destination': self.destination,
            'messageType': self.message_type,
            'dataType': self.data_type.value,
            'priority': self.priority,
            'clientId': self.client_id,
            'transactionId': self.transaction_id,
            'patientId': self.patient_id,
            'facilityId': self.facility_id,
            'payload': self.payload
        }


@dataclass
class TransmissionResult:
    """Result of message transmission attempt"""
    success: bool
    status: MessageStatus
    protocol_used: TransmissionProtocol
    message_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    retry_count: int = 0
    response_data: Optional[Dict[str, Any]] = None


@dataclass
class HealthcarePatient:
    """Patient information structure"""
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    national_id: Optional[str] = None
    
    def to_fhir_dict(self) -> Dict[str, Any]:
        """Convert to FHIR Patient resource format"""
        return {
            'resourceType': 'Patient',
            'id': self.patient_id,
            'name': [{
                'use': 'official',
                'given': [self.first_name],
                'family': self.last_name
            }],
            'birthDate': self.date_of_birth,
            'gender': self.gender.lower(),
            'telecom': [
                {'system': 'phone', 'value': self.phone_number}
            ] if self.phone_number else [],
            'address': [{
                'text': self.address
            }] if self.address else []
        }


@dataclass
class LabResult:
    """Laboratory test result structure"""
    test_id: str
    patient_id: str
    test_type: str
    test_name: str
    result_value: str
    reference_range: Optional[str] = None
    units: Optional[str] = None
    status: str = "final"
    performed_date: str = field(default_factory=lambda: datetime.now().isoformat())
    facility_id: Optional[str] = None
    
    def to_fhir_dict(self) -> Dict[str, Any]:
        """Convert to FHIR Observation resource format"""
        return {
            'resourceType': 'Observation',
            'id': self.test_id,
            'status': self.status,
            'code': {
                'coding': [{
                    'display': self.test_name
                }]
            },
            'subject': {
                'reference': f'Patient/{self.patient_id}'
            },
            'valueString': self.result_value,
            'effectiveDateTime': self.performed_date,
            'performer': [{
                'reference': f'Organization/{self.facility_id}'
            }] if self.facility_id else []
        }


@dataclass
class Prescription:
    """Prescription information structure"""
    prescription_id: str
    patient_id: str
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    prescriber_id: str
    prescribed_date: str = field(default_factory=lambda: datetime.now().isoformat())
    instructions: Optional[str] = None
    pharmacy_id: Optional[str] = None
    
    def to_fhir_dict(self) -> Dict[str, Any]:
        """Convert to FHIR MedicationRequest resource format"""
        return {
            'resourceType': 'MedicationRequest',
            'id': self.prescription_id,
            'status': 'active',
            'intent': 'order',
            'medicationCodeableConcept': {
                'text': self.medication_name
            },
            'subject': {
                'reference': f'Patient/{self.patient_id}'
            },
            'requester': {
                'reference': f'Practitioner/{self.prescriber_id}'
            },
            'dosageInstruction': [{
                'text': f'{self.dosage} {self.frequency} for {self.duration}',
                'additionalInstruction': [{
                    'text': self.instructions
                }] if self.instructions else []
            }],
            'authoredOn': self.prescribed_date
        }


@dataclass
class SMSFragment:
    """SMS message fragment for large messages"""
    fragment_id: str
    message_id: str
    part_number: int
    total_parts: int
    content: str
    phone_number: str
    
    def get_sms_text(self) -> str:
        """Get formatted SMS text with fragment information"""
        if self.total_parts > 1:
            return f"({self.part_number}/{self.total_parts}) {self.content}"
        return self.content


@dataclass
class FacilityInfo:
    """Healthcare facility information"""
    facility_id: str
    name: str
    type: str  # hospital, clinic, pharmacy, lab
    location: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    network_capabilities: Dict[str, bool] = field(default_factory=dict)
    
    def supports_protocol(self, protocol: TransmissionProtocol) -> bool:
        """Check if facility supports a transmission protocol"""
        return self.network_capabilities.get(protocol.value, False)