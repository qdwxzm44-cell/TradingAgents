"""最小 demo：打印中文白糖 SR 技术面分析报告（Mock）。"""

from tradingagents.agents.analysts.sugar_technical_analyst import (
    generate_sugar_technical_report,
)


def main():
    trade_date = "2026-05-08"
    print(generate_sugar_technical_report(trade_date, bars=12))


if __name__ == "__main__":
    main()
