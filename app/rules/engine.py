import json
import re
from pathlib import Path

import yaml

from app.parsers.base import LogEntry
from .models import Rule, MatchResult


def load_rules(path_yaml=None, path_json=None):
    seen_ids = set()
    rules = []
    for path in (path_yaml, path_json):
        if not path:
            continue
        p = Path(path)
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8") as f:
            if p.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        if isinstance(data, dict) and "rules" in data:
            data = data["rules"]
        if not isinstance(data, list):
            continue
        for r in data:
            if isinstance(r, dict):
                rid = r.get("id", "")
                if rid in seen_ids:
                    continue
                rule = Rule(
                    id=rid,
                    name=r.get("name", ""),
                    description=r.get("description", ""),
                    enabled=r.get("enabled", True),
                    severity=r.get("severity", "medium"),
                    sources=r.get("sources", []),
                    patterns=r.get("patterns", []),
                    pattern_type=r.get("pattern_type", "substring"),
                )
                if rule.id and rule.patterns:
                    seen_ids.add(rule.id)
                    rules.append(rule)
    return rules


class RuleEngine:
    def __init__(self, rules=None):
        self.rules = rules or []

    def match_entry(self, entry, source_key):
        results = []
        text = entry.raw
        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.sources and source_key not in rule.sources:
                continue
            for pat in rule.patterns:
                if rule.pattern_type == "regex":
                    try:
                        if re.search(pat, text, re.IGNORECASE):
                            results.append(
                                MatchResult(
                                    rule_id=rule.id,
                                    rule_name=rule.name,
                                    severity=rule.severity,
                                    message=rule.description or rule.name,
                                    log_raw=entry.raw,
                                    log_source=source_key,
                                    log_entry=entry,
                                )
                            )
                            break
                    except re.error:
                        continue
                else:
                    if pat.lower() in text.lower():
                        results.append(
                            MatchResult(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                severity=rule.severity,
                                message=rule.description or rule.name,
                                log_raw=entry.raw,
                                log_source=source_key,
                                log_entry=entry,
                            )
                        )
                        break
        return results

    def match_line(self, raw_line, source_key):
        entry = LogEntry(raw=raw_line, message=raw_line, source=source_key)
        return self.match_entry(entry, source_key)
