from pathlib import Path

from bncbot.config import BNCData


def test_load_empty_data(tmp_path: Path) -> None:
    data_file = tmp_path / "data.json"
    data_file.write_text("{}", encoding="utf-8")
    data = BNCData.load_config(data_file)
    assert not data.users


def test_load_missing_data(tmp_path: Path) -> None:
    data_file = tmp_path / "data.json"
    data = BNCData.load_config(data_file)
    assert not data.users


def test_save_data(tmp_path: Path) -> None:
    data_file = tmp_path / "data.json"
    data_file.write_text("{}", encoding="utf-8")
    data = BNCData.load_config(data_file)
    assert not data.users

    data.users["foo"] = "bar"
    data.save_config(data_file)

    assert (
        data_file.read_text(encoding="utf-8")
        == """\
{
    \"queue\": {},
    \"users\": {
        \"foo\": \"bar\"
    }
}"""
    )

    data1 = BNCData.load_config(data_file)
    assert data == data1
