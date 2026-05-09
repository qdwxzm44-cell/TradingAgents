"""中国白糖（SR）基本面分析 Agent。"""

from __future__ import annotations

from tradingagents.dataflows.cn_futures.sugar_fundamental_provider import load_sugar_fundamental_snapshot


_ALLOWED_VIEWS = ("偏多", "偏空", "中性")


def _score_bias(snapshot: dict) -> str:
    score = 0

    # 产量增长偏空，下降偏多
    if snapshot["production"]["yoy_change_pct"] > 0:
        score -= 1
    elif snapshot["production"]["yoy_change_pct"] < 0:
        score += 1

    # 库存下降偏多，库存上升偏空
    if snapshot["inventory"]["yoy_change_pct"] < 0:
        score += 1
    elif snapshot["inventory"]["yoy_change_pct"] > 0:
        score -= 1

    # 进口增长偏空（供应增加），下降偏多
    if snapshot["import"]["yoy_change_pct"] > 0:
        score -= 1
    elif snapshot["import"]["yoy_change_pct"] < 0:
        score += 1

    # 巴西原糖上涨偏多
    if snapshot["brazil_raw_sugar"]["raw_sugar_price_change_pct"] > 0:
        score += 1
    elif snapshot["brazil_raw_sugar"]["raw_sugar_price_change_pct"] < 0:
        score -= 1

    # 人民币走弱（USDCNY 上行）偏多
    if snapshot["fx"]["monthly_change_pct"] > 0:
        score += 1
    elif snapshot["fx"]["monthly_change_pct"] < 0:
        score -= 1

    # 天气风险中高偏多
    weather_risk = snapshot["weather"]["main_area_weather_risk"]
    if weather_risk in ("中等", "高"):
        score += 1

    if score >= 2:
        return "偏多"
    if score <= -2:
        return "偏空"
    return "中性"


def generate_sugar_fundamental_report(trade_date: str, fundamental_file: str | None = None) -> str:
    """生成中文白糖基本面报告（支持 mock / 本地 CSV / 本地 JSON）。"""
    snapshot, source_label, warning = load_sugar_fundamental_snapshot(trade_date, fundamental_file=fundamental_file)
    bias = _score_bias(snapshot)
    if bias not in _ALLOWED_VIEWS:
        bias = "中性"

    warning_block = f"\n- 数据警告：{warning}" if warning else ""

    report = f"""## 中国白糖 SR 基本面分析报告

- 分析日期：{snapshot['trade_date']}
- 研究定位：仅研究辅助，不自动下单
- 基本面数据源：{source_label}{warning_block}

### 1) 产量分析
{snapshot['production']['interpretation']}（同比：{snapshot['production']['yoy_change_pct']}%）

### 2) 库存分析
{snapshot['inventory']['interpretation']}（同比：{snapshot['inventory']['yoy_change_pct']}%）

### 3) 进口分析
{snapshot['import']['interpretation']}（同比：{snapshot['import']['yoy_change_pct']}%）

### 4) 巴西原糖影响
{snapshot['brazil_raw_sugar']['interpretation']}（原糖变动：{snapshot['brazil_raw_sugar']['raw_sugar_price_change_pct']}%）

### 5) 汇率影响
{snapshot['fx']['interpretation']}（USDCNY：{snapshot['fx']['usdcny']}，月变动：{snapshot['fx']['monthly_change_pct']}%）

### 6) 天气影响
{snapshot['weather']['interpretation']}（风险等级：{snapshot['weather']['main_area_weather_risk']}）

### 7) 政策影响
{snapshot['policy']['interpretation']}（政策基调：{snapshot['policy']['policy_tone']}）

## 最终判断
**{bias}**

> 风险提示：以上结论基于 mock 数据生成，仅用于系统开发与研究验证，不构成任何投资建议，禁止用于自动下单。
"""
    return report


def create_sugar_fundamental_analyst(_llm=None):
    """兼容现有 agent 工厂风格；本阶段不依赖 LLM，仅返回 mock 报告。"""

    def sugar_fundamental_node(state):
        trade_date = state.get("trade_date", "2026-01-01")
        report = generate_sugar_fundamental_report(str(trade_date))
        return {
            "sugar_fundamental_report": report,
        }

    return sugar_fundamental_node
