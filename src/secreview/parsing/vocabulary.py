"""Fixed vocabularies shared by the policy analysis and the design review."""

from typing import Literal
from typing import get_args as list_literal_values

Topic = Literal[
    "authentication",
    "authorization",
    "cryptography",
    "secrets",
    "network",
    "logging",
    "data-protection",
    "input-validation",
    "database-access",
    "operations",
    "resilience",
    "governance",
]
Wording = Literal["clear", "vague_or_advisory", "contradictory"]
TOPICS: tuple[str, ...] = list_literal_values(Topic)
WORDINGS: tuple[str, ...] = list_literal_values(Wording)
