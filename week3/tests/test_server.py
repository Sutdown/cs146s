"""MCP Weather Server 测试"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_mcp_server.config import Config, get_config
from weather_mcp_server.weather_client import (
    NotFoundError,
    RateLimitError,
    WeatherAPIError,
    get_current_weather,
    get_forecast_weather,
)
from weather_mcp_server.tools import (
    get_current_weather_handler,
    get_forecast_weather_handler,
)


# ============================================================
# Mock 数据
# ============================================================

MOCK_CURRENT_WEATHER = {
    "status": "1",
    "infocode": "10000",
    "count": "1",
    "info": "OK",
    "lives": [
        {
            "province": "北京",
            "city": "北京市",
            "adcode": "110000",
            "weather": "晴",
            "temperature": "15",
            "winddirection": "北",
            "windpower": "3级",
            "humidity": "45",
            "reporttime": "2024-01-15 10:30:00",
        }
    ],
}

MOCK_FORECAST_WEATHER = {
    "status": "1",
    "infocode": "10000",
    "count": "1",
    "info": "OK",
    "forecasts": [
        {
            "province": "北京",
            "city": "北京市",
            "adcode": "110000",
            "reporttime": "2024-01-15 10:30:00",
            "casts": [
                {
                    "date": "2024-01-15",
                    "week": "1",
                    "dayweather": "晴",
                    "nightweather": "多云",
                    "daytemp": "15",
                    "nighttemp": "5",
                    "daywind": "北",
                    "nightwind": "北",
                    "daypower": "3级",
                    "nightpower": "3级",
                }
            ],
        }
    ],
}


# ============================================================
# 配置测试
# ============================================================


class TestConfig:
    """配置模块测试"""

    def test_config_loads_from_env(self, monkeypatch):
        """测试配置从环境变量加载"""
        monkeypatch.setenv("AMAP_API_KEY", "test_key_123")
        monkeypatch.setenv("AMAP_BASE_URL", "https://custom.api.com")

        from weather_mcp_server import config as config_module
        config_module.get_config.cache_clear()
        cfg = config_module.get_config()

        assert cfg.api_key == "test_key_123"
        assert cfg.base_url == "https://custom.api.com"

    def test_config_defaults(self, monkeypatch):
        """测试配置默认值"""
        monkeypatch.delenv("AMAP_API_KEY", raising=False)
        monkeypatch.delenv("AMAP_BASE_URL", raising=False)

        from weather_mcp_server import config as config_module
        config_module.get_config.cache_clear()
        cfg = config_module.get_config()

        assert cfg.api_key == ""
        assert cfg.base_url == "https://restapi.amap.com/v3"


# ============================================================
# API 客户端测试
# ============================================================


@pytest.mark.asyncio
class TestWeatherClient:
    """天气 API 客户端测试"""

    async def test_get_current_weather_success(self, monkeypatch):
        """测试获取当前天气成功"""
        mock_response = AsyncMock()
        mock_response.json.return_value = MOCK_CURRENT_WEATHER

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            mock_client.return_value.__aexit__.return_value = None

            monkeypatch.setenv("AMAP_API_KEY", "test_key")
            from weather_mcp_server import config as config_module
            config_module.get_config.cache_clear()

            result = await get_current_weather(city="北京")

            assert result["city"] == "北京市"
            assert result["weather"] == "晴"
            assert result["temperature"] == "15"

    async def test_get_current_weather_not_found(self, monkeypatch):
        """测试城市未找到"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "status": "0",
            "infocode": "20000",
            "info": "city not found",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            mock_client.return_value.__aexit__.return_value = None

            monkeypatch.setenv("AMAP_API_KEY", "test_key")
            from weather_mcp_server import config as config_module
            config_module.get_config.cache_clear()

            with pytest.raises(NotFoundError):
                await get_current_weather(city="不存在的城市")

    async def test_get_current_weather_rate_limit(self, monkeypatch):
        """测试 API 速率限制"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "status": "0",
            "infocode": "10002",
            "info": "quota exhausted",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            mock_client.return_value.__aexit__.return_value = None

            monkeypatch.setenv("AMAP_API_KEY", "test_key")
            from weather_mcp_server import config as config_module
            config_module.get_config.cache_clear()

            with pytest.raises(RateLimitError):
                await get_current_weather(city="北京")


# ============================================================
# 工具处理器测试
# ============================================================


@pytest.mark.asyncio
class TestToolHandlers:
    """工具处理器测试"""

    async def test_get_current_weather_handler_success(self, monkeypatch):
        """测试当前天气处理器成功"""
        with patch(
            "weather_mcp_server.tools.get_current_weather",
            new_callable=AsyncMock,
            return_value=MOCK_CURRENT_WEATHER["lives"][0],
        ):
            result = await get_current_weather_handler(city="北京")

            assert result["success"] is True
            assert result["data"]["city"] == "北京市"

    async def test_get_current_weather_handler_api_error(self, monkeypatch):
        """测试当前天气处理器 API 错误"""
        with patch(
            "weather_mcp_server.tools.get_current_weather",
            new_callable=AsyncMock,
            side_effect=WeatherAPIError("API 错误"),
        ):
            result = await get_current_weather_handler(city="北京")

            assert result["success"] is False
            assert result["error_type"] == "APIError"

    async def test_get_forecast_weather_handler_success(self, monkeypatch):
        """测试预报天气处理器成功"""
        forecast_data = MOCK_FORECAST_WEATHER["forecasts"][0]

        with patch(
            "weather_mcp_server.tools.get_forecast_weather",
            new_callable=AsyncMock,
            return_value=forecast_data,
        ):
            result = await get_forecast_weather_handler(city="北京")

            assert result["success"] is True
            assert result["data"]["city"] == "北京市"
            assert len(result["data"]["forecasts"]) == 1


# ============================================================
# 集成测试 (需要真实 API Key)
# ============================================================


@pytest.mark.asyncio
class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def real_api_key(self):
        """获取真实 API Key"""
        key = os.environ.get("AMAP_API_KEY")
        if not key:
            pytest.skip("需要设置真实的 AMAP_API_KEY")
        return key

    async def test_real_api_current_weather(self, real_api_key):
        """测试真实 API - 获取当前天气"""
        from weather_mcp_server import config as config_module
        config_module.get_config.cache_clear()

        result = await get_current_weather(city="北京")
        assert "city" in result
        assert "temperature" in result

    async def test_real_api_forecast(self, real_api_key):
        """测试真实 API - 获取预报天气"""
        from weather_mcp_server import config as config_module
        config_module.get_config.cache_clear()

        result = await get_forecast_weather(city="上海")
        assert "city" in result
        assert "forecasts" in result
