-- Health-specific functions for protocol selection and message handling

-- Network detection function
CREATE OR REPLACE FUNCTION mq.update_network_status(
    p_channel_id bigint,
    p_network_type text,
    p_bandwidth int DEFAULT NULL
) RETURNS void AS $$ 
BEGIN
    INSERT INTO mq.network_status (channel_id, network_type, bandwidth_kbps, last_updated)
    VALUES (p_channel_id, p_network_type, p_bandwidth, now()) 
    ON CONFLICT (channel_id) DO UPDATE 
    SET 
        network_type = EXCLUDED.network_type,
        bandwidth_kbps = EXCLUDED.bandwidth_kbps,
        last_updated = now();
END;
$$ LANGUAGE plpgsql;

-- Function to fragment messages based on protocol
CREATE FUNCTION mq.fragment_message(
    p_message_id bigint,
    p_protocol text
) RETURNS int AS $$
DECLARE v_body text;
v_max_size int;
v_fragment_count int := 0;
v_chunk text;
BEGIN -- Get message body
SELECT body::text INTO v_body
FROM mq.message
WHERE message_id = p_message_id;
-- Set max size based on protocol
CASE p_protocol
    WHEN 'sms' THEN v_max_size := 140; -- Leave room for headers
    WHEN 'ussd' THEN v_max_size := 150;
    WHEN 'lorawan' THEN v_max_size := 200;
    ELSE v_max_size := 65000; -- Default large size
END CASE;
-- Fragment if needed
WHILE length(v_body) > 0 LOOP v_fragment_count := v_fragment_count + 1;
v_chunk := substr(v_body, 1, v_max_size);
v_body := substr(v_body, v_max_size + 1);
INSERT INTO mq.message_fragments (
        message_id,
        fragment_number,
        fragment_data,
        fragment_size,
        protocol
    )
VALUES (
        p_message_id,
        v_fragment_count,
        v_chunk,
        length(v_chunk),
        p_protocol
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
DECLARE v_original_size int;
v_body json;
BEGIN
SELECT body,
    length(body::text) INTO v_body,
    v_original_size
FROM mq.message
WHERE message_id = p_message_id;
-- For now, simulate compression by storing metadata
-- In production, call external compression service
UPDATE mq.message
SET original_size = v_original_size,
    compressed_size = v_original_size * 0.3,
    -- Simulated 70% compression
    compression_type = p_compression_type
WHERE message_id = p_message_id;
END;
$$ LANGUAGE plpgsql;
-- Smart protocol selection
CREATE FUNCTION mq.select_protocol(
    p_message_id bigint,
    p_channel_id bigint
) RETURNS text AS $$
DECLARE v_message RECORD;
v_network text;
v_bandwidth int;
v_protocol text;
BEGIN -- Get message details
SELECT * INTO v_message
FROM mq.message
WHERE message_id = p_message_id;
-- Get network status
SELECT network_type,
    bandwidth_kbps INTO v_network,
    v_bandwidth
FROM mq.network_status
WHERE channel_id = p_channel_id;
-- Decision tree for protocol selection
IF v_message.priority = 1
AND v_message.compressed_size < 140 THEN v_protocol := 'sms';
-- Critical and small: use most reliable
ELSIF v_network = 'offline' THEN v_protocol := 'store';
-- Store for later
ELSIF v_network IN ('2G', 'EDGE') THEN IF v_message.compressed_size < 150 THEN v_protocol := 'ussd';
ELSE v_protocol := 'sms_multipart';
END IF;
ELSIF v_network = '3G'
AND v_bandwidth > 100 THEN v_protocol := 'http_compressed';
ELSIF v_network = '4G' THEN v_protocol := 'https';
ELSE v_protocol := 'lorawan';
-- Fallback for rural
END IF;
-- Log protocol selection
INSERT INTO mq.message_protocol (message_id, current_protocol)
VALUES (p_message_id, v_protocol) ON CONFLICT (message_id) DO
UPDATE
SET current_protocol = EXCLUDED.current_protocol,
    protocol_history = mq.message_protocol.protocol_history || jsonb_build_object('protocol', v_protocol, 'timestamp', now());
RETURN v_protocol;
END;
$$ LANGUAGE plpgsql;