#!/usr/bin/env python3
"""
Healthcare Data Transmission System for OpenHIM Integration
===========================================================

A comprehensive message queue system for healthcare data transmission
supporting low bandwidth protocols (SMS/USSD) and high bandwidth (HTTP/HTTPS)
with automatic protocol selection based on network conditions.
"""

import json
import time
import asyncio
import logging
import psycopg2
import psycopg2.extras
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransmissionProtocol(Enum):
    """Available transmission protocols"""
    HTTP = "http"
    HTTPS = "https"
    SMS = "sms"
    SMS_MULTIPART = "sms_multipart"
    USSD = "ussd"


class DataType(Enum):
    """Healthcare data types with different priority levels"""
    EMERGENCY = "emergency"
    LAB_HIV_RESULT = "lab_hiv_result"
    PRESCRIPTION = "prescription"
    LAB_ROUTINE = "lab_routine"
    PATIENT_REGISTRATION = "patient_registration"
    VITALS = "vitals"
    APPOINTMENT = "appointment"
    ADMINISTRATIVE = "administrative"


class NetworkCondition(Enum):
    """Network condition states"""
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    SMS_ONLY = "sms_only"
    OFFLINE = "offline"


@dataclass
class OpenHIMMessage:
    """OpenHIM compatible message structure"""
    message_id: str
    timestamp: str
    source: str
    destination: str
    message_type: str
    data_type: DataType
    priority: int
    client_id: str
    transaction_id: str
    orchestration_id: Optional[str] = None
    patient_id: Optional[str] = None
    facility_id: Optional[str] = None
    provider_id: Optional[str] = None
    payload: Dict[str, Any] = None
    preferred_protocols: List[TransmissionProtocol] = None
    encryption_required: bool = True
    acknowledgment_required: bool = True
    ttl: int = 3600
    
    def __post_init__(self):
        if self.preferred_protocols is None:
            self.preferred_protocols = self._determine_preferred_protocols()
    
    def _determine_preferred_protocols(self) -> List[TransmissionProtocol]:
        """Determine preferred protocols based on data type"""
        protocols_map = {
            DataType.EMERGENCY: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.SMS,
                TransmissionProtocol.USSD
            ],
            DataType.LAB_HIV_RESULT: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.SMS
            ],
            DataType.PRESCRIPTION: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.USSD,
                TransmissionProtocol.SMS
            ],
            DataType.LAB_ROUTINE: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.SMS_MULTIPART
            ],
            DataType.PATIENT_REGISTRATION: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.USSD
            ],
            DataType.VITALS: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.SMS
            ],
            DataType.APPOINTMENT: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.SMS
            ],
            DataType.ADMINISTRATIVE: [
                TransmissionProtocol.HTTPS
            ],
        }
        return protocols_map.get(
            self.data_type, [TransmissionProtocol.HTTPS]
        )
    
    def to_openhim_format(self) -> Dict[str, Any]:
        """Convert to OpenHIM standard format"""
        return {
            "resourceType": "Message",
            "id": self.message_id,
            "meta": {
                "lastUpdated": self.timestamp,
                "source": self.source
            },
            "identifier": [
                {
                    "system": "transaction-id",
                    "value": self.transaction_id
                }
            ],
            "client": self.client_id,
            "orchestration": self.orchestration_id,
            "status": "pending",
            "priority": self.priority,
            "subject": {
                "reference": f"Patient/{self.patient_id}"
                if self.patient_id else None
            },
            "encounter": {
                "reference": f"Facility/{self.facility_id}"
                if self.facility_id else None
            },
            "payload": self.payload,
            "extensions": {
                "dataType": self.data_type.value,
                "encryptionRequired": self.encryption_required,
                "acknowledgmentRequired": self.acknowledgment_required,
                "ttl": self.ttl,
                "preferredProtocols": [p.value for p in self.preferred_protocols]
            }
        }


