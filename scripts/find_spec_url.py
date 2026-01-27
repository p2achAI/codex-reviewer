#!/usr/bin/env python3
import json
import os
import re
import sys

marker = os.getenv("SPEC_COMMENT_MARKER", "SPEC:").strip()
clickup_host = os.getenv("CLICKUP_HOST", "app.clickup.com").strip().lower()

try:
    data = json.load(sys.stdin)
except Exception:
    sys.stderr.write("Invalid JSON input for comments.\n")
    sys.exit(2)


def clean_url(url):
    url = url.strip()
    while url and url[-1] in ")]}>.,;":
        url = url[:-1]
    return url


marker_pattern = re.compile(re.escape(marker) + r"\s*(https?://\S+)", re.IGNORECASE) if marker else None
clickup_pattern = re.compile(
    r"https?://" + re.escape(clickup_host) + r"/t/\S+",
    re.IGNORECASE,
)


def find_by_marker():
    if not marker_pattern:
        return None
    for item in data:
        body = item.get("body") or ""
        match = marker_pattern.search(body)
        if match:
            return clean_url(match.group(1))
    return None


def find_clickup_link():
    for item in data:
        body = item.get("body") or ""
        match = clickup_pattern.search(body)
        if match:
            return clean_url(match.group(0))
    return None


url = find_by_marker()
if not url:
    url = find_clickup_link()

if url:
    print(url)
    sys.exit(0)

sys.exit(1)
