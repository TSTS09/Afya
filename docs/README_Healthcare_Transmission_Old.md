# Healthcare Data Transmission System

A comprehensive, production-ready healthcare data transmission system designed for Ghana's healthcare infrastructure. This system replaces simple debug scripts with a robust solution that handles real healthcare data transmission across multiple protocols with OpenHIM compliance.

## Overview

This system is designed to address the challenges of healthcare data transmission in environments with varying network conditions, from high-speed urban internet to SMS-only rural areas. It provides intelligent protocol selection, healthcare data prioritization, and standards-compliant message formatting.

## Key Features

### 🏥 Healthcare-Focused Design
- **OpenHIM Integration**: Full compliance with OpenHIM (Open Health Information Mediator) standards
- **FHIR Resource Support**: Native support for FHIR Patient, Observation, DiagnosticReport, and MedicationRequest resources
- **Healthcare Data Prioritization**: Automatic prioritization based on medical urgency (Emergency > HIV Results > Prescriptions > Routine Labs)
- **Ghana-Specific Adaptations**: Support for Ghana Card numbers, local phone formats, and healthcare facility structures

### 🌐 Multi-Protocol Transmission
- **HTTP/HTTPS**: For high-bandwidth, reliable connections
- **SMS**: For low-bandwidth environments with message fragmentation support
- **SMS Multipart**: For larger messages that can be split across multiple SMS
- **USSD**: For interactive, session-based communication
- **Automatic Protocol Selection**: Based on real-time network conditions

### 🎯 Intelligent Message Routing
- **Network-Aware Protocol Selection**: Automatically chooses the best available protocol
- **Message Fragmentation**: Splits large messages for SMS transmission
- **Retry Mechanisms**: Exponential backoff with configurable retry limits
- **Dead Letter Handling**: Proper handling of failed messages after max retries

### 🔒 Security & Compliance
- **End-to-End Encryption**: Configurable encryption for sensitive healthcare data
- **Audit Logging**: Comprehensive logging for compliance and debugging
- **Data Type Validation**: Healthcare-specific validation rules
- **GDPR/Privacy Compliance**: Patient data protection measures

## Architecture

### Core Components

1. **HealthcareTransmissionSystem**: Main orchestrator handling message queuing and processing
2. **OpenHIMMessageAdapter**: Converts healthcare data to/from OpenHIM standard formats
3. **Protocol Adapters**: Specialized adapters for each transmission protocol (HTTP, SMS, USSD)
4. **Network Monitor**: Tracks network conditions for intelligent protocol selection
5. **Configuration Management**: Centralized configuration with environment variable support

### Database Schema

The system extends the existing PostgreSQL message queue with healthcare-specific tables:

- `mq.message_protocol`: Tracks preferred protocols for each message
- `mq.network_status`: Real-time network condition monitoring
- `mq.message_fragments`: Manages SMS message fragmentation
- `mq.health_data_rules`: Healthcare data type configurations

## Installation & Setup

### Prerequisites

```bash
# Python 3.8+
pip install psycopg2-binary aiohttp cryptography

# PostgreSQL 12+ with the existing message queue schema
# Run the SQL files in Message Queue and DTN/src/
```

### Configuration

1. **Environment Variables** (Recommended for production):

```bash
# Database
export DB_HOST=localhost
export DB_NAME=pg_mq_poc
export DB_USER=postgres
export DB_PASSWORD=your_password

# OpenHIM
export OPENHIM_URL=https://openhim.yourhealth.gov.gh
export OPENHIM_USER=afya_system@health.gov.gh
export OPENHIM_PASSWORD=your_openhim_password
export OPENHIM_CLIENT_ID=afya_ghana_client

# SMS (Example for Africa's Talking)
export SMS_PROVIDER=africas_talking
export SMS_API_KEY=your_africas_talking_api_key
export SMS_SENDER_ID=AFYA_GH
export AT_USERNAME=your_africas_talking_username

# Security
export ENCRYPTION_KEY=your_256_bit_encryption_key
export ENABLE_ENCRYPTION=true
```

2. **Configuration File** (Alternative):

```python
from transmission_config import HealthcareTransmissionConfig

config = HealthcareTransmissionConfig()
# Modify config as needed
```

## Usage Examples

### Basic Message Transmission

