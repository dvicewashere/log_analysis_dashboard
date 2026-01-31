import re
from .base import BaseParser, LogEntry


class NginxAccessParser(BaseParser):
    name = "nginx_access"
    _RE = re.compile(
        r'^(?P<remote_addr>\S+)\s+-\s+(?P<remote_user>\S*)\s+\[(?P<time_local>[^\]]+)\]\s+'
        r'"(?P<method>\S+)\s+(?P<request_uri>\S+)\s+(?P<protocol>\S+)"\s+'
        r'(?P<status>\d+)\s+(?P<body_bytes>\S+)\s+"(?P<referer>[^"]*)"\s+'
        r'"(?P<user_agent>[^"]*)"\s*$'
    )

    def parse_line(self, line: str) -> LogEntry | None:
        m = self._RE.match(line.strip())
        if not m:
            return LogEntry(raw=line, message=line, source=self.name)
        g = m.groupdict()
        return LogEntry(
            raw=line,
            timestamp=g["time_local"],
            source=self.name,
            message=f"{g['method']} {g['request_uri']} -> {g['status']}",
            extra={
                "remote_addr": g["remote_addr"],
                "method": g["method"],
                "request_uri": g["request_uri"],
                "status": g["status"],
                "body_bytes": g["body_bytes"],
                "user_agent": g["user_agent"][:200],
            },
        )
