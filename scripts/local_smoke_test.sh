#!/bin/bash
set -euo pipefail

MODE="${1:---mock}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

EXPECTED_CODEX_VERSION="${EXPECTED_CODEX_VERSION:-0.115.0-alpha.27}"
CODEX_BIN="${CODEX_BIN:-${ROOT_DIR}/scripts/mock_codex.sh}"

if [ "${MODE}" = "--live" ]; then
  CODEX_BIN="${CODEX_BIN:-codex}"
  if [ -z "${OPENAI_API_KEY:-${CODEX_API_KEY:-}}" ]; then
    echo "OPENAI_API_KEY or CODEX_API_KEY is required for --live" >&2
    exit 2
  fi
fi

VERSION_OUTPUT="$("${CODEX_BIN}" --version)"
case "${VERSION_OUTPUT}" in
  *"${EXPECTED_CODEX_VERSION}"*)
    ;;
  *)
    echo "Unexpected codex version: ${VERSION_OUTPUT}" >&2
    exit 1
    ;;
esac

run_case() {
  local label="$1"
  local case_dir="${TMP_DIR}/$(echo "${label}" | tr -c 'a-zA-Z0-9' '_')"
  mkdir -p "${case_dir}"

  cat > "${case_dir}/pr.diff" <<'EOF'
diff --git a/apps/example.py b/apps/example.py
index 1111111..2222222 100644
--- a/apps/example.py
+++ b/apps/example.py
@@ -10,2 +10,3 @@
-value = 1
+value = 2
+flag = True
EOF

  cat > "${case_dir}/comments.md" <<'EOF'
# PR Comments

## reviewer

SPEC: https://app.clickup.com/t/9014951824/PR-1588
EOF

  cat > "${case_dir}/pr_description.md" <<'EOF'
# PR Description

테스트용 PR 설명
EOF

  cat > "${case_dir}/spec.md" <<'EOF'
# Spec

테스트용 스펙
EOF

  (
    cd "${case_dir}"
    ACTION_DIR="${ROOT_DIR}" \
    WORKDIR="${case_dir}" \
    CODEX_BIN="${CODEX_BIN}" \
    PYTHON_BIN="python3" \
    MODEL="gpt-5-mini" \
    LANGUAGE="korean" \
    TRIGGER_LABEL="${label}" \
    DEFAULT_LABEL="codex-review" \
    SPEC_LABEL="codex-review" \
    PERFSEC_LABEL="codex-review-perf" \
    BUG_LABEL="codex-review-bug" \
    PR_NUMBER="334" \
    SKIP_REMOTE_CONTEXT="true" \
    "${ROOT_DIR}/scripts/run_review.sh"
  )

  test -s "${case_dir}/review.md"
  grep -q "Mock Review\|P[0-3]" "${case_dir}/review.md"
}

run_case "codex-review"
run_case "codex-review-perf"
run_case "codex-review-bug"

echo "local smoke test passed with ${VERSION_OUTPUT}"
