#!/usr/bin/env python3
"""
SMS Webhook Server for Healthcare Message Queue
Provides HTTP endpoints for SMS gateway integration with healthcare message system.
Handles incoming webhooks, message validation, and integration with PostgreSQL queue.
"""
import json
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import os
import sys

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sms_gateway_adapter import SMSGatewayAdapter
except ImportError:
    print("Error: Cannot import SMS Gateway Adapter")
    print("Make sure sms_gateway_adapter.py is in the same directory")
    sys.exit(1)

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'afya_prototype',
    'user': 'postgres',
    'password': 'your_password'
}

GATEWAY_CONFIG = {
    'api_key': 'your_sms_gateway_api_key',
    'send_url': 'https://api.smsgateway.com/v1/messages/send',
    'webhook_url': 'https://your-server.com/sms/webhook',
    'sender_id': 'HealthSys'
}

# Flask app setup
app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sms_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global SMS adapter instance
sms_adapter = None


def initialize_sms_adapter():
    """Initializes SMS gateway adapter with database connection.
    
    Creates SMSGatewayAdapter instance, establishes database connectivity,
    and configures encryption for healthcare data processing.
    
    Returns:
        bool: True if adapter initialization succeeds, False otherwise.
    """
    global sms_adapter
    try:
        sms_adapter = SMSGatewayAdapter(
            db_config=DB_CONFIG,
            gateway_config=GATEWAY_CONFIG,
            encryption_password='healthcare_encryption_key_2025'
        )
        sms_adapter.connect_to_db()
        logger.info("SMS Gateway Adapter initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize SMS adapter: {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Provides service health status endpoint.
    
    Returns basic service information and timestamp for monitoring
    and load balancer health check integration.
    
    Returns:
        JSON response with service status and timestamp.
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'SMS Webhook Server'
    })


@app.route('/sms/webhook', methods=['POST'])
def sms_webhook():
    """Handles incoming SMS webhooks from gateway providers.
    
    Validates webhook payload, processes SMS content through healthcare
    classification system, and queues messages for delivery. Supports
    both structured JSON and plain text SMS formats.
    
    Returns:
        JSON response indicating processing success or failure with details.
    """
    try:
        # Log incoming request for audit trail
        logger.info(f"Received SMS webhook: {request.remote_addr}")
        
        # Extract webhook data from request payload
        webhook_data = request.get_json()
        if not webhook_data:
            logger.warning("No JSON data in webhook request")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        logger.info(f"Webhook payload: {webhook_data}")
        
        # Validate required fields
        required_fields = ['from', 'to', 'text']
        missing_fields = [field for field in required_fields 
                         if field not in webhook_data]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Process SMS asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                sms_adapter.receive_sms_webhook(webhook_data)
            )
            
            if success:
                logger.info("SMS processed successfully")
                return jsonify({
                    'status': 'success',
                    'message': 'SMS processed and queued',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                logger.error("Failed to process SMS")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to process SMS'
                }), 500
                
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error in SMS webhook: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }), 500


@app.route('/sms/send', methods=['POST'])
def send_sms():
    """Provides manual SMS sending endpoint for testing and integration.
    
    Accepts SMS message data and processes through the same pipeline
    as webhook-received messages for testing and manual message injection.
    
    Returns:
        JSON response indicating whether SMS was successfully queued.
    """
    try:
        data = request.get_json()
        
        required_fields = ['to', 'message', 'data_type']
        missing_fields = [field for field in required_fields 
                         if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # I create a mock webhook payload for sending
        webhook_data = {
            'from': 'SYSTEM',
            'to': data['to'],
            'text': data['message'],
            'data_type': data['data_type'],
            'facility_id': data.get('facility_id'),
            'patient_id': data.get('patient_id')
        }
        
        # Process through the same pipeline
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                sms_adapter.receive_sms_webhook(webhook_data)
            )
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'SMS queued for delivery'
                })
            else:
                return jsonify({
                    'status': 'error', 
                    'message': 'Failed to queue SMS'
                }), 500
                
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/sms/status', methods=['GET'])
def sms_status():
    """Retrieves SMS system operational status and statistics.
    
    Queries message queue database for current SMS processing metrics
    including waiting message counts and priority distribution.
    
    Returns:
        JSON response with system status and operational statistics.
    """
    try:
        # I query message queue for SMS statistics
        with sms_adapter.connection.cursor() as cur:
            # Get waiting SMS messages
            cur.execute("""
                SELECT 
                    COUNT(*) as waiting_count,
                    COUNT(CASE WHEN priority = 1 THEN 1 END) as critical_count,
                    COUNT(CASE WHEN priority = 2 THEN 1 END) as high_count
                FROM mq.message_waiting mw
                JOIN mq.message m ON m.message_id = mw.message_id
                JOIN mq.queue q ON q.queue_id = mw.queue_id
                WHERE q.queue_name LIKE '%SMS%' OR m.headers->'protocol' = 'sms'
            """)
            
            stats = cur.fetchone()
            
            return jsonify({
                'status': 'operational',
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'waiting_messages': stats[0] if stats else 0,
                    'critical_messages': stats[1] if stats else 0,
                    'high_priority_messages': stats[2] if stats else 0
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting SMS status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/sms/test', methods=['POST'])
def test_sms_flow():
    """Executes comprehensive SMS flow testing with sample healthcare data.
    
    Processes predefined healthcare SMS messages through complete pipeline
    including HIV results, prescriptions, and lab data for system validation.
    
    Returns:
        JSON response with test results and processing status for each message.
    """
    try:
        # I use sample healthcare SMS messages for testing
        test_messages = [
            {
                'from': '+233201234567',
                'to': '+233501234568', 
                'text': json.dumps({
                    'patient_id': 'P001',
                    'facility_id': 'FACILITY_001',
                    'data_type': 'hiv',
                    'result': 'CD4 count: 450 cells/μL',
                    'status': 'CRITICAL'
                })
            },
            {
                'from': '+233301234569',
                'to': '+233201234567',
                'text': 'PRESCRIPTION: Patient ID P002 - Paracetamol 500mg, 3x daily for 5 days. Facility: FACILITY_003'
            },
            {
                'from': '+233501234568',
                'to': '+233201234567',
                'text': 'LAB RESULTS: Glucose: 95mg/dL, Cholesterol: 180mg/dL - Patient P003'
            }
        ]
        
        results = []
        
        for msg in test_messages:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                success = loop.run_until_complete(
                    sms_adapter.receive_sms_webhook(msg)
                )
                results.append({
                    'message': msg['text'][:50] + '...',
                    'success': success
                })
            finally:
                loop.close()
        
        return jsonify({
            'status': 'test_complete',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in SMS test: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # I initialize SMS adapter
    if not initialize_sms_adapter():
        logger.error("Failed to initialize SMS adapter. Exiting.")
        sys.exit(1)
    
    logger.info("Starting SMS Webhook Server...")
    logger.info("Available endpoints:")
    logger.info("  POST /sms/webhook - Receive SMS from gateway")
    logger.info("  POST /sms/send - Send SMS (testing)")
    logger.info("  GET  /sms/status - Get system status")
    logger.info("  POST /sms/test - Test SMS flow")
    logger.info("  GET  /health - Health check")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Set to True for development
        threaded=True
    )