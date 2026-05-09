from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pathlib import Path
from typer.testing import CliRunner

from main import app
from tradingagents.agents.managers.sugar_research_manager import generate_and_archive_sugar_report

runner = CliRunner()


def test_cli_smoke_sugar_sr_backtest():
    result = runner.invoke(app, ["sugar-sr-backtest", "--provider", "mock", "--date", "2026-05-08"])
    assert result.exit_code == 0
    text = result.stdout + result.stderr
    assert "白糖 SR" in text
    assert "风险提示" in text


def test_markdown_export_archive(tmp_path: Path):
    report, path = generate_and_archive_sugar_report(
        trade_date="2026-05-08",
        provider="mock",
        archive_root=str(tmp_path / "reports" / "sugar_sr"),
    )
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert report.startswith("# 白糖 SR 投研日报")
    assert "风险提示" in content
