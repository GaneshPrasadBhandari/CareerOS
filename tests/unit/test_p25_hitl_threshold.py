from careeros.phase3.next_steps import _hitl_decision


def test_hitl_requires_approval_below_40_match_even_if_guardrails_pass():
    out = _hitl_decision(match_score=0.32, guardrails_status="pass", parser_skills=12)
    assert out["approval_required"] is True
    assert any("40%" in r for r in out["reasons"])


def test_hitl_can_pass_for_high_match_and_guardrails():
    out = _hitl_decision(match_score=0.86, guardrails_status="pass", parser_skills=12)
    assert out["approval_required"] is False
