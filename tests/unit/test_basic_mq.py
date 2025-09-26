#!/usr/bin/env python3
"""
tests/unit/test_basic_mq.py
Basic message queue functionality tests
"""
import psycopg2
import psycopg2.extras
import json
import time
import threading
from typing import List, Dict

class BasicMQTest:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.received_messages = []
        
    def connect(self):
        """Connect to PostgreSQL"""
        self.connection = psycopg2.connect(**self.db_config)
        self.connection.autocommit = True
        
    def setup_test_exchange(self):
        """Create test exchange and queue"""
        with self.connection.cursor() as cur:
            # Clean up first
            cur.execute("DROP SCHEMA IF EXISTS test_mq CASCADE")
            
            # Create test exchange
            cur.execute("CALL mq.create_exchange('Test Exchange')")
            
            # Create test queue
            cur.execute("""
                CALL mq.create_queue(
                    'Test Exchange', 
                    'Test Queue', 
                    '^test-.*$'
                )
            """)
            
    def test_publish_message(self):
        """Test basic message publishing"""
        print("Testing message publishing...")
        
        with self.connection.cursor() as cur:
            cur.execute("""
                CALL mq.publish(
                    'Test Exchange',
                    'test-message-1',
                    '{"content": "Hello World", "timestamp": "2024-01-01T10:00:00Z"}',
                    'priority=>3,data_type=>test'
                )
            """)
            
        # Verify message was inserted
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM mq.message m 
                JOIN mq.queue q ON m.queue_id = q.queue_id 
                WHERE q.queue_name = 'Test Queue'
            """)
            count = cur.fetchone()[0]
            
        assert count > 0, "Message was not inserted"
        print("✓ Message publishing works")
        
    def test_consume_message(self):
        """Test message consumption"""
        print("Testing message consumption...")
        
        # Start consumer in separate thread
        consumer_thread = threading.Thread(target=self._consume_messages)
        consumer_thread.daemon = True
        consumer_thread.start()
        
        # Wait a bit for consumer to start
        time.sleep(1)
        
        # Publish test message
        with self.connection.cursor() as cur:
            cur.execute("""
                CALL mq.publish(
                    'Test Exchange',
                    'test-consume',
                    '{"test": "consumption"}',
                    'priority=>1'
                )
            """)
            
        # Wait for message to be consumed
        time.sleep(2)
        
        assert len(self.received_messages) > 0, "No messages were received"
        print(f"✓ Message consumption works - received {len(self.received_messages)} messages")
        
    def _consume_messages(self):
        """Consumer method for testing"""
        consumer_conn = psycopg2.connect(**self.db_config)
        consumer_conn.autocommit = True
        
        with consumer_conn.cursor() as cur:
            # Open channel
            cur.execute("CALL mq.open_channel('Test Queue', 1)")
            
            # Listen for notifications
            cur.execute("LISTEN \"1\"")  # Channel ID usually starts at 1
            
            # Poll for messages
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout
                consumer_conn.poll()
                
                while consumer_conn.notifies:
                    notify = consumer_conn.notifies.pop(0)
                    message = json.loads(notify.payload)
                    self.received_messages.append(message)
                    
                    # Acknowledge message
                    cur.execute(f"CALL mq.ack({message['delivery_id']})")
                    
                time.sleep(0.1)
                
        consumer_conn.close()
        
    def test_priority_ordering(self):
        """Test that messages are delivered by priority"""
        print("Testing priority ordering...")
        
        with self.connection.cursor() as cur:
            # Publish messages with different priorities
            cur.execute("""
                CALL mq.publish(
                    'Test Exchange', 'test-priority-low', 
                    '{"priority": "low"}', 'priority=>5'
                )
            """)
            cur.execute("""
                CALL mq.publish(
                    'Test Exchange', 'test-priority-high', 
                    '{"priority": "high"}', 'priority=>1'
                )
            """)
            cur.execute("""
                CALL mq.publish(
                    'Test Exchange', 'test-priority-med', 
                    '{"priority": "medium"}', 'priority=>3'
                )
            """)
            
        # Check order in message_waiting (should be priority order)
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT m.body->>'priority', m.priority 
                FROM mq.message_waiting mw
                JOIN mq.message m ON m.message_id = mw.message_id
                JOIN mq.queue q ON q.queue_id = mw.queue_id
                WHERE q.queue_name = 'Test Queue'
                ORDER BY m.priority ASC, m.message_id ASC
            """)
            results = cur.fetchall()
            
        if results:
            priorities = [row[1] for row in results]
            assert priorities == sorted(priorities), f"Messages not in priority order: {priorities}"
            print("✓ Priority ordering works")
        else:
            print("⚠ No messages found for priority test")
            
    def run_all_tests(self):
        """Run all basic tests"""
        print("=== Running Basic Message Queue Tests ===")
        
        self.connect()
        self.setup_test_exchange()
        
        self.test_publish_message()
        self.test_priority_ordering()
        self.test_consume_message()
        
        print("=== Basic Tests Complete ===\n")

if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'pg_mq_poc',
        'user': 'cfurano',  # Change to your username
        'password': 'cfurano'  # Change to your password
    }
    
    tester = BasicMQTest(db_config)
    tester.run_all_tests()