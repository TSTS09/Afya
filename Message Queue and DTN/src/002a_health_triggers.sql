-- Health-specific trigger enhancements

-- Enhanced message insertion with priority assignment
CREATE OR REPLACE FUNCTION mq.insert_message()
RETURNS TRIGGER AS $$
DECLARE
    v_priority int;
    v_data_type text;
    v_ttl interval;
BEGIN
    -- Extract data type from headers if present
    v_data_type := NEW.headers->'data_type';
    
    -- Get priority from health rules if data type is known
    IF v_data_type IS NOT NULL THEN
        SELECT priority_default, ttl 
        INTO v_priority, v_ttl
        FROM mq.health_data_rules
        WHERE data_type = v_data_type;
    END IF;
    
    -- Override with explicit priority if provided
    IF NEW.headers ? 'priority' THEN
        v_priority := (NEW.headers->'priority')::int;
    END IF;
    
    -- Default priority if not set
    IF v_priority IS NULL THEN
        v_priority := 5;
    END IF;

    INSERT INTO mq.message(
        exchange_id, routing_key, body, headers, publish_time, 
        queue_id, priority, data_type, ttl
    )
    SELECT 
        NEW.exchange_id, 
        NEW.routing_key, 
        NEW.body, 
        NEW.headers, 
        NEW.publish_time, 
        q.queue_id,
        v_priority,
        v_data_type,
        COALESCE(now() + v_ttl, now() + interval '24 hours')
    FROM mq.queue q
    WHERE NEW.exchange_id = q.exchange_id 
        AND NEW.routing_key ~ q.routing_key_pattern
    ON CONFLICT DO NOTHING;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Clean up expired messages
CREATE OR REPLACE FUNCTION mq.cleanup_expired_messages()
RETURNS void AS $$
BEGIN
    DELETE FROM mq.message 
    WHERE ttl < now()
    AND message_id IN (
        SELECT message_id FROM mq.message_waiting
    );
END;
$$ LANGUAGE plpgsql;