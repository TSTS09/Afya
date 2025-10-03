# SMS Gateway Integration for Healthcare Message Queue

## Overview

This SMS gateway integration adds secure SMS packet collection, queuing, and forwarding capabilities to your healthcare message queue system. It's designed specifically for African healthcare infrastructure with intermittent connectivity and the need for secure patient data transmission.

## Architecture

```
SMS Gateway → Webhook Server → Message Queue → Protocol Selection → Delivery
     ↓              ↓               ↓                ↓              ↓
  External      Encryption     Priority Queue   Network Aware   SMS/HTTP/LoRaWAN
  SMS API       Validation     Health Rules     Selection       Delivery
```

## Key Features

### 🏥 Healthcare-Specific
- **Automatic Priority Assignment**: HIV results = Priority 1, Prescriptions = Priority 2, etc.
- **Medical Data Encryption**: Sensitive data automatically encrypted
- **Facility Mapping**: Phone numbers mapped to healthcare facilities
- **TTL Management**: Time limits based on medical urgency (HIV: 1hr, Labs: 24hr)

### 📱 SMS Intelligence
- **Protocol Selection**: Automatic SMS/HTTP/LoRaWAN selection based on network
- **Message Fragmentation**: Large messages split for SMS/USSD constraints
- **Store-and-Forward**: Messages queued during network outages
- **Retry Logic**: Exponential backoff with priority-aware timing

### 🔒 Security
- **End-to-End Encryption**: Sensitive medical data encrypted in transit
- **Facility Authentication**: Phone number to facility ID mapping
- **Webhook Validation**: Secure webhook endpoint with authentication
- **Audit Trails**: Complete message tracking and logging

## Installation

### 1. Prerequisites
```bash
# Python 3.8+ required
python --version

# PostgreSQL with message queue schema
# (Run your existing database initialization first)
```

### 2. Install SMS Gateway Components
```bash
# Navigate to Message Queue directory
cd "Message Queue and DTN"

# Run setup script
python setup_sms_gateway.py
```

### 3. Configure SMS Gateway
Edit `sms_config.py`:

```python
# Update database connection
DATABASE = {
    'host': 'localhost',
    'database': 'afya_prototype',
    'user': 'postgres', 
    'password': 'your_actual_password'
}

# Configure your SMS gateway (example for Africa's Talking)
AFRICAS_TALKING_CONFIG = {
    'api_key': 'your_actual_api_key',
    'username': 'your_username',
    'send_url': 'https://api.africastalking.com/version1/messaging',
    'sender_id': 'HealthSys'
}

# Use your SMS gateway
SMS_GATEWAY = AFRICAS_TALKING_CONFIG

# Set strong encryption password
ENCRYPTION = {
    'password': 'your_very_secure_password_here'
}

# Map facility phone numbers
FACILITY_MAPPING = {
    '+233201234567': 'ACCRA_GENERAL_001',
    '+233501234568': 'KUMASI_HEALTH_002',
    # Add your actual facility phone numbers
}
```

## Usage

### 1. Start SMS Gateway Services

**Windows:**
```batch
start_sms_gateway.bat
```

**Linux/Mac:**
```bash
./start_sms_gateway.sh
```

**Manual startup:**
```bash
# Terminal 1: Start webhook server
python sms_webhook_server.py

# Terminal 2: Start SMS gateway adapter  
python -c "import asyncio; from sms_gateway_adapter import main; asyncio.run(main())"
```

### 2. Configure SMS Gateway Webhook

Point your SMS gateway webhook to:
```
http://your-server.com:5000/sms/webhook
```

For production, use HTTPS:
```
https://your-domain.com/sms/webhook
```

### 3. Test SMS Integration

```bash
# Run comprehensive SMS tests
python test_sms_integration.py

# Test individual components
python -c "
import requests
response = requests.get('http://localhost:5000/health')
print(response.json())
"
```

## SMS Message Formats

### Structured JSON SMS
```json
{
  "patient_id": "P001",
  "facility_id": "FACILITY_001", 
  "data_type": "hiv",
  "result": "CD4 count: 450 cells/μL",
  "status": "CRITICAL"
}
```

### Plain Text SMS
```
PRESCRIPTION: Patient P002 - Amoxicillin 500mg, 3x daily, 7 days. Pharmacy: Central
```

### Lab Results SMS
```
LAB RESULTS: Patient P003 - Glucose: 95mg/dL, Cholesterol: 180mg/dL - Normal range
```

## Priority System

| Data Type | Priority | TTL | Auto-Encryption | Protocols |
|-----------|----------|-----|-----------------|-----------|
| HIV | 1 (Critical) | 1 hour | ✅ Yes | SMS, USSD |
| Prescription | 2 (High) | 4 hours | ✅ Yes | SMS, HTTP |
| Lab Results | 3 (Medium) | 24 hours | ✅ Yes | SMS, HTTP, Email |
| Appointment | 4 (Low) | 72 hours | ❌ No | SMS, Email |
| Insurance | 5 (Routine) | 7 days | ❌ No | SMS, Email, HTTP |

