import re
from .base import BaseParser, LogEntry


class UfwParser(BaseParser):
    name = "ufw"

    _RE = re.compile(
        r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\S+)\s+"
        r"(?P<host>\S+)\s+kernel:\s+\[[^\]]+\]\s+\[UFW\s+(?P<action>\w+)\]\s+"
        r"(?P<rest>.*)$"
    )
    _SRC = re.compile(r"\bSRC=(?P<src>\S+)")
    _DST = re.compile(r"\bDST=(?P<dst>\S+)")
    _DPT = re.compile(r"\bDPT=(?P<dpt>\d+)")
    _PROTO = re.compile(r"\bPROTO=(?P<proto>\w+)")

    def parse_line(self, line: str) -> LogEntry | None:
        m = self._RE.match(line.strip())
        if not m:
            return LogEntry(raw=line, message=line, source=self.name)
        g = m.groupdict()
        rest = g["rest"]
        src = self._SRC.search(rest)
        dst = self._DST.search(rest)
        dpt = self._DPT.search(rest)
        proto = self._PROTO.search(rest)
        ts = f"{g['month']} {g['day']} {g['time']}"
        return LogEntry(
            raw=line,
            timestamp=ts,
            source=self.name,
            message=f"UFW {g['action']}",
            extra={
                "host": g["host"],
                "action": g["action"],
                "src": src.group("src") if src else "",
                "dst": dst.group("dst") if dst else "",
                "dpt": dpt.group("dpt") if dpt else "",
                "proto": proto.group("proto") if proto else "",
            },
        )
