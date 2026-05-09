"""白糖 SR 简易历史回测模块（Phase 14）。

约束：
- 仅用于研究验证与风险分析，禁止自动下单。
- 仅使用 SR OHLC 价格逻辑，不使用成交量与动量指标。
- 策略信号：20日突破做多观察信号 + ATR止损 + 固定止盈止损。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from tradingagents.dataflows.cn_futures.sugar_sr_provider import SugarSRProvider


@dataclass
class _Trade:
    entry_date: str
    exit_date: str
    entry: float
    exit: float
    pnl: float


def _true_range(curr: dict, prev_close: float) -> float:
    return max(curr["high"] - curr["low"], abs(curr["high"] - prev_close), abs(curr["low"] - prev_close))


def _calc_atr_window(rows: list[dict], idx: int, period: int = 14) -> float:
    start = max(1, idx - period + 1)
    trs = [_true_range(rows[i], rows[i - 1]["close"]) for i in range(start, idx + 1)]
    return sum(trs) / len(trs) if trs else 0.0


def _max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            max_dd = max(max_dd, (peak - v) / peak)
    return max_dd


def generate_sugar_backtest_report(provider: str = "real", trade_date: str | None = None, bars: int = 240) -> str:
    """生成中文回测摘要。"""
    end_date = trade_date or date.today().isoformat()
    data_provider = SugarSRProvider(provider=provider)
    ohlc = data_provider.get_kline(end_date, bars=max(60, bars))

    if len(ohlc) < 25:
        return (
            "## 白糖 SR 回测摘要\n\n"
            "数据不足，无法进行有效回测（至少需要 25 根K线）。\n\n"
            "> 风险提示：本模块仅用于研究验证，不构成投资建议，禁止自动下单。"
        )

    trades: list[_Trade] = []
    equity = [1.0]
    signal_count = 0

    in_pos = False
    entry_price = 0.0
    entry_date = ""
    stop_loss = 0.0
    take_profit = 0.0

    for i in range(20, len(ohlc)):
        bar = ohlc[i]
        prev20_high = max(x["high"] for x in ohlc[i - 20 : i])

        if not in_pos:
            if bar["close"] > prev20_high:
                signal_count += 1
                atr = _calc_atr_window(ohlc, i, period=14)
                entry_price = bar["close"]
                entry_date = bar["date"]
                stop_loss = max(entry_price - 2 * atr, entry_price * (1 - 0.02))
                take_profit = entry_price * (1 + 0.04)
                in_pos = True
            continue

        exit_price = None
        if bar["low"] <= stop_loss:
            exit_price = stop_loss
        elif bar["high"] >= take_profit:
            exit_price = take_profit

        if exit_price is not None:
            pnl = (exit_price - entry_price) / entry_price
            trades.append(_Trade(entry_date, bar["date"], entry_price, exit_price, pnl))
            equity.append(equity[-1] * (1 + pnl))
            in_pos = False

    if in_pos:
        last = ohlc[-1]
        pnl = (last["close"] - entry_price) / entry_price
        trades.append(_Trade(entry_date, last["date"], entry_price, last["close"], pnl))
        equity.append(equity[-1] * (1 + pnl))

    wins = [t for t in trades if t.pnl > 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0.0
    avg_pnl = (sum(t.pnl for t in trades) / len(trades) * 100) if trades else 0.0
    mdd = _max_drawdown(equity) * 100

    equity_summary = " → ".join([f"{x:.3f}" for x in equity[-6:]])
    return f"""## 白糖 SR 简单历史回测摘要

- 回测区间：{ohlc[0]['date']} 至 {ohlc[-1]['date']}
- 数据源：{data_provider.last_source}
- 策略说明：20日突破做多观察信号 + ATR止损 + 固定2%止损/4%止盈
- 信号次数：{signal_count}
- 完成交易数：{len(trades)}
- 胜率：{win_rate:.2f}%
- 平均盈亏：{avg_pnl:.2f}% / 笔
- 最大回撤：{mdd:.2f}%
- 简单资金曲线摘要（最近6节点）：{equity_summary}

{data_provider.last_warning}
> 风险提示：本回测仅用于研究验证，不代表未来收益，不构成投资建议，严禁用于自动下单或实盘交易指令生成。
"""
