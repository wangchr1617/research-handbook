-- 在新建的教学数据库中查看 run、消息与事件；不输出密码或会话令牌。
-- 用法：sqlite3 -header -column /tmp/agent-backend-lab/demo.db < inputs/backend/查看任务.sql
SELECT id, client_key, status, attempt, error_code, cancel_requested
FROM runs ORDER BY created_at, id;

SELECT r.client_key, m.role, COUNT(*) AS message_count
FROM messages AS m JOIN runs AS r ON r.id = m.run_id
GROUP BY r.client_key, m.role ORDER BY r.client_key, m.role;

SELECT r.client_key, e.kind, COUNT(*) AS event_count
FROM run_events AS e JOIN runs AS r ON r.id = e.run_id
GROUP BY r.client_key, e.kind ORDER BY r.client_key, e.kind;
