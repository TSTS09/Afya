"""
OpenHIM Message Format Adapter
=============================

Handles OpenHIM (Open Health Information Mediator) message format
compliance for healthcare interoperability standards.

This module provides utilities to:
- Convert between internal message formats and OpenHIM standards
- Validate OpenHIM message structure
- Handle FHIR resource integration
- Manage healthcare-specific routing and metadata
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class OpenHIMStatus(Enum):
    """OpenHIM transaction status values"""
    PROCESSING = "Processing"
    SUCCESSFUL = "Successful" 
    COMPLETED = "Completed"
    COMPLETED_WITH_ERRORS = "Completed with errors"
    FAILED = "Failed"


class FHIRResourceType(Enum):
    """Common FHIR resource types for healthcare data"""
    PATIENT = "Patient"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    MEDICATION_REQUEST = "MedicationRequest"
    ENCOUNTER = "Encounter"
    PRACTITIONER = "Practitioner"
    ORGANIZATION = "Organization"
    BUNDLE = "Bundle"


@dataclass
class OpenHIMRequest:
    """OpenHIM request structure"""
    path: str
    headers: Dict[str, str]
    querystring: str = ""
    body: str = ""
    method: str = "POST"
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class OpenHIMResponse:
    """OpenHIM response structure"""
    status: int
    headers: Dict[str, str]
    body: str = ""
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class OpenHIMOrchestration:
    """OpenHIM orchestration structure for mediator responses"""
    name: str
    request: OpenHIMRequest
    response: OpenHIMResponse
    error: Optional[str] = None


@dataclass
class OpenHIMTransaction:
    """Complete OpenHIM transaction structure"""
    _id: str
    client_id: str
    channel_id: str
    request: OpenHIMRequest
    response: OpenHIMResponse
    status: OpenHIMStatus
    orchestrations: List[OpenHIMOrchestration]
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class OpenHIMMessageAdapter:
    """
    Adapter for converting healthcare messages to/from OpenHIM format
    """
    
    def __init__(self, client_id: str, default_channel: str = "healthcare-channel"):
        self.client_id = client_id
        self.default_channel = default_channel
    
    def create_openhim_transaction(
        self,
        message_data: Dict[str, Any],
        endpoint: str,
        method: str = "POST",
        channel_id: str = None
    ) -> OpenHIMTransaction:
        """
        Create OpenHIM transaction from healthcare message data
        """
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create request
        request = OpenHIMRequest(
            path=endpoint,
            method=method,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Custom {self.client_id}",
                "X-OpenHIM-TransactionID": transaction_id
            },
            body=json.dumps(message_data),
            timestamp=timestamp
        )
        
        # Create initial response (will be updated by mediator)
        response = OpenHIMResponse(
            status=202,  # Accepted
            headers={"Content-Type": "application/json"},
            body=json.dumps({"status": "accepted", "transaction_id": transaction_id}),
            timestamp=timestamp
        )
        
        # Create transaction
        transaction = OpenHIMTransaction(
            _id=transaction_id,
            client_id=self.client_id,
            channel_id=channel_id or self.default_channel,
            request=request,
            response=response,
            status=OpenHIMStatus.PROCESSING,
            orchestrations=[]
        )
        
        return transaction
    
    def create_fhir_bundle(
        self,
        resources: List[Dict[str, Any]],
        bundle_type: str = "transaction"
    ) -> Dict[str, Any]:
        """
        Create FHIR Bundle from list of resources
        """
        bundle_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        entries = []
        for resource in resources:
            entry = {
                "resource": resource,
                "request": {
                    "method": "POST",
                    "url": resource.get("resourceType", "Unknown")
                }
            }
            entries.append(entry)
        
        bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "lastUpdated": timestamp,
                "source": f"afya-system#{self.client_id}"
            },
            "identifier": {
                "system": "https://afya.health.gh/bundle-id",
                "value": bundle_id
            },
            "type": bundle_type,
            "timestamp": timestamp,
            "total": len(entries),
            "entry": entries
        }
        
        return bundle
    
    def create_patient_resource(
        self,
        patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create FHIR Patient resource from patient data
        """
        patient_id = patient_data.get('id', str(uuid.uuid4()))
        
        # Build name
        name = []
        if patient_data.get('name'):
            name_parts = patient_data['name'].split()
            name_entry = {
                "use": "official",
                "family": name_parts[-1] if name_parts else "",
                "given": name_parts[:-1] if len(name_parts) > 1 else name_parts
            }
            name.append(name_entry)
        
        # Build contact info
        telecom = []
        if patient_data.get('phone'):
            telecom.append({
                "system": "phone",
                "value": patient_data['phone'],
                "use": "mobile"
            })
        
        # Build address
        address = []
        if patient_data.get('address'):
            address.append({
                "use": "home",
                "text": patient_data['address'],
                "country": "GH"  # Ghana
            })
        
        patient_resource = {
            "resourceType": "Patient",
            "id": patient_id,
            "meta": {
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
                "source": f"afya-system#{self.client_id}"
            },
            "identifier": [
                {
                    "system": "https://afya.health.gh/patient-id",
                    "value": patient_id
                }
            ],
            "active": True,
            "name": name,
            "telecom": telecom,
            "gender": patient_data.get('gender', 'unknown'),
            "birthDate": patient_data.get('birth_date'),
            "address": address
        }
        
        # Add Ghana-specific extensions
        if patient_data.get('ghana_card_number'):
            patient_resource["identifier"].append({
                "system": "https://nia.gov.gh/ghana-card",
                "value": patient_data['ghana_card_number']
            })
        
        return patient_resource
    
    def create_observation_resource(
        self,
        observation_data: Dict[str, Any],
        patient_id: str
    ) -> Dict[str, Any]:
        """
        Create FHIR Observation resource (for vitals, lab results, etc.)
        """
        observation_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Map common observation types to LOINC codes
        loinc_mappings = {
            'blood_pressure': '85354-9',
            'heart_rate': '8867-4',
            'temperature': '8310-5',
            'weight': '29463-7',
            'height': '8302-2',
            'blood_glucose': '33747-0',
            'hiv_test': '25835-0'
        }
        
        observation_type = observation_data.get('type', 'unknown')
        loinc_code = loinc_mappings.get(observation_type, '85354-9')
        
        observation = {
            "resourceType": "Observation",
            "id": observation_id,
            "meta": {
                "lastUpdated": timestamp,
                "source": f"afya-system#{self.client_id}"
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": loinc_code,
                        "display": observation_data.get('display_name', observation_type)
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": observation_data.get('timestamp', timestamp),
            "valueQuantity": {
                "value": observation_data.get('value'),
                "unit": observation_data.get('unit', ''),
                "system": "http://unitsofmeasure.org"
            }
        }
        
        # Add reference range if provided
        if observation_data.get('reference_range'):
            observation["referenceRange"] = [
                {
                    "low": {
                        "value": observation_data['reference_range'].get('low'),
                        "unit": observation_data.get('unit', '')
                    },
                    "high": {
                        "value": observation_data['reference_range'].get('high'),
                        "unit": observation_data.get('unit', '')
                    }
                }
            ]
        
        return observation
    
    def create_diagnostic_report_resource(
        self,
        report_data: Dict[str, Any],
        patient_id: str,
        observations: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create FHIR DiagnosticReport resource for lab results
        """
        report_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        diagnostic_report = {
            "resourceType": "DiagnosticReport",
            "id": report_id,
            "meta": {
                "lastUpdated": timestamp,
                "source": f"afya-system#{self.client_id}"
            },
            "identifier": [
                {
                    "system": "https://afya.health.gh/diagnostic-report-id",
                    "value": report_id
                }
            ],
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                            "code": "LAB",
                            "display": "Laboratory"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": report_data.get('loinc_code', '11502-2'),
                        "display": report_data.get('test_name', 'Laboratory report')
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": report_data.get('test_date', timestamp),
            "issued": timestamp,
            "conclusion": report_data.get('conclusion', '')
        }
        
        # Add observation references
        if observations:
            diagnostic_report["result"] = [
                {"reference": f"Observation/{obs_id}"} for obs_id in observations
            ]
        
        return diagnostic_report
    
    def create_medication_request_resource(
        self,
        prescription_data: Dict[str, Any],
        patient_id: str,
        practitioner_id: str = None
    ) -> Dict[str, Any]:
        """
        Create FHIR MedicationRequest resource for prescriptions
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        medication_request = {
            "resourceType": "MedicationRequest",
            "id": request_id,
            "meta": {
                "lastUpdated": timestamp,
                "source": f"afya-system#{self.client_id}"
            },
            "identifier": [
                {
                    "system": "https://afya.health.gh/prescription-id",
                    "value": request_id
                }
            ],
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.whocc.no/atc",
                        "code": prescription_data.get('atc_code', ''),
                        "display": prescription_data.get('medication_name', '')
                    }
                ],
                "text": prescription_data.get('medication_name', '')
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "authoredOn": timestamp,
            "dosageInstruction": [
                {
                    "text": prescription_data.get('dosage_instructions', ''),
                    "timing": {
                        "repeat": {
                            "frequency": prescription_data.get('frequency', 1),
                            "period": 1,
                            "periodUnit": "d"
                        }
                    },
                    "doseAndRate": [
                        {
                            "doseQuantity": {
                                "value": prescription_data.get('dose_value', 1),
                                "unit": prescription_data.get('dose_unit', 'tablet'),
                                "system": "http://unitsofmeasure.org"
                            }
                        }
                    ]
                }
            ]
        }
        
        # Add practitioner reference if provided
        if practitioner_id:
            medication_request["requester"] = {
                "reference": f"Practitioner/{practitioner_id}"
            }
        
        # Add dispense request
        if prescription_data.get('quantity'):
            medication_request["dispenseRequest"] = {
                "quantity": {
                    "value": prescription_data['quantity'],
                    "unit": prescription_data.get('quantity_unit', 'tablet'),
                    "system": "http://unitsofmeasure.org"
                }
            }
        
        return medication_request
    
    def add_orchestration(
        self,
        transaction: OpenHIMTransaction,
        name: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        status_code: int = 200,
        error: str = None
    ):
        """
        Add orchestration step to OpenHIM transaction
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        orchestration = OpenHIMOrchestration(
            name=name,
            request=OpenHIMRequest(
                path=f"/mediator/{name}",
                headers={"Content-Type": "application/json"},
                body=json.dumps(request_data),
                timestamp=timestamp
            ),
            response=OpenHIMResponse(
                status=status_code,
                headers={"Content-Type": "application/json"},
                body=json.dumps(response_data),
                timestamp=timestamp
            ),
            error=error
        )
        
        transaction.orchestrations.append(orchestration)
    
    def update_transaction_status(
        self,
        transaction: OpenHIMTransaction,
        status: OpenHIMStatus,
        response_data: Dict[str, Any] = None
    ):
        """
        Update transaction status and response
        """
        transaction.status = status
        
        if response_data:
            transaction.response.body = json.dumps(response_data)
            transaction.response.timestamp = datetime.now(timezone.utc).isoformat()
    
    def validate_openhim_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Validate OpenHIM transaction structure
        """
        required_fields = ['_id', 'clientID', 'channelID', 'request', 'response', 'status']
        
        for field in required_fields:
            if field not in transaction_data:
                return False
        
        # Validate request structure
        request = transaction_data.get('request', {})
        if not all(key in request for key in ['path', 'headers', 'method']):
            return False
        
        # Validate response structure
        response = transaction_data.get('response', {})
        if not all(key in response for key in ['status', 'headers']):
            return False
        
        return True
    
    def serialize_transaction(self, transaction: OpenHIMTransaction) -> str:
        """
        Serialize OpenHIM transaction to JSON string
        """
        # Convert dataclasses to dictionaries
        transaction_dict = {
            '_id': transaction._id,
            'clientID': transaction.client_id,
            'channelID': transaction.channel_id,
            'request': asdict(transaction.request),
            'response': asdict(transaction.response),
            'status': transaction.status.value,
            'orchestrations': [asdict(orch) for orch in transaction.orchestrations],
            'properties': transaction.properties
        }
        
        return json.dumps(transaction_dict, indent=2)


