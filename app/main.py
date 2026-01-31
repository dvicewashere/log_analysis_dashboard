# flask api ve dashboard
import os
import queue
from pathlib import Path
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from app.config import LOG_PATHS, RULES_PATH, RULES_PATH_JSON, REPORTS_DIR
from app.parsers import PARSERS
from app.rules.engine import RuleEngine, load_rules
from app.tailer import get_tailer
from app.reports import export_logs_to_csv

_ROOT = Path(__file__).resolve().parent.parent
app = Flask(__name__, static_folder=str(_ROOT / "static"), template_folder=str(_ROOT / "templates"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "altay")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

_rules = load_rules(RULES_PATH, RULES_PATH_JSON)
_engine = RuleEngine(_rules)


_alert_queue = queue.Queue()

def _on_alert_from_tailer(alert):
    _alert_queue.put_nowait(alert)

def _emit_alerts_loop():
    import eventlet
    while True:
        try:
            alert = _alert_queue.get(timeout=0.25)
            socketio.emit("alert", alert, broadcast=True)
        except queue.Empty:
            pass
        eventlet.sleep(0.02)

_tailer = get_tailer()
_tailer.on_alert = _on_alert_from_tailer
_tailer.start_background(interval=1.0)
socketio.start_background_task(_emit_alerts_loop)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/logs")
def list_logs():
    sonuc = []
    for key, path in LOG_PATHS.items():
        sonuc.append({"id": key, "path": path, "exists": os.path.exists(path), "readable": os.path.isfile(path) and os.access(path, os.R_OK)})
    return jsonify(sonuc)


@app.route("/api/analyze/<source>")
def analyze(source):
    if source not in LOG_PATHS:
        return jsonify({"error": "Geçersiz kaynak"}), 400
    path = LOG_PATHS[source]
    if not os.path.isfile(path):
        return jsonify({"error": "Dosya bulunamadı", "path": path}), 404
    parser_cls = PARSERS.get(source)
    if not parser_cls:
        return jsonify({"error": "Parser bulunamadı"}), 400
    parser = parser_cls()
    entries = list(parser.parse_file(path))
    alerts = []
    for e in entries:
        alerts.extend(_engine.match_entry(e, source))
    severity_counts = {}
    rule_counts = {}
    for a in alerts:
        severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
        rule_counts[a.rule_name] = rule_counts.get(a.rule_name, 0) + 1
    summary = {
        "source": source,
        "path": path,
        "total_lines": len(entries),
        "alerts_count": len(alerts),
        "severity_counts": severity_counts,
        "rule_counts": rule_counts,
    }
    alerts_list = [{"rule_id": a.rule_id, "rule_name": a.rule_name, "severity": a.severity, "message": a.message, "log_raw": a.log_raw[:300], "log_source": a.log_source} for a in alerts[:200]]
    sample = [e.to_dict() for e in entries[:50]]
    return jsonify({"summary": summary, "alerts": alerts_list, "sample_entries": sample})


@app.route("/api/tail/alerts")
def tail_alerts():
    limit = request.args.get("limit", type=int) or 100
    return jsonify(_tailer.get_recent_alerts(limit=limit))


@app.route("/api/rules")
def list_rules():
    return jsonify([{"id": r.id, "name": r.name, "description": r.description, "enabled": r.enabled, "severity": r.severity, "sources": r.sources, "patterns": r.patterns, "pattern_type": r.pattern_type} for r in _rules])


@app.route("/api/export/<source>", methods=["GET"])
def export_csv(source):
    if source not in LOG_PATHS:
        return jsonify({"error": "Geçersiz kaynak"}), 400
    path = LOG_PATHS[source]
    if not os.path.isfile(path):
        return jsonify({"error": "Dosya bulunamadı"}), 404
    max_lines = request.args.get("max_lines", type=int) or 10000
    parser_cls = PARSERS.get(source)
    if not parser_cls:
        return jsonify({"error": "Parser bulunamadı"}), 400
    parser = parser_cls()
    entries = list(parser.parse_file(path, max_lines=max_lines))
    if not entries:
        return jsonify({"error": "Dışa aktarılacak satır yok"}), 400
    try:
        out_path = export_logs_to_csv(entries, source)
        return send_file(str(out_path), as_attachment=True, download_name=out_path.name, mimetype="text/csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports")
def list_reports():
    if not REPORTS_DIR.exists():
        return jsonify([])
    files = []
    for f in sorted(REPORTS_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True):
        files.append({"name": f.name, "path": str(f), "size": f.stat().st_size})
    return jsonify(files[:50])


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "images/yanaqlibebekdvice.ico", mimetype="image/x-icon")

@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/<path:path>")
def static_route(path):
    if path.startswith("api/"):
        return jsonify({"error": "Bulunamadı"}), 404

    static_path = path[7:] if path.startswith("static/") else path
    p = Path(app.static_folder) / static_path
    if p.is_file():
        return send_from_directory(app.static_folder, static_path)
    return send_from_directory(app.template_folder, "index.html")


@socketio.on("connect")
def ws_connect():
    emit("connected", {"message": "baglandi"})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
