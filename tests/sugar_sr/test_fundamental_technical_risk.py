from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tradingagents.agents.analysts.sugar_technical_analyst import _breakout_state, _calc_atr
from tradingagents.agents.risk_mgmt import sugar_risk_analyst as risk_mod
from tradingagents.dataflows.cn_futures.sugar_fundamental_provider import load_sugar_fundamental_snapshot


def test_fundamental_csv_json_fallback(tmp_path):
    csvf = tmp_path / "f.csv"
    csvf.write_text(
        "date,production,sales,inventory,import_volume,raw_sugar_price,usdcny,weather_note,policy_note\n"
        "2026-05-08,1000,900,300,50,18.2,7.2,正常,中性\n",
        encoding="utf-8",
    )
    snap_csv, src_csv, warn_csv = load_sugar_fundamental_snapshot("2026-05-08", str(csvf))
    assert src_csv == "LOCAL CSV"
    assert warn_csv is None
    assert snap_csv["sales"] == 900.0

    json_bad = tmp_path / "bad.json"
    json_bad.write_text('{"date":"2026-05-08","production":1}', encoding="utf-8")
    _snap, src_bad, warn_bad = load_sugar_fundamental_snapshot("2026-05-08", str(json_bad))
    assert src_bad == "MOCK FALLBACK"
    assert "字段缺失" in (warn_bad or "")


def test_atr_and_breakout_logic():
    bars = [
        {"date": "2026-05-06", "open": 6100, "high": 6120, "low": 6090, "close": 6110},
        {"date": "2026-05-07", "open": 6110, "high": 6130, "low": 6100, "close": 6120},
        {"date": "2026-05-08", "open": 6120, "high": 6160, "low": 6110, "close": 6150},
    ]
    atr = _calc_atr(bars, period=14)
    assert atr > 0
    assert _breakout_state(6200, 6000, 6150) == "是（向上突破）"
    assert _breakout_state(5900, 6000, 6150) == "是（向下突破）"
    assert _breakout_state(6100, 6000, 6150) == "否"


def test_risk_level_low_mid_high_reachable(monkeypatch):
    base = risk_mod._mock_risk_snapshot("2026-05-08")

    def _low(_):
        s = dict(base)
        s.update(margin_ratio=0.05, open_fee=1.0, close_fee=1.0, gap_risk_score=0, extreme_event_score=0, policy_tone="中性", raw_sugar_change_pct=0.1)
        return s

    def _mid(_):
        s = dict(base)
        s.update(margin_ratio=0.08, open_fee=2.5, close_fee=2.5, gap_risk_score=2, extreme_event_score=1, policy_tone="中性", raw_sugar_change_pct=0.5)
        return s

    def _high(_):
        s = dict(base)
        s.update(margin_ratio=0.12, open_fee=5.0, close_fee=5.0, gap_risk_score=4, extreme_event_score=4, policy_tone="偏紧", raw_sugar_change_pct=3.0)
        return s

    monkeypatch.setattr(risk_mod, "_mock_risk_snapshot", _low)
    assert risk_mod._risk_level(5) == "低"

    monkeypatch.setattr(risk_mod, "_mock_risk_snapshot", _mid)
    assert "**中**" in risk_mod.generate_sugar_risk_report("2026-05-08")

    monkeypatch.setattr(risk_mod, "_mock_risk_snapshot", _high)
    assert "**高**" in risk_mod.generate_sugar_risk_report("2026-05-08")
