"""白糖 SR 基本面本地数据 Provider（Phase 11）。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from tradingagents.dataflows.cn_futures.fundamental_mock_data import get_sugar_fundamental_mock_snapshot

_REQUIRED_FIELDS = {
    "date",
    "production",
    "sales",
    "inventory",
    "import_volume",
    "raw_sugar_price",
    "usdcny",
    "weather_note",
    "policy_note",
}


def _safe_float(v: str | float | int | None, default: float = 0.0) -> float:
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _build_snapshot(record: dict[str, object], trade_date: str) -> dict:
    raw_price = _safe_float(record.get("raw_sugar_price"))
    return {
        "trade_date": str(record.get("date") or trade_date),
        "production": {
            "current_season_million_tons": _safe_float(record.get("production")),
            "yoy_change_pct": 0.0,
            "interpretation": f"产量读数：{record.get('production')}。",
        },
        "inventory": {
            "industrial_inventory_million_tons": _safe_float(record.get("inventory")),
            "yoy_change_pct": 0.0,
            "interpretation": f"库存读数：{record.get('inventory')}。",
        },
        "import": {
            "monthly_import_million_tons": _safe_float(record.get("import_volume")),
            "yoy_change_pct": 0.0,
            "interpretation": f"进口读数：{record.get('import_volume')}。",
        },
        "brazil_raw_sugar": {
            "raw_sugar_price_change_pct": 0.0,
            "freight_change_pct": 0.0,
            "interpretation": f"原糖价格：{raw_price}。",
        },
        "fx": {
            "usdcny": _safe_float(record.get("usdcny")),
            "monthly_change_pct": 0.0,
            "interpretation": f"USDCNY：{record.get('usdcny')}。",
        },
        "weather": {
            "main_area_weather_risk": "中等",
            "interpretation": str(record.get("weather_note") or "天气信息缺失。"),
        },
        "policy": {
            "policy_tone": "中性",
            "interpretation": str(record.get("policy_note") or "政策信息缺失。"),
        },
        "sales": _safe_float(record.get("sales")),
    }


def load_sugar_fundamental_snapshot(trade_date: str, fundamental_file: str | None = None) -> tuple[dict, str, str | None]:
    """读取白糖基本面快照。

    返回：(snapshot, source_label, warning)
    """
    if not fundamental_file:
        return get_sugar_fundamental_mock_snapshot(trade_date), "MOCK", None

    path = Path(fundamental_file)
    if not path.exists():
        return (
            get_sugar_fundamental_mock_snapshot(trade_date),
            "MOCK FALLBACK",
            f"警告：基本面本地文件不存在（{path}），已回退到 MOCK 数据。",
        )

    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            if not rows:
                raise ValueError("CSV 内容为空")
            record = rows[-1]
            source = "LOCAL CSV"
        elif suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                if not data:
                    raise ValueError("JSON 列表为空")
                record = data[-1]
            elif isinstance(data, dict):
                record = data
            else:
                raise ValueError("JSON 格式无效")
            source = "LOCAL JSON"
        else:
            raise ValueError("仅支持 CSV/JSON 文件")

        missing = [x for x in _REQUIRED_FIELDS if x not in record]
        if missing:
            return (
                get_sugar_fundamental_mock_snapshot(trade_date),
                "MOCK FALLBACK",
                f"警告：本地基本面字段缺失 {missing}，已回退到 MOCK 数据。",
            )

        return _build_snapshot(record, trade_date), source, None
    except Exception as exc:
        return (
            get_sugar_fundamental_mock_snapshot(trade_date),
            "MOCK FALLBACK",
            f"警告：读取本地基本面文件失败（{exc}），已回退到 MOCK 数据。",
        )

