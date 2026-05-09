"""最小 demo：输出中文白糖基本面分析报告（Mock）。"""

from tradingagents.agents.analysts.sugar_fundamental_analyst import (
    generate_sugar_fundamental_report,
)


def main():
    trade_date = "2026-05-08"
    report = generate_sugar_fundamental_report(trade_date)
    print(report)


if __name__ == "__main__":
    main()
