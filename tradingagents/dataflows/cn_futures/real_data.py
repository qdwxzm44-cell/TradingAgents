"""白糖 SR 真实行情数据提供（Phase 8）。

说明：
- 仅用于研究辅助与风险分析；禁止自动下单。
- 优先使用 akshare 获取郑商所白糖 SR 主力连续日线。
- 获取失败时由上层 provider 自动回退 mock 数据。
"""

from __future__ import annotations

from datetime import datetime
from math import isnan


def _normalize_rows(df) -> list[dict]:
    rename_map = {
        "日期": "date",
        "date": "date",
        "开盘": "open",
        "open": "open",
        "最高": "high",
        "high": "high",
        "最低": "low",
        "low": "low",
        "收盘": "close",
        "close": "close",
    }
    df = df.rename(columns=rename_map)
    required = ["date", "open", "high", "low", "close"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"真实行情缺少字段: {missing_cols}")

    rows = df[required].copy()
    rows["date"] = rows["date"].astype(str).str[:10]
    for c in ["open", "high", "low", "close"]:
        rows[c] = rows[c].astype(float)

    return rows.to_dict(orient="records")


def _to_float(v) -> float:
    value = float(v)
    if isnan(value):
        raise ValueError("存在 NaN 数值")
    return value


def validate_and_clean_ohlc_rows(rows: list[dict]) -> list[dict]:
    if not rows:
        raise ValueError("真实行情为空")

    required = ["date", "open", "high", "low", "close"]
    clean_rows: list[dict] = []
    for i, row in enumerate(rows):
        for key in required:
            if key not in row or row[key] is None:
                raise ValueError(f"第 {i} 条K线存在空值: {key}")
        try:
            date_obj = datetime.fromisoformat(str(row["date"])[:10]).date()
        except Exception as exc:
            raise ValueError(f"第 {i} 条K线日期不可解析: {row['date']}") from exc

        try:
            o = _to_float(row["open"])
            h = _to_float(row["high"])
            l = _to_float(row["low"])
            c = _to_float(row["close"])
        except Exception as exc:
            raise ValueError(f"第 {i} 条K线OHLC包含非数字值") from exc

        if h < max(o, c, l):
            raise ValueError(f"第 {i} 条K线不满足 high >= max(open, close, low)")
        if l > min(o, c, h):
            raise ValueError(f"第 {i} 条K线不满足 low <= min(open, close, high)")

        clean_rows.append(
            {"date": date_obj.isoformat(), "open": o, "high": h, "low": l, "close": c}
        )

    # 删除重复日期（保留最后一条）
    dedup: dict[str, dict] = {}
    for row in clean_rows:
        dedup[row["date"]] = row

    ordered_rows = sorted(dedup.values(), key=lambda x: x["date"])
    parsed = [datetime.fromisoformat(r["date"]) for r in ordered_rows]
    if parsed != sorted(parsed):
        raise ValueError("真实行情日期未按升序排列")

    full_span = (parsed[-1] - parsed[0]).days + 1
    if len(parsed) < min(full_span, len(parsed) + 3):
        # 交易日天然可能跳空（周末/节假日），这里做轻量缺失检查：若跨度远大于条数则报错。
        if full_span > len(parsed) * 3:
            raise ValueError("真实行情日期存在异常缺失")
    return ordered_rows


def get_real_sugar_main_daily(trade_date: str, bars: int = 12) -> list[dict]:
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("未安装 akshare，无法拉取真实行情") from exc

    # 使用主力连续 SR0（日线）
    df = ak.futures_main_sina(symbol="SR0")
    rows = _normalize_rows(df)
    rows = [r for r in rows if r["date"] <= trade_date]
    if not rows:
        raise ValueError(f"在 {trade_date} 前未获取到 SR 主力连续数据")

    rows = rows[-bars:]
    rows = validate_and_clean_ohlc_rows(rows)
    return rows
