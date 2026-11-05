from yadocinfo.services.checksum import calculate_checksum


def test_sha256(tmp_path):
    file = tmp_path / "sample.txt"
    file.write_text("yadocinfo", encoding="utf-8")
    assert len(calculate_checksum(file)) == 64
    assert len(calculate_checksum(file, "md5")) == 32
