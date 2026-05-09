"""白糖 SR 简易历史回测模块（Phase 14）。

约束：
- 仅用于研究验证与风险分析，禁止自动下单。
- 仅使用 SR OHLC 价格逻辑，不使用成交量与动量指标。
- 策略信号：20日突破做多观察信号 + ATR止损 + 固定止盈止损。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import product

from tradingagents.dataflows.cn_futures.sugar_sr_provider import SugarSRProvider


@dataclass
class _Trade:
    entry_date: str
    exit_date: str
    entry: float
    exit: float
    pnl: float


@dataclass(frozen=True)
class BacktestParams:
    breakout_window: int = 20
    atr_period: int = 14
    stop_loss: float = 0.15
    take_profit: float = 0.35
    initial_cash: float = 1_000_000


@dataclass(frozen=True)
class OptimizeResult:
    params: BacktestParams
    win_rate: float
    max_drawdown: float
    avg_pnl: float
    signal_count: int
    trade_count: int


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


def _run_backtest(ohlc: list[dict], params: BacktestParams) -> OptimizeResult:
    breakout_period = params.breakout_window
    atr_period = params.atr_period
    stop_loss_ratio = params.stop_loss
    take_profit_ratio = params.take_profit
    initial_cash = params.initial_cash

    trades: list[_Trade] = []
    equity = [initial_cash]
    signal_count = 0

    in_pos = False
    entry_price = 0.0
    entry_date = ""
    stop_loss = 0.0
    take_profit = 0.0

    for i in range(breakout_period, len(ohlc)):
        bar = ohlc[i]
        prev20_high = max(x["high"] for x in ohlc[i - breakout_period : i])

        if not in_pos:
            if bar["close"] > prev20_high:
                signal_count += 1
                atr = _calc_atr_window(ohlc, i, period=atr_period)
                entry_price = bar["close"]
                entry_date = bar["date"]
                stop_loss = max(entry_price - 2 * atr, entry_price * (1 - stop_loss_ratio))
                take_profit = entry_price * (1 + take_profit_ratio)
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
    return OptimizeResult(
        params=params,
        win_rate=win_rate,
        max_drawdown=mdd,
        avg_pnl=avg_pnl,
        signal_count=signal_count,
        trade_count=len(trades),
    )


def generate_sugar_backtest_report(
    provider: str = "real",
    trade_date: str | None = None,
    bars: int = 240,
    params: BacktestParams | None = None,
) -> str:
    """生成中文回测摘要。"""
    end_date = trade_date or date.today().isoformat()
    data_provider = SugarSRProvider(provider=provider)
    ohlc = data_provider.get_kline(end_date, bars=max(60, bars))

    conf = params or BacktestParams()
    breakout_period = conf.breakout_window
    atr_period = conf.atr_period
    stop_loss_ratio = conf.stop_loss
    take_profit_ratio = conf.take_profit
    initial_cash = conf.initial_cash

    if len(ohlc) < 25:
        return (
            "## 白糖 SR 回测摘要\n\n"
            "数据不足，无法进行有效回测（至少需要 25 根K线）。\n\n"
            "### 参数摘要\n"
            f"- 突破周期：{breakout_period}\n"
            f"- ATR周期：{atr_period}\n"
            f"- 止损比例：{stop_loss_ratio:.0%}\n"
            f"- 止盈比例：{take_profit_ratio:.0%}\n\n"
            "### 防过拟合提示\n"
            "- 不要只看单次回测。\n"
            "- 不要频繁调参迎合历史。\n"
            "- 必须考虑手续费、滑点、换月、极端行情。\n"
            "- 必须做样本外验证。\n\n"
            "> 风险提示：本回测不构成投资建议，不代表未来收益，不可直接用于实盘自动交易。"
        )

    metrics = _run_backtest(ohlc, conf)
    win_rate = metrics.win_rate
    avg_pnl = metrics.avg_pnl
    mdd = metrics.max_drawdown
    signal_count = metrics.signal_count
    trade_count = metrics.trade_count
    equity_summary = "回测优化请使用 sugar-sr-optimize 查看参数排行。"
    return f"""## 白糖 SR 简单历史回测摘要

