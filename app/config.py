import os
from pathlib import Path


LOG_BASE = os.environ.get("LOG_BASE", "/var/log")

LOG_PATHS = {
    "auth": os.environ.get("AUTH_LOG", os.path.join(LOG_BASE, "auth.log")),
    "syslog": os.environ.get("SYSLOG", os.path.join(LOG_BASE, "syslog")),
    "nginx_access": os.environ.get("NGINX_ACCESS", os.path.join(LOG_BASE, "nginx", "access.log")),
    "ufw": os.environ.get("UFW_LOG", os.path.join(LOG_BASE, "ufw.log")),
}

RULES_PATH = os.environ.get("RULES_PATH", "/app/config/rules.yaml")
RULES_PATH_JSON = os.environ.get("RULES_PATH_JSON", "/app/config/rules.json")

REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "/app/reports"))
try:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

TAIL_BUFFER_SIZE = 100
SECRET_KEY = os.environ.get("SECRET_KEY", "altay")
