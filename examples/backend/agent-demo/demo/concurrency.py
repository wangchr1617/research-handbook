"""并发工具练习：python -m demo.concurrency；Python 3.12+，超时单位为秒。"""
import asyncio
import json
import time


async def tool(name, delay, limit, semaphore):
    # 超时包含等待并发名额的时间；只把预期超时转成局部结果。
    try:
        async with asyncio.timeout(limit):
            async with semaphore:
                await asyncio.sleep(delay)
                if name == "broken":
                    raise ValueError("invalid tool input")
                return {"tool": name, "status": "ok"}
    except TimeoutError:
        return {"tool": name, "status": "timeout"}
    except asyncio.CancelledError:
        # 在这里关闭连接、清理临时文件，然后把取消继续向上传播。
        raise


async def call_tools(specs, total=2.0):
    semaphore = asyncio.Semaphore(2)
    async with asyncio.timeout(total):
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(tool(*spec, semaphore)) for spec in specs]
    return [task.result() for task in tasks]


async def main():
    start = time.monotonic()
    results = await call_tools([("search", .1, .5), ("metadata", .1, .5), ("slow", .3, .15)])
    print(json.dumps(results, ensure_ascii=False), f"elapsed={time.monotonic() - start:.2f}s")
    task = asyncio.create_task(call_tools([("cancel_me", 10, 20)], total=30))
    await asyncio.sleep(.01)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled and awaited")


if __name__ == "__main__":
    asyncio.run(main())
