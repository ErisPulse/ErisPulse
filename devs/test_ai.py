from ErisPulse import sdk
import asyncio
from typing import Dict, Any

async def main():
    sdk.init()
    try:
        await sdk.adapter.startup()
        # 保持程序运行
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await sdk.adapter.shutdown()

if __name__ == "__main__":
    asyncio.run(main())