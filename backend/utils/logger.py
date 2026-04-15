# utils/logger.py - 统一日志配置
# 所有 routers 必须从此模块导入 logger，禁止直接 print
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """获取标准化 logger 实例"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 避免重复添加 handler

    logger.setLevel(logging.INFO)

    # 控制台输出（本地开发可见）
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
        datefmt="%H:%M:%S"
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    return logger
