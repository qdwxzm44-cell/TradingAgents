from __future__ import annotations

from pathlib import Path

from tradingagents.agents.analysts.sugar_fundamental_analyst import generate_sugar_fundamental_report


def test_mock_mode_contains_source() -> None:
    report = generate_sugar_fundamental_report("2026-05-08")
    assert "基本面数据源：MOCK" in report


def test_csv_mode_contains_source(tmp_path: Path) -> None:
    fp = tmp_path / "fund.csv"
    fp.write_text(
        "date,production,sales,inventory,import_volume,raw_sugar_price,usdcny,weather_note,policy_note\n"
        "2026-05-08,10,9,5,0.4,19.5,7.2,天气平稳,政策中性\n",
        encoding="utf-8",
    )
    report = generate_sugar_fundamental_report("2026-05-08", fundamental_file=str(fp))
    assert "基本面数据源：LOCAL CSV" in report


def test_json_mode_contains_source(tmp_path: Path) -> None:
    fp = tmp_path / "fund.json"
    fp.write_text(
        '[{"date":"2026-05-08","production":10,"sales":9,"inventory":5,"import_volume":0.4,'
        '"raw_sugar_price":19.5,"usdcny":7.2,"weather_note":"天气平稳","policy_note":"政策中性"}]',
        encoding="utf-8",
    )
    report = generate_sugar_fundamental_report("2026-05-08", fundamental_file=str(fp))
    assert "基本面数据源：LOCAL JSON" in report


def test_missing_file_fallback() -> None:
    report = generate_sugar_fundamental_report("2026-05-08", fundamental_file="/tmp/not-exist.csv")
    assert "基本面数据源：MOCK FALLBACK" in report
    assert "警告：基本面本地文件不存在" in report
