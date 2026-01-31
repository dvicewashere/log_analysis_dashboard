import re
from .base import BaseParser, LogEntry


class SyslogParser(BaseParser):
    name = "syslog"

    _RE = re.compile(
        r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\S+)\s+"
        r"(?P<host>\S+)\s+(?P<tag>\S+?):\s*(?P<message>.*)$"
    )

    def parse_line(self, line: str) -> LogEntry | None:
        m = self._RE.match(line.strip())
        if not m:
            return LogEntry(raw=line, message=line, source=self.name)
        g = m.groupdict()
        ts = f"{g['month']} {g['day']} {g['time']}"
        return LogEntry(
            raw=line,
            timestamp=ts,
            source=self.name,
            message=g["message"],
            extra={"host": g["host"], "tag": g["tag"]},
        )
