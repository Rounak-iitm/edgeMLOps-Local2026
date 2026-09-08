from __future__ import annotations
import json, os, time

def audit(event: str, **fields):
    path = os.environ.get("EDGE_AUDIT_LOG", "logs/audit.log")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    record = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, **fields}
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass
