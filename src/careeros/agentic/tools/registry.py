from __future__ import annotations

from typing import Any
from .spec import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Duplicate tool name: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def list(self) -> list[str]:
        return sorted(self._tools.keys())

    def describe(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for name in self.list():
            t = self._tools[name]
            out.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "requires_approval": t.requires_approval,
                    "side_effects": t.side_effects,
                    "owner": t.owner,
                    "version": t.version,
                    "input_model": t.input_model.__name__,
                    "output_model": t.output_model.__name__,
                }
            )
        return out
