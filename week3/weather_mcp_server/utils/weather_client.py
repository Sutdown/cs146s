"""天气 API 客户端模块 - 封装高德地图天气 API"""

import logging
from typing import Any

import httpx

from .config import config

logger = logging.getLogger(__name__)


# ============================================================
# 异常定义
# ============================================================


class WeatherAPIError(Exception):
    """天气 API 错误基类"""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(WeatherAPIError):
    """API 速率限制错误"""
    pass


class NotFoundError(WeatherAPIError):
    """城市未找到错误"""
    pass


# ============================================================
# API 客户端
# ============================================================


async def _make_request(params: dict[str, Any]) -> dict[str, Any]:
    """发送 API 请求并处理响应"""
    url = f"{config.base_url}/weather/weatherInfo"

    # 调试日志
    logger.info(f"API Key: {config.api_key[:10] if config.api_key else 'EMPTY'}...")
    logger.info(f"请求 URL: {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            logger.debug(f"API 请求: {response.url}")
            logger.debug(f"响应状态: {response.status_code}")

            data = response.json()
            logger.info(f"API 响应: {data}")

            # 检查高德 API 状态码
            infocode = str(data.get("infocode", ""))
            status = data.get("status", "")

            if infocode == "10000" or status == "1":
                # 成功
                return data
            elif infocode == "10001":
                raise WeatherAPIError("API Key 错误或已过期", 401)
            elif infocode == "10002":
                raise RateLimitError("服务调用超限，请稍后重试")
            elif infocode == "20000":
                raise NotFoundError("城市不存在或城市编码错误")
            elif infocode == "20001":
                raise WeatherAPIError("查询无结果")
            elif infocode == "30001":
                raise WeatherAPIError("格式错误")
            else:
                raise WeatherAPIError(f"API 返回错误: {data.get('info', '未知错误')}", int(infocode) if infocode else None)

        except httpx.TimeoutException:
            raise WeatherAPIError("API 请求超时")
        except Exception as e:
            if isinstance(e, WeatherAPIError):
                raise
            logger.exception(f"API 请求失败: {e}")
            raise WeatherAPIError(f"网络请求失败: {str(e)}")


async def get_current_weather(city: str) -> dict[str, Any]:
    """
    获取当前实况天气

    API: GET /v3/weather/weatherInfo?key=xxx&city=xxx&extensions=base
    文档: https://lbs.amap.com/api/webservice/guide/api/weatherinfo
    """
    params = {
        "key": config.api_key,
        "city": city,
        "extensions": "base",  # base=实况天气, all=预报天气
        "output": "json",
    }

    data = await _make_request(params)

    # 解析实况天气数据
    lives = data.get("lives", [])
    if not lives:
        raise WeatherAPIError("未获取到天气数据")

    live = lives[0]
    return {
        "province": live.get("province", ""),
        "city": live.get("city", ""),
        "weather": live.get("weather", ""),
        "temperature": live.get("temperature", ""),
        "wind_direction": live.get("winddirection", ""),
        "wind_power": live.get("windpower", ""),
        "humidity": live.get("humidity", ""),
        "report_time": live.get("reporttime", ""),
    }


async def get_forecast_weather(city: str) -> dict[str, Any]:
    """
    获取当前预报天气

    API: GET /v3/weather/weatherInfo?key=xxx&city=xxx&extensions=all
    文档: https://lbs.amap.com/api/webservice/guide/api/weatherinfo
    """
    params = {
        "key": config.api_key,
        "city": city,
        "extensions": "all",  # 预报天气
        "output": "json",
    }

    data = await _make_request(params)

    # 解析预报天气数据
    forecasts = data.get("forecasts", [])
    if not forecasts:
        raise WeatherAPIError("未获取到预报数据")

    forecast_data = forecasts[0]
    casts = forecast_data.get("casts", [])

    return {
        "province": forecast_data.get("province", ""),
        "city": forecast_data.get("city", ""),
        "report_time": forecast_data.get("reporttime", ""),
        "forecasts": [
            {
                "date": cast.get("date", ""),
                "week": cast.get("week", ""),
                "day_weather": cast.get("dayweather", ""),
                "night_weather": cast.get("nightweather", ""),
                "day_temp": cast.get("daytemp", ""),
                "night_temp": cast.get("nighttemp", ""),
                "day_wind": cast.get("daywind", ""),
                "night_wind": cast.get("nightwind", ""),
                "day_wind_power": cast.get("daypower", ""),
                "night_wind_power": cast.get("nightpower", ""),
            }
            for cast in casts
        ],
    }
