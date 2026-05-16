# MCP Weather Server

基于高德地图天气 API 的 MCP (Model Context Protocol) 服务器，支持 STDIO 和 HTTP 两种运行模式。

## 功能特性

- **两个 MCP 工具**: 当前实况天气、预报天气
- **双传输模式**: STDIO (本地) + HTTP/SSE (远程)
- **健壮的错误处理**: API 错误、速率限制、网络超时
- **类型安全**: 完整的类型提示

## 环境要求

- Python 3.10+
- 高德地图 API Key

## 安装

```bash
pip install -r requirements.txt
```

## 配置

### 设置环境变量

```bash
# Windows PowerShell
$env:AMAP_API_KEY = "你的API_KEY"

# Linux/Mac
export AMAP_API_KEY="你的API_KEY"
```

## 运行模式

### 1. STDIO 模式 (默认 - Claude Desktop)

```bash
python weather_mcp_server/main.py
# 或
python weather_mcp_server/main.py --mode stdio
```

### 2. HTTP 模式 (远程调用)

```bash
python weather_mcp_server/main.py --mode http --port 8000
```

- MCP 端点: `http://localhost:8000/mcp/`
- 健康检查: `http://localhost:8000/health`

### 3. 双模式 (同时运行)

```bash
python weather_mcp_server/main.py --mode both --port 8000
```

## MCP 工具

### 1. get_current_weather

获取指定城市的当前实况天气。

**参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市编码或城市名称，如 '110100' 或 '北京' |

### 2. get_forecast_weather

获取指定城市未来4天的预报天气。

**参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市编码或城市名称 |

## 客户端集成

### Claude Desktop (STDIO 模式)

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

### HTTP 模式 (SDK 调用示例)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 使用 stdio 连接到本地 HTTP 服务器
# 或使用 SSE 客户端连接远程服务器

async def main():
    # 创建 SSE 传输连接
    async with sse_client("http://localhost:8000/mcp/") as (read, write):
        async with ClientSession(
            read,
            write,
        ) as session:
            await session.initialize()
            
            # 调用工具
            result = await session.call_tool(
                "get_current_weather",
                {"city": "北京"}
            )
            print(result)
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 快速测试 API
python test_api.py
```

## 项目结构

```
weather_mcp_server/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── weather_client.py    # 高德地图 API 封装
├── tools.py             # MCP 工具定义
├── server.py            # STDIO 服务器
├── http_server.py       # HTTP 服务器
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
