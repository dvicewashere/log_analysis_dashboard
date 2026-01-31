import csv
from datetime import datetime

from app.config import REPORTS_DIR
from app.parsers.base import LogEntry


def entries_to_csv_rows(entries):
    if not entries:
        return []
    rows = []
    for e in entries:
        rows.append(e.to_csv_row())
    return rows


def write_csv(filepath, rows, fieldnames=None):
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def generate_report_filename(source, suffix=""):
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    name = f"{source}{suffix}_{ts}.csv"
    return REPORTS_DIR / name


def export_logs_to_csv(entries, source):
    rows = entries_to_csv_rows(entries)
    if not rows:
        raise ValueError("Export için en az bir satır gerekli")
    path = generate_report_filename(source)
    fieldnames = list(rows[0].keys())
    write_csv(path, rows, fieldnames)
    return path
