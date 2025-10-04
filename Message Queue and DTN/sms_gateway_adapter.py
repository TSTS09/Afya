#!/usr/bin/env python3
"""
SMS Gateway Adapter for Healthcare Data Transmission
Handles SMS packet collection, queuing, and secure forwarding across healthcare facilities.
Provides automatic medical data prioritization and network-aware protocol selection.
"""
import json
import hashlib
import base64
import time
import logging
import asyncio
import aiohttp
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class SMSMessage:
    """Represents an SMS message within the healthcare communication system.
    
    Contains all necessary metadata for healthcare-specific routing, prioritization,
    and security handling. Supports both structured JSON and plain text formats.
    """
    sender: str
    recipient: str
    content: str
    timestamp: datetime
    message_id: str
    data_type: Optional[str] = None
    facility_id: Optional[str] = None
    patient_id: Optional[str] = None
    priority: int = 5
    is_encrypted: bool = False


class SMSEncryption:
    """Provides encryption and decryption services for sensitive healthcare data.
    
    Implements Fernet symmetric encryption with PBKDF2 key derivation to ensure
    patient data confidentiality during SMS transmission between healthcare facilities.
    """
    
    def __init__(self, password: str):
        self.password = password.encode()
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """Derives encryption key from password using PBKDF2 key derivation function.
        
        Returns:
            bytes: Base64-encoded encryption key suitable for Fernet cipher.
        """
        salt = b'healthcare_sms_salt'  # In production, use random salt per message
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return key
    
    def encrypt_message(self, message: str) -> str:
        """Encrypts sensitive healthcare data using Fernet symmetric encryption.
        
        Args:
            message: Plain text message containing healthcare data.
            
        Returns:
            str: Base64-encoded encrypted message suitable for secure transmission.
        """
        encrypted = self.cipher.encrypt(message.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_message(self, encrypted_message: str) -> str:
        """Decrypts healthcare data from Base64-encoded encrypted format.
        
        Args:
            encrypted_message: Base64-encoded encrypted healthcare data.
            
        Returns:
            str: Decrypted plain text healthcare message.
        """
        encrypted_data = base64.urlsafe_b64decode(encrypted_message.encode())
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode()


class SMSGatewayAdapter:
    """Primary SMS gateway adapter for healthcare message queue integration.
    
    Manages SMS packet collection, healthcare data type detection, automatic
    prioritization, encryption for sensitive data, and network-aware delivery
    protocol selection. Integrates with PostgreSQL message queue for reliable
    store-and-forward capability.
    """
    
    def __init__(self, db_config: Dict, gateway_config: Dict, encryption_password: str):
        self.db_config = db_config
        self.gateway_config = gateway_config
        self.encryption = SMSEncryption(encryption_password)
        self.connection = None
        self.logger = self._setup_logging()
        
        # Healthcare data type patterns
        self.data_patterns = {
            'hiv': ['hiv', 'cd4', 'viral load', 'art'],
            'prescription': ['prescription', 'medication', 'dosage', 'pharmacy'],
            'lab_results': ['glucose', 'cholesterol', 'hemoglobin', 'results'],
            'appointment': ['appointment', 'visit', 'clinic', 'schedule'],
            'insurance': ['insurance', 'nhis', 'coverage', 'claim']
        }
        
        # Priority mapping for healthcare data
        self.priority_map = {
            'hiv': 1,           # Critical - HIV results
            'prescription': 2,   # High - Medication orders
            'lab_results': 3,    # Medium - Lab results
            'appointment': 4,    # Low - Scheduling
            'insurance': 5       # Routine - Administrative
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Configures logging infrastructure for SMS gateway operations.
        
        Creates file handler with structured formatting for audit trail compliance.
        Logs are written to 'sms_gateway.log' for operational monitoring.
        
        Returns:
            logging.Logger: Configured logger instance for SMS operations.
        """
        logger = logging.getLogger('sms_gateway')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('sms_gateway.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def connect_to_db(self):
        """Establishes connection to PostgreSQL message queue database.
        
        Configures autocommit mode for immediate transaction execution.
        Logs connection status for operational monitoring.
        
        Raises:
            Exception: If database connection fails with configuration details.
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = True
            self.logger.info("Connected to message queue database")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    def detect_data_type(self, content: str) -> Tuple[str, int]:
        """Analyzes SMS content to identify healthcare data type and priority.
        
        Searches message content for medical keywords to classify data type
        and automatically assign appropriate priority level for healthcare urgency.
        
        Args:
            content: SMS message text content to analyze.
            
        Returns:
            Tuple[str, int]: Data type identifier and corresponding priority level.
                Priority levels: 1=Critical (HIV), 2=High (Rx), 3=Medium (Labs),
                4=Low (Appointments), 5=Routine (Administrative).
        """
        content_lower = content.lower()
        
        for data_type, keywords in self.data_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                priority = self.priority_map[data_type]
                return data_type, priority
        
        return 'general', 5  # Default priority
    
    def parse_sms_content(self, raw_content: str) -> Dict:
        """Parses SMS content to extract structured healthcare data.
        
        Attempts JSON parsing first for structured data, falls back to
        key-value pair extraction from plain text SMS messages.
        
        Args:
            raw_content: Raw SMS message content to parse.
            
        Returns:
            Dict: Extracted data fields including patient_id, facility_id,
                 data_type, and other healthcare-specific metadata.
        """
        try:
            # Try to parse as JSON first (structured data)
            data = json.loads(raw_content)
            return data
        except json.JSONDecodeError:
            # Handle plain text SMS
            lines = raw_content.strip().split('\n')
            parsed_data = {'content': raw_content}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed_data[key.strip().lower()] = value.strip()
            
            return parsed_data
    
    def should_encrypt(self, data_type: str, content: str) -> bool:
        """Determines whether message requires encryption based on sensitivity.
        
        Evaluates data type and content for sensitive medical information
        requiring HIPAA-compliant encryption during transmission.
        
        Args:
            data_type: Classified healthcare data type (hiv, prescription, etc.).
            content: Message content to analyze for sensitive keywords.
            
        Returns:
            bool: True if message contains sensitive data requiring encryption.
        """
        sensitive_types = ['hiv', 'prescription', 'lab_results']
        sensitive_keywords = ['patient', 'result', 'positive', 'negative', 'medication']
        
        if data_type in sensitive_types:
            return True
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in sensitive_keywords)
    
    async def receive_sms_webhook(self, webhook_data: Dict) -> bool:
        """Processes incoming SMS webhook from gateway provider.
        
        Validates webhook payload, extracts SMS data, performs healthcare
        classification, applies encryption if needed, and queues message
        for delivery through the healthcare message queue system.
        
        Args:
            webhook_data: SMS gateway webhook payload containing message details.
            
        Returns:
            bool: True if SMS was successfully processed and queued.
        """
        try:
            # Extract SMS data from webhook payload
            # Adjust these fields based on your SMS gateway's format
            sender = webhook_data.get('from', webhook_data.get('sender'))
            recipient = webhook_data.get('to', webhook_data.get('recipient'))
            content = webhook_data.get('text', webhook_data.get('message', webhook_data.get('body')))
            message_id = webhook_data.get('id', f"sms_{int(time.time())}")
            
            if not all([sender, recipient, content]):
                self.logger.warning(f"Incomplete SMS data: {webhook_data}")
                return False
            
            # Parse and process the SMS
            parsed_content = self.parse_sms_content(content)
            data_type, priority = self.detect_data_type(content)
            
            # Create SMS message object
            sms_message = SMSMessage(
                sender=sender,
                recipient=recipient,
                content=content,
                timestamp=datetime.now(),
                message_id=message_id,
                data_type=data_type,
                facility_id=parsed_content.get('facility_id'),
                patient_id=parsed_content.get('patient_id'),
                priority=priority
            )
            
            # Encrypt if sensitive data
            if self.should_encrypt(data_type, content):
                sms_message.content = self.encryption.encrypt_message(content)
                sms_message.is_encrypted = True
                self.logger.info(f"Encrypted sensitive {data_type} message from {sender}")
            
            # Queue the message
            await self.queue_sms_message(sms_message)
            
            self.logger.info(f"Processed SMS: {data_type} priority {priority} from {sender}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing SMS webhook: {e}")
            return False
    
    async def queue_sms_message(self, sms_message: SMSMessage):
        """Queues SMS message in PostgreSQL message queue system.
        
        Prepares message headers with healthcare metadata, determines routing
        key based on data type and priority, and publishes to appropriate
        exchange for consumption by healthcare facility endpoints.
        
        Args:
            sms_message: Processed SMS message with healthcare metadata.
            
        Raises:
            Exception: If message queuing fails with database error details.
        """
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Prepare message headers
                headers = {
                    'sender': sms_message.sender,
                    'recipient': sms_message.recipient,
                    'data_type': sms_message.data_type,
                    'priority': str(sms_message.priority),
                    'protocol': 'sms',
                    'encrypted': str(sms_message.is_encrypted),
                    'timestamp': sms_message.timestamp.isoformat()
                }
                
                if sms_message.facility_id:
                    headers['facility_id'] = sms_message.facility_id
                if sms_message.patient_id:
                    headers['patient_id'] = sms_message.patient_id
                
                # Prepare message body
                message_body = {
                    'content': sms_message.content,
                    'sms_id': sms_message.message_id,
                    'routing_info': {
                        'source_facility': self.extract_facility_from_number(sms_message.sender),
                        'target_facility': self.extract_facility_from_number(sms_message.recipient)
                    }
                }
                
                # Determine routing key based on data type and priority
                routing_key = f"sms.{sms_message.data_type}.priority_{sms_message.priority}"
                
                # Publish to message queue
                cur.execute("""
                    CALL mq.publish(
                        %s,  -- exchange_name
                        %s,  -- routing_key 
                        %s,  -- body (json)
                        %s   -- headers (hstore)
                    )
                """, (
                    'Health Exchange',
                    routing_key,
                    json.dumps(message_body),
                    headers
                ))
                
                self.logger.info(f"Queued SMS message {sms_message.message_id} with routing key {routing_key}")
                
        except Exception as e:
            self.logger.error(f"Error queuing SMS message: {e}")
            raise
    
    def extract_facility_from_number(self, phone_number: str) -> str:
        """Maps phone number to healthcare facility identifier.
        
        Uses configured facility mapping to identify source or destination
        healthcare facility based on phone number. Placeholder implementation
        should be replaced with actual facility database lookup.
        
        Args:
            phone_number: Phone number to map to facility.
            
        Returns:
            str: Facility identifier or 'UNKNOWN_FACILITY' if not mapped.
        """
        # This is a placeholder - implement your facility mapping logic
        # For example, you might have a database of phone numbers to facilities
        facility_mapping = {
            '+233201234567': 'FACILITY_001',  # Accra General Hospital
            '+233501234568': 'FACILITY_002',  # Kumasi Health Center
            '+233301234569': 'FACILITY_003',  # Cape Coast Clinic
        }
        
        return facility_mapping.get(phone_number, 'UNKNOWN_FACILITY')
    
    async def send_sms_via_gateway(self, message_data: Dict) -> bool:
        """Sends SMS through configured gateway API provider.
        
        Formats message payload according to gateway requirements,
        authenticates with API credentials, and transmits SMS with
        error handling and logging for delivery confirmation.
        
        Args:
            message_data: Message content and recipient information.
            
        Returns:
            bool: True if SMS was successfully sent through gateway.
        """
        try:
            # Prepare SMS payload for your gateway
            sms_payload = {
                'to': message_data['recipient'],
                'from': self.gateway_config.get('sender_id', 'HealthSystem'),
                'text': message_data['content']
            }
            
            # Add gateway-specific headers
            headers = {
                'Authorization': f"Bearer {self.gateway_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.gateway_config['send_url'],
                    json=sms_payload,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"SMS sent successfully: {result}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"SMS send failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending SMS: {e}")
            return False
    
    async def process_outbound_messages(self):
        """I process messages from queue for SMS delivery"""
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Open channel for SMS queue
                cur.execute("CALL mq.open_channel('SMS Queue', 5)")
                
                # Listen for messages
                cur.execute("LISTEN \"1\"")  # Channel ID 1 for SMS
                
                while True:
                    # Check for notifications
                    self.connection.poll()
                    
                    while self.connection.notifies:
                        notify = self.connection.notifies.pop(0)
                        
                        # Process the notification
                        await self.handle_outbound_sms(notify.payload)
                    
                    await asyncio.sleep(1)  # Prevent busy waiting
                    
        except Exception as e:
            self.logger.error(f"Error processing outbound messages: {e}")
    
    async def handle_outbound_sms(self, delivery_info: str):
        """I handle individual outbound SMS"""
        try:
            # Parse delivery info (delivery_id, message_id, channel_id)
            parts = delivery_info.split(',')
            if len(parts) >= 2:
                delivery_id = int(parts[0])
                message_id = int(parts[1])
                
                # Get message details
                with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT m.*, d.delivery_id
                        FROM mq.message m
                        JOIN mq.delivery d ON d.message_id = m.message_id
                        WHERE d.delivery_id = %s
                    """, (delivery_id,))
                    
                    result = cur.fetchone()
                    if not result:
                        self.logger.warning(f"No message found for delivery {delivery_id}")
                        return
                    
                    # Prepare message for SMS sending
                    message_data = json.loads(result['body'])
                    
                    # Decrypt if needed
                    content = message_data['content']
                    if result['headers'].get('encrypted') == 'true':
                        content = self.encryption.decrypt_message(content)
                    
                    sms_data = {
                        'recipient': result['headers'].get('recipient'),
                        'content': content
                    }
                    
                    # Send SMS
                    success = await self.send_sms_via_gateway(sms_data)
                    
                    if success:
                        # Acknowledge successful delivery
                        cur.execute("CALL mq.ack(%s)", (delivery_id,))
                        self.logger.info(f"Successfully delivered SMS for message {message_id}")
                    else:
                        # NACK for retry
                        cur.execute("CALL mq.nack(%s)", (delivery_id,))
                        self.logger.warning(f"Failed to deliver SMS for message {message_id}, will retry")
                        
        except Exception as e:
            self.logger.error(f"Error handling outbound SMS: {e}")


# Example configuration
GATEWAY_CONFIG = {
    'api_key': 'your_sms_gateway_api_key',
    'send_url': 'https://api.smsgateway.com/v1/messages/send',
    'webhook_url': 'https://your-server.com/sms/webhook',
    'sender_id': 'HealthSys'
}

DB_CONFIG = {
    'host': 'localhost',
    'database': 'afya_prototype',
    'user': 'postgres',
    'password': 'your_password'
}


async def main():
    """I am the main function to run SMS gateway adapter"""
    sms_adapter = SMSGatewayAdapter(
        db_config=DB_CONFIG,
        gateway_config=GATEWAY_CONFIG,
        encryption_password='your_encryption_password_here'
    )
    
    sms_adapter.connect_to_db()
    
    # Start processing outbound messages
    await sms_adapter.process_outbound_messages()


if __name__ == "__main__":
    asyncio.run(main())