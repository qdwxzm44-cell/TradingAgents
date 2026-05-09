"""中国白糖（SR）技术面分析 Agent（Phase 3, Mock-only）。

约束：
- 仅使用 OHLC K线与 ATR 派生信息。
- 禁用成交量、MACD、RSI、KDJ、各类动量指标。
- 仅用于研究辅助，禁止自动下单。
"""

from __future__ import annotations

from tradingagents.dataflows.cn_futures.sugar_sr_provider import SugarSRProvider


_ALLOWED_VIEWS = ("偏多", "偏空", "中性")


def _true_range(curr: dict, prev_close: float) -> float:
    return max(
        curr["high"] - curr["low"],
        abs(curr["high"] - prev_close),
        abs(curr["low"] - prev_close),
    )


def _calc_atr(bars: list[dict], period: int = 5) -> float:
    if len(bars) < 2:
        return 0.0
    trs = []
    for i in range(1, len(bars)):
        trs.append(_true_range(bars[i], bars[i - 1]["close"]))
    window = trs[-period:] if len(trs) >= period else trs
    return round(sum(window) / len(window), 2) if window else 0.0


def _trend_direction(bars: list[dict]) -> str:
    if len(bars) < 2:
        return "震荡"
    first = bars[0]["close"]
    last = bars[-1]["close"]
    if last > first:
        return "上行"
    if last < first:
        return "下行"
    return "震荡"


def _support_resistance(bars: list[dict], lookback: int = 6) -> tuple[float, float]:
    window = bars[-lookback:] if len(bars) >= lookback else bars
    support = min(x["low"] for x in window)
    resistance = max(x["high"] for x in window)
    return float(support), float(resistance)


def _breakout_state(last_close: float, support: float, resistance: float, atr: float) -> str:
    band = atr * 0.2
    if last_close > resistance - band:
        return "上沿附近，存在向上突破可能"
    if last_close < support + band:
        return "下沿附近，存在向下破位风险"
    return "区间内运行，暂未突破"


def _risk_level(atr: float, close_price: float) -> str:
    if close_price <= 0:
        return "中"
    atr_pct = atr / close_price
    if atr_pct >= 0.02:
        return "高"
    if atr_pct >= 0.01:
        return "中"
    return "低"


def generate_sugar_technical_report(trade_date: str, bars: int = 12, provider: str | None = None) -> str:
    """生成中文技术面分析报告（基于 SR OHLC + ATR）。"""
    data_provider = SugarSRProvider(provider=provider)
    ohlc = data_provider.get_kline(trade_date, bars=bars)
    if not ohlc:
        return "无法生成技术分析报告：缺少K线数据。"

    trend = _trend_direction(ohlc)
    support, resistance = _support_resistance(ohlc)
    atr = _calc_atr(ohlc, period=5)
    last_close = float(ohlc[-1]["close"])
    breakout = _breakout_state(last_close, support, resistance, atr)
    risk = _risk_level(atr, last_close)

    bias_score = 0
    if trend == "上行":
        bias_score += 1
    elif trend == "下行":
        bias_score -= 1

    if "向上突破" in breakout:
        bias_score += 1
    elif "向下破位" in breakout:
        bias_score -= 1

    if bias_score > 0:
        bias = "偏多"
    elif bias_score < 0:
        bias = "偏空"
    else:
        bias = "中性"

    if bias not in _ALLOWED_VIEWS:
        bias = "中性"

    return f"""## 中国白糖 SR 技术面分析报告（Mock）

- 分析日期：{trade_date}
- 研究定位：仅研究辅助，不自动下单
- 数据源：{data_provider.last_source}
- 数据范围：最近 {len(ohlc)} 根 OHLC K线

### 1) 当前趋势
当前趋势判断：**{trend}**。

### 2) 关键支撑位
关键支撑位：**{support:.2f}**。

### 3) 关键压力位
关键压力位：**{resistance:.2f}**。

### 4) ATR 波动风险
ATR(5)：**{atr:.2f}**，收盘价：**{last_close:.2f}**，ATR/收盘约 **{(atr/last_close*100):.2f}%**。

### 5) 是否处于突破阶段
{breakout}。

### 6) 风险等级
综合波动风险等级：**{risk}**。

## 技术面结论
**{bias}**

{data_provider.last_warning}

> 风险提示：本报告仅用于研究辅助与风险分析，不构成投资建议，禁止用于自动下单。
"""


def create_sugar_technical_analyst(_llm=None):
    """兼容现有 agent 工厂风格；本阶段不依赖 LLM。"""

    def sugar_technical_node(state):
        trade_date = str(state.get("trade_date", "2026-01-01"))
        report = generate_sugar_technical_report(trade_date)
        return {
            "sugar_technical_report": report,
        }

    return sugar_technical_node
