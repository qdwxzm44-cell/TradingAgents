"""项目统一 CLI 入口。"""
from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

from tradingagents.agents.managers.sugar_research_manager import (
    generate_and_archive_sugar_report,
    generate_sugar_full_report,
)
from tradingagents.agents.managers.sugar_backtest_manager import BacktestParams, generate_sugar_backtest_report
from tradingagents.agents.managers.sugar_backtest_manager import optimize_sugar_backtest
from tradingagents.config.sugar_sr_config import load_sugar_sr_config, summarize_config

load_dotenv()
load_dotenv(".env.enterprise", override=False)

app = typer.Typer(help="TradingAgents 统一 CLI（含白糖 SR mock 入口）", no_args_is_help=True)


def _parse_int_range(raw: str, flag_name: str) -> list[int]:
    try:
        values = [int(x.strip()) for x in raw.split(",") if x.strip()]
    except ValueError as exc:
        raise typer.BadParameter(f"参数异常：{flag_name} 必须是逗号分隔整数") from exc
    if not values or any(v < 2 for v in values):
        raise typer.BadParameter(f"参数异常：{flag_name} 至少包含一个 >= 2 的整数")
    return values


def _parse_float_range(raw: str, flag_name: str, low: float, high: float) -> list[float]:
    try:
        values = [float(x.strip()) for x in raw.split(",") if x.strip()]
    except ValueError as exc:
        raise typer.BadParameter(f"参数异常：{flag_name} 必须是逗号分隔小数") from exc
    if not values or any(v <= low or v >= high for v in values):
        raise typer.BadParameter(f"参数异常：{flag_name} 必须在 ({low}, {high}) 区间")
    return values


@app.command("sugar-sr")
def sugar_sr(
    date: str = typer.Option(..., "--date", help="交易日期，格式 YYYY-MM-DD"),
    output: str | None = typer.Option(None, "--output", help="可选：将日报导出为 Markdown 文件路径"),
    provider: str | None = typer.Option(None, "--provider", help="数据源: real 或 mock（默认读取配置）"),
    fundamental_file: str | None = typer.Option(
        None,
        "--fundamental-file",
        help="白糖 SR 基本面本地文件路径（CSV/JSON），例如 data/sugar_fundamental.csv",
    ),
    archive: bool = typer.Option(False, "--archive", help="启用历史归档与上一期对比，写入 reports/sugar_sr/YYYY-MM-DD.md"),
) -> None:
    conf, warnings = load_sugar_sr_config()
    for w in warnings:
        typer.echo(w)
    provider_effective = provider or conf.provider
    typer.echo(summarize_config(conf))

    if archive:
        report, archive_path = generate_and_archive_sugar_report(
            date,
            provider=provider_effective,
            fundamental_file=fundamental_file,
            archive_root=conf.archive_dir,
        )
    else:
        report = generate_sugar_full_report(date, provider=provider_effective, fundamental_file=fundamental_file)
        archive_path = None

    typer.echo(report)
    if archive_path:
        typer.echo(f"\n已归档日报：{archive_path}")

    output_target = output
    if not output_target and conf.markdown_export_enabled:
        output_target = str(Path(conf.report_output_dir) / f"sugar_sr_{date}.md")

    if output_target:
        output_path = Path(output_target)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        typer.echo(f"\n已导出 Markdown 报告：{output_path}")


