from dataclasses import dataclass
from typing import Any


@dataclass
class Rule:
    id: str
    name: str
    description: str = ""
    enabled: bool = True
    severity: str = "medium"
    sources: list = None
    patterns: list = None
    pattern_type: str = "substring"

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.patterns is None:
            self.patterns = []


@dataclass
class MatchResult:
    rule_id: str
    rule_name: str
    severity: str
    message: str
    log_raw: str
    log_source: str
    log_entry: Any = None