@dataclass
class NetworkStatus:
    """Network status information"""
    facility_id: str
    network_type: str
    bandwidth_kbps: int
    latency_ms: int
    packet_loss_percent: float
    last_updated: datetime
    is_active: bool = True
    
    def get_condition(self) -> NetworkCondition:
        """Determine network condition based on metrics"""
        if not self.is_active:
            return NetworkCondition.OFFLINE
        
        if (self.bandwidth_kbps >= 1000 and self.latency_ms <= 100
                and self.packet_loss_percent <= 1):
            return NetworkCondition.EXCELLENT
        elif (self.bandwidth_kbps >= 256 and self.latency_ms <= 500
              and self.packet_loss_percent <= 5):
            return NetworkCondition.GOOD
        elif (self.bandwidth_kbps >= 64
              and self.packet_loss_percent <= 15):
            return NetworkCondition.POOR
        else:
            return NetworkCondition.SMS_ONLY


class MessageFragmenter:
    """Handles message fragmentation for SMS transmission"""
    
    MAX_SMS_SIZE = 160
    HEADER_SIZE = 20
    
    @classmethod
    def fragment_message(cls, message: str,
                         message_id: str) -> List[Dict[str, Any]]:
        """Fragment a message for SMS transmission"""
        max_content_size = cls.MAX_SMS_SIZE - cls.HEADER_SIZE
        fragments = []
        
        total_fragments = ((len(message) + max_content_size - 1)
                          // max_content_size)
        
        for i in range(total_fragments):
            start_pos = i * max_content_size
            end_pos = min(start_pos + max_content_size, len(message))
            fragment_data = message[start_pos:end_pos]
            
            fragment = {
                'message_id': message_id,
                'fragment_number': i + 1,
                'total_fragments': total_fragments,
                'fragment_data': fragment_data,
                'fragment_size': len(fragment_data)
            }
            fragments.append(fragment)
        
        return fragments
    
    @classmethod
    def reconstruct_message(cls,
                            fragments: List[Dict[str, Any]]) -> Optional[str]:
        """Reconstruct message from fragments"""
        if not fragments:
            return None
        
        sorted_fragments = sorted(fragments,
                                  key=lambda x: x['fragment_number'])
        
        total_fragments = sorted_fragments[0]['total_fragments']
        if len(sorted_fragments) != total_fragments:
            return None
        
        message = ''.join(frag['fragment_data'] for frag in sorted_fragments)
        return message


class ProtocolAdapter(ABC):
    """Abstract base class for protocol adapters"""
    
    @abstractmethod
    async def send_message(self, message: OpenHIMMessage,
                           destination: str) -> bool:
        """Send message using this protocol"""
        pass
    
    @abstractmethod
    def get_max_message_size(self) -> int:
        """Get maximum message size for this protocol"""
        pass
    
    @abstractmethod
    def supports_fragmentation(self) -> bool:
        """Check if protocol supports message fragmentation"""
        pass


class HTTPAdapter(ProtocolAdapter):
    """HTTP/HTTPS protocol adapter for high bandwidth transmission"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
    
    async def send_message(self, message: OpenHIMMessage,
                           destination: str) -> bool:
        """Send message via HTTP/HTTPS"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            openhim_payload = message.to_openhim_format()
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.config.get('auth_token', '')}",
                'X-OpenHIM-TransactionID': message.transaction_id
            }
            
            async with self.session.post(
                destination,
                json=openhim_payload,
                headers=headers,
                timeout=30
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"HTTP transmission failed: {e}")
            return False
    
    def get_max_message_size(self) -> int:
        return 10 * 1024 * 1024  # 10MB
    
    def supports_fragmentation(self) -> bool:
        return False


