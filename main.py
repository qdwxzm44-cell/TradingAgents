"""项目统一 CLI 入口。"""
from __future__ import annotations

import typer
from dotenv import load_dotenv

from tradingagents.agents.managers.sugar_research_manager import generate_sugar_full_report

load_dotenv()
load_dotenv(".env.enterprise", override=False)

app = typer.Typer(help="TradingAgents 统一 CLI（含白糖 SR mock 入口）", no_args_is_help=True)


@app.command("sugar-sr")
def sugar_sr(date: str = typer.Option(..., "--date", help="交易日期，格式 YYYY-MM-DD")) -> None:
    """输出白糖 SR 当日投研日报（mock）。"""
    typer.echo(generate_sugar_full_report(date))


@app.command("stock-demo")
def stock_demo() -> None:
    """兼容旧入口：引导使用原股票 CLI 流程。"""
    typer.echo("请使用 `python -m cli.main analyze` 运行原股票多智能体流程（仅研究辅助）。")


if __name__ == "__main__":
    app()
