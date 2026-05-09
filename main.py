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

load_dotenv()
load_dotenv(".env.enterprise", override=False)

app = typer.Typer(help="TradingAgents 统一 CLI（含白糖 SR mock 入口）", no_args_is_help=True)


@app.command("sugar-sr")
def sugar_sr(
    date: str = typer.Option(..., "--date", help="交易日期，格式 YYYY-MM-DD"),
    output: str | None = typer.Option(None, "--output", help="可选：将日报导出为 Markdown 文件路径"),
    provider: str = typer.Option("real", "--provider", help="数据源: real 或 mock"),
    fundamental_file: str | None = typer.Option(
        None,
        "--fundamental-file",
        help="白糖 SR 基本面本地文件路径（CSV/JSON），例如 data/sugar_fundamental.csv",
    ),
    archive: bool = typer.Option(False, "--archive", help="启用历史归档与上一期对比，写入 reports/sugar_sr/YYYY-MM-DD.md"),
) -> None:
    """输出白糖 SR 当日投研日报。"""
    if archive:
        report, archive_path = generate_and_archive_sugar_report(
            date,
            provider=provider,
            fundamental_file=fundamental_file,
        )
    else:
        report = generate_sugar_full_report(date, provider=provider, fundamental_file=fundamental_file)
        archive_path = None

    typer.echo(report)

    if archive_path:
        typer.echo(f"\n已归档日报：{archive_path}")

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        typer.echo(f"\n已导出 Markdown 报告：{output_path}")


@app.command("sugar-sr-backtest")
def sugar_sr_backtest(
    provider: str = typer.Option("real", "--provider", help="数据源: real 或 mock"),
    date: str | None = typer.Option(None, "--date", help="可选：回测结束日期 YYYY-MM-DD（默认今日）"),
    output: str | None = typer.Option(None, "--output", help="可选：将回测报告导出为 Markdown 文件路径"),
    breakout_window: int = typer.Option(20, "--breakout-window", help="突破窗口（默认20）"),
    atr_period: int = typer.Option(14, "--atr-period", help="ATR周期（默认14）"),
    stop_loss: float = typer.Option(0.15, "--stop-loss", help="止损比例（默认0.15）"),
    take_profit: float = typer.Option(0.35, "--take-profit", help="止盈比例（默认0.35）"),
    initial_cash: float = typer.Option(1_000_000, "--initial-cash", help="初始资金（默认1000000）"),
) -> None:
    """输出白糖 SR 研究用途的简单历史回测摘要。"""
    if breakout_window < 2:
        raise typer.BadParameter("参数异常：--breakout-window 必须 >= 2")
    if atr_period < 2:
        raise typer.BadParameter("参数异常：--atr-period 必须 >= 2")
    if not (0 < stop_loss < 1):
        raise typer.BadParameter("参数异常：--stop-loss 必须在 (0, 1) 区间")
    if not (0 < take_profit < 2):
        raise typer.BadParameter("参数异常：--take-profit 必须在 (0, 2) 区间")
    if initial_cash <= 0:
        raise typer.BadParameter("参数异常：--initial-cash 必须 > 0")

    params = BacktestParams(
        breakout_window=breakout_window,
        atr_period=atr_period,
        stop_loss=stop_loss,
        take_profit=take_profit,
        initial_cash=initial_cash,
    )
    typer.echo(
        "参数摘要："
        f"breakout_window={params.breakout_window}, "
        f"atr_period={params.atr_period}, "
        f"stop_loss={params.stop_loss}, "
        f"take_profit={params.take_profit}, "
        f"initial_cash={params.initial_cash}"
    )
    report = generate_sugar_backtest_report(provider=provider, trade_date=date, params=params)
    typer.echo(report)

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        typer.echo(f"\n已导出 Markdown 回测报告：{output_path}")


@app.command("stock-demo")
def stock_demo() -> None:
    """兼容旧入口：引导使用原股票 CLI 流程。"""
    typer.echo("请使用 `python -m cli.main analyze` 运行原股票多智能体流程（仅研究辅助）。")


if __name__ == "__main__":
    app()
