#!/usr/bin/env python3
"""
SMS Service for Healthcare Data Transmission
===========================================

SMS transmission service with support for multiple providers
(Twilio, Africa's Talking) and message fragmentation for
healthcare data in low-bandwidth scenarios.
"""

import logging
import re
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod
import asyncio
import aiohttp

from ..core.models import SMSFragment, TransmissionResult, MessageStatus, TransmissionProtocol
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SMSProvider(ABC):
    """Abstract base class for SMS providers"""
    
    @abstractmethod
    async def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """Send SMS message. Returns (success, message_id_or_error)"""
        pass
    
    @abstractmethod
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        pass


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider implementation"""
    
    def __init__(self, account_sid: str, auth_token: str, sender_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.sender_number = sender_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    async def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """Send SMS via Twilio API"""
        try:
            auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
            data = {
                'From': self.sender_number,
                'To': phone_number,
                'Body': message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, auth=auth, data=data) as response:
                    result = await response.json()
                    
                    if response.status == 201:
                        return True, result.get('sid', 'unknown')
                    else:
                        error_msg = result.get('message', f'HTTP {response.status}')
                        logger.error(f"Twilio SMS failed: {error_msg}")
                        return False, error_msg
        
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return False, str(e)
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number for Twilio (E.164 format)"""
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number))


class AfricasTalkingSMSProvider(SMSProvider):
    """Africa's Talking SMS provider implementation"""
    
    def __init__(self, username: str, api_key: str, sender_id: Optional[str] = None):
        self.username = username
        self.api_key = api_key
        self.sender_id = sender_id or "AfricasTalking"
        self.base_url = "https://api.africastalking.com/version1/messaging"
    
    async def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """Send SMS via Africa's Talking API"""
        try:
            headers = {
                'ApiKey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'username': self.username,
                'to': phone_number,
                'message': message,
                'from': self.sender_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, data=data) as response:
                    result = await response.json()
                    
                    if response.status == 201:
                        sms_message_data = result.get('SMSMessageData', {})
                        recipients = sms_message_data.get('Recipients', [])
                        
                        if recipients and recipients[0].get('status') == 'Success':
                            message_id = recipients[0].get('messageId', 'unknown')
                            return True, message_id
                        else:
                            error_msg = recipients[0].get('status', 'Unknown error') if recipients else 'No recipients'
                            return False, error_msg
                    else:
                        error_msg = result.get('message', f'HTTP {response.status}')
                        logger.error(f"Africa's Talking SMS failed: {error_msg}")
                        return False, error_msg
        
        except Exception as e:
            logger.error(f"Africa's Talking SMS error: {str(e)}")
            return False, str(e)
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number for Africa's Talking"""
        # Accept both +254XXXXXXXXX and 254XXXXXXXXX formats
        pattern = r'^(\+?254|0)[7-9]\d{8}$'
        return bool(re.match(pattern, phone_number))


