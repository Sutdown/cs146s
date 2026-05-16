"""快速测试高德 API"""
import asyncio
import httpx

async def test():
    api_key = "2f551ae52b44a6391b8c01c84f24e5cb"

    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": api_key,
        "city": "110100",
        "extensions": "base",
        "output": "json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")

asyncio.run(test())
