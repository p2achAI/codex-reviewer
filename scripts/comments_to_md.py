#!/usr/bin/env python3
import json
import sys
from datetime import datetime

def fmt_time(ts):
    if not ts:
        return ""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).isoformat()
    except Exception:
        return ts

try:
    data = json.load(sys.stdin)
except Exception:
    sys.stderr.write("Invalid JSON input for comments.\n")
    sys.exit(2)

lines = ["# PR Comments", ""]
for item in data:
    user = (item.get("user") or {}).get("login", "unknown")
    created = fmt_time(item.get("created_at"))
    body = item.get("body") or ""
    lines.append(f"## {user} ({created})")
    lines.append("")
    lines.append(body.strip())
    lines.append("")

sys.stdout.write("\n".join(lines))
