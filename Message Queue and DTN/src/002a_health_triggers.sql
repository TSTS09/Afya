-- Health-specific trigger enhancements

-- Core utility functions (from 002_triggers.sql)
CREATE FUNCTION mq.notify_channel(delivery_id bigint, message_id bigint, channel_name text)
RETURNS VOID AS $$
DECLARE
  payload TEXT;
BEGIN
  SELECT row_to_json(md) INTO payload 
    FROM (SELECT delivery_id, m.routing_key, m.body, m.headers
      FROM mq.message m
      WHERE m.message_id = notify_channel.message_id) md;
  PERFORM pg_notify(channel_name, payload);
  RAISE NOTICE 'Sent message % to channel %', notify_channel.message_id, channel_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION mq.take_waiting_message(queue_id bigint)
RETURNS bigint AS $$
  DELETE FROM mq.message_waiting mw
  WHERE mw.message_id = (
    SELECT mw.message_id 
    FROM mq.message_waiting mw
    JOIN mq.message m ON m.message_id = mw.message_id
    WHERE mw.queue_id = take_waiting_message.queue_id
      AND (mw.not_until_time IS NULL OR mw.not_until_time <= now())
    ORDER BY 
      m.priority ASC,     -- Priority first
      m.retry_count ASC,  -- Retry count second
      m.message_id ASC    -- Then FIFO
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  ) RETURNING mw.message_id;
$$ LANGUAGE SQL;

CREATE FUNCTION mq.take_waiting_channel(queue_id bigint)
RETURNS SETOF mq.channel_waiting AS $$
  WITH row_to_delete AS (
    SELECT * FROM mq.channel_waiting c
    WHERE c.queue_id = queue_id
    ORDER BY c.since_time
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  ) 
  DELETE FROM mq.channel_waiting cw
  WHERE cw.channel_id = (SELECT channel_id FROM row_to_delete) AND cw.slot = (SELECT slot FROM row_to_delete)
  RETURNING *; 
$$ LANGUAGE SQL;

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

CREATE TRIGGER insert_message_before_insert
BEFORE INSERT ON mq.message_intake
   FOR EACH ROW EXECUTE PROCEDURE mq.insert_message();

-- INSERT MESSAGE WAITING
CREATE FUNCTION mq.insert_message_waiting()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO mq.message_waiting(message_id, queue_id)
  VALUES (NEW.message_id, NEW.queue_id)
  ON CONFLICT DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER insert_message_waiting_after_insert
AFTER INSERT ON mq.message
   FOR EACH ROW EXECUTE PROCEDURE mq.insert_message_waiting();

-- DELIVER MESSAGE
CREATE FUNCTION mq.deliver_message()
RETURNS TRIGGER AS $$
BEGIN
  EXECUTE mq.notify_channel(NEW.delivery_id, NEW.message_id, text(NEW.channel_id));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER deliver_message_after_insert
AFTER INSERT ON mq.delivery
   FOR EACH ROW EXECUTE PROCEDURE mq.deliver_message();

-- CHANNEL INITIALIZE
CREATE FUNCTION mq.channel_initialize()
RETURNS TRIGGER AS $$
BEGIN
  FOR i IN 1..NEW.maximum_messages LOOP
    RAISE NOTICE 'Creating channel waiting slot: %', i;
    INSERT INTO mq.channel_waiting(channel_id, slot, queue_id)
      VALUES (NEW.channel_id, i, NEW.queue_id);
  END LOOP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER channel_initialize_after_insert
AFTER INSERT ON mq.channel
   FOR EACH ROW EXECUTE PROCEDURE mq.channel_initialize();

-- MATCH MESSAGE
CREATE FUNCTION mq.match_message()
RETURNS TRIGGER AS $$
DECLARE
  selected_message_id bigint;
BEGIN
  SELECT mq.take_waiting_message(NEW.queue_id) INTO selected_message_id;
  IF selected_message_id IS NULL THEN
    RETURN NEW;
  END IF;
  INSERT INTO mq.delivery(message_id, channel_id, slot, queue_id)
      VALUES (selected_message_id, NEW.channel_id, NEW.slot, NEW.queue_id);
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER match_message_before_insert
BEFORE INSERT ON mq.channel_waiting
  FOR EACH ROW EXECUTE PROCEDURE mq.match_message();

CREATE FUNCTION mq.match_channel()
RETURNS TRIGGER AS $$
DECLARE
  selected_channel record;
BEGIN
  IF NEW.not_until_time IS NOT NULL AND NEW.not_until_time > now() THEN
    RETURN NEW;
  END IF;
  SELECT * FROM mq.take_waiting_channel(NEW.queue_id) INTO selected_channel;
  IF selected_channel IS NULL THEN
    RETURN NEW;
  END IF;
  INSERT INTO mq.delivery(message_id, channel_id, slot, queue_id)
      VALUES (NEW.message_id, selected_channel.channel_id, selected_channel.slot, NEW.queue_id);
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER match_channel_before_insert
BEFORE INSERT ON mq.message_waiting
  FOR EACH ROW EXECUTE PROCEDURE mq.match_channel();

-- Clean up expired messages
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