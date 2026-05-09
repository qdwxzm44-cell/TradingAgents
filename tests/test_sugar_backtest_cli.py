import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from typer.testing import CliRunner

from main import app


runner = CliRunner()


def test_backtest_default_params() -> None:
    result = runner.invoke(app, ["sugar-sr-backtest", "--provider", "mock", "--date", "2026-05-08"])

    assert result.exit_code == 0
    assert "参数摘要：" in (result.stdout + result.stderr)
    assert "breakout_window=20" in (result.stdout + result.stderr)
    assert "ATR周期：14" in (result.stdout + result.stderr)


def test_backtest_custom_params_and_markdown(tmp_path: Path) -> None:
    out = tmp_path / "bt.md"
    result = runner.invoke(
        app,
        [
            "sugar-sr-backtest",
            "--provider",
            "mock",
            "--date",
            "2026-05-08",
            "--breakout-window",
            "25",
            "--atr-period",
            "16",
            "--stop-loss",
            "0.12",
            "--take-profit",
            "0.3",
            "--initial-cash",
            "1500000",
            "--output",
            str(out),
        ],
    )

    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "突破周期：25" in content
    assert "ATR周期：16" in content
    assert "止损比例：12%" in content
    assert "止盈比例：30%" in content
    assert "初始资金：1,500,000.00" in content


def test_backtest_invalid_params_error() -> None:
    result = runner.invoke(app, ["sugar-sr-backtest", "--provider", "mock", "--stop-loss", "1.2"])

    assert result.exit_code != 0
    assert "参数异常：--stop-loss 必须在 (0, 1) 区间" in (result.stdout + result.stderr)
