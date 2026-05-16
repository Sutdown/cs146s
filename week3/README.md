# MCP Weather Server

基于高德地图天气 API 的 MCP (Model Context Protocol) 服务器，提供天气查询功能。

## 功能特性

- **两个 MCP 工具**: 当前实况天气、预报天气
- **健壮的错误处理**: API 错误、速率限制、网络超时
- **类型安全**: 完整的类型提示
- **灵活配置**: 支持环境变量配置

## 环境要求

- Python 3.10+
- 高德地图 API Key

## 安装

```bash
pip install -r requirements.txt
```

## 配置

### 获取 API Key

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册账号并创建应用
3. 获取 Web服务 API Key

### 设置环境变量

```bash
# Windows PowerShell
$env:AMAP_API_KEY = "你的API_KEY"

# Linux/Mac
export AMAP_API_KEY="你的API_KEY"
```

## 运行

```bash
python weather_mcp_server/main.py
```

## MCP 工具

### 1. get_current_weather

获取指定城市的当前实况天气。

**参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市编码或城市名称，如 '110100' 或 '北京' |

**返回示例:**
```json
{
  "success": true,
  "data": {
    "province": "北京",
    "city": "北京市",
    "weather": "晴",
    "temperature": "15",
    "wind_direction": "北",
    "wind_power": "3级",
    "humidity": "45",
    "report_time": "2024-01-15 10:30:00"
  }
}
```

### 2. get_forecast_weather

获取指定城市未来4天的预报天气。

**参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市编码或城市名称 |

**返回示例:**
```json
{
  "success": true,
  "data": {
    "province": "北京",
    "city": "北京市",
    "report_time": "2024-01-15 10:30:00",
    "forecasts": [
      {
        "date": "2024-01-15",
        "week": "1",
        "day_weather": "晴",
        "night_weather": "多云",
        "day_temp": "15",
        "night_temp": "5",
        "day_wind": "北",
        "night_wind": "北",
        "day_wind_power": "3级",
        "night_wind_power": "3级"
      }
    ]
  }
}
```

## Claude Desktop 集成

编辑配置文件:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["weather_mcp_server/main.py"],
      "env": {
        "AMAP_API_KEY": "你的API_KEY"
      }
    }
  }
}
```

## 测试

```bash
pytest tests/ -v
```

## 项目结构

```
weather_mcp_server/
├── __init__.py          # 包初始化
├── config.py            # 配置管理 (环境变量)
├── weather_client.py    # 高德地图 API 封装
├── tools.py             # MCP 工具定义
├── server.py            # MCP 服务器
└── main.py              # 入口点
tests/
└── test_server.py       # 测试代码
```

## 高德 API 错误码

| 错误码 | 说明 |
|--------|------|
| 10000 | 成功 |
| 10001 | API Key 错误 |
| 10002 | 服务调用超限 |
| 20000 | 城市不存在 |
| 20001 | 查询无结果 |
| 30001 | 格式错误 |
