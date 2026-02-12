"""Phase 3 bootstrap services.

This module intentionally runs in "dry-run" mode:
- validates typed contracts (P20)
- simulates an agent step and writes artifacts (P21 bootstrap)

No external LLM/API calls are performed here yet.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from careeros.phase3.contracts import AgentTaskInput, AgentTaskOutput, ContractValidationResult


PHASE3_STEPS = [
    "P20: Agent contracts",
    "P21: LangGraph workflow",
    "P22: Human approval nodes",
    "P23: Memory and persistence upgrades",
    "P24: Evaluation harness",
]


def validate_contract(payload: dict) -> ContractValidationResult:
    """Validate incoming payload against `AgentTaskInput` schema."""
    try:
        model = AgentTaskInput.model_validate(payload)
        return ContractValidationResult(status="ok", normalized=model.model_dump())
    except Exception as exc:
        return ContractValidationResult(status="error", errors=[str(exc)])


def dry_run_agent_step(inp: AgentTaskInput) -> AgentTaskOutput:
    """Execute a non-LLM dry run and persist request artifact.

    Writes one JSON file to `outputs/phase3/` so users can inspect
    contract payloads and resulting metadata before enabling live tools.
    """

    notes = [
        f"Dry run for agent={inp.agent}",
        "No external API call executed",
        "Use this to validate payload contracts before Phase 3 live integrations",
    ]
    artifacts: list[str] = []

    out_dir = Path("outputs/phase3")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    fp = out_dir / f"dry_run_{inp.agent}_{stamp}.json"
    fp.write_text(inp.model_dump_json(indent=2), encoding="utf-8")
    artifacts.append(str(fp))

    return AgentTaskOutput(
        run_id=inp.run_id,
        agent=inp.agent,
        status="ok",
        artifact_paths=artifacts,
        notes=notes,
    )
