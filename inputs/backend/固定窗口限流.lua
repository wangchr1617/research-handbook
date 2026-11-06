-- 固定窗口计数；ARGV[1] 为窗口秒数，调用者在返回计数超过限额时拒绝请求。
-- 用法：redis-cli --eval inputs/backend/固定窗口限流.lua handbook:practice:rate:user-demo , 60
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
