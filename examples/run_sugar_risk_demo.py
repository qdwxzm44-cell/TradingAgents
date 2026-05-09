"""最小 demo：打印中文白糖 SR 风险分析报告（Mock）。"""

from tradingagents.agents.risk_mgmt.sugar_risk_analyst import generate_sugar_risk_report


def main():
    trade_date = "2026-05-08"
    print(generate_sugar_risk_report(trade_date))


if __name__ == "__main__":
    main()
