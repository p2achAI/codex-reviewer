#!/bin/bash
set -euo pipefail

ACTION_DIR="${ACTION_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
WORKDIR="${WORKDIR:-$(pwd)}"
CODEX_BIN="${CODEX_BIN:-codex}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MODEL="${MODEL:-gpt-5-mini}"
LANGUAGE="${LANGUAGE:-english}"
CUSTOM_PROMPT="${CUSTOM_PROMPT:-}"
CLICKUP_URL_INPUT="${CLICKUP_URL_INPUT:-}"
CLICKUP_API_TOKEN="${CLICKUP_API_TOKEN:-}"
CLICKUP_TEAM_ID="${CLICKUP_TEAM_ID:-}"
CLICKUP_CUSTOM_TASK_IDS="${CLICKUP_CUSTOM_TASK_IDS:-false}"
SPEC_SOURCE="${SPEC_SOURCE:-auto}"
SPEC_MARKER="${SPEC_MARKER:-SPEC:}"
SPEC_LABEL="${SPEC_LABEL:-codex-review}"
PERFSEC_LABEL="${PERFSEC_LABEL:-codex-review-perf}"
BUG_LABEL="${BUG_LABEL:-codex-review-bug}"
DEFAULT_LABEL="${DEFAULT_LABEL:-codex-review}"
TRIGGER_LABEL="${TRIGGER_LABEL:-}"
PR_NUMBER="${PR_NUMBER:-0}"
BASE_BRANCH="${BASE_BRANCH:-}"
HEAD_BRANCH="${HEAD_BRANCH:-}"
SKIP_REMOTE_CONTEXT="${SKIP_REMOTE_CONTEXT:-false}"

if [ -z "${TRIGGER_LABEL}" ]; then
  TRIGGER_LABEL="${DEFAULT_LABEL}"
fi

cd "${WORKDIR}"

touch review.md

if [ ! -f pr.diff ]; then
  if [ -n "${BASE_BRANCH}" ] && [ -n "${HEAD_BRANCH}" ]; then
    echo "Using pr into ${BASE_BRANCH} from ${HEAD_BRANCH} (PR #${PR_NUMBER})"
    git fetch origin "${BASE_BRANCH}:${BASE_BRANCH}"
    git fetch origin "${HEAD_BRANCH}:${HEAD_BRANCH}"
    git diff "${BASE_BRANCH}"..."${HEAD_BRANCH}" > pr.diff
    echo "head -n 10 pr.diff"
    head -n 10 pr.diff
  else
    echo "pr.diff is missing and BASE_BRANCH/HEAD_BRANCH are not set." >&2
    exit 1
  fi
fi

PROMPT_TEMPLATE=""
case "${TRIGGER_LABEL}" in
  "${SPEC_LABEL}")
    PROMPT_TEMPLATE="${ACTION_DIR}/prompts/agent_spec.txt"
    ;;
  "${PERFSEC_LABEL}"|"${BUG_LABEL}")
    PROMPT_TEMPLATE="${ACTION_DIR}/prompts/agent_base.txt"
    ;;
  *)
    PROMPT_TEMPLATE="${ACTION_DIR}/prompt.txt"
    ;;
esac

if [ "${SKIP_REMOTE_CONTEXT}" != "true" ]; then
  SPEC_URL=""
  if [ -n "${CLICKUP_URL_INPUT}" ]; then
    SPEC_URL="${CLICKUP_URL_INPUT}"
  elif [ "${SPEC_SOURCE}" = "comment" ] || [ "${SPEC_SOURCE}" = "auto" ]; then
    echo "Searching PR comments for spec URL with marker: ${SPEC_MARKER}"
    COMMENTS_JSON=$(curl -sS -H "Authorization: token ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" \
      "${GITHUB_API_URL}/repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/comments") || true
    PR_JSON=$(curl -sS -H "Authorization: token ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" \
      "${GITHUB_API_URL}/repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}") || true
    echo "${COMMENTS_JSON}" | "${PYTHON_BIN}" "${ACTION_DIR}/scripts/comments_to_md.py" > comments.md || echo "Warning: failed to render comments.md"
    echo "${PR_JSON}" | "${PYTHON_BIN}" "${ACTION_DIR}/scripts/pr_body_to_md.py" > pr_description.md || echo "Warning: failed to render pr_description.md"
    SPEC_URL=$(echo "${COMMENTS_JSON}" | SPEC_COMMENT_MARKER="${SPEC_MARKER}" "${PYTHON_BIN}" "${ACTION_DIR}/scripts/find_spec_url.py" || true)
  fi

  if [ -n "${SPEC_URL}" ]; then
    echo "Spec URL found: ${SPEC_URL}"
    CLICKUP_URL="${SPEC_URL}" CLICKUP_API_TOKEN="${CLICKUP_API_TOKEN}" \
      CLICKUP_TEAM_ID="${CLICKUP_TEAM_ID}" CLICKUP_CUSTOM_TASK_IDS="${CLICKUP_CUSTOM_TASK_IDS}" \
      OUTPUT_FILE="spec.md" \
      "${PYTHON_BIN}" "${ACTION_DIR}/scripts/fetch_clickup_task.py" || echo "Warning: failed to fetch ClickUp spec."
  else
    echo "No spec URL found. Spec context will be empty."
  fi
fi

if [ ! -f spec.md ]; then
  : > spec.md
fi
if [ ! -f comments.md ]; then
  : > comments.md
fi
if [ ! -f pr_description.md ]; then
  : > pr_description.md
fi

ROLE="General review"
case "${TRIGGER_LABEL}" in
  "${SPEC_LABEL}")
    ROLE="기획문서 준수 + 테스트(ClickUp + PR description)"
    ;;
  "${PERFSEC_LABEL}")
    ROLE="성능/보안"
    ;;
  "${BUG_LABEL}")
    ROLE="정합성/버그"
    ;;
esac

if [ -n "${CUSTOM_PROMPT}" ]; then
  printf '%s\n' "${CUSTOM_PROMPT}" > prompt.txt
elif [ "${PROMPT_TEMPLATE}" = "${ACTION_DIR}/prompt.txt" ]; then
  cp "${ACTION_DIR}/prompt.txt" ./prompt.txt
else
  ROLE="${ROLE}" OUTPUT_FILE="review.md" LANGUAGE="${LANGUAGE}" CUSTOM_INSTRUCTIONS="${CUSTOM_PROMPT}" \
    COMMENTS_FILE="comments.md" \
    PR_DESCRIPTION_FILE="pr_description.md" \
    "${PYTHON_BIN}" "${ACTION_DIR}/scripts/render_prompt.py" "${PROMPT_TEMPLATE}" "prompt.txt"
fi

LANGUAGE_VALUE="${LANGUAGE}" "${PYTHON_BIN}" - <<'PY'
import os
from pathlib import Path
path = Path("prompt.txt")
language = os.environ["LANGUAGE_VALUE"]
path.write_text(path.read_text(encoding="utf-8").replace("LANGUAGE", language), encoding="utf-8")
PY
cat prompt.txt

"${CODEX_BIN}" exec --full-auto -m "${MODEL}" -o review.md - < prompt.txt

if [ ! -s review.md ]; then
  echo "Codex failed to generate review in review.md. Creating default message..."
  {
    echo "## Code Review for PR #${PR_NUMBER}"
    echo
    echo "Sorry, the automated review system encountered an issue while analyzing this PR."
    echo "Please try again by re-applying the label \`${TRIGGER_LABEL:-${DEFAULT_LABEL}}\`."
  } > review.md
fi
