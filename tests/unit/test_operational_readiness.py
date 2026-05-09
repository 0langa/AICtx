"""Unit tests for readiness helpers and safe workflows."""

from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from aictx.cli import app
from aictx.config import LLMConfig
from aictx.errors import ConfigError, PatchApplyError
from aictx.io.patches import apply_patch, make_unified_diff
from aictx.llm.base import ChatRequest
from aictx.llm.dry_run import DryRunProvider
from aictx.llm.providers import create_model_provider
from aictx.oci.bundle import create_result_bundle, verify_bundle
from aictx.oci.doctor import run_oci_doctor
from aictx.oci.snapshot import create_snapshot, verify_snapshot
from aictx.scan.scanner import scan_repository
from aictx.verify.verifier import verify_detailed
from tests.fixtures.git_repos import (
    create_binary_heavy_fixture,
    create_broken_docs_fixture,
    create_docs_heavy_fixture,
    create_generated_output_heavy_fixture,
    create_git_repo,
    create_large_dependency_fixture,
    create_monorepo_fixture,
    create_secret_heavy_fixture,
)

runner = CliRunner()


def _mock_oci_sdk(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Make importlib.util.find_spec('oci') return a dummy spec, and stub _require_oci_sdk."""
    from unittest.mock import MagicMock

    fake_spec = importlib.util.spec_from_loader("oci", loader=None)
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: fake_spec if name == "oci" else None
    )
    fake_oci = MagicMock()
    fake_oci.config.from_file.return_value = {}
    fake_oci.generative_ai_inference.GenerativeAiInferenceClient.return_value = MagicMock()
    fake_oci.generative_ai_inference.models.GenericChatRequest.return_value = MagicMock()
    fake_oci.generative_ai_inference.models.OnDemandServingMode.return_value = MagicMock()
    fake_oci.generative_ai_inference.models.ChatDetails.return_value = MagicMock()
    fake_oci.generative_ai_inference.models.SystemMessage.return_value = MagicMock()
    fake_oci.generative_ai_inference.models.UserMessage.return_value = MagicMock()
    fake_oci.generative_ai_inference.models.AssistantMessage.return_value = MagicMock()
    fake_oci.exceptions.ServiceError = Exception
    fake_oci.exceptions.ClientError = Exception
    monkeypatch.setattr("aictx.llm.oci_genai._require_oci_sdk", lambda: fake_oci)
    return fake_oci


def test_model_provider_defaults_to_dry_run_and_blocks_oci_without_opt_in() -> None:
    provider = create_model_provider(LLMConfig())
    assert isinstance(provider, DryRunProvider)

    with pytest.raises(ConfigError, match="--allow-ai"):
        create_model_provider(LLMConfig(provider="oci_genai", compartment_id="ocid1.compartment"))


def test_provider_dry_run_behavior_is_deterministic() -> None:
    provider = create_model_provider(LLMConfig())

    first = provider.chat(
        ChatRequest(
            system_prompt="system",
            messages=[{"role": "user", "content": "hello"}],
            run_id="run-1",
            purpose="unit",
        )
    )
    second = provider.chat(
        ChatRequest(
            system_prompt="system",
            messages=[{"role": "user", "content": "hello"}],
            run_id="run-1",
            purpose="unit",
        )
    )

    assert first == second
    assert first.finish_reason == "stop"
    assert first.input_tokens > 0
    assert provider.metadata()["provider"] == "dry_run"


def test_provider_missing_oci_sdk_fails_before_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigError, match="OCI SDK not installed"):
        create_model_provider(LLMConfig(provider="oci_genai", model="test"), allow_ai=True)


def test_provider_creation_validates_model_id_before_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_oci_sdk(monkeypatch)
    with pytest.raises(ConfigError, match="model"):
        create_model_provider(
            LLMConfig(provider="oci_genai", compartment_id="ocid1.comp"), allow_ai=True
        )


def test_provider_creation_validates_compartment_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_oci_sdk(monkeypatch)
    monkeypatch.delenv("OCI_COMPARTMENT_ID", raising=False)
    with pytest.raises(ConfigError, match="compartment_id"):
        create_model_provider(LLMConfig(provider="oci_genai", model="test"), allow_ai=True)


def test_provider_unsupported_name_fails_clearly() -> None:
    with pytest.raises(ConfigError, match="Unsupported provider"):
        create_model_provider(LLMConfig(provider="unknown"), allow_ai=True)


def test_oci_doctor_reports_missing_local_prerequisites(tmp_path: Path) -> None:
    report = run_oci_doctor(config_file=tmp_path / "missing-config")

    assert report.config_file_exists is False
    assert report.ready is False
    assert str(tmp_path / "missing-config") in report.missing


def test_oci_doctor_reports_ready_when_all_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_spec = importlib.util.spec_from_loader("oci", loader=None)
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: fake_spec if name == "oci" else None
    )
    config_path = tmp_path / "oci_config"
    config_path.write_text("[DEFAULT]\ncompartment_id=ocid1.compartment\n", encoding="utf-8")
    report = run_oci_doctor(
        config_file=config_path,
        model_id="cohere.command",
        compartment_id="ocid1.compartment",
    )
    assert report.sdk_available is True
    assert report.config_file_exists is True
    assert report.profile_exists is True
    assert report.compartment_id_present is True
    assert report.model_id_present is True
    assert report.ready is True
    assert not report.missing


def test_oci_doctor_reports_bucket_and_region_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_spec = importlib.util.spec_from_loader("oci", loader=None)
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: fake_spec if name == "oci" else None
    )

    class FakeObjectClient:
        def __init__(self, _config: dict[str, Any]) -> None:
            pass

        def get_namespace(self) -> Any:
            return type("Resp", (), {"data": "ns"})()

        def head_bucket(self, namespace: str, bucket: str) -> None:
            assert namespace == "ns"
            assert bucket == "demo-bucket"

    fake_oci = type(
        "FakeOCI",
        (),
        {
            "config": type(
                "Cfg",
                (),
                {
                    "from_file": staticmethod(
                        lambda file_location, profile_name: {"region": "eu-frankfurt-1"}
                    )
                },
            ),
            "object_storage": type(
                "Obj",
                (),
                {"ObjectStorageClient": FakeObjectClient},
            ),
        },
    )
    monkeypatch.setitem(__import__("sys").modules, "oci", fake_oci)

    config_path = tmp_path / "oci_config"
    config_path.write_text("[DEFAULT]\ncompartment_id=ocid1.compartment\n", encoding="utf-8")
    report = run_oci_doctor(
        config_file=config_path,
        model_id="cohere.command",
        compartment_id="ocid1.compartment",
        region="eu-frankfurt-1",
        bucket="demo-bucket",
    )
    assert report.auth_ok is True
    assert report.region_matches is True
    assert report.bucket_access is True


def test_snapshot_create_is_deterministic(tmp_path: Path) -> None:
    repo = create_git_repo({"README.md": "# Test\n", "src/main.py": "print('ok')\n"})
    inventory = scan_repository(repo)
    out_dir = tmp_path / "snapshots"
    first = create_snapshot(repo, out_dir, inventory=inventory)
    second = create_snapshot(repo, out_dir, inventory=inventory)
    assert first.read_bytes() == second.read_bytes()
    verified = verify_snapshot(first)
    assert verified["valid"] is True


def test_bundle_verification_detects_corruption(tmp_path: Path) -> None:
    patch_path = tmp_path / "aictx.patch"
    patch_path.write_text("diff --git a/x b/x\n", encoding="utf-8")
    bundle = create_result_bundle(
        output_dir=tmp_path,
        patch_path=patch_path,
        validation_report="# ok\n",
        run_report={"status": "success"},
    )
    assert verify_bundle(bundle)["valid"] is True

    corrupt_path = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(bundle, "r") as src, zipfile.ZipFile(corrupt_path, "w") as dst:
        for name in src.namelist():
            data = src.read(name)
            if name == "aictx.patch":
                data = b"bad"
            dst.writestr(name, data)
    checked = verify_bundle(corrupt_path)
    assert checked["valid"] is False


def test_clean_oci_dry_run_requires_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = create_git_repo({"README.md": "# Test\n"})
    config_dir = repo / ".aictx"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.toml").write_text(
        "[oci]\n"
        "enabled = true\n"
        "region = 'eu-frankfurt-1'\n"
        "compartment_id = 'ocid1.compartment'\n"
        "bucket = 'demo-bucket'\n"
        "profile = 'DEFAULT'\n"
        "config_file = 'C:/tmp/oci'\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "aictx.cli._handle_oci_cleanup",
        lambda project, run_id, yes, max_age_days: (
            (_ for _ in ()).throw(SystemExit(0)) if not yes else None
        ),
    )
    result = runner.invoke(app, ["clean", "--project", str(repo), "--oci"])
    assert result.exit_code == 0


def test_oci_doctor_reports_missing_model_id(tmp_path: Path) -> None:
    report = run_oci_doctor(config_file=tmp_path / "missing-config")
    assert report.model_id_present is False
    assert "model_id" in report.missing


def test_apply_patch_validates_then_applies_git_patch() -> None:
    repo = create_git_repo({"README.md": "old\n"})
    patch_text = make_unified_diff("old\n", "new\n", "a/README.md", "b/README.md")

    apply_patch(patch_text, repo)

    assert (repo / "README.md").read_text(encoding="utf-8") == "new\n"


def test_apply_patch_rejects_escaping_paths() -> None:
    repo = create_git_repo({"README.md": "old\n"})
    patch_text = make_unified_diff("", "bad\n", "/dev/null", "b/../bad.md")

    with pytest.raises(PatchApplyError):
        apply_patch(patch_text, repo)


def test_public_docs_update_generates_review_patch_for_changed_sources() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "src/main.py": "print('ok')\n",
        }
    )
    run_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "apply",
            "--allow-dirty",
        ],
    )
    assert run_result.exit_code == 0, run_result.output
    (repo / "src" / "main.py").write_text("print('changed')\n", encoding="utf-8")

    update_result = runner.invoke(
        app,
        [
            "public-docs",
            "update",
            "--project",
            str(repo),
            "--scope",
            "changed",
            "--write",
            "patch",
        ],
    )

    assert update_result.exit_code == 0, update_result.output
    assert "Public docs review generated" in update_result.output
    assert not (repo / "docs" / "AIprojectcontext" / "public-docs-review.md").exists()
    latest = sorted(
        [
            path
            for path in (repo / ".aictx" / "runs").iterdir()
            if path.is_dir() and path.name.endswith("-public-docs")
        ]
    )[-1]
    impact = json.loads((latest / "public-docs-impact.json").read_text(encoding="utf-8"))
    assert impact["impacted_docs"] == {"README.md": ["src/main.py"]}
    assert (latest / "public-docs.patch").exists()


def test_public_docs_update_full_scope_generates_review_for_mapped_docs() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "documentation/README.md": "# Docs\n",
            "src/main.py": "print('ok')\n",
        }
    )
    run_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "apply",
            "--allow-dirty",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    update_result = runner.invoke(
        app,
        [
            "public-docs",
            "update",
            "--project",
            str(repo),
            "--scope",
            "full",
            "--write",
            "patch",
        ],
    )

    assert update_result.exit_code == 0, update_result.output
    latest = sorted(
        [
            path
            for path in (repo / ".aictx" / "runs").iterdir()
            if path.is_dir() and path.name.endswith("-public-docs")
        ]
    )[-1]
    impact = json.loads((latest / "public-docs-impact.json").read_text(encoding="utf-8"))
    assert sorted(impact["impacted_docs"]) == ["README.md", "documentation/README.md"]
    assert (latest / "public-docs.patch").exists()


def test_public_docs_update_apply_writes_only_review_artifact() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "src/main.py": "print('ok')\n",
        }
    )
    original_readme = (repo / "README.md").read_text(encoding="utf-8")
    run_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "apply",
        ],
    )
    assert run_result.exit_code == 0, run_result.output
    (repo / "src" / "main.py").write_text("print('changed')\n", encoding="utf-8")

    update_result = runner.invoke(
        app,
        [
            "public-docs",
            "update",
            "--project",
            str(repo),
            "--scope",
            "changed",
            "--write",
            "apply",
        ],
    )

    assert update_result.exit_code == 0, update_result.output
    assert (repo / "docs" / "AIprojectcontext" / "public-docs-review.md").exists()
    assert (repo / "README.md").read_text(encoding="utf-8") == original_readme


def test_public_docs_map_is_targeted_not_all_source_files() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "documentation/ARCHITECTURE.md": "# Arch\n",
            "src/main.py": "print('ok')\n",
            "src/helper.py": "def helper():\n    return 1\n",
            "tests/test_main.py": "def test_ok():\n    assert True\n",
            "pyproject.toml": "[project]\nname='demo'\nversion='0.1.0'\n",
        }
    )

    run_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "apply",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    report = verify_detailed(repo, strict=True)
    assert report.result == "PASS"

    lock_path = repo / "docs" / "AIprojectcontext" / "context.lock.json"
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    docs_map = {entry["path"]: entry for entry in payload["public_docs_map"]}

    assert docs_map["README.md"]["source_paths"] == ["src/main.py"]
    assert "tests/test_main.py" not in docs_map["documentation/ARCHITECTURE.md"]["source_paths"]


def test_context_regen_refreshes_public_doc_source_hashes() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "src/main.py": "print('ok')\n",
        }
    )
    apply_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "apply",
        ],
    )
    assert apply_result.exit_code == 0, apply_result.output
    (repo / "src" / "main.py").write_text("print('changed')\n", encoding="utf-8")

    regen_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "changed",
            "--write",
            "apply",
            "--allow-dirty",
        ],
    )
    assert regen_result.exit_code == 0, regen_result.output

    report = verify_detailed(repo, strict=True)
    assert report.result == "PASS"
    assert report.public_docs_impacts == {}


def test_clean_keep_runs_is_dry_run_until_confirmed() -> None:
    repo = create_git_repo({"README.md": "# Test repo\n"})
    runs_dir = repo / ".aictx" / "runs"
    (runs_dir / "001").mkdir(parents=True)
    (runs_dir / "002").mkdir(parents=True)

    dry_result = runner.invoke(app, ["clean", "--project", str(repo), "--keep-runs", "1"])
    assert dry_result.exit_code == 0, dry_result.output
    assert (runs_dir / "001").exists()

    apply_result = runner.invoke(
        app, ["clean", "--project", str(repo), "--keep-runs", "1", "--yes"]
    )
    assert apply_result.exit_code == 0, apply_result.output
    assert not (runs_dir / "001").exists()
    assert (runs_dir / "002").exists()


def test_run_with_oci_provider_blocks_without_allow_ai() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "src/main.py": "print('ok')\n",
        }
    )
    config_dir = repo / ".aictx"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.toml").write_text(
        """
[llm]
provider = "oci_genai"
model = "cohere.command"
compartment_id = "ocid1.compartment"
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "patch",
        ],
    )
    assert result.exit_code != 0
    assert "--allow-ai" in result.output