```python
import asyncio
from healthcare_transmission_system import HealthcareTransmissionSystem, OpenHIMMessage, DataType
from transmission_config import HealthcareTransmissionConfig

async def send_lab_result():
    # Initialize system
    config = HealthcareTransmissionConfig()
    system = HealthcareTransmissionSystem(
        config.database.to_dict(),
        config.get_protocol_configs()
    )
    await system.initialize()
    
    # Create healthcare message
    message = OpenHIMMessage(
        message_id="lab_12345",
        timestamp=datetime.now().isoformat(),
        source="clinic_001",
        destination="central_hie",
        message_type="LabResult",
        data_type=DataType.LAB_ROUTINE,
        priority=3,
        client_id="afya_client",
        transaction_id="txn_12345",
        patient_id="patient_001",
        payload={
            "test_type": "blood_glucose",
            "result": "95 mg/dL",
            "normal_range": "70-100 mg/dL",
            "status": "NORMAL"
        }
    )
    
    # Queue and process message
    await system.queue_message(message)
    await system.process_pending_messages()
    
    await system.shutdown()

# Run the example
asyncio.run(send_lab_result())
```

### Real Healthcare Data Processing

```python
from real_healthcare_transmission_example import run_comprehensive_example

# Run comprehensive example with real data
asyncio.run(run_comprehensive_example())
```

### Network Condition Simulation

```python
from healthcare_transmission_system import NetworkStatus, NetworkCondition

# Create network status for different facilities
urban_hospital = NetworkStatus(
    facility_id="urban_hospital_001",
    network_type="fiber",
    bandwidth_kbps=5000,
    latency_ms=20,
    packet_loss_percent=0.1,
    last_updated=datetime.now(),
    is_active=True
)

rural_clinic = NetworkStatus(
    facility_id="rural_clinic_002", 
    network_type="3g",
    bandwidth_kbps=128,
    latency_ms=300,
    packet_loss_percent=5.0,
    last_updated=datetime.now(),
    is_active=True
)

print(f"Urban hospital condition: {urban_hospital.get_condition()}")
print(f"Rural clinic condition: {rural_clinic.get_condition()}")
```

## Protocol Selection Logic

The system automatically selects the best protocol based on:

### Network Conditions
- **Excellent**: Bandwidth ≥1000 kbps, Latency ≤100ms, Packet Loss ≤1%
  - Uses: HTTPS, HTTP
- **Good**: Bandwidth ≥256 kbps, Latency ≤500ms, Packet Loss ≤5%
  - Uses: HTTPS, HTTP, SMS_MULTIPART
- **Poor**: Bandwidth ≥64 kbps, Packet Loss ≤15%
  - Uses: SMS_MULTIPART, SMS, USSD
- **SMS Only**: Limited or no internet connectivity
  - Uses: SMS, USSD

### Healthcare Data Priority
1. **Emergency** (Priority 1): Any protocol available, prefers fastest
2. **HIV/Critical Lab Results** (Priority 1): Secure protocols preferred
3. **Prescriptions** (Priority 2): Interactive protocols (USSD) suitable
4. **Routine Labs** (Priority 3): Can use multipart SMS for larger data
5. **Administrative** (Priority 5): HTTP only, non-urgent

## OpenHIM Integration

### FHIR Resource Creation

The system automatically creates FHIR-compliant resources:

```python
from openhim_adapter import OpenHIMMessageAdapter

adapter = OpenHIMMessageAdapter("afya_client")

# Create FHIR Patient resource
patient = adapter.create_patient_resource({
    'id': 'patient_123',
    'name': 'Kwame Asante',
    'phone': '0200123456',
    'ghana_card_number': 'GHA-123456789-0'
})

# Create FHIR Observation (lab result)
observation = adapter.create_observation_resource({
    'type': 'blood_glucose',
    'value': 95,
    'unit': 'mg/dL',
    'reference_range': {'low': 70, 'high': 100}
}, patient['id'])

# Create FHIR Bundle
bundle = adapter.create_fhir_bundle([patient, observation])
```

### OpenHIM Transaction Format

All messages are formatted as OpenHIM transactions:

```json
{
  "_id": "transaction_uuid",
  "clientID": "afya_client", 
  "channelID": "lab-results-channel",
  "request": {
    "path": "/fhir/Bundle",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": "FHIR Bundle JSON"
  },
  "response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"}, 
    "body": "Response JSON"
  },
  "status": "Successful",
  "orchestrations": [...]
}
```

## SMS Integration

### Supported SMS Providers
- **Africa's Talking**: Optimized for African markets
- **Twilio**: Global SMS service
- **Generic SMS Gateway**: Configurable for any REST API

### Message Fragmentation

Large messages are automatically fragmented for SMS:

