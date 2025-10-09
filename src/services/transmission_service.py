#!/usr/bin/env python3
"""
Healthcare Transmission Service
==============================

Main orchestration service for healthcare data transmission
with protocol selection, message processing, and OpenHIM integration.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.models import (
    OpenHIMMessage, TransmissionResult, MessageStatus, 
    TransmissionProtocol, NetworkStatus, NetworkCondition
)
from ..services.database_service import DatabaseService
from ..services.sms_service import SMSService
from ..adapters.openhim_adapter import OpenHIMAdapter
from ..utils.logger import get_logger
from ..utils.network_monitor import NetworkMonitor

logger = get_logger(__name__)


class HealthcareTransmissionService:
    """Main healthcare data transmission orchestration service"""
    
    def __init__(
        self,
        database_service: DatabaseService,
        sms_service: Optional[SMSService] = None,
        openhim_adapter: Optional[OpenHIMAdapter] = None,
        network_monitor: Optional[NetworkMonitor] = None
    ):
        self.database_service = database_service
        self.sms_service = sms_service
        self.openhim_adapter = openhim_adapter
        self.network_monitor = network_monitor
        self.logger = get_logger(f"{__name__}.HealthcareTransmissionService")
        
        # Protocol preference based on network conditions
        self.protocol_preferences = {
            NetworkCondition.EXCELLENT: [TransmissionProtocol.HTTPS, TransmissionProtocol.HTTP],
            NetworkCondition.GOOD: [TransmissionProtocol.HTTPS, TransmissionProtocol.HTTP, TransmissionProtocol.SMS],
            NetworkCondition.POOR: [TransmissionProtocol.SMS],
            NetworkCondition.OFFLINE: [TransmissionProtocol.SMS]  # Store for later transmission
        }
    
    async def initialize(self) -> bool:
        """Initialize all services"""
        try:
            # Initialize database
            if not await self.database_service.initialize():
                return False
            
            # Setup healthcare tables
            if not await self.database_service.setup_healthcare_tables():
                return False
            
            self.logger.info("Healthcare transmission service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize transmission service: {str(e)}")
            return False
    
    async def queue_message(
        self, 
        message: OpenHIMMessage, 
        exchange_name: str = "healthcare_exchange"
    ) -> bool:
        """Queue a healthcare message for transmission"""
        try:
            # Ensure exchange and queue exist
            queue_name = f"{exchange_name}_queue"
            routing_pattern = f"healthcare.{message.data_type.value}.*"
            
            success = await self.database_service.ensure_exchange_and_queue(
                exchange_name, queue_name, routing_pattern
            )
            
            if not success:
                return False
            
            # Queue the message
            return await self.database_service.queue_message(message, exchange_name)
        
        except Exception as e:
            self.logger.error(f"Failed to queue message {message.message_id}: {str(e)}")
            return False
    
    async def select_transmission_protocol(
        self, 
        message: OpenHIMMessage, 
        destination: str
    ) -> TransmissionProtocol:
        """Select optimal transmission protocol based on network conditions and message priority"""
        try:
            # Get current network status
            if self.network_monitor:
                network_status = await self.network_monitor.check_network_status()
                condition = network_status.get_condition()
            else:
                # Default to GOOD if no network monitoring
                condition = NetworkCondition.GOOD
            
            # For critical messages, prefer reliable protocols
            if message.priority <= 2:  # Critical or high priority
                if condition in [NetworkCondition.EXCELLENT, NetworkCondition.GOOD]:
                    return TransmissionProtocol.HTTPS
                else:
                    return TransmissionProtocol.SMS
            
            # For normal/low priority, use network-optimized selection
            preferred_protocols = self.protocol_preferences.get(condition, [TransmissionProtocol.SMS])
            
            # Check if destination supports the preferred protocol
            # For now, return the first available protocol
            return preferred_protocols[0] if preferred_protocols else TransmissionProtocol.SMS
        
        except Exception as e:
            self.logger.error(f"Error selecting protocol for message {message.message_id}: {str(e)}")
            return TransmissionProtocol.SMS  # Fallback to SMS
    
    async def transmit_message(
        self, 
        message: OpenHIMMessage, 
        protocol: TransmissionProtocol,
        destination: str
    ) -> TransmissionResult:
        """Transmit message using specified protocol"""
        try:
            if protocol == TransmissionProtocol.SMS:
                if not self.sms_service:
                    return TransmissionResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        protocol_used=protocol,
                        message_id=message.message_id,
                        error_message="SMS service not configured"
                    )
                
                # Convert message to SMS format
                sms_content = self._format_message_for_sms(message)
                return await self.sms_service.send_message(
                    destination, sms_content, message.message_id
                )
            
            elif protocol in [TransmissionProtocol.HTTP, TransmissionProtocol.HTTPS]:
                if not self.openhim_adapter:
                    return TransmissionResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        protocol_used=protocol,
                        message_id=message.message_id,
                        error_message="OpenHIM adapter not configured"
                    )
                
                # Send via OpenHIM
                return await self.openhim_adapter.send_message(message, destination)
            
            else:
                return TransmissionResult(
                    success=False,
                    status=MessageStatus.FAILED,
                    protocol_used=protocol,
                    message_id=message.message_id,
                    error_message=f"Unsupported protocol: {protocol.value}"
                )
        
        except Exception as e:
            self.logger.error(f"Error transmitting message {message.message_id}: {str(e)}")
            return TransmissionResult(
                success=False,
                status=MessageStatus.FAILED,
                protocol_used=protocol,
                message_id=message.message_id,
                error_message=str(e)
            )
    
    def _format_message_for_sms(self, message: OpenHIMMessage) -> str:
        """Format OpenHIM message for SMS transmission"""
        try:
            # Create concise SMS format for healthcare data
            if message.data_type.value == "lab_result":
                return f"LAB: P:{message.patient_id} T:{message.payload.get('test_type', 'N/A')} R:{message.payload.get('result', 'N/A')} F:{message.facility_id}"
            
            elif message.data_type.value == "prescription":
                return f"RX: P:{message.patient_id} M:{message.payload.get('medication', 'N/A')} D:{message.payload.get('dosage', 'N/A')}"
            
            elif message.data_type.value == "emergency":
                return f"EMERGENCY: P:{message.patient_id} T:{message.payload.get('emergency_type', 'N/A')} L:{message.payload.get('location', 'N/A')}"
            
            else:
                # Generic format
                return f"HEALTH: {message.message_type} P:{message.patient_id} F:{message.facility_id}"
        
        except Exception as e:
            self.logger.error(f"Error formatting message for SMS: {str(e)}")
            return f"HEALTH: {message.message_id}"
    
    async def process_queue(
        self, 
        queue_name: str = "healthcare_exchange_queue",
        batch_size: int = 10
    ) -> Dict[str, int]:
        """Process messages from the queue"""
        try:
            processed = 0
            successful = 0
            failed = 0
            
            messages = await self.database_service.consume_messages(queue_name, limit=batch_size)
            
            for message_data in messages:
                try:
                    # Parse message
                    payload = message_data['payload']
                    message = OpenHIMMessage(**payload)
                    
                    # Select protocol
                    protocol = await self.select_transmission_protocol(
                        message, payload.get('destination', 'default')
                    )
                    
                    # Transmit message
                    result = await self.transmit_message(
                        message, protocol, payload.get('destination', 'default')
                    )
                    
                    # Store result
                    await self.database_service.store_transmission_result(result)
                    
                    # Acknowledge message if successful
                    if result.success:
                        await self.database_service.acknowledge_message(
                            queue_name, message_data['delivery_id']
                        )
                        successful += 1
                    else:
                        failed += 1
                    
                    processed += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing message {message_data.get('message_id', 'unknown')}: {str(e)}")
                    failed += 1
                    processed += 1
            
            if processed > 0:
                self.logger.info(f"Processed {processed} messages: {successful} successful, {failed} failed")
            
            return {
                'processed': processed,
                'successful': successful,
                'failed': failed
            }
        
        except Exception as e:
            self.logger.error(f"Error processing queue {queue_name}: {str(e)}")
            return {'processed': 0, 'successful': 0, 'failed': 0}
    
    async def retry_failed_messages(self) -> Dict[str, int]:
        """Retry failed message transmissions"""
        try:
            failed_messages = await self.database_service.get_failed_messages()
            retried = 0
            successful = 0
            
            for msg_data in failed_messages:
                try:
                    # This would require retrieving the original message
                    # For now, we'll just update the retry count
                    retried += 1
                    
                except Exception as e:
                    self.logger.error(f"Error retrying message {msg_data['message_id']}: {str(e)}")
            
            return {'retried': retried, 'successful': successful}
        
        except Exception as e:
            self.logger.error(f"Error retrying failed messages: {str(e)}")
            return {'retried': 0, 'successful': 0}
    
    async def get_transmission_stats(self) -> Dict[str, Any]:
        """Get transmission statistics"""
        try:
            # This would query the database for stats
            # Implementation depends on specific requirements
            return {
                'total_messages': 0,
                'successful_transmissions': 0,
                'failed_transmissions': 0,
                'pending_messages': 0
            }
        except Exception as e:
            self.logger.error(f"Error getting transmission stats: {str(e)}")
            return {}
    
    async def close(self):
        """Clean shutdown of all services"""
        try:
            if self.database_service:
                await self.database_service.close()
            
            self.logger.info("Healthcare transmission service closed")
        except Exception as e:
            self.logger.error(f"Error closing transmission service: {str(e)}")