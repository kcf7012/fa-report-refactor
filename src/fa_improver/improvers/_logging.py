"""Improver 共用的 logging 模組

提供:
- 統一的 logger name(`fa_improver.improvers`)
- 預設 debug 模式(透過環境變數 FA_IMPROVER_DEBUG=1 開啟)
- 便利函式 `log_action_start` / `log_action_done` / `log_action_failed`

設計理由:批次執行時,handoff `2026-08-31-batch-eval-rendering-issues-handoff.md`
指出有 8 張空白頁但 orchestrator 沒有任何 log,導致 silent error。
此模組提供最小侵入的 logging 機制。
"""

from __future__ import annotations

import logging
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager

# 統一 logger name,可用 `logging.getLogger("fa_improver.improvers")` 取得
LOGGER_NAME = "fa_improver.improvers"

# 環境變數名稱:設為 "1"/"true"/"yes" 開啟 DEBUG
DEBUG_ENV_VAR = "FA_IMPROVER_DEBUG"


def get_logger() -> logging.Logger:
    """取得 improver 模組的 logger

    自動根據環境變數 FA_IMPROVER_DEBUG 設定等級:
    - "1"/"true"/"yes" → DEBUG
    - 其他 → WARNING(預設,避免污染 stdout)

    若 root logger 沒有 handler,新增 StreamHandler 到 stderr。
    """
    logger = logging.getLogger(LOGGER_NAME)

    # 只在第一次呼叫時設定 handler(避免重複)
    if not logger.handlers and not logger.parent.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)

    # 決定 log 等級
    debug_env = os.environ.get(DEBUG_ENV_VAR, "").lower()
    if debug_env in ("1", "true", "yes", "on"):
        logger.setLevel(logging.DEBUG)
    elif not logger.level:
        # 預設 INFO(可看到一般進度),不污染
        logger.setLevel(logging.INFO)

    # 不要讓 log 訊息 propagate 到 root(因為 root 可能會再輸出)
    logger.propagate = False

    return logger


@contextmanager
def log_action(action_name: str, **context) -> Iterator[logging.Logger]:
    """上下文管理器:記錄 action 開始/結束/失敗

    Usage:
        with log_action("add_basic_info_slide", filename="foo.pptx"):
            # ... do stuff

    Args:
        action_name: 動作名稱
        **context: 額外 context(會顯示在 log 中)

    Yields:
        logger 物件
    """
    logger = get_logger()
    ctx_str = " ".join(f"{k}={v!r}" for k, v in context.items())
    start = time.time()
    logger.info("▶ START %s %s", action_name, ctx_str)
    try:
        yield logger
    except Exception as e:
        elapsed = time.time() - start
        logger.error("✗ FAILED %s (after %.2fs): %s: %s", action_name, elapsed, type(e).__name__, e)
        raise
    else:
        elapsed = time.time() - start
        logger.info("✓ DONE %s (%.2fs)", action_name, elapsed)
