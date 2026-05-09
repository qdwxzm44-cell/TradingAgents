"""白糖基本面 Mock 数据（Phase 2）。

仅用于研究系统联调，不代表真实数据，不可用于自动交易。
"""

from __future__ import annotations


def get_sugar_fundamental_mock_snapshot(trade_date: str) -> dict:
    """返回白糖基本面七维 mock 快照。"""
    return {
        "trade_date": trade_date,
        "production": {
            "current_season_million_tons": 10.2,
            "yoy_change_pct": 2.4,
            "interpretation": "国内产量温和增长，供应端偏宽松。",
        },
        "inventory": {
            "industrial_inventory_million_tons": 5.1,
            "yoy_change_pct": -3.0,
            "interpretation": "工业库存同比下降，近月供给缓冲有所减弱。",
        },
        "import": {
            "monthly_import_million_tons": 0.42,
            "yoy_change_pct": 6.5,
            "interpretation": "进口维持恢复，缓解阶段性缺口。",
        },
        "brazil_raw_sugar": {
            "raw_sugar_price_change_pct": 1.8,
            "freight_change_pct": 0.6,
            "interpretation": "巴西原糖小幅走强，抬升国内进口成本中枢。",
        },
        "fx": {
            "usdcny": 7.18,
            "monthly_change_pct": 0.9,
            "interpretation": "人民币偏弱提升进口糖折算成本，对内盘略偏多。",
        },
        "weather": {
            "main_area_weather_risk": "中等",
            "interpretation": "主产区降雨偏离常年，单产存在扰动风险。",
        },
        "policy": {
            "policy_tone": "中性偏稳",
            "interpretation": "短期未见超预期政策冲击，政策面对盘面影响中性。",
        },
    }
