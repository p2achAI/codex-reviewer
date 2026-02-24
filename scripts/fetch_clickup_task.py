#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.parse
import urllib.request


clickup_url = os.getenv("CLICKUP_URL", "").strip()
api_token = os.getenv("CLICKUP_API_TOKEN", "").strip()
team_id = os.getenv("CLICKUP_TEAM_ID", "").strip()
custom_task_ids_flag = os.getenv("CLICKUP_CUSTOM_TASK_IDS", "false").strip().lower() == "true"
out_file = os.getenv("OUTPUT_FILE", "spec.md")


def extract_task_view(data):
    markdown_desc = data.get("markdown_description")
    plain_desc = data.get("description")
    desc = (markdown_desc or plain_desc or "").strip()
    return {
        "id": (str(data.get("id", "")).strip()),
        "name": (data.get("name") or "").strip(),
        "description": desc,
        "url": (data.get("url") or "").strip(),
    }


def fetch_task(task_id, *, use_custom_task_ids, team_id, api_token):
    params = {"include_markdown_description": "true"}
    if use_custom_task_ids:
        params["custom_task_ids"] = "true"
        params["team_id"] = team_id

    query = urllib.parse.urlencode(params) if params else ""
    api_url = f"https://api.clickup.com/api/v2/task/{task_id}"
    if query:
        api_url = f"{api_url}?{query}"

    req = urllib.request.Request(
        api_url,
        headers={
            "Authorization": api_token,
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = resp.read().decode("utf-8")

    return json.loads(payload)


if not clickup_url:
    sys.stderr.write("No CLICKUP_URL provided.\n")
    sys.exit(2)

if not api_token:
    sys.stderr.write("No CLICKUP_API_TOKEN provided.\n")
    sys.exit(3)

if "/docs/" in clickup_url or "/doc/" in clickup_url:
    sys.stderr.write("ClickUp Docs URL detected; public Docs API is not supported.\n")
    sys.exit(4)

parsed = urllib.parse.urlparse(clickup_url)
match = re.search(r"/t/([^/?#]+(?:/[^/?#]+)*)", parsed.path)
if not match:
    sys.stderr.write("Could not extract ClickUp task ID from URL.\n")
    sys.exit(5)

path_after = (match.group(1) or "").strip("/")
parts = [part for part in path_after.split("/") if part]
if not parts:
    sys.stderr.write("Could not extract ClickUp task ID from URL.\n")
    sys.exit(5)

task_id = parts[-1]
team_id_from_url = parts[0] if len(parts) > 1 else ""

use_custom_task_ids = custom_task_ids_flag or (not task_id.isdigit())
if use_custom_task_ids:
    if not team_id and team_id_from_url.isdigit():
        team_id = team_id_from_url
    if not team_id:
        sys.stderr.write("custom_task_ids enabled but CLICKUP_TEAM_ID is missing.\n")
        sys.exit(4)

try:
    main_data = fetch_task(
        task_id,
        use_custom_task_ids=use_custom_task_ids,
        team_id=team_id,
        api_token=api_token,
    )
except urllib.error.HTTPError as e:
    if e.code in (401, 403):
        sys.stderr.write(f"Failed to fetch ClickUp task: HTTP {e.code} Unauthorized/Forbidden\n")
        sys.exit(6)
    sys.stderr.write(f"Failed to fetch ClickUp task: HTTP {e.code}\n")
    sys.exit(6)
except json.JSONDecodeError:
    sys.stderr.write("Invalid JSON response from ClickUp.\n")
    sys.exit(7)
except Exception as e:
    sys.stderr.write(f"Failed to fetch ClickUp task: {e}\n")
    sys.exit(6)

main_task = extract_task_view(main_data)

content_lines = [
    "# ClickUp Task",
    f"- URL: {clickup_url}",
    f"- ID: {task_id}",
]
if main_task["name"]:
    content_lines.append(f"- Title: {main_task['name']}")
content_lines.append("")
content_lines.append("## Description")
content_lines.append(main_task["description"] or "(No description provided in ClickUp task.)")
content_lines.append("")

with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(content_lines))
