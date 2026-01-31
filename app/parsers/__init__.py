from .base import BaseParser, LogEntry
from .auth import AuthLogParser
from .syslog import SyslogParser
from .nginx import NginxAccessParser
from .ufw import UfwParser

PARSERS = {
    "auth": AuthLogParser,
    "syslog": SyslogParser,
    "nginx_access": NginxAccessParser,
    "ufw": UfwParser,
}

