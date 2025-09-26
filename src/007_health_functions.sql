-- Track network conditions per channel/facility
CREATE TABLE mq.network_status (
    channel_id bigint REFERENCES mq.channel(channel_id),
    facility_id text, -- 'Accra-General-Hospital'
    network_type text, -- '4G', '3G', '2G', 'EDGE', 'offline'
    bandwidth_kbps int,
    latency_ms int,
    packet_loss_percent decimal(5,2),
    last_updated timestamptz DEFAULT now(),
    is_active boolean DEFAULT true
);

-- Network detection function
CREATE FUNCTION mq.update_network_status(
    p_channel_id bigint,
    p_network_type text,
    p_bandwidth int DEFAULT NULL
) RETURNS void AS $$
BEGIN
    INSERT INTO mq.network_status (channel_id, network_type, bandwidth_kbps)
    VALUES (p_channel_id, p_network_type, p_bandwidth)
    ON CONFLICT (channel_id) 
    DO UPDATE SET 
        network_type = EXCLUDED.network_type,
        bandwidth_kbps = EXCLUDED.bandwidth_kbps,
        last_updated = now();
END;
$$ LANGUAGE plpgsql;

-- Fragment large messages for SMS/USSD
CREATE TABLE mq.message_fragments (
    fragment_id bigserial PRIMARY KEY,
    message_id bigint REFERENCES mq.message(message_id),
    fragment_number int,
    total_fragments int,
    fragment_data text,
    fragment_size int,
    protocol text, -- 'sms', 'ussd'
    sent boolean DEFAULT false
);

-- Function to fragment messages based on protocol
CREATE FUNCTION mq.fragment_message(
    p_message_id bigint,
    p_protocol text
) RETURNS int AS $$
DECLARE
    v_body text;
    v_max_size int;
    v_fragment_count int := 0;
    v_chunk text;
BEGIN
    -- Get message body
    SELECT body::text INTO v_body FROM mq.message WHERE message_id = p_message_id;
    
    -- Set max size based on protocol
    CASE p_protocol
        WHEN 'sms' THEN v_max_size := 140; -- Leave room for headers
        WHEN 'ussd' THEN v_max_size := 150;
        WHEN 'lorawan' THEN v_max_size := 200;
        ELSE v_max_size := 65000; -- Default large size
    END CASE;
    
    -- Fragment if needed
    WHILE length(v_body) > 0 LOOP
        v_fragment_count := v_fragment_count + 1;
        v_chunk := substr(v_body, 1, v_max_size);
        v_body := substr(v_body, v_max_size + 1);
        
        INSERT INTO mq.message_fragments (
            message_id, fragment_number, fragment_data, 
            fragment_size, protocol
        ) VALUES (
            p_message_id, v_fragment_count, v_chunk,
            length(v_chunk), p_protocol
        );
    END LOOP;
    
    -- Update total fragments
    UPDATE mq.message_fragments 
    SET total_fragments = v_fragment_count 
    WHERE message_id = p_message_id;
    
    RETURN v_fragment_count;
END;
$$ LANGUAGE plpgsql;

-- Compression wrapper (you'd implement actual compression in application layer)
CREATE FUNCTION mq.compress_message(
    p_message_id bigint,
    p_compression_type text DEFAULT 'zstd'
) RETURNS void AS $$
DECLARE
    v_original_size int;
    v_body json;
BEGIN
    SELECT body, length(body::text) 
    INTO v_body, v_original_size 
    FROM mq.message 
    WHERE message_id = p_message_id;
    
    -- For now, simulate compression by storing metadata
    -- In production, call external compression service
    UPDATE mq.message 
    SET 
        original_size = v_original_size,
        compressed_size = v_original_size * 0.3, -- Simulated 70% compression
        compression_type = p_compression_type
    WHERE message_id = p_message_id;
END;
$$ LANGUAGE plpgsql;

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

-- Smart protocol selection
CREATE FUNCTION mq.select_protocol(
    p_message_id bigint,
    p_channel_id bigint
) RETURNS text AS $$
DECLARE
    v_message RECORD;
    v_network text;
    v_bandwidth int;
    v_protocol text;
BEGIN
    -- Get message details
    SELECT * INTO v_message 
    FROM mq.message 
    WHERE message_id = p_message_id;
    
    -- Get network status
    SELECT network_type, bandwidth_kbps 
    INTO v_network, v_bandwidth
    FROM mq.network_status
    WHERE channel_id = p_channel_id;
    
    -- Decision tree for protocol selection
    IF v_message.priority = 1 AND v_message.compressed_size < 140 THEN
        v_protocol := 'sms'; -- Critical and small: use most reliable
    ELSIF v_network = 'offline' THEN
        v_protocol := 'store'; -- Store for later
    ELSIF v_network IN ('2G', 'EDGE') THEN
        IF v_message.compressed_size < 150 THEN
            v_protocol := 'ussd';
        ELSE
            v_protocol := 'sms_multipart';
        END IF;
    ELSIF v_network = '3G' AND v_bandwidth > 100 THEN
        v_protocol := 'http_compressed';
    ELSIF v_network = '4G' THEN
        v_protocol := 'https';
    ELSE
        v_protocol := 'lorawan'; -- Fallback for rural
    END IF;
    
    -- Log protocol selection
    INSERT INTO mq.message_protocol (message_id, current_protocol)
    VALUES (p_message_id, v_protocol)
    ON CONFLICT (message_id) 
    DO UPDATE SET 
        current_protocol = EXCLUDED.current_protocol,
        protocol_history = mq.message_protocol.protocol_history || 
            jsonb_build_object('protocol', v_protocol, 'timestamp', now());
    
    RETURN v_protocol;
END;
$$ LANGUAGE plpgsql;

