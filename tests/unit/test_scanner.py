"""Unit tests for scanner utility functions."""

from __future__ import annotations

import hashlib
import random
import string
from pathlib import Path

from aictx.scan.scanner import (
    _detect_language,
    _is_binary,
    _is_doc,
    _is_manifest,
    _is_test,
    _sha256_file,
)
from aictx.scan.secrets import scan_for_secrets


def test_is_binary_text_file(tmp_path: Path) -> None:
    text_file = tmp_path / "hello.txt"
    text_file.write_text("hello world", encoding="utf-8")
    assert _is_binary(text_file) is False


def test_is_binary_empty_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.write_bytes(b"")
    assert _is_binary(empty) is False


def test_is_binary_null_bytes(tmp_path: Path) -> None:
    bin_file = tmp_path / "binary.dat"
    bin_file.write_bytes(b"\x00\x00\x00")
    assert _is_binary(bin_file) is True


def test_is_binary_high_nonprintable(tmp_path: Path) -> None:
    bin_file = tmp_path / "binary.bin"
    data = bytes(random.randint(0x10, 0x1F) for _ in range(1000))
    bin_file.write_bytes(data)
    assert _is_binary(bin_file) is True


def test_sha256_file_consistency(tmp_path: Path) -> None:
    data = "".join(random.choices(string.ascii_letters, k=10_000))
    f = tmp_path / "data.txt"
    f.write_text(data, encoding="utf-8")
    expected = hashlib.sha256(data.encode("utf-8")).hexdigest()
    assert _sha256_file(f) == expected


def test_sha256_file_empty(tmp_path: Path) -> None:
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    assert _sha256_file(f) == hashlib.sha256(b"").hexdigest()


def test_detect_language_python() -> None:
    assert _detect_language(Path("main.py")) == "python"


def test_detect_language_csharp() -> None:
    assert _detect_language(Path("App.cs")) == "csharp"


def test_detect_language_rust() -> None:
    assert _detect_language(Path("lib.rs")) == "rust"


def test_detect_language_unknown() -> None:
    assert _detect_language(Path("Makefile")) is None


def test_is_manifest_pyproject() -> None:
    assert _is_manifest(Path("pyproject.toml")) is True


def test_is_manifest_workflow() -> None:
    assert _is_manifest(Path(".github/workflows/ci.yml")) is True


def test_is_manifest_not(tmp_path: Path) -> None:
    assert _is_manifest(Path("readme.md")) is False


def test_is_test_python() -> None:
    assert _is_test(Path("tests/unit/test_scanner.py")) is True


def test_is_test_suffix() -> None:
    assert _is_test(Path("lib.Tests.cs")) is True


def test_is_doc_readme() -> None:
    assert _is_doc(Path("README.md")) is True


def test_is_doc_markdown() -> None:
    assert _is_doc(Path("docs/guide.md")) is True


def test_is_doc_not() -> None:
    assert _is_doc(Path("src/main.py")) is False


def test_scan_for_secrets_private_key(tmp_path: Path) -> None:
    f = tmp_path / "key.pem"
    f.write_text("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----")
    findings = scan_for_secrets(f.read_text(), f)
    assert any(f["detector_name"] == "private_key_header" for f in findings)


def test_scan_for_secrets_oci_api_key(tmp_path: Path) -> None:
    f = tmp_path / "config"
    f.write_text("OCI_API_KEY=abc123")
    findings = scan_for_secrets(f.read_text(), f)
    assert any(f["detector_name"] == "oci_api_key" for f in findings)


def test_scan_for_secrets_ignores_env_in_non_env(tmp_path: Path) -> None:
    f = tmp_path / "settings.py"
    f.write_text("AWS_SECRET_ACCESS_KEY=dont_find_me")
    findings = scan_for_secrets(f.read_text(), f)
    assert not any(f["detector_name"] == "env_file_secret" for f in findings)


def test_scan_for_secrets_finds_env_in_dotenv(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("AWS_SECRET_ACCESS_KEY=found_me")
    findings = scan_for_secrets(f.read_text(), f)
    assert any(f["detector_name"] == "env_file_secret" for f in findings)


def test_scan_for_secrets_connection_string(tmp_path: Path) -> None:
    f = tmp_path / "db.py"
    f.write_text("uri = 'postgresql://user:pass@host/db'")
    findings = scan_for_secrets(f.read_text(), f)
    assert any(f["detector_name"] == "connection_string" for f in findings)


def test_scan_for_secrets_skips_detector_source_file(tmp_path: Path) -> None:
    f = tmp_path / "src" / "aictx" / "scan" / "secrets.py"
    f.parent.mkdir(parents=True)
    f.write_text('pattern = "OCI_API_KEY"\nuri = "postgresql://user:pass@host/db"')

    findings = scan_for_secrets(f.read_text(), f)

    assert findings == []


def test_scan_for_secrets_skips_test_fixture_examples(tmp_path: Path) -> None:
    f = tmp_path / "tests" / "unit" / "sample.py"
    f.parent.mkdir(parents=True)
    f.write_text("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----")

    findings = scan_for_secrets(f.read_text(), f)

    assert findings == []


def test_secret_scan_supports_inline_suppression(tmp_path: Path) -> None:
    f = tmp_path / "settings.py"
    f.write_text("# aictx-secret-ignore\nOCI_API_KEY=abc123", encoding="utf-8")

    findings = scan_for_secrets(f.read_text(), f)

    assert findings == []


def test_unsuppressed_secret_is_still_reported(tmp_path: Path) -> None:
    f = tmp_path / "settings.py"
    f.write_text("OCI_API_KEY=abc123", encoding="utf-8")

    findings = scan_for_secrets(f.read_text(), f)

    assert any(item["detector_name"] == "oci_api_key" for item in findings)
