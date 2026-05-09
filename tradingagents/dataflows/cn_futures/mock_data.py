"""白糖 SR Mock 数据（Phase 1）。

注意：
- 本文件仅用于联调与演示，不代表真实行情或交易参数。
- 严禁将 mock 数据用于真实交易决策。
"""

from __future__ import annotations

from datetime import date, timedelta


def get_mock_main_contract(trade_date: str) -> dict:
    """返回 mock 主力合约信息。"""
    return {
        "trade_date": trade_date,
        "symbol": "SR",
        "main_contract": "SR609",
        "exchange": "CZCE",
        "rollover_hint": "mock: 本周无换月",
    }


def get_mock_contract_specs() -> dict:
    """返回 mock 合约参数。"""
    return {
        "margin_ratio": 0.08,
        "open_fee_per_lot": 3.0,
        "close_fee_per_lot": 3.0,
        "price_tick": 1,
        "contract_multiplier": 10,
    }


def get_mock_ohlc(trade_date: str, bars: int = 10) -> list[dict]:
    """生成简易 mock K 线（OHLC）。"""
    d = date.fromisoformat(trade_date)
    base = 6100
    rows: list[dict] = []
    for i in range(bars):
        day = d - timedelta(days=(bars - 1 - i))
        o = base + i * 3
        h = o + 12
        l = o - 10
        c = o + (2 if i % 2 == 0 else -1)
        rows.append(
            {
                "date": day.isoformat(),
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
            }
        )
    return rows
