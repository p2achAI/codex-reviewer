#!/usr/bin/env python3
"""Canonicalize a model no-finding verdict without masking findings."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


CANONICAL_NO_FINDING = "- Pn 규칙 기준으로 지적할 이슈 없음."
NO_FINDING_PREFIX = re.compile(
    r"^- (?:Pn|P4) 규칙 기준으로 지적할 이슈 없음\.(?:\s+.*)?$"
)
SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")


def normalize_review(review: str) -> str:
    """Return review with a single no-finding line made contract-exact.

    Normalization is deliberately fail-closed: it only applies when the review
    section has exactly one non-empty line and that line starts with the known
    no-finding verdict. Findings, mixed verdicts, and multi-line explanations
    are left untouched for the consuming repository to validate.
    """

    lines = review.splitlines(keepends=True)
    review_start: int | None = None
    review_end = len(lines)

    for index, line in enumerate(lines):
        heading = SECTION_HEADING.fullmatch(line.rstrip("\r\n"))
        if heading is None:
            continue
        if review_start is not None:
            review_end = index
            break
        if heading.group(1) == "리뷰":
            review_start = index + 1

    if review_start is None:
        return review

    content_indexes = [
        index
        for index in range(review_start, review_end)
        if lines[index].strip()
    ]
    if len(content_indexes) != 1:
        return review

    verdict_index = content_indexes[0]
    verdict = lines[verdict_index].strip()
    if NO_FINDING_PREFIX.fullmatch(verdict) is None:
        return review

    newline = "\r\n" if lines[verdict_index].endswith("\r\n") else "\n"
    if not lines[verdict_index].endswith(("\n", "\r")):
        newline = ""
    lines[verdict_index] = f"{CANONICAL_NO_FINDING}{newline}"
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_file", type=Path)
    args = parser.parse_args()
    review = args.review_file.read_text(encoding="utf-8")
    args.review_file.write_text(normalize_review(review), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
