"""最小 demo：打印 SR 主力合约信息、保证金、手续费、最小变动价位、mock K线。"""

from __future__ import annotations

from tradingagents.dataflows.cn_futures import SugarSRMockProvider


def main() -> None:
    trade_date = "2026-05-08"
    provider = SugarSRMockProvider()

    main_info = provider.get_main_contract_info(trade_date)
    specs = provider.get_contract_specs()
    kline = provider.get_mock_kline(trade_date, bars=8)

    print("=== 中国白糖期货 SR Mock Demo（仅研究辅助）===")
    print("SR 主力合约信息:")
    print(main_info)

    print("\n合约参数:")
    print(f"保证金比例: {specs['margin_ratio']}")
    print(f"开仓手续费(每手): {specs['open_fee_per_lot']}")
    print(f"平仓手续费(每手): {specs['close_fee_per_lot']}")
    print(f"最小变动价位: {specs['price_tick']}")

    print("\nMock K线数据(OHLC):")
    for row in kline:
        print(row)

    print("\n风险提示: 以上为 mock 演示数据，仅用于系统开发联调，不构成投资建议，禁止自动下单。")


if __name__ == "__main__":
    main()
