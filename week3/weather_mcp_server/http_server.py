"""HTTP 模式的 MCP 服务器"""

import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool

from .config import config
from .tools import TOOL_DEFINITIONS, ToolDefinition

logger = logging.getLogger(__name__)

# 创建 MCP Server 实例 (HTTP 模式)
http_server = Server("weather-mcp-server-http")


# ============================================================
# MCP 协议处理器 (与 STDIO 模式相同)
# ============================================================


@http_server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name=t.name,
            description=t.description,
            inputSchema=t.inputSchema,
        )
        for t in TOOL_DEFINITIONS
    ]


@http_server.call_tool()
async def call_tool(name: str, arguments: dict[str, object] | None) -> list[TextContent]:
    """调用工具处理请求"""
    logger.info(f"[HTTP] 调用工具: {name}, 参数: {arguments}")

    tool_def: ToolDefinition | None = None
    for td in TOOL_DEFINITIONS:
        if td.name == name:
            tool_def = td
            break

    if not tool_def:
        logger.error(f"[HTTP] 未知工具: {name}")
        return [TextContent(type="text", text=f"未知工具: {name}")]

    try:
        if arguments is None:
            arguments = {}

        result = await tool_def.handler(**arguments)

        import json
        if result.get("success"):
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        else:
            error_msg = result.get("error", "未知错误")
            return [TextContent(type="text", text=f"错误: {error_msg}")]

    except TypeError as e:
        logger.error(f"[HTTP] 参数错误: {e}")
        return [TextContent(type="text", text=f"参数错误: {str(e)}")]
    except Exception as e:
        logger.exception(f"[HTTP] 工具执行错误: {e}")
        return [TextContent(type="text", text=f"服务器错误: {str(e)}")]


# ============================================================
# HTTP 服务器入口点
# ============================================================


async def run_http_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """运行 HTTP 服务器"""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware.cors import CORSMiddleware

    # 创建 SSE 传输
    sse_transport = SseServerTransport("/mcp/")

    async def handle_sse(request):
        """处理 SSE 连接"""
        async with sse_transport.connect_sse(
            request.scope,
            request.receive,
            request.send,
        ) as streams:
            await http_server.run(
                streams[0],
                streams[1],
                http_server.create_initialization_options(),
            )

    # 健康检查端点
    async def health(request):
        from starlette.responses import JSONResponse
        return JSONResponse({
            "status": "ok",
            "service": "weather-mcp-server",
            "transport": "http/sse",
            "tools": [t.name for t in TOOL_DEFINITIONS],
        })

    # 路由
    routes = [
        Route("/mcp/", handle_sse, methods=["GET", "POST"]),
        Route("/health", health, methods=["GET"]),
    ]

    app = Starlette(routes=routes)

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("=" * 50)
    logger.info("MCP Weather Server (HTTP 模式) 启动")
    logger.info(f"监听地址: http://{host}:{port}")
    logger.info(f"MCP 端点: http://{host}:{port}/mcp/")
    logger.info(f"健康检查: http://{host}:{port}/health")
    logger.info("=" * 50)

    if not config.api_key:
        logger.warning("警告: 未设置 AMAP_API_KEY 环境变量!")

    config_uvicorn = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config_uvicorn)
    await server.serve()
