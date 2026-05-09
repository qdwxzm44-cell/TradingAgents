"""白糖 SR 日志工具（Phase 19）。

日志仅输出到 stderr，不影响 Markdown 报告正文。
"""
from __future__ import annotations

import logging

_LOGGER_NAME = "tradingagents.sugar_sr"


def configure_sugar_logger(verbose: bool = False, quiet: bool = False) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.handlers.clear()
    logger.propagate = False

    level = logging.INFO
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG

    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    return logger


def get_sugar_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        configure_sugar_logger()
    return logger