class SMSAdapter(ProtocolAdapter):
    """SMS protocol adapter for low bandwidth transmission"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send_message(self, message: OpenHIMMessage,
                           destination: str) -> bool:
        """Send message via SMS"""
        try:
            compact_message = self._create_compact_message(message)
            
            if len(compact_message) <= self.get_max_message_size():
                return await self._send_single_sms(destination,
                                                   compact_message)
            else:
                fragments = MessageFragmenter.fragment_message(
                    compact_message, message.message_id)
                return await self._send_fragmented_sms(destination, fragments)
                
        except Exception as e:
            logger.error(f"SMS transmission failed: {e}")
            return False
    
    def _create_compact_message(self, message: OpenHIMMessage) -> str:
        """Create compact message format for SMS"""
        compact = {
            'id': message.message_id[:8],
            'type': message.data_type.value[:3],
            'src': message.source[:10],
            'dst': message.destination[:10],
            'data': self._compress_payload(message.payload)
        }
        return json.dumps(compact, separators=(',', ':'))
    
    def _compress_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compress payload for SMS transmission"""
        if not payload:
            return {}
        
        compressed = {}
        for key, value in payload.items():
            short_key = self._abbreviate_key(key)
            compressed[short_key] = value
        
        return compressed
    
    def _abbreviate_key(self, key: str) -> str:
        """Abbreviate common healthcare data keys"""
        abbreviations = {
            'patient_id': 'pid',
            'provider_id': 'prov',
            'facility_id': 'fac',
            'timestamp': 'ts',
            'diagnosis': 'dx',
            'medication': 'med',
            'dosage': 'dose',
            'blood_pressure': 'bp',
            'temperature': 'temp',
            'heart_rate': 'hr'
        }
        return abbreviations.get(key, key[:4])
    
    async def _send_single_sms(self, destination: str, message: str) -> bool:
        """Send single SMS"""
        logger.info(f"Sending SMS to {destination}: {message[:50]}...")
        return True
    
    async def _send_fragmented_sms(self, destination: str,
                                   fragments: List[Dict[str, Any]]) -> bool:
        """Send fragmented SMS"""
        success_count = 0
        for fragment in fragments:
            fragment_text = (f"[{fragment['fragment_number']}/"
                           f"{fragment['total_fragments']}]"
                           f"{fragment['fragment_data']}")
            if await self._send_single_sms(destination, fragment_text):
                success_count += 1
        
        return success_count == len(fragments)
    
    def get_max_message_size(self) -> int:
        return 160
    
    def supports_fragmentation(self) -> bool:
        return True


