from yadocinfo.services.scanner import Scanner


def test_scanner_does_not_recurse(tmp_path):
    root = tmp_path / "base"
    root.mkdir()
    (root / "a.txt").write_text("a")
    child = root / "child"
    child.mkdir()
    (child / "b.txt").write_text("b")
    scanner = Scanner({"directories": [{"name": "docs", "path": str(root)}], "processing": {}})
    assert [p.name for p in scanner.files(root)] == ["a.txt"]
