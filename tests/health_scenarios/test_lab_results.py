#!/usr/bin/env python3
"""
tests/health_scenarios/test_lab_results.py
Test health-specific message handling
"""
import psycopg2
import json
import time

class HealthDataTest:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        
    def connect(self):
        self.connection = psycopg2.connect(**self.db_config)
        self.connection.autocommit = True
        
    def setup_health_exchange(self):
        """Set up health-specific exchange and queues"""
        with self.connection.cursor() as cur:
            # Create health exchange
            cur.execute("CALL mq.create_exchange('Health Exchange')")
            
            # Create queues for different data types
            cur.execute("""
                CALL mq.create_queue(
                    'Health Exchange', 
                    'Lab Results Queue', 
                    '^lab-.*$'
                )
            """)
            cur.execute("""
                CALL mq.create_queue(
                    'Health Exchange', 
                    'Prescription Queue', 
                    '^prescription-.*$'
                )
            """)
            cur.execute("""
                CALL mq.create_queue(
                    'Health Exchange', 
                    'Insurance Queue', 
                    '^insurance-.*$'
                )
            """)
            
    def test_hiv_result_priority(self):
        """Test that HIV results get highest priority"""
        print("Testing HIV result priority...")
        
        with self.connection.cursor() as cur:
            # Publish HIV result (should get priority 1)
            cur.execute("""
                CALL mq.publish(
                    'Health Exchange',
                    'lab-hiv-result-123',
                    '{"patient_id": "P123", "test_type": "HIV", "result": "negative"}',
                    'data_type=>lab_hiv_result,facility_id=>Accra-General'
                )
            """)
            
            # Publish routine lab (should get priority 3)
            cur.execute("""
                CALL mq.publish(
                    'Health Exchange',
                    'lab-routine-456',
                    '{"patient_id": "P456", "test_type": "CBC", "result": "normal"}',
                    'data_type=>lab_routine'
                )
            """)
            
        # Check priorities were assigned correctly
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT m.routing_key, m.priority, m.data_type
                FROM mq.message m
                JOIN mq.queue q ON m.queue_id = q.queue_id
                WHERE q.queue_name = 'Lab Results Queue'
                ORDER BY m.message_id DESC
                LIMIT 2
            """)
            results = cur.fetchall()
            
        hiv_priority = None
        routine_priority = None
        
        for routing_key, priority, data_type in results:
            if 'hiv' in routing_key:
                hiv_priority = priority
            elif 'routine' in routing_key:
                routine_priority = priority
                
        assert hiv_priority == 1, f"HIV result should have priority 1, got {hiv_priority}"
        assert routine_priority == 3, f"Routine lab should have priority 3, got {routine_priority}"
        
        print("✓ HIV results get highest priority")
        
    def test_prescription_routing(self):
        """Test prescription message routing"""
        print("Testing prescription routing...")
        
        with self.connection.cursor() as cur:
            cur.execute("""
                CALL mq.publish(
                    'Health Exchange',
                    'prescription-urgent-789',
                    '{
                        "patient_id": "P789",
                        "medication": "Insulin",
                        "urgency": "high",
                        "pharmacy_id": "PH001"
                    }',
                    'data_type=>prescription,priority=>2'
                )
            """)
            
        # Verify it went to prescription queue
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM mq.message m
                JOIN mq.queue q ON m.queue_id = q.queue_id
                WHERE q.queue_name = 'Prescription Queue'
                AND m.routing_key = 'prescription-urgent-789'
            """)
            count = cur.fetchone()[0]
            
        assert count == 1, "Prescription not routed to correct queue"
        print("✓ Prescription routing works")
        
    def test_message_fragmentation(self):
        """Test message fragmentation for SMS"""
        print("Testing message fragmentation...")
        
        # Create a large message that needs fragmentation
        large_message = {
            "patient_id": "P999",
            "lab_results": {
                "test_" + str(i): f"result_{i}" for i in range(50)
            }
        }
        
        with self.connection.cursor() as cur:
            # Insert message directly to test fragmentation
            cur.execute("""
                INSERT INTO mq.message (
                    exchange_id, routing_key, body, headers, queue_id, data_type
                ) VALUES (
                    (SELECT exchange_id FROM mq.exchange WHERE exchange_name = 'Health Exchange'),
                    'lab-large-999',
                    %s,
                    'data_type=>lab_routine',
                    (SELECT queue_id FROM mq.queue WHERE queue_name = 'Lab Results Queue'),
                    'lab_routine'
                ) RETURNING message_id
            """, (json.dumps(large_message),))
            
            message_id = cur.fetchone()[0]
            
            # Test fragmentation function
            cur.execute("SELECT mq.fragment_message(%s, 'sms')", (message_id,))
            fragment_count = cur.fetchone()[0]
            
        assert fragment_count > 1, f"Large message should be fragmented, got {fragment_count} fragments"
        print(f"✓ Message fragmentation works - {fragment_count} fragments created")
        
    def test_network_status_update(self):
        """Test network status tracking"""
        print("Testing network status updates...")
        
        with self.connection.cursor() as cur:
            # Open a channel first
            cur.execute("CALL mq.open_channel('Lab Results Queue', 1)")
            
            # Get the channel ID
            cur.execute("""
                SELECT channel_id FROM mq.channel 
                WHERE channel_name = %s
            """, (str(cur.connection.info.backend_pid),))
            result = cur.fetchone()
            
            if result:
                channel_id = result[0]
                
                # Update network status
                cur.execute("""
                    SELECT mq.update_network_status(%s, '3G', 500)
                """, (channel_id,))
                
                # Verify status was updated
                cur.execute("""
                    SELECT network_type, bandwidth_kbps 
                    FROM mq.network_status 
                    WHERE channel_id = %s
                """, (channel_id,))
                status = cur.fetchone()
                
                if status:
                    network_type, bandwidth = status
                    assert network_type == '3G', f"Expected 3G, got {network_type}"
                    assert bandwidth == 500, f"Expected 500, got {bandwidth}"
                    print("✓ Network status tracking works")
                else:
                    print("⚠ Network status not found")
            else:
                print("⚠ Channel not found for network test")
                
    def test_ttl_and_cleanup(self):
        """Test message TTL and cleanup"""
        print("Testing message TTL...")
        
        with self.connection.cursor() as cur:
            # Create message with short TTL
            cur.execute("""
                INSERT INTO mq.message (
                    exchange_id, routing_key, body, headers, queue_id, 
                    data_type, ttl
                ) VALUES (
                    (SELECT exchange_id FROM mq.exchange WHERE exchange_name = 'Health Exchange'),
                    'lab-expired-test',
                    '{"test": "expired"}',
                    'data_type=>lab_routine',
                    (SELECT queue_id FROM mq.queue WHERE queue_name = 'Lab Results Queue'),
                    'lab_routine',
                    now() - interval '1 hour'  -- Already expired
                )
            """)
            
            # Run cleanup
            cur.execute("SELECT mq.cleanup_expired_messages()")
            
            # Check if expired message was removed
            cur.execute("""
                SELECT COUNT(*) FROM mq.message 
                WHERE routing_key = 'lab-expired-test'
            """)
            count = cur.fetchone()[0]
            
        assert count == 0, "Expired message was not cleaned up"
        print("✓ TTL and cleanup works")
        
    def run_all_tests(self):
        """Run all health-specific tests"""
        print("=== Running Health Data Tests ===")
        
        self.connect()
        self.setup_health_exchange()
        
        self.test_hiv_result_priority()
        self.test_prescription_routing()
        self.test_message_fragmentation()
        self.test_network_status_update()
        self.test_ttl_and_cleanup()
        
        print("=== Health Tests Complete ===\n")

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'pg_mq_poc',
        'user': 'cfurano',  # Change to your username
        'password': 'cfurano'  # Change to your password
    }
    
    tester = HealthDataTest(db_config)
    tester.run_all_tests()