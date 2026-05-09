"""中国白糖 SR 总报告 Agent（Phase 5, Mock-only）。

职责：汇总基本面、技术面、风险面，输出中文投研日报。
约束：仅研究辅助，禁止自动下单。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tradingagents.agents.analysts.sugar_fundamental_analyst import (
    generate_sugar_fundamental_report,
)
from tradingagents.agents.analysts.sugar_technical_analyst import (
    generate_sugar_technical_report,
)
from tradingagents.agents.risk_mgmt.sugar_risk_analyst import generate_sugar_risk_report
from tradingagents.dataflows.cn_futures.sugar_sr_provider import SugarSRProvider


def _extract_last_bold_value(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("**") and ln.endswith("**") and len(ln) > 4:
            return ln.strip("*")
    return "中性"


def _extract_metric_line(text: str, key: str) -> str:
    candidates = []
    for ln in text.splitlines():
        raw = ln.strip()
        if key in raw:
            candidates.append(raw)
    for ln in candidates:
        if "：" in ln or ":" in ln:
            return ln
    return candidates[-1] if candidates else "未提取到"


def _extract_strategy(fund_bias: str, tech_bias: str, risk_level: str) -> str:
    if risk_level == "高":
        return "高风险禁止交易"
    if fund_bias == "偏多" and tech_bias == "偏多":
        return "谨慎偏多"
    if fund_bias == "偏空" and tech_bias == "偏空":
        return "谨慎偏空"
    return "观望"


def _extract_market_env(fund_bias: str, tech_bias: str, risk_level: str) -> str:
    if risk_level == "高":
        return "高波动高不确定环境"
    if fund_bias == tech_bias and fund_bias in ("偏多", "偏空"):
        return "方向相对一致但需风控"
    return "分歧环境，信号一致性一般"


def _build_pre_trade_checklist(
    fund_bias: str,
    tech_bias: str,
    risk_level: str,
    atr_line: str,
    rollover_line: str,
    night_line: str,
) -> str:
    atr_high = "是" if "偏高" in atr_line or "高波动" in atr_line else "否"
    near_rollover = "是" if "临近" in rollover_line else "否"
    policy_external_risk = "是" if ("政策" in night_line or "外盘" in night_line or "夜盘" in night_line) else "否"

    fundamental_support = "是" if fund_bias in ("偏多", "偏空") else "否"
    technical_breakout = "是" if tech_bias in ("偏多", "偏空") else "否"
    acceptable_risk = "是" if risk_level in ("低", "中") else "否"
    manual_review = "是" if (risk_level == "高" or atr_high == "是" or near_rollover == "是") else "否"

    focus_status = "是"
    if risk_level == "高" or atr_high == "是":
        focus_status = "谨慎"
    if near_rollover == "是" and risk_level == "高":
        focus_status = "否"

    final_state = "可观察"
    if risk_level == "高" or near_rollover == "是":
        final_state = "暂停交易"
    elif atr_high == "是" or policy_external_risk == "是" or fund_bias != tech_bias:
        final_state = "谨慎观察"

    return "\n".join(
        [
            f"- 今日是否允许关注：{focus_status}",
            f"- 基本面是否支持方向：{fundamental_support}",
            f"- 技术面是否出现突破：{technical_breakout}",
            f"- ATR 波动是否过高：{atr_high}",
            f"- 风险等级是否可接受：{acceptable_risk}",
            f"- 是否临近换月：{near_rollover}",
            f"- 是否存在政策/外盘/夜盘风险：{policy_external_risk}",
            f"- 是否建议人工复核：{manual_review}",
            f"- 最终状态：{final_state}",
        ]
    )


def generate_sugar_full_report(
    trade_date: str,
    provider: str | None = None,
    fundamental_file: str | None = None,
    previous_report_summary: str | None = None,
) -> str:
    """生成完整中文白糖 SR 投研日报。"""
    data_provider = SugarSRProvider(provider=provider)
    contract = data_provider.get_main_contract_info(trade_date)
    recent_klines = data_provider.get_kline(trade_date, bars=5)
    fund_report = generate_sugar_fundamental_report(trade_date, fundamental_file=fundamental_file)
    tech_report = generate_sugar_technical_report(trade_date, provider=provider)
    risk_report = generate_sugar_risk_report(trade_date)

    fund_bias = _extract_last_bold_value(fund_report)
    tech_bias = _extract_last_bold_value(tech_report)
    risk_level = _extract_last_bold_value(risk_report)

    support_line = _extract_metric_line(tech_report, "最近20日最低价")
    resistance_line = _extract_metric_line(tech_report, "最近20日最高价")
    atr_line = _extract_metric_line(tech_report, "ATR(14)")
    night_line = _extract_metric_line(risk_report, "夜盘时段")
    rollover_line = _extract_metric_line(risk_report, "换月提示")
    fundamental_source_line = _extract_metric_line(fund_report, "基本面数据源")

    market_env = _extract_market_env(fund_bias, tech_bias, risk_level)
    if risk_level == "高":
        long_short_bias = "中性"
    elif fund_bias == tech_bias:
        long_short_bias = fund_bias
    else:
        long_short_bias = "中性"

    strategy = _extract_strategy(fund_bias, tech_bias, risk_level)
    checklist = _build_pre_trade_checklist(
        fund_bias=fund_bias,
        tech_bias=tech_bias,
        risk_level=risk_level,
        atr_line=atr_line,
        rollover_line=rollover_line,
        night_line=night_line,
    )
    kline_preview = "\n".join([f"- {x['date']}: O={x['open']:.2f}, H={x['high']:.2f}, L={x['low']:.2f}, C={x['close']:.2f}" for x in recent_klines])


    compare_section = previous_report_summary or "暂无上一期报告可对比。"

    return f"""# 白糖 SR 投研日报

