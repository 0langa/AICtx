"""Local Phase 1 context generation pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from aictx.config import AictxConfig
from aictx.context.fact_extractor import extract_facts
from aictx.context.lockfile import load_lockfile, write_lockfile
from aictx.context.planner import plan_context
from aictx.context.writer import build_context_lock, write_context_scaffold
from aictx.errors import SafetyError, SecretScanError, TokenBudgetExceededError
from aictx.io.files import safe_write
from aictx.io.patches import make_unified_diff
from aictx.llm.providers import create_model_provider
from aictx.models.run_report import RunReport
from aictx.scan.scanner import scan_repository
from aictx.verify.verifier import determine_changed_source_paths


def run_local_context_pipeline(
    repo_root: Path,
    run_id: str,
    config: AictxConfig,
    scope: Literal["full", "changed"],
    write_mode: Literal["patch", "apply"],
    allow_ai: bool = False,
    allow_dirty: bool = False,
) -> RunReport:
    """Run the local Phase 1 context generation pipeline."""
    inventory = scan_repository(repo_root)
    if inventory.secrets:
        raise SecretScanError("High-confidence secrets detected; refusing context generation.")
    if (
        write_mode == "apply"
        and inventory.dirty_state
        and not (config.execution.allow_dirty or allow_dirty)
    ):
        raise SafetyError("Refusing --write apply on dirty worktree without --allow-dirty.")

    existing_context_dir = repo_root / config.project.context_dir
    existing_agents_md = repo_root / config.project.agents_file
    existing_lock = load_lockfile(existing_context_dir)
    changed_files = determine_changed_source_paths(inventory, existing_lock)

    plan = plan_context(
        inventory=inventory,
        existing_context_dir=existing_context_dir if existing_context_dir.exists() else None,
        existing_agents_md=existing_agents_md if existing_agents_md.exists() else None,
        scope=scope,
        config=config,
        existing_lock=existing_lock,
        changed_files=changed_files,
    )
    typed_plan = cast(dict[str, Any], plan)
    typed_plan["changed_files"] = changed_files if scope == "changed" else []
    estimated_token_cost = cast(int, plan["estimated_token_cost"])
    if estimated_token_cost > config.limits.max_input_tokens_per_run:
        raise TokenBudgetExceededError(
            "Planned context exceeds configured max_input_tokens_per_run."
        )

    provider = create_model_provider(config.llm, allow_ai=allow_ai)
    fact_packs = extract_facts(
        repo_root=repo_root, plan=typed_plan, provider=provider, run_id=run_id
    )

    runs_dir = repo_root / ".aictx" / "runs" / run_id
    out_dir = runs_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_run_artifacts(
        runs_dir=runs_dir,
        inventory=inventory.model_dump(mode="json"),
        plan=typed_plan,
        fact_packs=fact_packs,
    )

    staged_context_dir = out_dir / config.project.context_dir
    generated_paths = write_context_scaffold(
        repo_root=repo_root,
        out_dir=out_dir,
        inventory=inventory,
        plan=typed_plan,
        fact_packs=fact_packs,
    )
    lock = build_context_lock(
        repo_root=repo_root,
        out_dir=out_dir,
        inventory=inventory,
        plan=typed_plan,
        fact_packs=fact_packs,
        generated_paths=generated_paths,
        model_provider=config.llm.provider,
        model_name=config.llm.model,
        existing_lock=existing_lock,
        changed_files=changed_files,
    )
    write_lockfile(staged_context_dir, lock)
    generated_paths = [*generated_paths, staged_context_dir / "context.lock.json"]

    patch_text = _build_patch(repo_root=repo_root, out_dir=out_dir)
    patch_path = runs_dir / "aictx.patch"
    safe_write(patch_path, patch_text)

    if write_mode == "apply":
        _apply_out_dir(repo_root=repo_root, out_dir=out_dir)

    return RunReport(
        run_id=run_id,
        project_path=str(repo_root),
        mode="setup-context",
        scope=scope,
        execution="local",
        write_mode=write_mode,
        completed_at=datetime.now(UTC),
        status="success",
        files_scanned=len([f for f in inventory.files if not f.is_ignored]),
        files_selected=len(cast(list[str], typed_plan["selected_files"])),
        tokens_estimated_input=estimated_token_cost,
        tokens_estimated_output=sum(
            cast(int, pack.get("estimated_output_tokens", 0)) for pack in fact_packs
        ),
        model_calls=len(fact_packs),
        generated_files=[path.relative_to(out_dir).as_posix() for path in generated_paths],
        selected_files=cast(list[str], typed_plan["selected_files"]),
        warnings=[
            *cast(list[str], typed_plan.get("warnings", [])),
            *(
                [f"changed scope detected {len(changed_files)} changed source files"]
                if scope == "changed"
                else []
            ),
        ],
        output_dir=str(out_dir),
        patch_path=str(patch_path),
    )


def _build_patch(repo_root: Path, out_dir: Path) -> str:
    patches: list[str] = []
    for generated_file in sorted(out_dir.rglob("*")):
        if not generated_file.is_file():
            continue
        relative = generated_file.relative_to(out_dir)
        repo_target = repo_root / relative
        original = repo_target.read_text(encoding="utf-8") if repo_target.exists() else ""
        updated = generated_file.read_text(encoding="utf-8")
        if original == updated:
            continue
        from_name = f"a/{relative.as_posix()}" if repo_target.exists() else "/dev/null"
        to_name = f"b/{relative.as_posix()}"
        patches.append(make_unified_diff(original, updated, from_name, to_name))
    return "".join(patches)


def _apply_out_dir(repo_root: Path, out_dir: Path) -> None:
    for generated_file in out_dir.rglob("*"):
        if not generated_file.is_file():
            continue
        relative = generated_file.relative_to(out_dir)
        target = repo_root / relative
        safe_write(target, generated_file.read_text(encoding="utf-8"))


def _write_run_artifacts(
    runs_dir: Path,
    inventory: dict[str, Any],
    plan: dict[str, Any],
    fact_packs: list[dict[str, Any]],
) -> None:
    safe_write(runs_dir / "inventory.json", _json_dump(inventory))
    safe_write(runs_dir / "context-plan.json", _json_dump(plan))
    facts_dir = runs_dir / "facts"
    pack_name_map = {
        "project_identity": "project_identity",
        "architecture": "architecture",
        "feature": "feature",
        "workflow": "workflow",
        "docs": "docs",
        "risk": "risk",
    }
    seen_pack_names: set[str] = set()
    for pack in fact_packs:
        pack_name = pack_name_map.get(str(pack["name"]), str(pack["name"]))
        seen_pack_names.add(pack_name)
        safe_write(facts_dir / f"{pack_name}_facts.json", _json_dump(pack))
    for expected_pack_name in pack_name_map.values():
        if expected_pack_name in seen_pack_names:
            continue
        safe_write(
            facts_dir / f"{expected_pack_name}_facts.json",
            _json_dump(
                {
                    "name": expected_pack_name,
                    "facts": [],
                    "summary": "No deterministic facts extracted.",
                    "estimated_output_tokens": 0,
                }
            ),
        )
    safe_write(
        runs_dir / "coverage-report.json", _json_dump({"status": "deterministic", "missing": []})
    )
    safe_write(
        runs_dir / "contradictions.json", _json_dump({"status": "none", "contradictions": []})
    )


def _json_dump(payload: Any) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
