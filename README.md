# Healthcare Data Transmission System

A modern, well-architected healthcare data transmission system with SMS API integration, OpenHIM compliance, and proper separation of concerns.

## Features

### Core Features
- **OpenHIM Integration**: Full compliance with Open Health Information Mediator standards
- **Multi-Protocol Support**: HTTP/HTTPS, SMS with fragmentation, USSD support
- **FHIR Compliance**: Native support for FHIR healthcare data formats
- **Smart Protocol Selection**: Network-condition based protocol selection
- **Message Queue System**: PostgreSQL-based reliable message queuing
- **Healthcare Data Prioritization**: Automatic priority assignment based on data type

### SMS Integration
- **Multiple Providers**: Support for Twilio, Africa's Talking, and extensible provider system
- **Message Fragmentation**: Automatic splitting of large messages for SMS transmission
- **Phone Number Validation**: Provider-specific validation
- **Delivery Tracking**: Comprehensive delivery status tracking

### Architecture
- **Clean Architecture**: Proper separation of concerns with adapters, services, and core models
- **Configuration Management**: Environment-based configuration with validation
- **Comprehensive Logging**: Healthcare-compliant logging with PII protection
- **Network Monitoring**: Real-time network condition assessment
- **Error Handling**: Robust error handling and retry mechanisms

## Project Structure

```
├── src/
│   ├── core/
│   │   ├── models.py          # Core data models and enums
│   │   └── factory.py         # Application factory
│   ├── services/
│   │   ├── database_service.py    # PostgreSQL message queue service
│   │   ├── sms_service.py         # SMS transmission service
│   │   └── transmission_service.py # Main orchestration service
│   ├── adapters/
│   │   └── openhim_adapter.py     # OpenHIM/FHIR integration
│   └── utils/
│       ├── logger.py              # Logging utilities
│       └── network_monitor.py     # Network monitoring
├── config/
│   ├── settings.py            # Configuration management
│   └── .env.example          # Environment configuration template
├── examples/
│   └── healthcare_transmission_demo.py  # Comprehensive example
├── docs/                     # Documentation
├── tests/                    # Test suite
└── requirements.txt          # Dependencies
```

## Quick Start

### 1. Setup Environment

```bash
# Clone/navigate to the project directory
cd "Data Transmission module"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
copy config\.env.example config\.env

# Edit config\.env with your settings:
# - Database credentials
# - SMS provider credentials (Twilio or Africa's Talking)
# - OpenHIM configuration
```

### 3. Basic Usage

```python
import asyncio
from src.core.factory import create_development_system
from src.core.models import OpenHIMMessage, DataType

async def main():
    # Create transmission system
    system = create_development_system()
    
    # Initialize
    await system.initialize()
    
    # Create a healthcare message
    message = OpenHIMMessage(
        source="facility_001",
        destination="central_hie",
        message_type="LabResult",
        data_type=DataType.LAB_RESULT,
        priority=2,
        patient_id="PAT001",
        payload={
            "test_type": "blood_glucose",
            "result": "95 mg/dL",
            "status": "normal"
        }
    )
    
    # Queue for transmission
    success = await system.queue_message(message)
    print(f"Message queued: {success}")
    
    # Process queue
    stats = await system.process_queue()
    print(f"Processing stats: {stats}")
    
    # Cleanup
    await system.close()

# Run
asyncio.run(main())
```

## SMS Configuration

### Twilio Setup
```bash
# In config/.env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
SMS_SENDER_NUMBER=+1234567890
```

### Africa's Talking Setup
```bash
# In config/.env
SMS_PROVIDER=africastalking
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key
```

## Database Setup

The system uses PostgreSQL with the existing pg_mq message queue system. Ensure your database is configured:

```sql
-- The system will automatically create these tables:
-- healthcare_transmissions (for tracking)
-- healthcare_facilities (for facility management)
```

## Examples

### Processing Lab Results
```python
from examples.healthcare_transmission_demo import HealthcareDataProcessor

# Lab result data
lab_data = {
    'patient': {
        'patient_id': 'PAT001',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone_number': '+254712345678'
    },
    'test': {
        'test_type': 'hiv_test',
        'result_value': 'NEGATIVE'
    },
    'facility_id': 'FAC001'
}

# Process
processor = HealthcareDataProcessor(transmission_system)
await processor.process_lab_result(lab_data)
```

### Emergency Alerts
```python
emergency_data = {
    'patient_id': 'PAT002',
    'emergency_type': 'cardiac_arrest',
    'severity': 'critical',
    'location': 'Emergency Room',
    'facility_id': 'HOSP001'
}

await processor.process_emergency_alert(emergency_data)
```

## Testing

```bash
# Run comprehensive demo
python examples\healthcare_transmission_demo.py

# Run tests (when test suite is complete)
python -m pytest tests/
```

## Production Deployment

### 1. Environment Configuration
```bash
# Set production environment
ENVIRONMENT=production
DEBUG=false

# Configure secure credentials
DB_PASSWORD=secure_password
OPENHIM_CLIENT_PASSWORD=secure_password
TWILIO_AUTH_TOKEN=your_production_token
```

### 2. Create Production System
```python
from src.core.factory import create_production_system

# This enforces all security validations
system = create_production_system()
```

## Architecture Benefits

### Compared to Previous Simple Script
The original `debug_retry.py` was a simple script with:
- Hardcoded database credentials
- No error handling
- Single protocol support
- No healthcare data structures

This new system provides:
- **Configuration Management**: Environment-based, no hardcoded values
- **Multiple Protocols**: HTTP/HTTPS, SMS, USSD with intelligent selection
- **Healthcare Standards**: OpenHIM/FHIR compliance
- **Robust Error Handling**: Retry mechanisms, comprehensive logging
- **Scalable Architecture**: Proper separation of concerns
- **SMS API Integration**: Real SMS transmission for low-bandwidth scenarios
- **Production Ready**: Security validation, monitoring, metrics

## Contributing

1. Follow the established architecture patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure PII protection in logging
5. Validate against healthcare standards (FHIR, OpenHIM)

## License

Internal healthcare system - see organization policies.