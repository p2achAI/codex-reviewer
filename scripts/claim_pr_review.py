#!/usr/bin/env python3
"""Reserve one review attempt per PR. Caller MUST serialize by repository/PR."""

import json
import os
from pathlib import Path
import urllib.request

MARKER = "<!-- codex-reviewer:attempted:v1 -->"


def request_json(url, token, body=None):
    request = urllib.request.Request(
        url,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    # Do not retry a POST: a lost response may still mean the claim was saved.
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def claim_review(api_url, repository, pr_number, token):
    url = f"{api_url.rstrip('/')}/repos/{repository}/issues/{pr_number}/comments"
    page = 1
    while True:
        comments = request_json(f"{url}?per_page=100&page={page}", token)
        if any((comment.get("body") or "").startswith(MARKER) for comment in comments):
            return False
        if len(comments) < 100:
            break
        page += 1
    request_json(url, token, {"body": (
        f"{MARKER}\n"
        "이 PR의 AI 리뷰 실행권을 사용했습니다. PR당 1회만 실행하며, "
        "리뷰 실패·취소, 새 커밋, 다른 리뷰 라벨, Actions 재실행도 추가 실행하지 않습니다.\n"
        "비용 제한 기록이므로 이 댓글을 수정하거나 삭제하지 마세요."
    )})
    return True


def main():
    # Missing configuration or any API failure stops the action before model use.
    output = Path(os.environ["GITHUB_OUTPUT"])
    with output.open("a") as stream:
        stream.write("allowed=false\n")
    allowed = claim_review(
        os.environ.get("GITHUB_API_URL", "https://api.github.com"),
        os.environ["GITHUB_REPOSITORY"],
        int(os.environ["PR_NUMBER"]),
        os.environ["GITHUB_TOKEN"],
    )
    if allowed:
        with output.open("a") as stream:
            stream.write("allowed=true\n")
    else:
        print("PR당 1회 제한: 이미 실행권을 사용한 PR이므로 리뷰를 생략합니다.")


if __name__ == "__main__":
    main()
