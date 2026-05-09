"""白糖 SR Provider（支持 real/mock 自动切换）。

该 provider 只提供研究辅助信息，不包含任何交易执行能力。
"""

from __future__ import annotations

from tradingagents.config.cn_futures_config import get_cn_futures_config
from .mock_data import get_mock_contract_specs, get_mock_main_contract, get_mock_ohlc
from .real_data import get_real_sugar_main_daily


class SugarSRProvider:
    """中国白糖期货 SR 数据提供器（real 优先，失败回退 mock）。"""

    def __init__(self, provider: str | None = None):
        cfg = get_cn_futures_config()
        self.base_config = cfg["base"]
        self.sr_config = cfg["sr"]
        self.provider = (provider or self.sr_config.get("data_provider", "real")).lower()
        self.last_source = "MOCK"
        self.last_warning = ""

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

    def get_kline(self, trade_date: str, bars: int = 10) -> list[dict]:
        self.last_warning = ""
        if self.provider == "mock":
            self.last_source = "MOCK"
            return get_mock_ohlc(trade_date, bars=bars)

        try:
            rows = get_real_sugar_main_daily(trade_date, bars=bars)
            self.last_source = "REAL"
            return rows
        except Exception as exc:
            self.last_source = "MOCK FALLBACK"
            self.last_warning = f"⚠️ 中文警告：真实行情获取失败，已自动回退 mock 数据。原因：{exc}"
            return get_mock_ohlc(trade_date, bars=bars)
