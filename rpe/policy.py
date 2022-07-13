from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rpe.engines import Engine
from rpe.resources import Resource


@dataclass
class Policy:
    policy_id: str
    engine: Engine
    applies_to: List[str]
    description: str = ""


@dataclass
class Evaluation:
    resource: Resource
    engine: Engine
    policy_id: str

    compliant: bool
    remediable: bool

    # Static attributes on a given policy
    # Examples: severity, description, owner, etc.
    policy_attributes: Optional[Dict[str, Any]] = field(default_factory=dict)

    # Calculated attributes when evaluating the policy against a resource
    # Examples:
    #   * Why was a resource (non)compliant?
    #   * The prior `excluded` attribute can be implemented here
    evaluation_attributes: Optional[Dict[str, Any]] = field(default_factory=dict)

    def remediate(self):
        return self.engine.remediate(self.resource, self.policy_id)

    # This is to support the same interface as previous versions
    # and may be removed in a future release
    @property
    def excluded(self) -> bool:
        return self.evaluation_attributes.get("excluded", False)
