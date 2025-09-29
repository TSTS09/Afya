#!/usr/bin/env python3
"""
Debug retry mechanism
"""

import psycopg2
import json

def main():
    # Database connection
    connection = psycopg2.connect(
        host='localhost',
        database='pg_mq_poc',
        user='postgres',
        password='Christelle09123'
    )
    
    try:
        with connection.cursor() as cur:
            # Clean start
            cur.execute("DELETE FROM mq.delivery")
            cur.execute("DELETE FROM mq.message_waiting") 
            cur.execute("DELETE FROM mq.message")
            cur.execute("DELETE FROM mq.queue WHERE queue_name = 'Debug Queue'")
            cur.execute("DELETE FROM mq.exchange WHERE exchange_name = 'Debug Test'")
            
            # Create test setup
            cur.execute("CALL mq.create_exchange('Debug Test')")
            cur.execute("CALL mq.create_queue('Debug Test', 'Debug Queue', '^debug-.*$')")
            
            # Publish a message
            cur.execute("""
                CALL mq.publish(
                    'Debug Test',
                    'debug-test-1',
                    '{"test": "retry"}',
                    'priority=>1'
                )
            """)
            
            # Check initial retry count
            cur.execute("""
                SELECT retry_count FROM mq.message 
                WHERE routing_key = 'debug-test-1'
            """)
            result = cur.fetchone()
            print(f"Initial retry count: {result[0] if result else 'NOT FOUND'}")
            
            # Open channel and consume
            cur.execute("CALL mq.open_channel('Debug Queue', 1)")
            
            # Get delivery
            cur.execute("""
                SELECT delivery_id, message_id FROM mq.delivery 
                ORDER BY delivery_id DESC LIMIT 1
            """)
            delivery_result = cur.fetchone()
            
            if delivery_result:
                delivery_id, message_id = delivery_result
                print(f"Found delivery_id: {delivery_id}, message_id: {message_id}")
                
                # Check retry count before NACK
                cur.execute("""
                    SELECT retry_count FROM mq.message 
                    WHERE message_id = %s
                """, (message_id,))
                result = cur.fetchone()
                print(f"Retry count before NACK: {result[0] if result else 'NOT FOUND'}")
                
                # NACK the message
                cur.execute("CALL mq.nack(%s, '30 seconds')", (delivery_id,))
                print(f"Called NACK on delivery {delivery_id}")
                
                # Check retry count after NACK
                cur.execute("""
                    SELECT retry_count FROM mq.message 
                    WHERE message_id = %s
                """, (message_id,))
                result = cur.fetchone()
                print(f"Retry count after NACK: {result[0] if result else 'NOT FOUND'}")
                
                # Check if in message_waiting
                cur.execute("""
                    SELECT COUNT(*) FROM mq.message_waiting 
                    WHERE message_id = %s
                """, (message_id,))
                result = cur.fetchone()
                print(f"In message_waiting: {result[0] if result else 'NOT FOUND'}")
                
            else:
                print("❌ No delivery found!")
        
        connection.commit()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    main()