-- Track health data types and their routing rules
CREATE TABLE mq.health_data_rules (
    data_type text PRIMARY KEY,
    priority_default int,
    max_size_bytes int,
    ttl interval, -- Time to live
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
    ('patient_vitals', 3, 512, '2 hours', false, false, '{lorawan,http}');

-- Failed messages for audit
CREATE TABLE mq.failed_messages (
    id bigserial PRIMARY KEY,
    message_id bigint,
    reason text,
    failed_at timestamptz,
    message_snapshot jsonb -- Store full message for audit
);