```
[1/3] {"id":"lab_123","type":"glu","val":95,"unit":"mg/dL"}
[2/3] {"ref":{"low":70,"high":100},"ts":"2024-01-15T10:30Z"}  
[3/3] {"status":"NORMAL","facility":"clinic_001"}
```

### SMS Configuration

```python
# SMS configuration in transmission_config.py
sms_config = SMSConfig(
    provider="africas_talking",
    api_key="your_api_key",
    sender_id="AFYA_GH",
    max_message_length=160,
    enable_delivery_reports=True
)
```

## USSD Integration

### Interactive Health Services

USSD sessions provide interactive healthcare services:

```
*714# → Main Menu
1. Healthcare Provider
2. Patient Services  
3. Emergency
4. System Info

*714*1*1234# → Provider login with PIN
*714*2*1# → Patient view records
*714*3*1# → Emergency ambulance
```

### USSD Message Format

Health alerts via USSD are formatted for basic phone displays:

```
AFYA HEALTH ALERT
Type: PRESCRIPTION
From: clinic_001
Medication: Paracetamol 500mg
Reply *714*rx1234# for details
```

## Monitoring & Logging

### Health Checks

```python
# Check system health
system_status = await transmission_system.get_system_health()
print(f"Database: {system_status['database']}")
print(f"SMS Gateway: {system_status['sms_gateway']}")
print(f"OpenHIM: {system_status['openhim']}")
```

### Audit Logs

All healthcare data transmission is logged:

```
2024-01-15 10:30:00 - INFO - Queued lab result for patient_001
2024-01-15 10:30:05 - INFO - Selected HTTPS protocol for urban_hospital_001  
2024-01-15 10:30:10 - INFO - Successfully transmitted via HTTPS
2024-01-15 10:30:15 - INFO - Received acknowledgment from central_hie
```

### Performance Metrics

- Message throughput per protocol
- Average transmission time by network condition
- Retry rates and failure analysis
- Protocol selection efficiency

## Testing

### Run All Examples

```bash
python real_healthcare_transmission_example.py
```

### Unit Tests

```bash
python -m pytest tests/
```

### Integration Tests

```bash
python tests/test_full_workflow.py
```

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "real_healthcare_transmission_example.py"]
```

### Kubernetes Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthcare-transmission
spec:
  replicas: 3
  selector:
    matchLabels:
      app: healthcare-transmission
  template:
    metadata:
      labels:
        app: healthcare-transmission
    spec:
      containers:
      - name: transmission-system
        image: afya/healthcare-transmission:latest
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: host
```

### Scaling Considerations

- **Database Connection Pooling**: Use pgbouncer for PostgreSQL
- **Message Queue Partitioning**: Partition by facility or data type
- **Load Balancing**: Distribute across multiple instances
- **Caching**: Redis for frequently accessed data

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Verify connection string
   psql -h localhost -U postgres -d pg_mq_poc
   ```

2. **SMS Gateway Connection Failed**
   ```bash
   # Test SMS API
   curl -X POST https://api.africastalking.com/version1/messaging \
     -H "apiKey: your_api_key" \
     -d "username=your_username&to=+233200123456&message=Test"
   ```

3. **OpenHIM Integration Issues**
   ```bash
   # Check OpenHIM server status
   curl -k https://openhim.yourhealth.gov.gh:8080/heartbeat
   
   # Verify client authentication
   curl -k https://openhim.yourhealth.gov.gh:8080/clients \
     -H "Authorization: Custom afya_client"
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tuning

1. **Database Optimization**
   - Create indexes on frequently queried columns
   - Regular VACUUM and ANALYZE operations
   - Monitor connection pool usage

2. **Network Optimization**
   - Implement connection reuse for HTTP clients
   - Use compression for large messages
   - Cache network status to reduce database queries

3. **Message Processing**
   - Batch process multiple messages
   - Implement message priority queues
   - Use async processing for I/O operations

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-protocol`)
3. Commit changes (`git commit -am 'Add new protocol adapter'`)
4. Push to branch (`git push origin feature/new-protocol`)
5. Create Pull Request

### Development Setup

```bash
git clone https://github.com/your-org/healthcare-transmission
cd healthcare-transmission
pip install -r requirements-dev.txt
pre-commit install
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@afya.health.gh or create an issue in the GitHub repository.

## Roadmap

- [ ] Support for additional SMS providers (Nexmo, MessageBird)
- [ ] FHIR R5 compatibility
- [ ] Machine learning for protocol selection optimization
- [ ] Real-time dashboard for transmission monitoring
- [ ] Integration with WHO SMART Guidelines
- [ ] Support for telemedicine data transmission
- [ ] Blockchain integration for data integrity verification