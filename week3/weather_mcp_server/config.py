"""配置模块 - 管理环境变量和配置"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Config:
    """配置数据类"""
    api_key: str
    base_url: str
    timeout: int


@lru_cache()
def get_config() -> Config:
    """获取配置 (单例模式)"""
    return Config(
        api_key="",
        base_url=os.getenv("AMAP_BASE_URL", "https://restapi.amap.com/v3"),
        timeout=int(os.getenv("AMAP_TIMEOUT", "30")),
    )


# 导出便捷访问
config = get_config()
