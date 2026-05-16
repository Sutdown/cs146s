"""MCP Weather Server - 基于 OpenWeatherMap API 的 MCP 服务器"""

import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

from .config import config
from .tools import TOOL_DEFINITIONS, ToolDefinition

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger(__name__)

# 创建 MCP Server 实例
server = Server("weather-mcp-server")


# ============================================================
# MCP 协议处理器
# ============================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    logger.debug("列出工具请求")

    return [
        Tool(
            name=tool_def.name,
            description=tool_def.description,
            inputSchema=tool_def.inputSchema,
        )
        for tool_def in TOOL_DEFINITIONS
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, object] | None) -> CallToolResult:
    """调用工具处理请求"""
    logger.info(f"调用工具: {name}, 参数: {arguments}")

    # 查找对应的工具处理器
    tool_def: ToolDefinition | None = None
    for td in TOOL_DEFINITIONS:
        if td.name == name:
            tool_def = td
            break

    if not tool_def:
        logger.error(f"未知工具: {name}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"未知工具: {name}")],
            isError=True,
        )

    try:
        # 调用工具处理器
        if arguments is None:
            arguments = {}

        result = await tool_def.handler(**arguments)

        if result.get("success"):
            import json
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))],
            )
        else:
            error_msg = result.get("error", "未知错误")
            return CallToolResult(
                content=[TextContent(type="text", text=f"错误: {error_msg}")],
                isError=True,
            )

    except TypeError as e:
        # 参数错误
        logger.error(f"参数错误: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"参数错误: {str(e)}")],
            isError=True,
        )
    except Exception as e:
        logger.exception(f"工具执行错误: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"服务器错误: {str(e)}")],
            isError=True,
        )


# ============================================================
# 服务器入口点
# ============================================================


async def main():
    """主函数 - 启动 MCP 服务器"""
    logger.info("=" * 50)
    logger.info("MCP Weather Server 启动")
    logger.info(f"API Base URL: {config.base_url}")
    logger.info(f"API Key 设置: {'是' if config.api_key else '否'}")
    logger.info("=" * 50)

    if not config.api_key:
        logger.warning("警告: 未设置 OPENWEATHERMAP_API_KEY 环境变量!")
        logger.warning("请设置环境变量后重启服务器")

    # 使用 STDIO 传输启动服务器
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run():
    """同步入口点"""
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已关闭")
    except Exception as e:
        logger.exception(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
