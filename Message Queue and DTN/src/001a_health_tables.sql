-- Additional health-specific tables

-- Message protocol tracking
CREATE TABLE mq.message_protocol (
    message_id bigint PRIMARY KEY REFERENCES mq.message(message_id) ON DELETE CASCADE,
    preferred_protocol text[],
    current_protocol text,
    protocol_history jsonb DEFAULT '[]'
);

-- Network status tracking with proper unique constraint
CREATE TABLE mq.network_status (
    channel_id bigint PRIMARY KEY REFERENCES mq.channel(channel_id) ON DELETE CASCADE,
    facility_id text,
    network_type text DEFAULT 'unknown',
    bandwidth_kbps int,
    latency_ms int,
    packet_loss_percent decimal(5, 2),
    last_updated timestamptz DEFAULT now(),
    is_active boolean DEFAULT true
);

-- Fragment management for SMS/USSD
CREATE TABLE mq.message_fragments (
    fragment_id bigserial PRIMARY KEY,
    message_id bigint REFERENCES mq.message(message_id) ON DELETE CASCADE,
    fragment_number int,
    total_fragments int,
    fragment_data text,
    fragment_size int,
    protocol text,
    sent boolean DEFAULT false
);

-- Health data rules
CREATE TABLE mq.health_data_rules (
    data_type text PRIMARY KEY,
    priority_default int,
    max_size_bytes int,
    ttl interval,
    requires_encryption boolean DEFAULT true,
    requires_acknowledgment boolean DEFAULT true,
    allowed_protocols text[]
);

-- Insert health-specific rules
INSERT INTO mq.health_data_rules VALUES
    ('lab_hiv_result', 1, 1024, '1 hour', true, true, '{sms,ussd}'),
    ('lab_routine', 3, 10240, '24 hours', true, true, '{http,sms_multipart}'),
    ('prescription', 2, 2048, '4 hours', true, true, '{ussd,sms}'),
    ('insurance_claim', 4, 102400, '7 days', true, false, '{http,lorawan}'),
    ('patient_vitals', 3, 512, '2 hours', false, false, '{lorawan,http}'),
    ('test', 3, 1024, '1 hour', false, false, '{http}');

-- Add foreign key constraint now that the table exists
ALTER TABLE mq.message 
ADD CONSTRAINT fk_message_data_type 
FOREIGN KEY (data_type) REFERENCES mq.health_data_rules(data_type);

-- Failed messages audit
CREATE TABLE mq.failed_messages (
    id bigserial PRIMARY KEY,
    message_id bigint,
    reason text,
    failed_at timestamptz DEFAULT now(),
    message_snapshot jsonb
);