from pathlib import Path

from tradingagents.config.sugar_sr_config import load_sugar_sr_config


def test_load_normal_config(tmp_path: Path):
    p = tmp_path / "sugar.yaml"
    p.write_text("provider: mock\nbreakout_window: 30\nmarkdown_export_enabled: false\n", encoding="utf-8")
    conf, warnings = load_sugar_sr_config(str(p))
    assert conf.provider == "mock"
    assert conf.breakout_window == 30
    assert conf.markdown_export_enabled is False
    assert warnings == []


def test_missing_and_invalid_fields(tmp_path: Path):
    p = tmp_path / "sugar.yaml"
    p.write_text("breakout_window: abc\nunknown_x: 1\n", encoding="utf-8")
    conf, warnings = load_sugar_sr_config(str(p))
    assert conf.breakout_window == 20
    assert any("未知字段" in w for w in warnings)
    assert any("breakout_window 无效" in w for w in warnings)


def test_missing_file_uses_defaults(tmp_path: Path):
    conf, warnings = load_sugar_sr_config(str(tmp_path / "none.yaml"))
    assert conf.provider == "real"
    assert any("未找到配置文件" in w for w in warnings)
