#!/usr/bin/env python3
"""
Update cleanup function fix
"""

import psycopg2

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
            # Drop old function and create new one
            cur.execute("""
                DROP FUNCTION IF EXISTS mq.cleanup_expired_messages();
                
                CREATE OR REPLACE FUNCTION mq.cleanup_expired_messages()
                RETURNS void AS $$
                BEGIN
                    -- Delete from message_waiting first (FK constraint)
                    DELETE FROM mq.message_waiting 
                    WHERE message_id IN (
                        SELECT message_id FROM mq.message 
                        WHERE ttl < now()
                    );
                    
                    -- Then delete expired messages
                    DELETE FROM mq.message 
                    WHERE ttl < now();
                END;
                $$ LANGUAGE plpgsql;
            """)
            
        connection.commit()
        print("✓ Cleanup function updated successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    main()