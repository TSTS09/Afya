-- View for monitoring system health
CREATE VIEW mq.system_health AS
SELECT 
    q.queue_name,
    COUNT(DISTINCT mw.message_id) as waiting_messages,
    COUNT(DISTINCT cw.channel_id) as waiting_channels,
    AVG(m.retry_count) as avg_retries,
    COUNT(CASE WHEN m.priority = 1 THEN 1 END) as critical_messages
FROM mq.queue q
LEFT JOIN mq.message_waiting mw ON mw.queue_id = q.queue_id
LEFT JOIN mq.channel_waiting cw ON cw.queue_id = q.queue_id
LEFT JOIN mq.message m ON m.message_id = mw.message_id
GROUP BY q.queue_name;

-- View for protocol usage
CREATE VIEW mq.protocol_usage AS
SELECT 
    current_protocol,
    COUNT(*) as message_count,
    AVG(compressed_size) as avg_size,
    SUM(CASE WHEN priority = 1 THEN 1 ELSE 0 END) as critical_count
FROM mq.message_protocol mp
JOIN mq.message m ON m.message_id = mp.message_id
GROUP BY current_protocol;