- 日期：{trade_date}
- 研究定位：仅研究辅助，不自动下单
- 当前数据源：{data_provider.last_source}

1. 当前主力合约
{contract['main_contract']}（交易所：{contract['exchange']}）

2. 最近K线预览
{kline_preview}

3. 基本面结论
{fund_bias}

基本面数据源信息：{fundamental_source_line}

4. 技术面结论
{tech_bias}

5. 风险等级
{risk_level}

6. 当前市场环境
{market_env}

7. 多空倾向
{long_short_bias}

8. 关键支撑位
{support_line}

9. 关键压力位
{resistance_line}

10. ATR波动风险
{atr_line}

11. 夜盘风险
{night_line}

12. 换月风险
{rollover_line}

13. 策略建议
{strategy}

14. 风险提示
{data_provider.last_warning}
本报告仅用于投研与风险分析，不构成投资建议；禁止自动开仓、自动下单，且不提供任何精确盈利承诺。

15. 交易前检查清单（仅研究辅助）
{checklist}

16. 较上一期变化
{compare_section}
"""


def _extract_report_field(report_text: str, section_title: str) -> str:
    for idx, line in enumerate(report_text.splitlines()):
        if line.strip() == section_title:
            for next_line in report_text.splitlines()[idx + 1 :]:
                clean = next_line.strip()
                if clean:
                    return clean
    return "未提取到"


def _build_previous_compare_summary(current_report: str, previous_report: str) -> str:
    mappings = [
        ("3. 基本面结论", "基本面结论变化"),
        ("4. 技术面结论", "技术趋势变化"),
        ("5. 风险等级", "风险等级变化"),
        ("7. 多空倾向", "多空倾向变化"),
    ]
    lines: list[str] = []
    for section_title, change_label in mappings:
        current_value = _extract_report_field(current_report, section_title)
        previous_value = _extract_report_field(previous_report, section_title)
        if current_value == previous_value:
            lines.append(f"- {change_label}：无变化（上一期={previous_value}，本期={current_value}）")
        else:
            lines.append(f"- {change_label}：{previous_value} -> {current_value}")
    return "\n".join(lines)


def _get_previous_archive_path(archive_path: Path) -> Path | None:
    archive_dir = archive_path.parent
    if not archive_dir.exists():
        return None

    all_reports = sorted(archive_dir.glob("*.md"))
    previous_candidates = [p for p in all_reports if p.name < archive_path.name]
    return previous_candidates[-1] if previous_candidates else None


def generate_and_archive_sugar_report(
    trade_date: str,
    provider: str | None = None,
    fundamental_file: str | None = None,
    archive_root: str = "reports/sugar_sr",
) -> tuple[str, Path]:
    datetime.strptime(trade_date, "%Y-%m-%d")
    archive_path = Path(archive_root) / f"{trade_date}.md"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    previous_path = _get_previous_archive_path(archive_path)

    base_report = generate_sugar_full_report(
        trade_date,
        provider=provider,
        fundamental_file=fundamental_file,
        previous_report_summary="暂无上一期报告可对比。",
    )

    if previous_path and previous_path.exists():
        previous_report = previous_path.read_text(encoding="utf-8")
        compare_summary = _build_previous_compare_summary(base_report, previous_report)
        final_report = generate_sugar_full_report(
            trade_date,
            provider=provider,
            fundamental_file=fundamental_file,
            previous_report_summary=compare_summary,
        )
    else:
        final_report = base_report

    archive_path.write_text(final_report, encoding="utf-8")
    return final_report, archive_path


def create_sugar_research_manager(_llm=None):
    """兼容现有 manager 工厂风格；本阶段不依赖 LLM。"""

    def sugar_research_node(state):
        trade_date = str(state.get("trade_date", "2026-01-01"))
        report = generate_sugar_full_report(trade_date)
        return {
            "sugar_sr_daily_report": report,
        }

    return sugar_research_node
