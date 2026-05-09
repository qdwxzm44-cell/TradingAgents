# 白糖 SR 多智能体投研系统使用文档

> **风险提示**：本系统仅用于研究辅助与风险分析，不构成任何投资建议。期货交易风险较高，请结合自身风险承受能力谨慎决策。

## 1. 系统定位

- 当前版本：`v0.1.0`（里程碑日期：2026-05-09）。

- 本系统服务于郑商所白糖期货 SR 主力合约的研究分析。
- 系统输出用于投研参考，不构成买卖建议。
- 默认保留多 Agent 协作范式（基本面、技术面、风险与管理角色）。
- **禁止自动下单**：系统不连接实盘交易执行，不提供自动报单能力。

## 2. 功能概览

- 白糖 SR 日度投研报告生成（支持归档、对比上一期）。
- 白糖 SR 策略回测（突破 + ATR 风险控制）。
- 白糖 SR 参数扫描（网格组合排序）。
- Markdown 报告导出。
- 本地 CSV/JSON 基本面数据接入。
- 与原股票流程并存：`stock-demo` 仅做入口提示，原 `python -m cli.main analyze` 流程不受影响。

## 3. 安装依赖

```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -e .
```

可选：

```bash
cp .env.example .env
# 按需填写模型/API 密钥
```

## 4. 配置文件说明

白糖 SR 默认配置文件：`config/sugar_sr.yaml`。

核心字段：

- `provider`: 数据源（`real` / `mock`）。
- `fallback_enabled`: 真实源失败时是否回退。
- `breakout_window`, `atr_period`: 技术参数。
- `stop_loss`, `take_profit`: 风险参数。
- `initial_cash`: 回测初始资金。
- `report_output_dir`: Markdown 默认输出目录。
- `archive_dir`: 历史归档目录。
- `markdown_export_enabled`: 未传 `--output` 时是否自动导出。

## 5. CLI 使用方法

统一入口：

```bash
python main.py --help
```

查看白糖相关命令：

```bash
python main.py sugar-sr --help
python main.py sugar-sr-backtest --help
python main.py sugar-sr-optimize --help
```

## 6. 生成投研日报

```bash
python main.py sugar-sr --date 2026-05-08 --provider mock
```

启用归档：

```bash
python main.py sugar-sr --date 2026-05-08 --archive
```

接入本地基本面文件：

```bash
python main.py sugar-sr --date 2026-05-08 --fundamental-file data/sugar_fundamental.csv
```

## 7. Markdown 导出

显式导出：

```bash
python main.py sugar-sr --date 2026-05-08 --output reports/sugar_sr/sugar_sr_2026-05-08.md
```

当 `markdown_export_enabled: true` 且未传 `--output` 时，系统自动导出到 `report_output_dir`。

## 8. 历史归档

开启 `--archive` 后，日报归档到：

- `archive_dir/YYYY-MM-DD.md`

并自动尝试读取上一期（若存在）做对比摘要。

## 9. 本地 CSV/JSON 基本面数据格式

CSV 示例（列名建议）：

```csv
trade_date,inventory,import_cost,spot_basis,production_estimate,comment
2026-05-08,540000,5750,120,1020000,"产区天气偏干"
```

JSON 示例：

```json
{
  "trade_date": "2026-05-08",
  "inventory": 540000,
  "import_cost": 5750,
  "spot_basis": 120,
  "production_estimate": 1020000,
  "comment": "产区天气偏干"
}
```

说明：

- 建议包含 `trade_date`。
- 可附加任意扩展字段，系统将以“研究辅助”方式纳入文本分析。

## 10. 回测命令

```bash
python main.py sugar-sr-backtest --provider mock --date 2026-05-08
```

带参数：

```bash
python main.py sugar-sr-backtest \
  --provider real \
  --date 2026-05-08 \
  --breakout-window 20 \
  --atr-period 14 \
  --stop-loss 0.12 \
  --take-profit 0.30 \
  --initial-cash 1000000
```

## 11. 参数扫描命令

```bash
python main.py sugar-sr-optimize \
  --provider mock \
  --date 2026-05-08 \
  --breakout-range 10,20,30 \
  --atr-range 10,14,20 \
  --stop-loss-range 0.10,0.15 \
  --take-profit-range 0.20,0.35 \
  --top-n 10 \
  --output reports/sugar_sr/optimize_2026-05-08.md
```

## 12. 测试命令

白糖 SR 相关：

```bash
pytest tests/sugar_sr -q
```

可选补充：

```bash
pytest tests/test_sugar_backtest_cli.py tests/test_sugar_report_archive.py -q
```

## 13. 常见问题

1. **为什么没有实盘下单按钮？**  
   因为系统定位为研究辅助与风险分析，明确禁止自动下单。

2. **`provider=real` 报错怎么办？**  
   先用 `provider=mock` 验证流程；再检查网络、数据接口和本地环境变量。

3. **导出文件在哪里？**  
   优先看 `--output` 指定路径；未指定时看 `config/sugar_sr.yaml` 的 `report_output_dir`。

4. **如何保持股票流程不受影响？**  
   股票流程继续使用 `python -m cli.main analyze`；白糖流程在 `python main.py` 的独立命令下运行。

## 14. 当前限制

- 输出仅供研究，不做收益承诺。
- 白糖技术面使用 OHLC 价格与 ATR/突破逻辑，不使用成交量过滤。
- 不提供自动下单、资金托管、交易所撮合等交易执行能力。
- 参数扫描结果受样本区间与数据质量影响，需人工复核。

## 15. 禁止自动下单说明

- 本项目当前实现不包含自动下单接口。
- 文档、CLI 与配置均以“研究辅助”为边界。
- 如需接入交易系统，必须在合规评估、风控审批与人工确认机制完备后另行开发；本仓库当前阶段**不提供**该能力。

---

> **风险提示（再次强调）**：以上内容仅用于研究与教学演示，不构成投资建议或收益保证。期货市场波动较大，请审慎评估风险。
