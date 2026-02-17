import pytest
from pydantic import BaseModel

from careeros.agentic.state import OrchestratorState
from careeros.agentic.tools.registry import ToolRegistry
from careeros.agentic.tools.spec import ToolSpec


class InModel(BaseModel):
    x: int


class OutModel(BaseModel):
    y: int


def test_state_step_trace():
    st = OrchestratorState(run_id="run_test")
    st.start_step("s1", "tool.a", {"input_path": "a.json"})
    st.end_step("s1", "ok", {"output_path": "b.json"}, "done")

    assert len(st.steps) == 1
    assert st.steps[0].status == "ok"
    assert st.steps[0].input_ref["input_path"] == "a.json"
    assert st.steps[0].output_ref["output_path"] == "b.json"


def test_state_approval_decisions():
    st = OrchestratorState(run_id="run_test")
    assert st.is_approved("tool.sensitive") is False
    st.record_approval("tool.sensitive", True, "approved for demo")
    assert st.is_approved("tool.sensitive") is True


def test_registry_register_and_describe():
    reg = ToolRegistry()

    def handler(inp: InModel) -> OutModel:
        return OutModel(y=inp.x + 1)

    reg.register(
        ToolSpec(
            name="tool.inc",
            description="increment",
            input_model=InModel,
            output_model=OutModel,
            handler=handler,
            requires_approval=False,
            side_effects=False,
        )
    )

    assert reg.list() == ["tool.inc"]
    desc = reg.describe()[0]
    assert desc["name"] == "tool.inc"
    assert desc["input_model"] == "InModel"
    assert desc["output_model"] == "OutModel"


def test_registry_duplicate_rejected():
    reg = ToolRegistry()

    def handler(inp: InModel) -> OutModel:
        return OutModel(y=inp.x)

    spec = ToolSpec(
        name="tool.same",
        description="a",
        input_model=InModel,
        output_model=OutModel,
        handler=handler,
    )
    reg.register(spec)
    with pytest.raises(ValueError):
        reg.register(spec)
