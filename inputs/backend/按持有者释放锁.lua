-- 仅允许当前持有者删除互斥键；ARGV[1] 为创建锁时使用的随机 owner。
-- 用法：redis-cli --eval inputs/backend/按持有者释放锁.lua handbook:practice:lock:run-demo , owner-a
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