- 回测区间：{ohlc[0]['date']} 至 {ohlc[-1]['date']}
- 数据源：{data_provider.last_source}
- 策略说明：突破做多观察信号 + ATR止损 + 固定比例止盈止损

### 参数摘要
- 突破周期：{breakout_period}
- ATR周期：{atr_period}
- 止损比例：{stop_loss_ratio:.0%}
- 止盈比例：{take_profit_ratio:.0%}
- 初始资金：{initial_cash:,.2f}

### 回测统计
- 信号次数：{signal_count}
- 完成交易数：{trade_count}
- 胜率：{win_rate:.2f}%
- 平均盈亏：{avg_pnl:.2f}% / 笔
- 最大回撤：{mdd:.2f}%
- 简单资金曲线摘要（最近6节点）：{equity_summary}

### 防过拟合提示
- 不要只看单次回测。
- 不要频繁调参迎合历史。
- 必须考虑手续费、滑点、换月、极端行情。
- 必须做样本外验证。

{data_provider.last_warning}
> 风险提示：本回测不构成投资建议，不代表未来收益，不可直接用于实盘自动交易。
"""


def optimize_sugar_backtest(
    provider: str,
    trade_date: str | None,
    breakout_range: list[int],
    atr_range: list[int],
    stop_loss_range: list[float],
    take_profit_range: list[float],
    initial_cash: float,
    top_n: int = 10,
) -> tuple[str, list[OptimizeResult]]:
    end_date = trade_date or date.today().isoformat()
    data_provider = SugarSRProvider(provider=provider)
    ohlc = data_provider.get_kline(end_date, bars=240)
    if len(ohlc) < 60:
        return "数据不足，无法执行参数扫描（至少需要 60 根K线）。", []

    results: list[OptimizeResult] = []
    for b, a, sl, tp in product(breakout_range, atr_range, stop_loss_range, take_profit_range):
        params = BacktestParams(
            breakout_window=b,
            atr_period=a,
            stop_loss=sl,
            take_profit=tp,
            initial_cash=initial_cash,
        )
        results.append(_run_backtest(ohlc, params))

    ranked = sorted(results, key=lambda x: (x.win_rate, x.avg_pnl, -x.max_drawdown), reverse=True)
    selected = ranked[:top_n]
    lines = [
        "## 白糖 SR 回测参数扫描报告",
        "",
        f"- 回测区间：{ohlc[0]['date']} 至 {ohlc[-1]['date']}",
        f"- 数据源：{data_provider.last_source}",
        f"- 扫描组合数：{len(results)}",
        f"- TopN：{top_n}",
        "",
        "| 排名 | breakout | atr | stop_loss | take_profit | 胜率 | 最大回撤 | 平均盈亏 | 信号次数 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for i, item in enumerate(selected, start=1):
        p = item.params
        lines.append(
            f"| {i} | {p.breakout_window} | {p.atr_period} | {p.stop_loss:.2f} | {p.take_profit:.2f} | "
            f"{item.win_rate:.2f}% | {item.max_drawdown:.2f}% | {item.avg_pnl:.2f}% | {item.signal_count} |"
        )

    lines.extend(
        [
            "",
            "### 防过拟合提示",
            "- 参数扫描仅用于研究验证，不用于自动寻找“万能参数”或“圣杯参数”。",
            "- 排行靠前不代表未来有效，必须做样本外与跨阶段验证。",
            "- 必须纳入手续费、滑点、换月与极端行情压力测试。",
            "",
            f"{data_provider.last_warning}",
            "> 风险提示：本功能仅用于研究辅助与风险分析，不构成投资建议，禁止自动下单与自动实盘部署。",
        ]
    )
    return "\n".join(lines), selected
