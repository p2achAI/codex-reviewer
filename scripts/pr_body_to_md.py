#!/usr/bin/env python3
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.stderr.write("Invalid JSON input for PR body.\n")
    sys.exit(2)

body = data.get("body") or ""

lines = ["# PR Description", "", body.strip(), ""]

sys.stdout.write("\n".join(lines))
