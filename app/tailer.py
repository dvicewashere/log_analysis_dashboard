import os
import threading
import time
from collections import deque

from app.config import LOG_PATHS, RULES_PATH, RULES_PATH_JSON, TAIL_BUFFER_SIZE
from app.rules.engine import RuleEngine, load_rules


class LogTailer:
    def __init__(self, on_alert=None, buffer_size=TAIL_BUFFER_SIZE):
        self.on_alert = on_alert or (lambda _: None)
        self.buffer_size = buffer_size
        self._rules = load_rules(RULES_PATH, RULES_PATH_JSON)
        self._engine = RuleEngine(self._rules)
        self._file_positions = {}
        self._buffers = {k: deque(maxlen=buffer_size) for k in LOG_PATHS}
        self._alerts_buffer = deque(maxlen=500)
        self._running = False
        self._thread = None

    def _get_current_size(self, path):
        try:
            return os.path.getsize(path)
        except (FileNotFoundError, PermissionError):
            return 0

    def _read_new_lines(self, path, source_key):
        alerts = []
        try:
            pos = self._file_positions.get(path, 0)
            size = self._get_current_size(path)
            if size < pos:
                pos = 0
            if size <= pos:
                return alerts
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(pos)
                for line in f:
                    line = line.rstrip("\n")
                    if not line.strip():
                        continue
                    self._buffers[source_key].append(line)
                    matches = self._engine.match_line(line, source_key)
                    for m in matches:
                        alert = {
                            "rule_id": m.rule_id,
                            "rule_name": m.rule_name,
                            "severity": m.severity,
                            "message": m.message,
                            "log_raw": m.log_raw[:500],
                            "log_source": m.log_source,
                        }
                        alerts.append(alert)
                        self._alerts_buffer.append(alert)
                        self.on_alert(alert)
                self._file_positions[path] = f.tell()
        except (FileNotFoundError, PermissionError):
            pass
        return alerts

    def poll_once(self):
        all_alerts = []
        for source_key, path in LOG_PATHS.items():
            if not path or not os.path.exists(path):
                continue
            all_alerts.extend(self._read_new_lines(path, source_key))
        return all_alerts

    def get_recent_lines(self, source_key=None):
        if source_key:
            return {source_key: list(self._buffers.get(source_key, []))}
        return {k: list(v) for k, v in self._buffers.items()}

    def get_recent_alerts(self, limit=100):
        return list(self._alerts_buffer)[-limit:]

    def _run_loop(self, interval):
        while self._running:
            self.poll_once()
            time.sleep(interval)

    def start_background(self, interval=1.0):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, args=(interval,), daemon=True)
        self._thread.start()

    def stop_background(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None


_tailer = None

def get_tailer():
    global _tailer
    if _tailer is None:
        _tailer = LogTailer()
    return _tailer
