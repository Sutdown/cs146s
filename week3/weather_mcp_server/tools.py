"""MCP 工具定义"""

from __future__ import annotations

import logging
from collections.abc import Awaitable
from typing import Any, Callable

from .weather_client import (
    WeatherAPIError,
    get_current_weather,
    get_forecast_weather,
)

logger = logging.getLogger(__name__)


# ============================================================
# 类型定义
# ============================================================

ToolHandler = Callable[..., Awaitable[dict[str, Any]]]


class ToolDefinition:
    """单个工具定义"""
    name: str
    description: str
    inputSchema: dict[str, Any]
    handler: ToolHandler

    def __init__(
        self,
        name: str,
        description: str,
        inputSchema: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        self.name = name
        self.description = description
        self.inputSchema = inputSchema
        self.handler = handler


# ============================================================
# 工具处理器
# ============================================================


async def get_current_weather_handler(city: str) -> dict[str, Any]:
    """
    获取指定城市的当前实况天气

    参数:
        city: 城市编码或城市名称 (必需)
    """
    logger.info(f"获取当前实况天气: {city}")

    try:
        data = await get_current_weather(city=city)
        return {"success": True, "data": data}
    except WeatherAPIError as e:
        logger.error(f"天气 API 错误: {e}")
        return {"success": False, "error": str(e), "error_type": "APIError"}
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        return {"success": False, "error": "服务器内部错误", "error_type": "InternalError"}


async def get_forecast_weather_handler(city: str) -> dict[str, Any]:
    """
    获取指定城市的预报天气

    参数:
        city: 城市编码或城市名称 (必需)
    """
    logger.info(f"获取预报天气: {city}")

    try:
        data = await get_forecast_weather(city=city)
        return {"success": True, "data": data}
    except WeatherAPIError as e:
        logger.error(f"天气 API 错误: {e}")
        return {"success": False, "error": str(e), "error_type": "APIError"}
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        return {"success": False, "error": "服务器内部错误", "error_type": "InternalError"}


# ============================================================
# MCP 工具定义
# ============================================================

TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_current_weather",
        description="获取指定城市的当前实况天气，包括温度、湿度、风向、风力等",
        inputSchema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市编码或城市名称，如 '110100'（北京）或 '北京'",
                },
            },
            "required": ["city"],
        },
        handler=get_current_weather_handler,
    ),
    ToolDefinition(
        name="get_forecast_weather",
        description="获取指定城市未来4天的预报天气，包括每天的白天/夜间天气、温度、风向等",
        inputSchema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市编码或城市名称，如 '110100'（北京）或 '北京'",
                },
            },
            "required": ["city"],
        },
        handler=get_forecast_weather_handler,
    ),
]
