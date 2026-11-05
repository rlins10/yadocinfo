import yaml

from yadocinfo.config import DEFAULT_CONFIG, load_config


def test_config_defaults(tmp_path):
    path = tmp_path / "config.yaml"
    data = {
        "database": {"driver": "sqlite"},
        "directories": [{"name": "docs", "path": str(tmp_path)}],
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    loaded = load_config(path)
    assert loaded["ai"]["model"] == "gemma4:12b"
    assert loaded["integrity"]["algorithm"] == "sha256"
