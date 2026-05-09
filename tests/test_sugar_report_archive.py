import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from typer.testing import CliRunner

from main import app
from tradingagents.agents.managers.sugar_research_manager import generate_and_archive_sugar_report


runner = CliRunner()


def test_archive_without_previous_report(tmp_path: Path) -> None:
    report, archive_path = generate_and_archive_sugar_report(
        "2026-05-08",
        provider="mock",
        archive_root=str(tmp_path / "reports" / "sugar_sr"),
    )

    assert archive_path.exists()
    assert "15. 较上一期变化" in report
    assert "暂无上一期报告可对比。" in report


def test_archive_with_previous_report(tmp_path: Path) -> None:
    archive_root = tmp_path / "reports" / "sugar_sr"
    prev = archive_root / "2026-05-07.md"
    prev.parent.mkdir(parents=True, exist_ok=True)
    prev.write_text(
        """# 白糖 SR 投研日报

3. 基本面结论
偏空

4. 技术面结论
偏空

5. 风险等级
中

7. 多空倾向
偏空
""",
        encoding="utf-8",
    )

    report, archive_path = generate_and_archive_sugar_report(
        "2026-05-08",
        provider="mock",
        archive_root=str(archive_root),
    )

    assert archive_path.exists()
    assert "较上一期变化" in report
    assert "基本面结论变化" in report
    assert "技术趋势变化" in report
    assert "风险等级变化" in report
    assert "多空倾向变化" in report


def test_cli_archive_and_markdown_export(tmp_path: Path) -> None:
    out = tmp_path / "daily.md"
    result = runner.invoke(
        app,
        [
            "sugar-sr",
            "--date",
            "2026-05-08",
            "--provider",
            "mock",
            "--archive",
            "--output",
            str(out),
        ],
    )

    assert result.exit_code == 0
    assert "已归档日报" in result.stdout
    assert out.exists()
    assert "白糖 SR 投研日报" in out.read_text(encoding="utf-8")