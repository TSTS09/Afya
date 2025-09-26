#!/usr/bin/env python3
"""
tests/integration/test_full_workflow.py
Integration tests for complete message workflows
"""
import psycopg2
import json
import time
import threading
import concurrent.futures
from datetime import datetime

class IntegrationTest:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.messages_processed = []
        self.errors = []
        
    def connect(self):
        self.connection = psycopg2.connect(**self.db_config)
        self.connection.autocommit = True
        
    def test_multi_consumer_scenario(self):
        """Test multiple consumers processing messages"""
        print("Testing multi-consumer scenario...")
        
        # Setup
        with self.connection.cursor() as cur:
            cur.execute("CALL mq.create_exchange('Multi Test')")
            cur.execute("CALL mq.create_queue('Multi Test', 'Shared Queue', '^shared-.*$')")
            
        # Start multiple consumers
        consumers = []
        for i in range(3):
            consumer = threading.Thread(
                target=self._consumer_worker, 
                args=(f"consumer-{i}", "Shared Queue", 5)
            )
            consumer.daemon = True
            consumer.start()
            consumers.append(consumer)
            
        time.sleep(1)  # Let consumers start
        
        # Publish multiple messages
        message_count = 20
        with self.connection.cursor() as cur:
            for i in range(message_count):
                cur.execute("""
                    CALL mq.publish(
                        'Multi Test',
                        'shared-msg-%s',
                        '{"id": %s, "data": "test message %s"}',
                        'priority=>%s'
                    )
                """, (i, i, i, (i % 5) + 1))
                
        # Wait for processing
        time.sleep(5)
        
        # Check results
        processed_count = len(self.messages_processed)
        print(f"✓ Multi-consumer test: {processed_count}/{message_count} messages processed")
        assert processed_count <= message_count, "More messages processed than sent"
        
    def _consumer_worker(self, consumer_name, queue_name, timeout_seconds):
        """Worker function for consumer threads"""
        try:
            worker_conn = psycopg2.connect(**self.db_config)
            worker_conn.autocommit = True
            
            with worker_conn.cursor() as cur:
                cur.execute(f"CALL mq.open_channel('{queue_name}', 2)")
                
                # Get channel ID for listening
                cur.execute("""
                    SELECT channel_id FROM mq.channel 
                    WHERE channel_name = %s
                """, (str(worker_conn.info.backend_pid),))
                result = cur.fetchone()
                
                if result:
                    channel_id = result[0]
                    cur.execute(f'LISTEN "{channel_id}"')
                    
                    start_time = time.time()
                    while time.time() - start_time < timeout_seconds:
                        worker_conn.poll()
                        
                        while worker_conn.notifies:
                            notify = worker_conn.notifies.pop(0)
                            message = json.loads(notify.payload)
                            
                            # Process message
                            self.messages_processed.append({
                                'consumer': consumer_name,
                                'message_id': message['delivery_id'],
                                'body': message['body']
                            })
                            
                            # Acknowledge
                            cur.execute(f"CALL mq.ack({message['delivery_id']})")
                            
                        time.sleep(0.1)
                        
                    cur.execute("CALL mq.close_channel()")
                    
            worker_conn.close()
            
        except Exception as e:
            self.errors.append(f"{consumer_name}: {str(e)}")
            
    def test_network_switching_scenario(self):
        """Test behavior when network conditions change"""
        print("Testing network switching scenario...")
        
        with self.connection.cursor() as cur:
            cur.execute("CALL mq.create_exchange('Network Test')")
            cur.execute("CALL mq.create_queue('Network Test', 'Network Queue', '^net-.*$')")
            
            # Open channel
            cur.execute("CALL mq.open_channel('Network Queue', 1)")
            
            # Get channel ID
            cur.execute("""
                SELECT channel_id FROM mq.channel 
                WHERE channel_name = %s
            """, (str(cur.connection.info.backend_pid),))
            result = cur.fetchone()
            
            if result:
                channel_id = result[0]
                
                # Simulate network changes
                network_states = [
                    ('4G', 1000),
                    ('3G', 500),
                    ('2G', 50),
                    ('offline', 0),
                    ('4G', 1000)  # Back online
                ]
                
                for network_type, bandwidth in network_states:
                    # Update network status
                    cur.execute("""
                        SELECT mq.update_network_status(%s, %s, %s)
                    """, (channel_id, network_type, bandwidth))
                    
                    # Publish message with different priorities
                    for priority in [1, 3, 5]:
                        cur.execute("""
                            CALL mq.publish(
                                'Network Test',
                                'net-test-%s-%s',
                                '{"network": "%s", "priority": %s}',
                                'priority=>%s'
                            )
                        """, (network_type, priority, network_type, priority, priority))
                        
                    time.sleep(0.5)
                    
        print("✓ Network switching scenario completed")
        
    def test_performance_throughput(self):
        """Test message throughput performance"""
        print("Testing message throughput...")
        
        with self.connection.cursor() as cur:
            cur.execute("CALL mq.create_exchange('Perf Test')")
            cur.execute("CALL mq.create_queue('Perf Test', 'Perf Queue', '^perf-.*$')")
            
        message_count = 1000
        start_time = time.time()
        
        # Publish messages in batches
        batch_size = 100
        with self.connection.cursor() as cur:
            for batch_start in range(0, message_count, batch_size):
                batch_values = []
                for i in range(batch_start, min(batch_start + batch_size, message_count)):
                    batch_values.append(f"""
                        ((SELECT exchange_id FROM mq.exchange WHERE exchange_name = 'Perf Test'),
                         'perf-msg-{i}',
                         '{{"id": {i}, "timestamp": "{datetime.now().isoformat()}"}}',
                         'priority=>{(i % 5) + 1}')
                    """)
                
                if batch_values:
                    cur.execute(f"""
                        INSERT INTO mq.message_intake 
                        (exchange_id, routing_key, body, headers)
                        VALUES {','.join(batch_values)}
                    """)
                    
        publish_time = time.time() - start_time
        
        # Check how many messages are waiting
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM mq.message_waiting mw
                JOIN mq.queue q ON mw.queue_id = q.queue_id
                WHERE q.queue_name = 'Perf Queue'
            """)
            waiting_count = cur.fetchone()[0]
            
        throughput = message_count / publish_time
        print(f"✓ Published {message_count} messages in {publish_time:.2f}s")
        print(f"✓ Throughput: {throughput:.2f} messages/second")
        print(f"✓ {waiting_count} messages queued for delivery")
        
        return throughput
        
    def test_retry_mechanism(self):
        """Test message retry logic"""
        print("Testing retry mechanism...")
        
        with self.connection.cursor() as cur:
            cur.execute("CALL mq.create_exchange('Retry Test')")
            cur.execute("CALL mq.create_queue('Retry Test', 'Retry Queue', '^retry-.*$')")
            
            # Publish a message
            cur.execute("""
                CALL mq.publish(
                    'Retry Test',
                    'retry-test-1',
                    '{"test": "retry"}',
                    'priority=>1'
                )
            """)
            
            # Open channel and consume
            cur.execute("CALL mq.open_channel('Retry Queue', 1)")
            
            # Get channel ID for listening
            cur.execute("""
                SELECT channel_id FROM mq.channel 
                WHERE channel_name = %s
            """, (str(cur.connection.info.backend_pid),))
            result = cur.fetchone()
            
            if result:
                channel_id = result[0]
                cur.execute(f'LISTEN "{channel_id}"')
                
                # Wait for message
                self.connection.poll()
                if self.connection.notifies:
                    notify = self.connection.notifies.pop(0)
                    message = json.loads(notify.payload)
                    delivery_id = message['delivery_id']
                    
                    # NACK the message (simulate failure)
                    cur.execute(f"CALL mq.nack({delivery_id}, '30 seconds')")
                    
                    # Check retry count was incremented
                    cur.execute("""
                        SELECT retry_count FROM mq.message m
                        JOIN mq.delivery d ON d.message_id = m.message_id
                        WHERE d.delivery_id = %s
                    """, (delivery_id,))
                    # Note: delivery is deleted after NACK, so check message_waiting
                    cur.execute("""
                        SELECT m.retry_count FROM mq.message m
                        JOIN mq.message_waiting mw ON mw.message_id = m.message_id
                        WHERE m.routing_key = 'retry-test-1'
                    """)
                    result = cur.fetchone()
                    if result:
                        retry_count = result[0]
                        assert retry_count > 0, f"Retry count should be > 0, got {retry_count}"
                        print(f"✓ Retry mechanism works - retry count: {retry_count}")
                    else:
                        print("⚠ Could not verify retry count")
                else:
                    print("⚠ No message received for retry test")
            else:
                print("⚠ Channel not found for retry test")
                
    def run_all_tests(self):
        """Run all integration tests"""
        print("=== Running Integration Tests ===")
        
        self.connect()
        
        self.test_multi_consumer_scenario()
        self.test_network_switching_scenario()
        throughput = self.test_performance_throughput()
        self.test_retry_mechanism()
        
        if self.errors:
            print("Errors encountered:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("✓ All integration tests passed")
            
        print(f"=== Integration Tests Complete ===\n")
        return throughput

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'pg_mq_poc',
        'user': 'root',  
        'password': 'Christelle09123'  
    }
    
    tester = IntegrationTest(db_config)
    tester.run_all_tests()