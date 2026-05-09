"""白糖 SR 统一配置加载（Phase 18）。

仅用于研究辅助与风险分析；禁止自动下单。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tradingagents.utils.sugar_logger import get_sugar_logger


@dataclass(frozen=True)
class SugarSRConfig:
    provider: str = "real"
    breakout_window: int = 20
    atr_period: int = 14
    stop_loss: float = 0.15
    take_profit: float = 0.35
    initial_cash: float = 1_000_000
    report_output_dir: str = "reports/sugar_sr"
    archive_dir: str = "reports/sugar_sr"
    fallback_enabled: bool = True
    markdown_export_enabled: bool = True


DEFAULT_CONFIG = SugarSRConfig()


def _parse_scalar(raw: str):
    s = raw.strip()
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _read_simple_yaml(path: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        striped = line.strip()
        if not striped or striped.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = _parse_scalar(value)
    return result


def _validate_and_merge(raw: dict[str, object]) -> tuple[SugarSRConfig, list[str]]:
    warnings: list[str] = []
    defaults = DEFAULT_CONFIG
    allowed = set(defaults.__dataclass_fields__.keys())

    for key in raw.keys():
        if key not in allowed:
            warnings.append(f"[配置警告] 忽略未知字段: {key}")

    def as_int(name: str, default: int, minimum: int = 1) -> int:
        val = raw.get(name, default)
        if not isinstance(val, int) or val < minimum:
            warnings.append(f"[配置警告] {name} 无效，已回退默认值 {default}")
            return default
        return val

    def as_float(name: str, default: float, low: float, high: float) -> float:
        val = raw.get(name, default)
        if not isinstance(val, (int, float)) or not (low < float(val) < high):
            warnings.append(f"[配置警告] {name} 无效，已回退默认值 {default}")
            return default
        return float(val)

    def as_bool(name: str, default: bool) -> bool:
        val = raw.get(name, default)
        if not isinstance(val, bool):
            warnings.append(f"[配置警告] {name} 无效，已回退默认值 {default}")
            return default
        return val

    def as_str(name: str, default: str) -> str:
        val = raw.get(name, default)
        if not isinstance(val, str) or not val.strip():
            warnings.append(f"[配置警告] {name} 无效，已回退默认值 {default}")
            return default
        return val.strip()

    return SugarSRConfig(
        provider=as_str("provider", defaults.provider).lower(),
        breakout_window=as_int("breakout_window", defaults.breakout_window, minimum=2),
        atr_period=as_int("atr_period", defaults.atr_period, minimum=2),
        stop_loss=as_float("stop_loss", defaults.stop_loss, 0, 1),
        take_profit=as_float("take_profit", defaults.take_profit, 0, 2),
        initial_cash=as_float("initial_cash", float(defaults.initial_cash), 0, 1e16),
        report_output_dir=as_str("report_output_dir", defaults.report_output_dir),
        archive_dir=as_str("archive_dir", defaults.archive_dir),
        fallback_enabled=as_bool("fallback_enabled", defaults.fallback_enabled),
        markdown_export_enabled=as_bool("markdown_export_enabled", defaults.markdown_export_enabled),
    ), warnings


def load_sugar_sr_config(path: str = "config/sugar_sr.yaml") -> tuple[SugarSRConfig, list[str]]:
    logger = get_sugar_logger()
    p = Path(path)
    if not p.exists():
        msg = f"[配置警告] 未找到配置文件 {path}，已使用默认配置"
        logger.warning(msg)
        return DEFAULT_CONFIG, [msg]
    try:
        raw = _read_simple_yaml(p)
    except Exception as exc:
        msg = f"[配置警告] 读取配置失败: {exc}，已使用默认配置"
        logger.error(msg)
        return DEFAULT_CONFIG, [msg]
    return _validate_and_merge(raw)


def summarize_config(conf: SugarSRConfig) -> str:
    return (
        "当前生效配置："
        f"provider={conf.provider}, breakout_window={conf.breakout_window}, atr_period={conf.atr_period}, "
        f"stop_loss={conf.stop_loss}, take_profit={conf.take_profit}, initial_cash={conf.initial_cash}, "
        f"report_output_dir={conf.report_output_dir}, archive_dir={conf.archive_dir}, "
        f"fallback_enabled={conf.fallback_enabled}, markdown_export_enabled={conf.markdown_export_enabled}"
    )
