"""中国白糖（SR）风险分析 Agent（Phase 4, Mock-only）。

约束：
- 仅用于研究辅助，不允许自动下单。
- 当前阶段仅使用 mock 数据，不接真实风控源。
"""

from __future__ import annotations

from tradingagents.config.cn_futures_config import get_cn_futures_config
from tradingagents.dataflows.cn_futures.fundamental_mock_data import (
    get_sugar_fundamental_mock_snapshot,
)
from tradingagents.dataflows.cn_futures.mock_data import get_mock_main_contract


def _mock_risk_snapshot(trade_date: str) -> dict:
    cfg = get_cn_futures_config()
    sr = cfg["sr"]
    fundamental = get_sugar_fundamental_mock_snapshot(trade_date)
    contract = get_mock_main_contract(trade_date)

    return {
        "trade_date": trade_date,
        "main_contract": contract["main_contract"],
        "margin_ratio": sr["margin_ratio"],
        "open_fee": sr["open_fee_per_lot"],
        "close_fee": sr["close_fee_per_lot"],
        "night_session": sr["night_session"],
        "policy_tone": fundamental["policy"]["policy_tone"],
        "raw_sugar_change_pct": fundamental["brazil_raw_sugar"]["raw_sugar_price_change_pct"],
        "weather_risk": fundamental["weather"]["main_area_weather_risk"],
        "rollover_hint": contract["rollover_hint"],
        "gap_risk_score": 2,
        "extreme_event_score": 2,
    }


def _risk_level(score: int) -> str:
    """将风险评分映射为低/中/高。

    评分区间（当前规则总分通常在 8~14）：
    - 低：<= 8
    - 中：9~11
    - 高：>= 12
    这样三个等级在不同场景均可达。
    """
    if score >= 12:
        return "高"
    if score >= 9:
        return "中"
    return "低"


def generate_sugar_risk_report(trade_date: str) -> str:
    """生成中文白糖风险分析报告（Mock）。"""
    s = _mock_risk_snapshot(trade_date)

    score = 0

    # 1 保证金风险
    margin_line = "保证金比例处于可控区间。"
    if s["margin_ratio"] >= 0.1:
        score += 2
        margin_line = "保证金比例较高，资金占用与追加保证金压力较大。"
    elif s["margin_ratio"] >= 0.08:
        score += 1
        margin_line = "保证金比例中等，需关注波动放大时的资金安全垫。"

    # 2 手续费成本
    fee_total = s["open_fee"] + s["close_fee"]
    fee_line = "手续费成本可控。"
    if fee_total >= 8:
        score += 2
        fee_line = "双边手续费较高，频繁交易将显著侵蚀收益。"
    elif fee_total >= 5:
        score += 1
        fee_line = "双边手续费中等，需控制交易频次。"

    # 3 跳空风险
    gap_line = "跳空风险当前可控。"
    if s["gap_risk_score"] >= 3:
        score += 2
        gap_line = "跳空风险偏高，止损可能出现滑点与失效风险。"
    else:
        score += 1
        gap_line = "存在一定跳空风险，需预留风控缓冲。"

    # 4 夜盘风险
    night_line = f"夜盘时段（{s['night_session']}）流动性波动需关注。"
    score += 1

    # 5 主力换月风险
    rollover_line = f"主力合约：{s['main_contract']}，换月提示：{s['rollover_hint']}。"
    score += 1

    # 6 政策风险
    policy_line = f"政策基调：{s['policy_tone']}，短期政策冲击风险中性。"
    if "偏紧" in s["policy_tone"]:
        score += 2
    else:
        score += 1

    # 7 外盘原糖波动风险
    raw_line = f"外盘原糖变动：{s['raw_sugar_change_pct']}%，对内盘成本端存在传导。"
    if abs(s["raw_sugar_change_pct"]) >= 2:
        score += 2
    else:
        score += 1

    # 8 极端行情风险
    extreme_line = "存在极端行情尾部风险（天气/宏观/政策共振）。"
    if s["extreme_event_score"] >= 3:
        score += 2
    else:
        score += 1

    level = _risk_level(score)

    return f"""## 中国白糖 SR 风险分析报告（Mock）

- 分析日期：{s['trade_date']}
- 研究定位：仅研究辅助，不自动下单

### 1) 保证金风险
{margin_line}

### 2) 手续费成本
{fee_line}

### 3) 跳空风险
{gap_line}

### 4) 夜盘风险
{night_line}

### 5) 主力合约换月风险
{rollover_line}

### 6) 政策风险
{policy_line}

### 7) 外盘原糖波动风险
{raw_line}

### 8) 极端行情风险
{extreme_line}

## 综合风险等级
**{level}**

> 风险提示：本报告基于 mock 风控数据，仅用于研发与研究验证，不构成投资建议；严禁用于自动交易或自动下单。
"""


def create_sugar_risk_analyst(_llm=None):
    """兼容现有 agent 工厂风格；本阶段不依赖 LLM。"""

    def sugar_risk_node(state):
        trade_date = str(state.get("trade_date", "2026-01-01"))
        report = generate_sugar_risk_report(trade_date)
        return {
            "sugar_risk_report": report,
        }

    return sugar_risk_node