@app.command("sugar-sr-backtest")
def sugar_sr_backtest(
    provider: str | None = typer.Option(None, "--provider", help="数据源: real 或 mock（默认读取配置）"),
    date: str | None = typer.Option(None, "--date", help="可选：回测结束日期 YYYY-MM-DD（默认今日）"),
    output: str | None = typer.Option(None, "--output", help="可选：将回测报告导出为 Markdown 文件路径"),
    breakout_window: int | None = typer.Option(None, "--breakout-window", help="突破窗口（默认读取配置）"),
    atr_period: int | None = typer.Option(None, "--atr-period", help="ATR周期（默认读取配置）"),
    stop_loss: float | None = typer.Option(None, "--stop-loss", help="止损比例（默认读取配置）"),
    take_profit: float | None = typer.Option(None, "--take-profit", help="止盈比例（默认读取配置）"),
    initial_cash: float | None = typer.Option(None, "--initial-cash", help="初始资金（默认读取配置）"),
) -> None:
    conf, warnings = load_sugar_sr_config()
    for w in warnings:
        typer.echo(w)
    provider_effective = provider or conf.provider
    bw = breakout_window if breakout_window is not None else conf.breakout_window
    ap = atr_period if atr_period is not None else conf.atr_period
    sl = stop_loss if stop_loss is not None else conf.stop_loss
    tp = take_profit if take_profit is not None else conf.take_profit
    cash = initial_cash if initial_cash is not None else conf.initial_cash

    if bw < 2:
        raise typer.BadParameter("参数异常：--breakout-window 必须 >= 2")
    if ap < 2:
        raise typer.BadParameter("参数异常：--atr-period 必须 >= 2")
    if not (0 < sl < 1):
        raise typer.BadParameter("参数异常：--stop-loss 必须在 (0, 1) 区间")
    if not (0 < tp < 2):
        raise typer.BadParameter("参数异常：--take-profit 必须在 (0, 2) 区间")
    if cash <= 0:
        raise typer.BadParameter("参数异常：--initial-cash 必须 > 0")

    params = BacktestParams(breakout_window=bw, atr_period=ap, stop_loss=sl, take_profit=tp, initial_cash=cash)
    typer.echo(summarize_config(conf))
    typer.echo(
        "参数摘要："
        f"breakout_window={params.breakout_window}, atr_period={params.atr_period}, stop_loss={params.stop_loss}, "
        f"take_profit={params.take_profit}, initial_cash={params.initial_cash}, provider={provider_effective}"
    )
    report = generate_sugar_backtest_report(provider=provider_effective, trade_date=date, params=params)
    typer.echo(report)

    output_target = output
    if not output_target and conf.markdown_export_enabled:
        target_date = date or "latest"
        output_target = str(Path(conf.report_output_dir) / f"sugar_sr_backtest_{target_date}.md")
    if output_target:
        output_path = Path(output_target)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        typer.echo(f"\n已导出 Markdown 回测报告：{output_path}")


@app.command("stock-demo")
def stock_demo() -> None:
    """兼容旧入口：引导使用原股票 CLI 流程。"""
    typer.echo("请使用 `python -m cli.main analyze` 运行原股票多智能体流程（仅研究辅助）。")


@app.command("sugar-sr-optimize")
def sugar_sr_optimize(
    provider: str = typer.Option("real", "--provider", help="数据源: real 或 mock"),
    date: str | None = typer.Option(None, "--date", help="可选：回测结束日期 YYYY-MM-DD（默认今日）"),
    breakout_range: str = typer.Option("10,20,30", "--breakout-range", help="突破窗口范围，如 10,20,30"),
    atr_range: str = typer.Option("10,14,20", "--atr-range", help="ATR 周期范围，如 10,14,20"),
    stop_loss_range: str = typer.Option("0.10,0.15", "--stop-loss-range", help="止损比例范围，如 0.10,0.15"),
    take_profit_range: str = typer.Option("0.20,0.35", "--take-profit-range", help="止盈比例范围，如 0.20,0.35"),
    initial_cash: float = typer.Option(1_000_000, "--initial-cash", help="初始资金（默认1000000）"),
    top_n: int = typer.Option(10, "--top-n", help="输出前 N 个结果"),
    output: str | None = typer.Option(None, "--output", help="可选：导出 Markdown 排行报告路径"),
) -> None:
    if initial_cash <= 0:
        raise typer.BadParameter("参数异常：--initial-cash 必须 > 0")
    if top_n <= 0:
        raise typer.BadParameter("参数异常：--top-n 必须 > 0")
    b_range = _parse_int_range(breakout_range, "--breakout-range")
    a_range = _parse_int_range(atr_range, "--atr-range")
    sl_range = _parse_float_range(stop_loss_range, "--stop-loss-range", 0, 1)
    tp_range = _parse_float_range(take_profit_range, "--take-profit-range", 0, 2)
    report, _ = optimize_sugar_backtest(provider=provider, trade_date=date, breakout_range=b_range, atr_range=a_range, stop_loss_range=sl_range, take_profit_range=tp_range, initial_cash=initial_cash, top_n=top_n)
    typer.echo(report)
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        typer.echo(f"\n已导出 Markdown 参数扫描报告：{output_path}")


if __name__ == "__main__":
    app()
