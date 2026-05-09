import sys
from pathlib import Path

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


runner = CliRunner()


def test_default_mode_is_concise() -> None:
    result = runner.invoke(app, ["sugar-sr-backtest", "--provider", "mock", "--date", "2026-05-08"])
    assert result.exit_code == 0
    text = result.stdout + result.stderr
    assert "[INFO]" in text


def test_verbose_mode_outputs_info() -> None:
    result = runner.invoke(app, ["--verbose", "sugar-sr-backtest", "--provider", "mock", "--date", "2026-05-08"])
    assert result.exit_code == 0
    text = result.stdout + result.stderr
    assert "[INFO]" in text


def test_quiet_mode_suppresses_info() -> None:
    result = runner.invoke(app, ["--quiet", "sugar-sr-backtest", "--provider", "mock", "--date", "2026-05-08"])
    assert result.exit_code == 0
    text = result.stdout + result.stderr
    assert "[INFO]" not in text


def test_provider_fallback_warning() -> None:
    result = runner.invoke(app, ["sugar-sr-backtest", "--provider", "real", "--date", "2026-05-08"])
    assert result.exit_code == 0
    text = result.stdout + result.stderr
    assert "回退 mock 数据" in text or "MOCK FALLBACK" in text


def test_config_missing_warning(tmp_path: Path) -> None:
    from tradingagents.config.sugar_sr_config import load_sugar_sr_config

    _, warnings = load_sugar_sr_config(str(tmp_path / "none.yaml"))
    assert any("未找到配置文件" in w for w in warnings)