def test_run_dry_run_ignores_oci_config() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "src/main.py": "print('ok')\n",
        }
    )
    result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "patch",
            "--provider",
            "dry_run",
        ],
    )
    assert result.exit_code == 0, result.output


def test_run_report_includes_performance_and_entropy_metrics() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n\nIntro\n\nIntro\n",
            "src/main.py": "print('ok')\n",
        }
    )
    result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "patch",
        ],
    )
    assert result.exit_code == 0, result.output
    latest = sorted((repo / ".aictx" / "runs").iterdir())[-1]
    report = json.loads((latest / "run-report.json").read_text(encoding="utf-8"))
    assert report["patch_size_bytes"] is not None
    assert report["timing"]["scan_duration_ms"] >= 0
    assert report["timing"]["generation_duration_ms"] >= 0
    assert report["entropy"]["total_bytes"] >= 0
    assert "unused_shards" in report["entropy"]


@pytest.mark.parametrize(
    "factory",
    [
        create_monorepo_fixture,
        create_docs_heavy_fixture,
        create_binary_heavy_fixture,
        create_secret_heavy_fixture,
        create_broken_docs_fixture,
        create_generated_output_heavy_fixture,
        create_large_dependency_fixture,
    ],
)
def test_integration_style_fixtures_support_full_run(factory: Any) -> None:
    repo = factory()
    result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "patch",
        ],
    )
    assert result.exit_code == 0, result.output


def test_verify_json_output_schema_is_machine_readable() -> None:
    repo = create_git_repo({"README.md": "# Test\n"})
    result = runner.invoke(app, ["verify", "--project", str(repo), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert set(payload) >= {
        "status",
        "stale_sections",
        "docs_impacts",
        "missing_sources",
        "warnings",
        "errors",
    }


def test_verify_json_reports_pass_status_for_initialized_repo() -> None:
    repo = create_git_repo({"README.md": "# Test\n", "src/main.py": "print('ok')\n"})
    init_result = runner.invoke(app, ["init", "--project", str(repo)])
    assert init_result.exit_code == 0, init_result.output
    verify_result = runner.invoke(app, ["verify", "--project", str(repo), "--strict", "--json"])
    assert verify_result.exit_code == 0, verify_result.output
    payload = json.loads(verify_result.stdout)
    assert payload["status"] == "PASS"
    assert payload["errors"] == []
