from pathlib import Path

from orbitops.cli import build_parser, main


def test_generate_command_writes_requested_records(tmp_path: Path) -> None:
    exit_code = main(["--data-dir", str(tmp_path), "generate", "--records", "3", "--seed", "9"])

    assert exit_code == 0
    assert len((tmp_path / "raw" / "telemetry.jsonl").read_text().splitlines()) == 3


def test_status_requires_ingestion(tmp_path: Path) -> None:
    assert main(["--data-dir", str(tmp_path), "status"]) == 2


def test_parser_requires_a_command() -> None:
    parser = build_parser()
    assert parser.prog == "orbitops"


def test_ingest_empty_file_returns_quality_error(tmp_path: Path) -> None:
    raw = tmp_path / "empty.jsonl"
    raw.write_text("", encoding="utf-8")

    assert main(["--data-dir", str(tmp_path), "ingest", str(raw)]) == 3
