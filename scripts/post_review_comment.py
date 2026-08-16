#!/usr/bin/env python3
"""Post the generated review as a pull request issue comment."""

import json
import os
import sys
import urllib.error
import urllib.request


def post_comment(api_url, repository, pr_number, body, token):
    """Create a pull request issue comment through the GitHub REST API."""
    url = f"{api_url}/repos/{repository}/issues/{pr_number}/comments"
    data = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("Content-Type", "application/json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = os.environ.get("PR_NUMBER", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    review_file = os.environ.get("REVIEW_FILE", "review.md")

    if not token or not repository or not pr_number:
        print(
            "Missing required env vars (GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER)",
            file=sys.stderr,
        )
        return 1

    try:
        with open(review_file, "r", encoding="utf-8") as review:
            body = review.read()
    except OSError as error:
        print(f"Unable to read review file {review_file}: {error}", file=sys.stderr)
        return 1

    if not body.strip():
        print(f"Review file {review_file} is empty", file=sys.stderr)
        return 1

    try:
        result = post_comment(api_url, repository, pr_number, body, token)
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        print(f"GitHub API error {error.code}: {error_body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"GitHub API request failed: {error.reason}", file=sys.stderr)
        return 1

    print(f"Review comment posted: {result.get('html_url', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
