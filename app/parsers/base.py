from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class LogEntry:
    raw: str
    timestamp: Optional[str] = None
    source: str = ""
    level: str = ""
    message: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "raw": self.raw,
            "timestamp": self.timestamp,
            "source": self.source,
            "level": self.level,
            "message": self.message,
        }
        d.update(self.extra)
        return d

    def to_csv_row(self):
        return self.to_dict()


class BaseParser(ABC):
    name: str = "base"
    encoding: str = "utf-8"
    errors: str = "replace"

    @abstractmethod
    def parse_line(self, line: str) -> Optional[LogEntry]:
        pass

    def parse_file(self, path: str, max_lines: Optional[int] = None) -> Iterator[LogEntry]:
        try:
            with open(path, "r", encoding=self.encoding, errors=self.errors) as f:
                count = 0
                for line in f:
                    line = line.rstrip("\n")
                    if not line.strip():
                        continue
                    entry = self.parse_line(line)
                    if entry:
                        yield entry
                        count += 1
                        if max_lines and count >= max_lines:
                            break
        except FileNotFoundError:
            return
        except PermissionError:
            return
