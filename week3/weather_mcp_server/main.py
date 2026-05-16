"""主入口点 - 支持 STDIO 和 HTTP 两种模式"""
import argparse
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="MCP Weather Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http", "both"],
        default="stdio",
        help="运行模式: stdio (默认), http, 或 both (同时运行)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="HTTP 服务器监听地址 (默认: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP 服务器监听端口 (默认: 8000)",
    )

    args = parser.parse_args()

    if args.mode == "stdio":
        print("启动 STDIO 模式...")
        from weather_mcp_server.server import run
        run()

    elif args.mode == "http":
        print(f"启动 HTTP 模式 (http://{args.host}:{args.port})...")
        import asyncio
        from weather_mcp_server.http_server import run_http_server
        asyncio.run(run_http_server(host=args.host, port=args.port))

    elif args.mode == "both":
        print("启动 STDIO + HTTP 双模式...")
        import asyncio
        import threading

        # 启动 HTTP 服务器在后台线程
        from weather_mcp_server.http_server import run_http_server

        def run_http():
            asyncio.run(run_http_server(host=args.host, port=args.port))

        http_thread = threading.Thread(target=run_http, daemon=True)
        http_thread.start()

        # 主线程运行 STDIO 服务器
        from weather_mcp_server.server import run
        run()


if __name__ == "__main__":
    main()