class USSDAdapter(ProtocolAdapter):
    """USSD protocol adapter for interactive low bandwidth transmission"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send_message(self, message: OpenHIMMessage,
                           destination: str) -> bool:
        """Send message via USSD session"""
        try:
            ussd_content = self._create_ussd_content(message)
            return await self._initiate_ussd_session(destination,
                                                     ussd_content)
            
        except Exception as e:
            logger.error(f"USSD transmission failed: {e}")
            return False
    
    def _create_ussd_content(self, message: OpenHIMMessage) -> str:
        """Create USSD-friendly content"""
        content = f"AFYA HEALTH ALERT\n"
        content += f"Type: {message.data_type.value.upper()}\n"
        content += f"From: {message.source}\n"
        
        if message.payload:
            if 'diagnosis' in message.payload:
                content += f"Diagnosis: {message.payload['diagnosis'][:30]}\n"
            if 'medication' in message.payload:
                content += f"Medication: {message.payload['medication'][:30]}\n"
        
        content += f"Reply *714*{message.message_id[:6]}# for details"
        return content
    
    async def _initiate_ussd_session(self, destination: str,
                                     content: str) -> bool:
        """Initiate USSD session"""
        logger.info(f"Initiating USSD session to {destination}: "
                   f"{content[:50]}...")
        return True
    
    def get_max_message_size(self) -> int:
        return 182
    
    def supports_fragmentation(self) -> bool:
        return False


class HealthcareTransmissionSystem:
    """Main healthcare data transmission system"""
    
    def __init__(self, db_config: Dict[str, str],
                 transmission_config: Dict[str, Any]):
        self.db_config = db_config
        self.transmission_config = transmission_config
        self.connection = None
        
        self.adapters = {
            TransmissionProtocol.HTTP: HTTPAdapter(
                transmission_config.get('http', {})),
            TransmissionProtocol.HTTPS: HTTPAdapter(
                transmission_config.get('https', {})),
            TransmissionProtocol.SMS: SMSAdapter(
                transmission_config.get('sms', {})),
            TransmissionProtocol.SMS_MULTIPART: SMSAdapter(
                transmission_config.get('sms', {})),
            TransmissionProtocol.USSD: USSDAdapter(
                transmission_config.get('ussd', {}))
        }
    
    async def initialize(self):
        """Initialize the transmission system"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = True
            logger.info("Healthcare transmission system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def queue_message(self, message: OpenHIMMessage,
                            exchange_name: str = 'healthcare_exchange') -> bool:
        """Queue a healthcare message for transmission"""
        try:
            with self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                
                cur.execute("""
                    INSERT INTO mq.exchange (exchange_name) 
                    VALUES (%s) ON CONFLICT (exchange_name) DO NOTHING
                """, (exchange_name,))
                
                routing_key = self._create_routing_key(message)
                queue_name = f"{message.data_type.value}_queue"
                await self._ensure_queue_exists(cur, exchange_name,
                                              queue_name, routing_key)
                
                await self._store_protocol_preferences(cur, message)
                
                cur.execute("""
                    CALL mq.publish(%s, %s, %s, %s)
                """, (
                    exchange_name,
                    routing_key,
                    json.dumps(message.to_openhim_format()),
                    f'priority=>{message.priority},'
                    f'data_type=>{message.data_type.value}'
                ))
                
                logger.info(f"Queued message {message.message_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
            return False
    
    def _create_routing_key(self, message: OpenHIMMessage) -> str:
        """Create routing key based on message characteristics"""
        key_parts = [
            message.data_type.value,
            f"priority_{message.priority}",
            message.destination.replace('.', '_')
        ]
        
        if message.facility_id:
            key_parts.append(f"facility_{message.facility_id}")
        
        return '.'.join(key_parts)
    
    async def _ensure_queue_exists(self, cursor, exchange_name: str,
                                   queue_name: str, routing_key: str):
        """Ensure required queue exists"""
        pattern = routing_key.replace('.', r'\.').replace('*', '.*')
        pattern = f"^{pattern}$"
        
        cursor.execute("""
            INSERT INTO mq.queue (exchange_id, queue_name, routing_key_pattern)
            SELECT e.exchange_id, %s, %s
            FROM mq.exchange e
            WHERE e.exchange_name = %s
            ON CONFLICT (queue_name) DO NOTHING
        """, (queue_name, pattern, exchange_name))
    
    async def _store_protocol_preferences(self, cursor,
                                          message: OpenHIMMessage):
        """Store protocol preferences for message"""
        cursor.execute("""
            INSERT INTO mq.message_protocol (message_id, preferred_protocol,
                                           current_protocol)
            VALUES (currval('mq.message_message_id_seq'), %s, %s)
            ON CONFLICT (message_id) DO UPDATE SET
                preferred_protocol = EXCLUDED.preferred_protocol,
                current_protocol = EXCLUDED.current_protocol
        """, (
            [p.value for p in message.preferred_protocols],
            (message.preferred_protocols[0].value
             if message.preferred_protocols else 'https')
        ))
    
    async def process_pending_messages(self):
        """Process pending messages in the queue"""
        try:
            with self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                
                cur.execute("""
                    SELECT 
                        m.message_id,
                        m.routing_key,
                        m.body,
                        m.priority,
                        m.retry_count,
                        m.max_retries,
                        mp.preferred_protocol,
                        mp.current_protocol
                    FROM mq.message m
                    LEFT JOIN mq.message_protocol mp 
                        ON m.message_id = mp.message_id
                    WHERE m.message_id IN (
                        SELECT mw.message_id 
                        FROM mq.message_waiting mw
                        WHERE mw.not_until_time IS NULL 
                           OR mw.not_until_time <= NOW()
                    )
                    ORDER BY m.priority ASC, m.publish_time ASC
                    LIMIT 10
                """)
                
                messages = cur.fetchall()
                
                for msg_row in messages:
                    await self._process_single_message(cur, msg_row)
                    
        except Exception as e:
            logger.error(f"Error processing pending messages: {e}")
    
    async def _process_single_message(self, cursor, msg_row):
        """Process a single message"""
        try:
            message_id = msg_row['message_id']
            message_body = msg_row['body']
            
            openhim_data = (json.loads(message_body)
                          if isinstance(message_body, str)
                          else message_body)
            
            destination = self._extract_destination(openhim_data)
            best_protocol = await self._select_best_protocol(
                msg_row['preferred_protocol'], destination
            )
            
            adapter = self.adapters.get(best_protocol)
            if not adapter:
                logger.error(f"No adapter found for protocol {best_protocol}")
                return
            
            message = self._create_message_from_openhim(openhim_data)
            success = await adapter.send_message(message, destination)
            
            if success:
                await self._mark_message_delivered(cursor, message_id)
                logger.info(f"Successfully transmitted message {message_id}")
            else:
                await self._handle_transmission_failure(cursor, msg_row)
                
        except Exception as e:
            logger.error(f"Error processing message "
                        f"{msg_row.get('message_id', 'unknown')}: {e}")
    
    def _extract_destination(self, openhim_data: Dict[str, Any]) -> str:
        """Extract destination from OpenHIM data"""
        return openhim_data.get('destination', 'unknown')
    
    async def _select_best_protocol(self, preferred_protocols: List[str],
                                    destination: str) -> TransmissionProtocol:
        """Select best available protocol based on network conditions"""
        network_condition = await self._get_network_condition(destination)
        
        protocol_map = {
            NetworkCondition.EXCELLENT: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.HTTP
            ],
            NetworkCondition.GOOD: [
                TransmissionProtocol.HTTPS,
                TransmissionProtocol.HTTP,
                TransmissionProtocol.SMS_MULTIPART
            ],
            NetworkCondition.POOR: [
                TransmissionProtocol.SMS_MULTIPART,
                TransmissionProtocol.SMS,
                TransmissionProtocol.USSD
            ],
            NetworkCondition.SMS_ONLY: [
                TransmissionProtocol.SMS,
                TransmissionProtocol.USSD
            ],
            NetworkCondition.OFFLINE: []
        }
        
        suitable_protocols = protocol_map.get(network_condition, [])
        
        if preferred_protocols:
            for pref_proto in preferred_protocols:
                try:
                    proto_enum = TransmissionProtocol(pref_proto)
                    if proto_enum in suitable_protocols:
                        return proto_enum
                except ValueError:
                    continue
        
        if suitable_protocols:
            return suitable_protocols[0]
        
        return TransmissionProtocol.SMS
    
    async def _get_network_condition(self,
                                     destination: str) -> NetworkCondition:
        """Get current network condition for destination"""
        try:
            with self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM mq.network_status 
                    WHERE facility_id = %s AND is_active = true
                    ORDER BY last_updated DESC LIMIT 1
                """, (destination,))
                
                status_row = cur.fetchone()
                if status_row:
                    status = NetworkStatus(**status_row)
                    return status.get_condition()
                
        except Exception as e:
            logger.error(f"Error getting network condition: {e}")
        
        return NetworkCondition.SMS_ONLY
    
    def _create_message_from_openhim(self,
                                     openhim_data: Dict[str, Any]) -> OpenHIMMessage:
        """Create OpenHIMMessage object from OpenHIM data"""
        extensions = openhim_data.get('extensions', {})
        
        return OpenHIMMessage(
            message_id=openhim_data.get('id', ''),
            timestamp=openhim_data.get('meta', {}).get('lastUpdated', ''),
            source=openhim_data.get('meta', {}).get('source', ''),
            destination=openhim_data.get('destination', ''),
            message_type=openhim_data.get('resourceType', 'Message'),
            data_type=DataType(extensions.get('dataType', 'administrative')),
            priority=openhim_data.get('priority', 5),
            client_id=openhim_data.get('client', ''),
            transaction_id=(openhim_data.get('identifier', [{}])[0]
                          .get('value', '')),
            orchestration_id=openhim_data.get('orchestration'),
            payload=openhim_data.get('payload', {}),
            encryption_required=extensions.get('encryptionRequired', True),
            acknowledgment_required=extensions.get('acknowledgmentRequired',
                                                   True),
            ttl=extensions.get('ttl', 3600)
        )
    
    async def _mark_message_delivered(self, cursor, message_id: int):
        """Mark message as successfully delivered"""
        cursor.execute("""
            DELETE FROM mq.message_waiting WHERE message_id = %s
        """, (message_id,))
        
        logger.debug(f"Marked message {message_id} as delivered")
    
    async def _handle_transmission_failure(self, cursor, msg_row):
        """Handle transmission failure with retry logic"""
        message_id = msg_row['message_id']
        retry_count = msg_row['retry_count']
        max_retries = msg_row['max_retries']
        
        if retry_count < max_retries:
            delay_minutes = min(2 ** retry_count, 60)
            retry_time = datetime.now() + timedelta(minutes=delay_minutes)
            
            cursor.execute("""
                UPDATE mq.message 
                SET retry_count = retry_count + 1 
                WHERE message_id = %s
            """, (message_id,))
            
            cursor.execute("""
                UPDATE mq.message_waiting 
                SET not_until_time = %s 
                WHERE message_id = %s
            """, (retry_time, message_id))
            
            logger.info(f"Scheduled retry for message {message_id}")
        else:
            await self._handle_max_retries_exceeded(cursor, message_id)
    
    async def _handle_max_retries_exceeded(self, cursor, message_id: int):
        """Handle messages that have exceeded max retries"""
        logger.error(f"Message {message_id} exceeded max retries")
        
        cursor.execute("""
            DELETE FROM mq.message_waiting WHERE message_id = %s
        """, (message_id,))
    
    async def update_network_status(self, facility_id: str,
                                    network_status: NetworkStatus):
        """Update network status for a facility"""
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO mq.network_status 
                    (channel_id, facility_id, network_type, bandwidth_kbps,
                     latency_ms, packet_loss_percent, last_updated, is_active)
                    VALUES (1, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (channel_id) DO UPDATE SET
                        facility_id = EXCLUDED.facility_id,
                        network_type = EXCLUDED.network_type,
                        bandwidth_kbps = EXCLUDED.bandwidth_kbps,
                        latency_ms = EXCLUDED.latency_ms,
                        packet_loss_percent = EXCLUDED.packet_loss_percent,
                        last_updated = EXCLUDED.last_updated,
                        is_active = EXCLUDED.is_active
                """, (
                    facility_id,
                    network_status.network_type,
                    network_status.bandwidth_kbps,
                    network_status.latency_ms,
                    network_status.packet_loss_percent,
                    network_status.last_updated,
                    network_status.is_active
                ))
                
        except Exception as e:
            logger.error(f"Failed to update network status: {e}")
    
    async def shutdown(self):
        """Shutdown the transmission system"""
        if self.connection:
            self.connection.close()
        
        for adapter in self.adapters.values():
            if hasattr(adapter, 'session') and adapter.session:
                await adapter.session.close()
        
        logger.info("Healthcare transmission system shutdown complete")


