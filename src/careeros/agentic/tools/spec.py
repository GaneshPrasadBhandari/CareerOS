from __future__ import annotations

from typing import Callable, Generic, Optional, Type, TypeVar
from pydantic import BaseModel

InT = TypeVar("InT", bound=BaseModel)
OutT = TypeVar("OutT", bound=BaseModel)


class ToolSpec(Generic[InT, OutT]):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        input_model: Type[InT],
        output_model: Type[OutT],
        handler: Callable[[InT], OutT],
        requires_approval: bool = False,
        side_effects: bool = True,
        owner: str = "core",
        version: str = "v1",
    ):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model
        self.handler = handler
        self.requires_approval = requires_approval
        self.side_effects = side_effects
        self.owner = owner
        self.version = version
