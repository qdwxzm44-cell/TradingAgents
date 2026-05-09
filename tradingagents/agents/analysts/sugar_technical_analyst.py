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


def _calc_atr(bars: list[dict], period: int = 14) -> float:
    if len(bars) < 2:
        return 0.0
    trs = []
    for i in range(1, len(bars)):
        trs.append(_true_range(bars[i], bars[i - 1]["close"]))
    window = trs[-period:] if len(trs) >= period else trs
    return round(sum(window) / len(window), 2) if window else 0.0


def _swing_structure(bars: list[dict], lookback: int = 6) -> dict:
    if len(bars) < 2:
        return {
            "structure_state": "数据不足",
            "trend": "震荡",
            "hh": False,
            "hl": False,
            "lh": False,
            "ll": False,
        }
    window = bars[-lookback:] if len(bars) >= lookback else bars
    highs = [x["high"] for x in window]
    lows = [x["low"] for x in window]
    hh = highs[-1] > max(highs[:-1]) if len(highs) > 1 else False
    ll = lows[-1] < min(lows[:-1]) if len(lows) > 1 else False
    hl = lows[-1] > lows[0] if len(lows) > 1 else False
    lh = highs[-1] < highs[0] if len(highs) > 1 else False

    if hh and hl:
        trend = "多头结构"
    elif ll and lh:
        trend = "空头结构"
    else:
        trend = "震荡结构"
    tags = []
    if hh:
        tags.append("Higher High")
    if hl:
        tags.append("Higher Low")
    if lh:
        tags.append("Lower High")
    if ll:
        tags.append("Lower Low")
    return {
        "structure_state": " + ".join(tags) if tags else "无明显结构",
        "trend": trend,
        "hh": hh,
        "hl": hl,
        "lh": lh,
        "ll": ll,
    }


def _support_resistance(bars: list[dict], lookback: int = 20) -> tuple[float, float]:
    window = bars[-lookback:] if len(bars) >= lookback else bars
    support = min(x["low"] for x in window)
    resistance = max(x["high"] for x in window)
    return float(support), float(resistance)


def _breakout_state(last_close: float, low20: float, high20: float) -> str:
    if last_close > high20:
        return "是（向上突破）"
    if last_close < low20:
        return "是（向下突破）"
    return "否"


def _volatility_state(atr: float, close_price: float) -> str:
    if close_price <= 0:
        return "正常波动"
    atr_pct = atr / close_price
    if atr_pct >= 0.025:
        return "高波动"
    if atr_pct >= 0.012:
        return "正常波动"
    return "低波动"


def generate_sugar_technical_report(trade_date: str, bars: int = 30, provider: str | None = None) -> str:
    """生成中文技术面分析报告（基于 SR OHLC + ATR）。"""
    data_provider = SugarSRProvider(provider=provider)
    fetch_bars = max(bars, 30)
    ohlc = data_provider.get_kline(trade_date, bars=fetch_bars)
    if not ohlc:
        return "无法生成技术分析报告：缺少K线数据。"
    warning_msgs = []
    if len(ohlc) < 20:
        warning_msgs.append("⚠️ 中文警告：K线少于20根，20日高低点与突破判断可能失真。")
    if len(ohlc) < 15:
        warning_msgs.append("⚠️ 中文警告：K线少于15根，ATR(14)稳定性不足，仅供参考。")

    support, resistance = _support_resistance(ohlc, lookback=20)
    atr = _calc_atr(ohlc, period=14)
    last_close = float(ohlc[-1]["close"])
    breakout = _breakout_state(last_close, support, resistance)
    structure = _swing_structure(ohlc, lookback=6)
    trend = structure["trend"]
    volatility = _volatility_state(atr, last_close)

    bias_score = 0
    if trend == "多头结构":
        bias_score += 1
    elif trend == "空头结构":
        bias_score -= 1

    if "向上突破" in breakout:
        bias_score += 1
    elif "向下突破" in breakout:
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

### 1) 技术结构
趋势：**{trend}**  
结构状态：**{structure['structure_state']}**

### 2) 20日关键位
最近20日最低价：**{support:.2f}**  
最近20日最高价：**{resistance:.2f}**

### 3) ATR 波动率
ATR(14)：**{atr:.2f}**，收盘价：**{last_close:.2f}**，ATR/收盘约 **{(atr/last_close*100):.2f}%**。  
波动率状态：**{volatility}**

### 4) Breakout 检测（20日）
20日突破：**{breakout}**

## 技术面结论
**{bias}**

{"".join([msg + "\n" for msg in warning_msgs])}{data_provider.last_warning}

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