# Example usage functions
def create_lab_result_message(patient_data: Dict, lab_data: Dict) -> Dict[str, Any]:
    """
    Example function to create a complete lab result message in OpenHIM format
    """
    adapter = OpenHIMMessageAdapter("afya_client", "lab-results-channel")
    
    # Create FHIR resources
    patient = adapter.create_patient_resource(patient_data)
    
    observations = []
    for test in lab_data.get('tests', []):
        observation = adapter.create_observation_resource(test, patient['id'])
        observations.append(observation)
    
    diagnostic_report = adapter.create_diagnostic_report_resource(
        lab_data,
        patient['id'],
        [obs['id'] for obs in observations]
    )
    
    # Create FHIR bundle
    resources = [patient] + observations + [diagnostic_report]
    bundle = adapter.create_fhir_bundle(resources, "transaction")
    
    # Create OpenHIM transaction
    transaction = adapter.create_openhim_transaction(
        bundle,
        "/fhir/Bundle",
        channel_id="lab-results-channel"
    )
    
    return json.loads(adapter.serialize_transaction(transaction))


def create_prescription_message(patient_data: Dict, prescription_data: Dict) -> Dict[str, Any]:
    """
    Example function to create a prescription message in OpenHIM format
    """
    adapter = OpenHIMMessageAdapter("afya_client", "prescription-channel")
    
    # Create FHIR resources
    patient = adapter.create_patient_resource(patient_data)
    medication_request = adapter.create_medication_request_resource(
        prescription_data,
        patient['id']
    )
    
    # Create FHIR bundle
    bundle = adapter.create_fhir_bundle([patient, medication_request], "transaction")
    
    # Create OpenHIM transaction
    transaction = adapter.create_openhim_transaction(
        bundle,
        "/fhir/Bundle",
        channel_id="prescription-channel"
    )
    
    return json.loads(adapter.serialize_transaction(transaction))


