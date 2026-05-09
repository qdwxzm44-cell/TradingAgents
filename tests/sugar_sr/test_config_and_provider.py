from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import types

from tradingagents.config.sugar_sr_config import load_sugar_sr_config
from tradingagents.dataflows.cn_futures import real_data
from tradingagents.dataflows.cn_futures.sugar_sr_provider import SugarSRProvider


def test_config_load_basic(tmp_path):
    p = tmp_path / "sugar_sr.yaml"
    p.write_text("provider: mock\nbreakout_window: 26\nmarkdown_export_enabled: false\n", encoding="utf-8")
    conf, warnings = load_sugar_sr_config(str(p))
    assert conf.provider == "mock"
    assert conf.breakout_window == 26
    assert conf.markdown_export_enabled is False
    assert warnings == []


def test_mock_provider_no_network_dependency():
    p = SugarSRProvider(provider="mock")
    rows = p.get_kline("2026-05-08", bars=12)
    assert len(rows) == 12
    assert p.last_source == "MOCK"


def test_real_provider_fallback_when_akshare_fails(monkeypatch):
    def _boom(*_, **__):
        raise RuntimeError("akshare mocked failure")

    monkeypatch.setattr("tradingagents.dataflows.cn_futures.sugar_sr_provider.get_real_sugar_main_daily", _boom)
    p = SugarSRProvider(provider="real")
    rows = p.get_kline("2026-05-08", bars=10)
    assert len(rows) == 10
    assert p.last_source == "MOCK FALLBACK"
    assert "真实行情获取失败" in p.last_warning


def test_real_data_module_mock_akshare(monkeypatch):
    class _AK:
        @staticmethod
        def futures_main_sina(symbol: str):
            import pandas as pd

            return pd.DataFrame(
                [
                    {"日期": "2026-05-06", "开盘": 6100, "最高": 6120, "最低": 6090, "收盘": 6110},
                    {"日期": "2026-05-07", "开盘": 6110, "最高": 6130, "最低": 6100, "收盘": 6120},
                    {"日期": "2026-05-08", "开盘": 6120, "最高": 6140, "最低": 6110, "收盘": 6130},
                ]
            )

    monkeypatch.setitem(__import__("sys").modules, "akshare", _AK())
    rows = real_data.get_real_sugar_main_daily("2026-05-08", bars=2)
    assert len(rows) == 2
    assert rows[-1]["date"] == "2026-05-08"
