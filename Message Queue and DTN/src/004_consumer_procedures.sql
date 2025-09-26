/* REGISTER */

CREATE PROCEDURE mq.open_channel(queue_name text, maximum_messages int DEFAULT 1) 
LANGUAGE plpgsql
AS $$
DECLARE 
  queue_id bigint;
  new_channel_id bigint;
  new_channel_name text;
BEGIN
  SELECT q.queue_id INTO queue_id FROM mq.queue q WHERE q.queue_name = open_channel.queue_name;
  IF queue_id IS NULL THEN
    RAISE WARNING 'No such queue';
    RETURN;
  END IF;
  new_channel_name := text(pg_backend_pid());
  SELECT channel_id FROM mq.channel c WHERE c.channel_name = new_channel_name INTO new_channel_id;
  IF new_channel_id IS NULL THEN
    INSERT INTO mq.channel(channel_name, queue_id, maximum_messages) 
      VALUES (new_channel_name, queue_id, open_channel.maximum_messages) 
      RETURNING channel_id INTO new_channel_id;
  END IF;
  EXECUTE format('LISTEN "%s"', new_channel_id);
END;
$$;

CREATE PROCEDURE mq.close_channel() 
LANGUAGE plpgsql 
AS $$
DECLARE 
  current_channel_id bigint;
  current_channel_name text;
BEGIN
  current_channel_name := text(pg_backend_pid());
  SELECT channel_id FROM mq.channel c WHERE c.channel_name = current_channel_name INTO current_channel_id;
  IF current_channel_id IS NULL THEN
    RETURN;
  END IF;
  CALL mq.close_channel(current_channel_id);
END;
$$;

CREATE PROCEDURE mq.close_channel(close_channel_id bigint) 
LANGUAGE plpgsql 
AS $$
BEGIN
  EXECUTE format('UNLISTEN "%s"', close_channel_id);
  INSERT INTO mq.message_waiting 
    (SELECT message_id, queue_id FROM mq.delivery WHERE channel_id = close_channel_id)
    ON CONFLICT DO NOTHING;
  DELETE FROM mq.channel c WHERE c.channel_id = close_channel_id;
END;
$$;

CREATE PROCEDURE mq.close_dead_channels()
LANGUAGE plpgsql
AS $$
DECLARE
  dead_channel record;
BEGIN
  FOR dead_channel IN (SELECT * FROM mq.channel c WHERE c.channel_name::int NOT IN (SELECT pid FROM pg_catalog.pg_stat_activity psa)) LOOP
    CALL mq.close_channel(dead_channel.channel_id);
  END LOOP;
END;
$$;

CREATE PROCEDURE mq.sweep_waiting_message (queue_name text) 
LANGUAGE plpgsql 
AS $$
DECLARE 
  queue_id bigint;
  current_channel record;
BEGIN
  SELECT q.queue_id INTO queue_id FROM mq.queue q WHERE q.queue_name = sweep_waiting_message.queue_name;
  IF queue_id IS NULL THEN
    RAISE WARNING 'No such queue';
    RETURN;
  END IF;
  CALL mq.sweep_waiting_message(queue_id);
END;
$$;

CREATE PROCEDURE mq.sweep_waiting_message (queue_id bigint) 
LANGUAGE plpgsql 
AS $$
DECLARE
  selected_message_id bigint;
  selected_channel record;
BEGIN
  SELECT mq.take_waiting_message(queue_id) INTO selected_message_id;
  IF selected_message_id IS NULL THEN
    RETURN;
  END IF;

  SELECT * FROM mq.take_waiting_channel(queue_id) INTO selected_channel;
  IF selected_channel IS NULL THEN
    RETURN;
  END IF;

  INSERT INTO mq.delivery(message_id, channel_id, slot, queue_id)
      VALUES (selected_message_id, selected_channel.channel_id, selected_channel.slot, queue_id);
END;
$$;

/* ACK */ 
CREATE PROCEDURE mq.ack (delivery_id bigint) 
LANGUAGE plpgsql
AS $$
DECLARE
  delivery RECORD;
BEGIN
  SELECT * INTO delivery  
    FROM mq.delivery d WHERE d.delivery_id = ack.delivery_id;
  IF delivery IS NULL THEN
    RAISE WARNING 'No such delivery';
    RETURN;
  END IF;
  DELETE FROM mq.message m WHERE m.message_id = delivery.message_id;
  INSERT INTO mq.channel_waiting(channel_id, slot, queue_id) 
    VALUES (delivery.channel_id, delivery.slot, delivery.queue_id)
    ON CONFLICT DO NOTHING;
END;
$$;


/* NACK */
-- Enhanced NACK with smart retry
CREATE OR REPLACE PROCEDURE mq.nack(
    delivery_id bigint, 
    retry_after interval DEFAULT '0s'::interval
) 
LANGUAGE plpgsql
AS $$
DECLARE
    delivery RECORD;
    v_retry_interval interval;
    v_network_type text;
BEGIN
    SELECT d.*, m.retry_count, m.priority 
    INTO delivery  
    FROM mq.delivery d 
    JOIN mq.message m ON m.message_id = d.message_id
    WHERE d.delivery_id = nack.delivery_id;
    
    IF delivery IS NULL THEN
        RAISE WARNING 'No such delivery';
        RETURN;
    END IF;
    
    -- Get current network status
    SELECT network_type INTO v_network_type
    FROM mq.network_status
    WHERE channel_id = delivery.channel_id;
    
    -- Calculate retry interval based on priority and network
    IF delivery.priority = 1 THEN -- Critical
        v_retry_interval := interval '30 seconds' * (delivery.retry_count + 1);
    ELSIF v_network_type = 'offline' THEN
        v_retry_interval := interval '5 minutes'; -- Don't retry often when offline
    ELSE
        -- Exponential backoff: 1min, 2min, 4min, 8min...
        v_retry_interval := interval '1 minute' * power(2, delivery.retry_count);
    END IF;
    
    -- Update retry count
    UPDATE mq.message 
    SET retry_count = retry_count + 1
    WHERE message_id = delivery.message_id;
    
    -- Check if max retries exceeded
    IF delivery.retry_count >= 10 THEN
        -- Move to dead letter queue
        INSERT INTO mq.failed_messages (message_id, reason, failed_at)
        VALUES (delivery.message_id, 'max_retries_exceeded', now());
        
        DELETE FROM mq.delivery WHERE delivery_id = nack.delivery_id;
        RETURN;
    END IF;
    
    -- Regular NACK process
    DELETE FROM mq.delivery d WHERE d.delivery_id = nack.delivery_id;
    INSERT INTO mq.message_waiting(message_id, queue_id, not_until_time)
        VALUES (delivery.message_id, delivery.queue_id, now() + v_retry_interval)
        ON CONFLICT DO NOTHING;
    INSERT INTO mq.channel_waiting(channel_id, slot, queue_id) 
        VALUES (delivery.channel_id, delivery.slot, delivery.queue_id)
        ON CONFLICT DO NOTHING;
END;
$$;