async def main():
    """Example usage of the healthcare transmission system"""
    
    db_config = {
        'host': 'localhost',
        'database': 'pg_mq_poc',
        'user': 'postgres',
        'password': 'Christelle09123'
    }
    
    transmission_config = {
        'http': {'auth_token': 'your-openhim-token'},
        'sms': {'api_key': 'your-sms-api-key', 'sender_id': 'AFYA'},
        'ussd': {'service_code': '*714#'}
    }
    
    system = HealthcareTransmissionSystem(db_config, transmission_config)
    await system.initialize()
    
    try:
        message = OpenHIMMessage(
            message_id="msg_" + str(int(time.time())),
            timestamp=datetime.now().isoformat(),
            source="clinic_001",
            destination="hospital_main",
            message_type="LabResult",
            data_type=DataType.LAB_ROUTINE,
            priority=3,
            client_id="afya_client",
            transaction_id="txn_" + str(int(time.time())),
            patient_id="patient_123",
            facility_id="facility_001",
            provider_id="provider_456",
            payload={
                "test_type": "blood_glucose",
                "result": "120 mg/dL",
                "normal_range": "70-100 mg/dL",
                "status": "HIGH",
                "timestamp": datetime.now().isoformat(),
                "notes": "Patient should follow up with endocrinologist"
            }
        )
        
        success = await system.queue_message(message)
        if success:
            print(f"Successfully queued message {message.message_id}")
            await system.process_pending_messages()
        else:
            print("Failed to queue message")
            
    finally:
        await system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())