## API Endpoints

### Webhook Endpoints
- `POST /sms/webhook` - Receive SMS from gateway
- `GET /health` - Health check
- `GET /sms/status` - System status and statistics

### Testing Endpoints  
- `POST /sms/send` - Send test SMS
- `POST /sms/test` - Run test message flow

## Network Intelligence

The system automatically selects the best protocol based on network conditions:

```python
# Network conditions → Protocol selection
'offline'     → 'store_and_forward'  # Queue until online
'2G/EDGE'     → 'sms'               # Most reliable
'3G'          → 'http_compressed'    # Efficient
'4G/WiFi'     → 'https'             # Full features
'Rural'       → 'lorawan'           # Long range, low power
```

## Security Features

### Encryption
- Sensitive medical data automatically encrypted using Fernet (AES 128)
- PBKDF2 key derivation with 100,000 iterations
- Per-message encryption for patient data

### Authentication
- Webhook signature validation
- Facility-based phone number authentication
- IP whitelisting for SMS gateway

### Audit Trails
- Complete message flow logging
- Delivery confirmation tracking
- Failed message analysis

## Monitoring

### Real-time Status
```bash
curl http://localhost:5000/sms/status
```

### Queue Statistics
```sql
-- Check SMS queue status
SELECT * FROM mq.system_health WHERE queue_name LIKE '%SMS%';

-- Check protocol usage
SELECT * FROM mq.protocol_usage;
```

### Log Files
- `sms_gateway.log` - SMS adapter operations
- `sms_webhook.log` - Webhook server activity

## Production Deployment

### 1. Process Management
```bash
# Using systemd (Linux)
sudo systemctl enable sms-webhook
sudo systemctl enable sms-adapter

# Using supervisor (cross-platform)
supervisorctl start sms-gateway
```

### 2. Reverse Proxy (Nginx)
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location /sms/ {
        proxy_pass http://localhost:5000/sms/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. SSL Configuration
```bash
# Let's Encrypt certificate
certbot --nginx -d your-domain.com
```

## Troubleshooting

### Common Issues

**1. SMS Not Received**
```bash
# Check webhook server logs
tail -f sms_webhook.log

# Verify database connection
python -c "from sms_config import DATABASE; import psycopg2; psycopg2.connect(**DATABASE)"

# Test webhook endpoint
curl -X POST http://localhost:5000/sms/webhook \
  -H "Content-Type: application/json" \
  -d '{"from":"+233201234567","to":"+233501234568","text":"Test message"}'
```

**2. Database Connection Issues**
```bash
# Check PostgreSQL status
pg_isready -h localhost

# Verify schema exists
psql -d afya_prototype -c "SELECT * FROM mq.exchange LIMIT 1;"
```

**3. SMS Gateway API Issues**
```bash
# Test API credentials
python -c "
from sms_config import SMS_GATEWAY
import requests
print('API Key:', SMS_GATEWAY['api_key'][:10] + '...')
"
```

### Debug Mode
```bash
# Start webhook server in debug mode
FLASK_DEBUG=1 python sms_webhook_server.py

# Enable verbose logging
export LOG_LEVEL=DEBUG
```

## SMS Gateway Providers

### Africa's Talking
```python
AFRICAS_TALKING_CONFIG = {
    'api_key': 'your_api_key',
    'username': 'your_username', 
    'send_url': 'https://api.africastalking.com/version1/messaging',
    'sender_id': 'HealthSys'
}
```

### Twilio
```python
TWILIO_CONFIG = {
    'api_key': 'your_account_sid',
    'api_secret': 'your_auth_token',
    'send_url': 'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json',
    'sender_id': '+1234567890'
}
```

### Generic SMS Gateway
```python
GENERIC_SMS_CONFIG = {
    'api_key': 'your_api_key',
    'send_url': 'https://api.yourgateway.com/v1/sms/send',
    'sender_id': 'HealthSystem',
    'auth_header': 'Bearer'
}
```

## Performance

### Throughput
- **SMS Processing**: 60+ messages/minute
- **Queue Throughput**: 1000+ messages/hour  
- **Concurrent Consumers**: 5+ channels per queue

### Latency
- **SMS to Queue**: < 2 seconds
- **Priority 1 Delivery**: < 30 seconds
- **Normal Delivery**: < 5 minutes

## License

This SMS gateway integration is part of the Healthcare Message Queue system and follows the same license as the main project.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review log files for error details
3. Verify SMS gateway API credentials and limits
4. Test with the included test scripts

## Contributing

To extend the SMS gateway:
1. Add new SMS providers in `sms_config.py`
2. Implement provider-specific authentication in `sms_gateway_adapter.py`
3. Add tests in `test_sms_integration.py`
4. Update this documentation