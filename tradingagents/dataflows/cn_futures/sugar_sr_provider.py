"""白糖 SR Provider（Phase 1: Mock）。

该 provider 只提供研究辅助信息，不包含任何交易执行能力。
"""

from __future__ import annotations

from tradingagents.config.cn_futures_config import get_cn_futures_config
from .mock_data import get_mock_contract_specs, get_mock_main_contract, get_mock_ohlc


class SugarSRMockProvider:
    """中国白糖期货 SR Mock 数据提供器。"""

    def __init__(self):
        cfg = get_cn_futures_config()
        self.base_config = cfg["base"]
        self.sr_config = cfg["sr"]

    def get_main_contract_info(self, trade_date: str) -> dict:
        info = get_mock_main_contract(trade_date)
        info.update(
            {
                "instrument_name": self.sr_config["name"],
                "research_only": self.base_config["research_only"],
                "auto_trading_enabled": self.base_config["auto_trading_enabled"],
            }
        )
        return info

    def get_contract_specs(self) -> dict:
        specs = get_mock_contract_specs()
        specs.update(
            {
                "symbol": self.sr_config["symbol"],
                "exchange": self.sr_config["exchange"],
                "night_session": self.sr_config["night_session"],
            }
        )
        return specs

    def get_mock_kline(self, trade_date: str, bars: int = 10) -> list[dict]:
        return get_mock_ohlc(trade_date, bars=bars)