if __name__ == "__main__":
    # Example usage
    
    # Sample patient data
    patient_data = {
        'id': 'patient_123',
        'name': 'Kwame Asante',
        'phone': '0200123456',
        'ghana_card_number': 'GHA-123456789-0',
        'gender': 'male',
        'birth_date': '1985-03-15',
        'address': 'Accra, Greater Accra Region, Ghana'
    }
    
    # Sample lab result data
    lab_data = {
        'test_name': 'Complete Blood Count',
        'loinc_code': '58410-2',
        'test_date': '2024-01-15T10:30:00Z',
        'conclusion': 'Normal results within reference ranges',
        'tests': [
            {
                'type': 'blood_glucose',
                'display_name': 'Blood Glucose',
                'value': 95,
                'unit': 'mg/dL',
                'reference_range': {'low': 70, 'high': 100},
                'timestamp': '2024-01-15T10:30:00Z'
            }
        ]
    }
    
    # Create lab result message
    lab_message = create_lab_result_message(patient_data, lab_data)
    print("Lab Result OpenHIM Message:")
    print(json.dumps(lab_message, indent=2)[:500] + "...")
    
    # Sample prescription data
    prescription_data = {
        'medication_name': 'Paracetamol 500mg',
        'atc_code': 'N02BE01',
        'dosage_instructions': 'Take 1 tablet every 6 hours as needed for pain',
        'frequency': 4,
        'dose_value': 1,
        'dose_unit': 'tablet',
        'quantity': 20,
        'quantity_unit': 'tablet'
    }
    
    # Create prescription message
    prescription_message = create_prescription_message(patient_data, prescription_data)
    print("\nPrescription OpenHIM Message:")
    print(json.dumps(prescription_message, indent=2)[:500] + "...")