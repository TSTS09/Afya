#!/usr/bin/env python3
"""
Database Service for Healthcare Transmission System
==================================================

PostgreSQL database service for message queue management,
healthcare data storage, and transmission tracking.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
import asyncpg
from datetime import datetime

from ..core.models import OpenHIMMessage, TransmissionResult, MessageStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """PostgreSQL database service for healthcare data transmission"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> bool:
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            return False
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def ensure_exchange_and_queue(self, exchange_name: str, queue_name: str, routing_pattern: str = ".*") -> bool:
        """Ensure exchange and queue exist"""
        try:
            async with self.pool.acquire() as connection:
                # Create exchange if not exists
                await connection.execute(
                    "SELECT mq.create_exchange($1)",
                    exchange_name
                )
                
                # Create queue if not exists
                await connection.execute(
                    "SELECT mq.create_queue($1, $2, $3)",
                    exchange_name, queue_name, routing_pattern
                )
                
                logger.debug(f"Ensured exchange '{exchange_name}' and queue '{queue_name}'")
                return True
        except Exception as e:
            logger.error(f"Failed to ensure exchange/queue: {str(e)}")
            return False
    
    async def queue_message(self, message: OpenHIMMessage, exchange_name: str, routing_key: Optional[str] = None) -> bool:
        """Queue a healthcare message for transmission"""
        try:
            if routing_key is None:
                routing_key = f"healthcare.{message.data_type.value}.{message.priority}"
            
            message_data = json.dumps(message.to_dict())
            properties = f"priority=>{message.priority}"
            
            async with self.pool.acquire() as connection:
                await connection.execute(
                    "SELECT mq.publish($1, $2, $3, $4)",
                    exchange_name, routing_key, message_data, properties
                )
            
            logger.info(f"Queued message {message.message_id} to exchange '{exchange_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to queue message {message.message_id}: {str(e)}")
            return False
    
    async def consume_messages(self, queue_name: str, channel_id: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        """Consume messages from queue"""
        try:
            async with self.pool.acquire() as connection:
                # Open channel
                await connection.execute(
                    "SELECT mq.open_channel($1, $2)",
                    queue_name, channel_id
                )
                
                # Consume messages
                messages = []
                for _ in range(limit):
                    result = await connection.fetchrow(
                        "SELECT * FROM mq.consume($1, $2)",
                        queue_name, channel_id
                    )
                    
                    if result and result[0]:  # message_id exists
                        message_data = {
                            'message_id': result[0],
                            'routing_key': result[1],
                            'payload': json.loads(result[2]) if result[2] else {},
                            'properties': result[3],
                            'delivery_id': result[4]
                        }
                        messages.append(message_data)
                    else:
                        break  # No more messages
                
                logger.debug(f"Consumed {len(messages)} messages from queue '{queue_name}'")
                return messages
        except Exception as e:
            logger.error(f"Failed to consume messages from queue '{queue_name}': {str(e)}")
            return []
    
    async def acknowledge_message(self, queue_name: str, delivery_id: int, channel_id: int = 1) -> bool:
        """Acknowledge successful message processing"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute(
                    "SELECT mq.acknowledge($1, $2, $3)",
                    queue_name, channel_id, delivery_id
                )
            
            logger.debug(f"Acknowledged message delivery_id {delivery_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge message {delivery_id}: {str(e)}")
            return False
    
    async def store_transmission_result(self, result: TransmissionResult) -> bool:
        """Store transmission result for tracking and analytics"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO healthcare_transmissions 
                    (message_id, status, protocol_used, timestamp, error_message, retry_count, response_data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (message_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    protocol_used = EXCLUDED.protocol_used,
                    timestamp = EXCLUDED.timestamp,
                    error_message = EXCLUDED.error_message,
                    retry_count = EXCLUDED.retry_count,
                    response_data = EXCLUDED.response_data
                """,
                    result.message_id,
                    result.status.value,
                    result.protocol_used.value,
                    result.timestamp,
                    result.error_message,
                    result.retry_count,
                    json.dumps(result.response_data) if result.response_data else None
                )
            
            logger.debug(f"Stored transmission result for message {result.message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store transmission result: {str(e)}")
            return False
    
    async def get_failed_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get failed messages for retry processing"""
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch("""
                    SELECT message_id, status, protocol_used, error_message, retry_count
                    FROM healthcare_transmissions
                    WHERE status IN ('failed', 'retry') AND retry_count < 3
                    ORDER BY timestamp ASC
                    LIMIT $1
                """, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get failed messages: {str(e)}")
            return []
    
    async def setup_healthcare_tables(self) -> bool:
        """Setup healthcare-specific tables"""
        try:
            async with self.pool.acquire() as connection:
                # Create healthcare transmissions tracking table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS healthcare_transmissions (
                        id SERIAL PRIMARY KEY,
                        message_id VARCHAR(255) UNIQUE NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        protocol_used VARCHAR(20) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        response_data JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create index for efficient querying
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_healthcare_transmissions_status 
                    ON healthcare_transmissions (status)
                """)
                
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_healthcare_transmissions_timestamp 
                    ON healthcare_transmissions (timestamp)
                """)
                
                # Create healthcare facilities table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS healthcare_facilities (
                        facility_id VARCHAR(100) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        type VARCHAR(50) NOT NULL,
                        location VARCHAR(255),
                        phone_number VARCHAR(20),
                        email VARCHAR(255),
                        network_capabilities JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                logger.info("Healthcare database tables setup completed")
                return True
        except Exception as e:
            logger.error(f"Failed to setup healthcare tables: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """Perform database health check"""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False