-- TABLES 

CREATE EXTENSION IF NOT EXISTS hstore;

CREATE TABLE mq.exchange (
    exchange_id serial PRIMARY KEY,
    exchange_name text NOT NULL UNIQUE
);

CREATE TABLE mq.message_intake (
    exchange_id int NOT NULL REFERENCES mq.exchange(exchange_id) ON DELETE CASCADE,
    routing_key text NOT NULL,
    body json NOT NULL,
    headers hstore NOT NULL DEFAULT '',
    publish_time timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE mq.queue (
    queue_id bigserial PRIMARY KEY,
    exchange_id int NOT NULL REFERENCES mq.exchange(exchange_id) ON DELETE CASCADE,
    queue_name text NOT NULL UNIQUE,
    routing_key_pattern text NOT NULL DEFAULT '^.*$'
);

-- ENHANCED message table with health-specific columns
CREATE TABLE mq.message (
    message_id bigserial PRIMARY KEY,
    exchange_id int NOT NULL,
    routing_key text NOT NULL,
    body json NOT NULL,
    headers hstore NOT NULL DEFAULT '',
    publish_time timestamptz NOT NULL DEFAULT now(),
    queue_id bigint NOT NULL REFERENCES mq.queue(queue_id) ON DELETE CASCADE,
    -- Health-specific additions
    priority int DEFAULT 5 CHECK (priority BETWEEN 1 AND 5),
    retry_count int DEFAULT 0,
    max_retries int DEFAULT 10,
    original_size int,
    compressed_size int,
    compression_type text DEFAULT 'none',
    data_type text REFERENCES mq.health_data_rules(data_type),
    ttl timestamptz DEFAULT (now() + interval '24 hours')
);
CREATE INDEX ON mq.message(queue_id);
CREATE INDEX ON mq.message(priority);

CREATE TABLE mq.message_waiting (
    message_id bigint PRIMARY KEY REFERENCES mq.message(message_id) ON DELETE CASCADE,
    queue_id bigint NOT NULL REFERENCES mq.queue(queue_id) ON DELETE CASCADE,
    since_time timestamptz NOT NULL DEFAULT now(),
    not_until_time timestamptz NULL
);
CREATE INDEX ON mq.message_waiting(queue_id);

CREATE TABLE mq.channel (
    channel_id bigserial PRIMARY KEY,
    channel_name text NOT NULL UNIQUE,
    queue_id bigint NOT NULL REFERENCES mq.queue(queue_id) ON DELETE CASCADE,
    maximum_messages int NOT NULL DEFAULT 1
);

CREATE TABLE mq.channel_waiting (
    channel_id bigint NOT NULL REFERENCES mq.channel(channel_id) ON DELETE CASCADE,
    slot int NOT NULL,
    queue_id bigint NOT NULL REFERENCES mq.queue(queue_id) ON DELETE CASCADE,
    since_time timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(channel_id, slot)
);
CREATE INDEX ON mq.channel_waiting(queue_id);

CREATE TABLE mq.delivery (
    delivery_id bigserial PRIMARY KEY,
    message_id bigint NOT NULL REFERENCES mq.message(message_id) ON DELETE CASCADE,
    channel_id bigint NOT NULL REFERENCES mq.channel(channel_id) ON DELETE CASCADE,
    slot int NOT NULL,
    queue_id bigint NOT NULL REFERENCES mq.queue(queue_id) ON DELETE CASCADE,
    delivery_time timestamptz NOT NULL DEFAULT now()
);