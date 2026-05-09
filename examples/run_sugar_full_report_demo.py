"""最小 demo：打印完整中文白糖 SR 投研日报（Mock）。"""

from tradingagents.agents.managers.sugar_research_manager import generate_sugar_full_report


def main():
    trade_date = "2026-05-08"
    print(generate_sugar_full_report(trade_date))


if __name__ == "__main__":
    main()
