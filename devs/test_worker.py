import asyncio
import json
import time
import uuid
import aiohttp
import websockets

# 配置信息
WORKER_URL = "https://yunhu-sse.wsu2059.workers.dev/"  # 替换为您的Worker URL
WS_URL = WORKER_URL.replace("https", "wss") + "/ws"
SSE_URL = WORKER_URL + "/sse"
CLIENT_NAME = f"test_client_{uuid.uuid4().hex[:8]}"
AUTH_TOKEN = "your_test_token_here"  # 替换为有效的token

async def test_websocket():
    """测试WebSocket连接和API调用"""
    print(f"\n{'='*50}\nStarting WebSocket Test\n{'='*50}")
    
    async with websockets.connect(WS_URL) as ws:
        # 1. 认证连接
        auth_msg = {
            "type": "auth",
            "name": CLIENT_NAME,
            "authType": "token",
            "authParams": {"token": AUTH_TOKEN},
            "baseUrl": "https://api.example.com"  # 模拟的API基础URL
        }
        await ws.send(json.dumps(auth_msg))
        print(f"Sent auth message: {auth_msg}")

        # 接收认证响应
        auth_response = await ws.recv()
        print(f"Auth response: {json.loads(auth_response)}")

        # 2. 查询可用端点
        list_endpoints_msg = {
            "type": "list_endpoints",
            "requestId": str(uuid.uuid4())
        }
        await ws.send(json.dumps(list_endpoints_msg))
        print(f"\nRequesting available endpoints...")
        
        endpoints_response = await ws.recv()
        print(f"Available endpoints: {json.loads(endpoints_response)}")

        # 3. 测试API调用
        test_api_msg = {
            "type": "callapi",
            "name": CLIENT_NAME,
            "endpoint": "send_message",  # 假设这是预定义的端点
            "params": {
                "text": f"Hello from {CLIENT_NAME}",
                "timestamp": int(time.time())
            },
            "requestId": str(uuid.uuid4())
        }
        await ws.send(json.dumps(test_api_msg))
        print(f"\nSending API request: {test_api_msg}")

        api_response = await ws.recv()
        print(f"API response: {json.loads(api_response)}")

        # 4. 保持连接并监听事件
        print("\nListening for events (press Ctrl+C to stop)...")
        try:
            while True:
                message = await ws.recv()
                print(f"\nReceived event: {json.loads(message)}")
        except KeyboardInterrupt:
            print("Stopping WebSocket client...")

async def test_sse():
    """测试SSE事件流"""
    print(f"\n{'='*50}\nStarting SSE Test\n{'='*50}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(SSE_URL) as resp:
            if resp.status != 200:
                print(f"SSE connection failed with status {resp.status}")
                return

            print("Connected to SSE stream. Waiting for events...")
            buffer = ""
            
            try:
                async for data in resp.content:
                    buffer += data.decode('utf-8')
                    
                    # SSE消息以两个换行符分隔
                    while "\n\n" in buffer:
                        message, buffer = buffer.split("\n\n", 1)
                        lines = message.strip().split('\n')
                        
                        event_data = None
                        for line in lines:
                            if line.startswith("data:"):
                                event_data = json.loads(line[5:].strip())
                        
                        if event_data:
                            print(f"\nSSE Event received: {event_data}")
                            
            except asyncio.CancelledError:
                print("SSE client stopped by user")
            except Exception as e:
                print(f"SSE error: {str(e)}")

async def main():
    """主测试函数"""
    print(f"Starting tests for client: {CLIENT_NAME}")
    
    # 同时运行WebSocket和SSE测试
    ws_task = asyncio.create_task(test_websocket())
    sse_task = asyncio.create_task(test_sse())
    
    # 等待任意一个任务完成（通常WS会先完成）
    done, pending = await asyncio.wait(
        [ws_task, sse_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    # 取消剩余的任务
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest stopped by user")