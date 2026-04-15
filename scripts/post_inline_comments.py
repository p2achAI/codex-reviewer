#!/usr/bin/env python3
"""Parse review.md and post inline PR review comments via GitHub API."""

import json
import os
import re
import sys
import urllib.request
import urllib.error


def parse_diff(diff_path):
    """Parse unified diff to extract commentable new-file line numbers per file.

    Returns dict: file_path -> set of line numbers visible in the diff.
    """
    valid_lines = {}
    current_file = None
    new_line = 0

    with open(diff_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            m = re.match(r"^diff --git a/.+ b/(.+)$", line)
            if m:
                current_file = m.group(1)
                valid_lines.setdefault(current_file, set())
                new_line = 0
                continue

            m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if m:
                new_line = int(m.group(1))
                continue

            if current_file is None or new_line == 0:
                continue

            if line.startswith("-"):
                continue
            elif line.startswith("+") or line.startswith(" "):
                valid_lines[current_file].add(new_line)
                new_line += 1

    return valid_lines


def parse_findings(review_path):
    """Extract structured findings from review markdown.

    Expected format: - [Pn] `path/to/file:start-end` description
    """
    findings = []

    with open(review_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"- \[P([0-3])\] `([^`]+?):(\d+)(?:-(\d+))?`\s+(.+)"
    for m in re.finditer(pattern, content):
        findings.append(
            {
                "severity": int(m.group(1)),
                "file_path": m.group(2),
                "start_line": int(m.group(3)),
                "end_line": int(m.group(4)) if m.group(4) else int(m.group(3)),
                "description": m.group(5).strip(),
            }
        )

    return findings


def build_inline_comments(findings, valid_lines):
    """Convert findings into GitHub PR review inline comments.

    Only includes comments whose line range overlaps with diff lines.
    """
    comments = []

    for f in findings:
        file_lines = valid_lines.get(f["file_path"], set())
        if not file_lines:
            continue

        overlap = set(range(f["start_line"], f["end_line"] + 1)) & file_lines
        if not overlap:
            continue

        comment_start = min(overlap)
        comment_end = max(overlap)

        body = f"**[P{f['severity']}]** {f['description']}"

        comment = {
            "path": f["file_path"],
            "line": comment_end,
            "side": "RIGHT",
            "body": body,
        }
        if comment_start != comment_end:
            comment["start_line"] = comment_start
            comment["start_side"] = "RIGHT"

        comments.append(comment)

    return comments


def github_api(url, payload, token):
    """POST JSON to a GitHub API endpoint."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", "token " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print("GitHub API error %d: %s" % (e.code, error_body), file=sys.stderr)
        return None


def post_review(api_url, owner_repo, pr_number, commit_sha, body, comments, token):
    """Submit a GitHub PR review with optional inline comments."""
    url = "%s/repos/%s/pulls/%s/reviews" % (api_url, owner_repo, pr_number)

    payload = {
        "commit_id": commit_sha,
        "body": body,
        "event": "COMMENT",
        "comments": comments,
    }

    return github_api(url, payload, token)


def main():
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repository = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = os.environ.get("PR_NUMBER", "0")
    commit_sha = os.environ.get("COMMIT_SHA", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    if not github_token or not github_repository or pr_number == "0" or not commit_sha:
        print(
            "Missing required env vars (GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER, COMMIT_SHA)",
            file=sys.stderr,
        )
        sys.exit(0)

    diff_path = os.environ.get("DIFF_FILE", "pr.diff")
    review_path = os.environ.get("REVIEW_FILE", "review.md")

    if not os.path.isfile(diff_path) or not os.path.isfile(review_path):
        print("pr.diff or review.md not found, skipping inline comments")
        sys.exit(0)

    valid_lines = parse_diff(diff_path)
    findings = parse_findings(review_path)

    if not findings:
        print("No findings to post as inline comments")
        sys.exit(0)

    comments = build_inline_comments(findings, valid_lines)

    if not comments:
        print("No findings matched diff lines, skipping inline comments")
        sys.exit(0)

    print("Posting %d inline comment(s)..." % len(comments))

    result = post_review(
        api_url,
        github_repository,
        pr_number,
        commit_sha,
        "",
        comments,
        github_token,
    )

    if result:
        print("Review posted: %s" % result.get("html_url", ""))
        sys.exit(0)

    # Batch failed – try posting comments one by one
    print("Batch post failed, trying individual comments...", file=sys.stderr)
    posted = 0
    for c in comments:
        r = post_review(
            api_url, github_repository, pr_number, commit_sha, "", [c], github_token
        )
        if r:
            posted += 1
    print("Posted %d/%d inline comments individually" % (posted, len(comments)))


if __name__ == "__main__":
    main()