class SMSService:
    """Main SMS service with message fragmentation and provider abstraction"""
    
    def __init__(self, provider: SMSProvider, max_message_length: int = 160):
        self.provider = provider
        self.max_message_length = max_message_length
        self.logger = get_logger(f"{__name__}.SMSService")
    
    def fragment_message(self, message: str, message_id: str, phone_number: str) -> List[SMSFragment]:
        """Split long messages into SMS fragments"""
        if len(message) <= self.max_message_length:
            return [SMSFragment(
                fragment_id=f"{message_id}_1",
                message_id=message_id,
                part_number=1,
                total_parts=1,
                content=message,
                phone_number=phone_number
            )]
        
        # Calculate space for fragment info "(1/3) "
        fragment_info_space = 6  # "(x/y) "
        available_space = self.max_message_length - fragment_info_space
        
        # Split message into chunks
        chunks = []
        for i in range(0, len(message), available_space):
            chunks.append(message[i:i + available_space])
        
        # Create fragments
        fragments = []
        total_parts = len(chunks)
        
        for i, chunk in enumerate(chunks, 1):
            fragment = SMSFragment(
                fragment_id=f"{message_id}_{i}",
                message_id=message_id,
                part_number=i,
                total_parts=total_parts,
                content=chunk,
                phone_number=phone_number
            )
            fragments.append(fragment)
        
        return fragments
    
    async def send_message(self, phone_number: str, message: str, message_id: str) -> TransmissionResult:
        """Send SMS message with fragmentation support"""
        try:
            # Validate phone number
            if not self.provider.validate_phone_number(phone_number):
                return TransmissionResult(
                    success=False,
                    status=MessageStatus.FAILED,
                    protocol_used=TransmissionProtocol.SMS,
                    message_id=message_id,
                    error_message=f"Invalid phone number format: {phone_number}"
                )
            
            # Fragment the message if needed
            fragments = self.fragment_message(message, message_id, phone_number)
            self.logger.info(f"Sending message {message_id} in {len(fragments)} fragment(s)")
            
            # Send all fragments
            sent_fragments = []
            failed_fragments = []
            
            for fragment in fragments:
                sms_text = fragment.get_sms_text()
                success, result = await self.provider.send_sms(phone_number, sms_text)
                
                if success:
                    sent_fragments.append(fragment.fragment_id)
                    self.logger.debug(f"Fragment {fragment.fragment_id} sent successfully: {result}")
                else:
                    failed_fragments.append(fragment.fragment_id)
                    self.logger.error(f"Fragment {fragment.fragment_id} failed: {result}")
                
                # Small delay between fragments to avoid rate limiting
                if len(fragments) > 1:
                    await asyncio.sleep(0.5)
            
            # Determine overall result
            if len(sent_fragments) == len(fragments):
                status = MessageStatus.SENT
                success = True
                error_message = None
            elif sent_fragments:
                status = MessageStatus.FAILED
                success = False
                error_message = f"Partial failure: {len(failed_fragments)} of {len(fragments)} fragments failed"
            else:
                status = MessageStatus.FAILED
                success = False
                error_message = "All fragments failed to send"
            
            return TransmissionResult(
                success=success,
                status=status,
                protocol_used=TransmissionProtocol.SMS,
                message_id=message_id,
                error_message=error_message,
                response_data={
                    'total_fragments': len(fragments),
                    'sent_fragments': sent_fragments,
                    'failed_fragments': failed_fragments
                }
            )
        
        except Exception as e:
            self.logger.error(f"SMS service error for message {message_id}: {str(e)}")
            return TransmissionResult(
                success=False,
                status=MessageStatus.FAILED,
                protocol_used=TransmissionProtocol.SMS,
                message_id=message_id,
                error_message=str(e)
            )
    
    @staticmethod
    def create_provider(provider_name: str, config: Dict[str, Any]) -> SMSProvider:
        """Factory method to create SMS provider instances"""
        if provider_name.lower() == 'twilio':
            return TwilioSMSProvider(
                account_sid=config['account_sid'],
                auth_token=config['auth_token'],
                sender_number=config['sender_number']
            )
        elif provider_name.lower() == 'africastalking':
            return AfricasTalkingSMSProvider(
                username=config['username'],
                api_key=config['api_key'],
                sender_id=config.get('sender_id')
            )
        else:
            raise ValueError(f"Unsupported SMS provider: {provider_name}")


def create_sms_service_from_config(sms_config) -> SMSService:
    """Create SMS service from configuration"""
    provider_config = {}
    
    if sms_config.provider.lower() == 'twilio':
        provider_config = {
            'account_sid': sms_config.account_sid,
            'auth_token': sms_config.auth_token,
            'sender_number': sms_config.sender_number
        }
    elif sms_config.provider.lower() == 'africastalking':
        provider_config = {
            'username': sms_config.africastalking_username,
            'api_key': sms_config.africastalking_api_key,
            'sender_id': getattr(sms_config, 'sender_id', None)
        }
    
    provider = SMSService.create_provider(sms_config.provider, provider_config)
    return SMSService(provider, sms_config.max_message_length)