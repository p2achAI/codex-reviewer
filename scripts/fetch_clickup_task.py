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


def parse_parent_id(parent):
    if isinstance(parent, str):
        return parent.strip() or ""
    if isinstance(parent, dict):
        parent_id = parent.get("id")
        if isinstance(parent_id, str):
            return parent_id.strip() or ""
    return ""


def extract_task_view(data):
    markdown_desc = data.get("markdown_description")
    plain_desc = data.get("description")
    desc = (markdown_desc or plain_desc or "").strip()
    return {
        "id": (str(data.get("id", "")).strip()),
        "name": (data.get("name") or "").strip(),
        "description": desc,
        "url": (data.get("url") or "").strip(),
        "parent_id": parse_parent_id(data.get("parent")),
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


def resolve_parent_chain(start_parent_id, *, use_custom_task_ids, team_id, api_token):
    parent_chain = []
    warnings = []
    visited = set()
    current_parent_id = (start_parent_id or "").strip()

    while current_parent_id:
        if current_parent_id in visited:
            warnings.append(
                f"Cycle detected in parent chain at task ID {current_parent_id}. Stopped traversal."
            )
            break

        visited.add(current_parent_id)
        try:
            parent_data = fetch_task(
                current_parent_id,
                use_custom_task_ids=use_custom_task_ids,
                team_id=team_id,
                api_token=api_token,
            )
            parent_view = extract_task_view(parent_data)
            parent_chain.append(parent_view)
            current_parent_id = parent_view["parent_id"]
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                warnings.append(
                    f"Parent task {current_parent_id} fetch failed: HTTP {e.code} Unauthorized/Forbidden"
                )
            else:
                warnings.append(
                    f"Parent task {current_parent_id} fetch failed: HTTP {e.code}"
                )
            break
        except json.JSONDecodeError:
            warnings.append(
                f"Parent task {current_parent_id} fetch failed: Invalid JSON response from ClickUp"
            )
            break
        except Exception as e:
            warnings.append(f"Parent task {current_parent_id} fetch failed: {e}")
            break

    return parent_chain, warnings


def render_task_section(task):
    lines = [f"- ID: {task.get('id') or '(Unknown)'}"]
    if task.get("url"):
        lines.append(f"- URL: {task['url']}")
    if task.get("name"):
        lines.append(f"- Title: {task['name']}")
    lines.append("- Description:")
    lines.append(task.get("description") or "(No description provided in ClickUp task.)")
    return lines


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
parent_chain, parent_warnings = resolve_parent_chain(
    main_task["parent_id"],
    use_custom_task_ids=use_custom_task_ids,
    team_id=team_id,
    api_token=api_token,
)

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

content_lines.append("## Parent Tasks (nearest -> root)")
if not parent_chain:
    content_lines.append("- None")
else:
    for idx, parent_task in enumerate(parent_chain, start=1):
        content_lines.append(f"### Parent {idx}")
        content_lines.extend(render_task_section(parent_task))
        content_lines.append("")

if parent_warnings:
    content_lines.append("## Parent Fetch Warnings")
    for warning in parent_warnings:
        content_lines.append(f"- {warning}")
    content_lines.append("")

with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(content_lines))
