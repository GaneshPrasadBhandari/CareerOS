from __future__ import annotations

from careeros.guardrails.service import validate_package_against_evidence


def run(**kwargs):
    return validate_package_against_evidence(**kwargs)
