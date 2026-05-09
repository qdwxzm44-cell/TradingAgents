"""中国期货市场（白糖 SR）配置层（Phase 1: Mock only）。

说明：
- 本模块仅提供研究辅助所需静态配置，不包含任何自动下单能力。
- 本模块不修改 LangGraph 工作流，仅作为可选配置与数据源描述。
"""

from __future__ import annotations

CN_FUTURES_BASE_CONFIG = {
    "market": "CN_FUTURES",
    "exchange": "CZCE",
    "output_language": "Chinese",
    "research_only": True,
    "auto_trading_enabled": False,
    "supports_night_session": True,
    "risk_flags": {
        "gap_risk": True,
        "margin_call_risk": True,
    },
}

SR_CONTRACT_CONFIG = {
    "symbol": "SR",
    "name": "白糖期货",
    "exchange": "CZCE",
    "main_contract_rule": "mock_main_contract",
    "price_tick": 1,
    "contract_multiplier": 10,
    "margin_ratio": 0.08,
    "open_fee_per_lot": 3.0,
    "close_fee_per_lot": 3.0,
    "night_session": "21:00-23:00",
    "data_provider": "real",
}


def get_cn_futures_config() -> dict:
    """返回中国期货研究配置（只读拷贝）。"""
    return {
        "base": CN_FUTURES_BASE_CONFIG.copy(),
        "sr": SR_CONTRACT_CONFIG.copy(),
    }
