#!/bin/bash
set -euo pipefail

MODE="${1:---mock}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

EXPECTED_CODEX_VERSION="${EXPECTED_CODEX_VERSION:-0.115.0-alpha.27}"
EXPECTED_CLAUDE_VERSION="${EXPECTED_CLAUDE_VERSION:-2.1.105}"
CODEX_BIN="${CODEX_BIN:-${ROOT_DIR}/scripts/mock_codex.sh}"
CLAUDE_BIN="${CLAUDE_BIN:-${ROOT_DIR}/scripts/mock_claude.sh}"

if [ "${MODE}" = "--live" ]; then
  CODEX_BIN="codex"
  if [ -z "${OPENAI_API_KEY:-${CODEX_API_KEY:-}}" ]; then
    echo "OPENAI_API_KEY or CODEX_API_KEY is required for --live" >&2
    exit 2
  fi
elif [ "${MODE}" = "--live-claude" ]; then
  CLAUDE_BIN="claude"
  if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "ANTHROPIC_API_KEY is required for --live-claude" >&2
    exit 2
  fi
fi

if [ "${MODE}" != "--live-claude" ]; then
  VERSION_OUTPUT="$("${CODEX_BIN}" --version)"
  case "${VERSION_OUTPUT}" in
    *"${EXPECTED_CODEX_VERSION}"*)
      ;;
    *)
      echo "Unexpected codex version: ${VERSION_OUTPUT}" >&2
      exit 1
      ;;
  esac
fi

setup_fixtures() {
  local case_dir="$1"

  cat > "${case_dir}/pr.diff" <<'DIFF'
diff --git a/apps/user_service.py b/apps/user_service.py
index aaa1111..bbb2222 100644
--- a/apps/user_service.py
+++ b/apps/user_service.py
@@ -1,10 +1,18 @@
+import os
 import json
-from flask import Flask, request
+from flask import Flask, request, jsonify

 app = Flask(__name__)

 @app.route("/users", methods=["POST"])
 def create_user():
-    data = request.get_json()
-    username = data["username"]
-    return json.dumps({"ok": True, "username": username}), 201
+    data = request.get_json(force=True)
+    username = data.get("username", "")
+    email = data.get("email", "")
+    if not username:
+        return jsonify({"error": "username is required"}), 400
+    query = f"INSERT INTO users (name, email) VALUES ('{username}', '{email}')"
+    db_url = os.environ["DATABASE_URL"]
+    # TODO: execute query
+    return jsonify({"ok": True, "username": username}), 201
DIFF

  cat > "${case_dir}/comments.md" <<'EOF'
# PR Comments

## reviewer

사용자 생성 API 엔드포인트 추가
EOF

  cat > "${case_dir}/pr_description.md" <<'EOF'
# PR Description

사용자 생성 API를 추가합니다. POST /users 엔드포인트로 username과 email을 받아 DB에 저장합니다.
EOF

  cat > "${case_dir}/spec.md" <<'EOF'
# Spec

사용자 생성 API 스펙:
- POST /users
- 필수 필드: username, email
- 성공 시 201 반환
- username 중복 시 409 반환
EOF
}

setup_capture_claude_bin() {
  local case_dir="$1"
  local capture_file="${case_dir}/claude_invocation.txt"
  local capture_bin="${case_dir}/capture_claude.sh"

  cat > "${capture_bin}" <<EOF
#!/bin/bash
set -euo pipefail

if [ "\${1:-}" = "--version" ] || [ "\${1:-}" = "-v" ]; then
  echo "2.1.105 (Claude Code)"
  exit 0
fi

printf '%s\n' "\$@" > "${capture_file}"
cat >/dev/null
cat <<'MOCK'
## Mock Review

- P2 \`apps/example.py:10-12\` 예시 이슈: 로컬 스모크 테스트용 출력입니다.
MOCK
EOF

  chmod +x "${capture_bin}"
  printf '%s\n' "${capture_bin}"
}

setup_capture_codex_bin() {
  local case_dir="$1"
  local capture_file="${case_dir}/codex_invocation.txt"
  local capture_bin="${case_dir}/capture_codex.sh"

  cat > "${capture_bin}" <<EOF
#!/bin/bash
set -euo pipefail

if [ "\${1:-}" = "--version" ]; then
  echo "codex-cli ${EXPECTED_CODEX_VERSION}"
  exit 0
fi

printf '%s\n' "\$@" > "${capture_file}"

output_file=""
while [ "\$#" -gt 0 ]; do
  case "\$1" in
    -o|--output-last-message)
      output_file="\$2"
      shift 2
      ;;
    -m|--model|--reasoning-effort|-C|--cd|-c|--config)
      shift 2
      ;;
    exec|--full-auto|--skip-git-repo-check|--ephemeral|--json|--dangerously-bypass-approvals-and-sandbox|--)
      shift
      ;;
    -)
      shift
      ;;
    *)
      shift
      ;;
  esac
done

if [ -z "\${output_file}" ]; then
  echo "capture_codex requires -o <file>" >&2
  exit 2
fi

cat >/dev/null
cat > "\${output_file}" <<'MOCK'
## Mock Review

- P2 \`apps/example.py:10-12\` 예시 이슈: 로컬 스모크 테스트용 출력입니다.
MOCK
EOF

  chmod +x "${capture_bin}"
  printf '%s\n' "${capture_bin}"
}

run_case() {
  local label="$1"
  local case_dir="${TMP_DIR}/$(echo "${label}" | tr -c 'a-zA-Z0-9' '_')"
  mkdir -p "${case_dir}"
  setup_fixtures "${case_dir}"

  (
    cd "${case_dir}"
    ACTION_DIR="${ROOT_DIR}" \
    WORKDIR="${case_dir}" \
    PROVIDER="openai" \
    CODEX_BIN="${CODEX_BIN}" \
    OPENAI_API_KEY="${OPENAI_API_KEY:-mock-key}" \
    PYTHON_BIN="python3" \
    MODEL="gpt-5-mini" \
    LANGUAGE="korean" \
    TRIGGER_LABEL="${label}" \
    DEFAULT_LABEL="codex-review" \
    SPEC_LABEL="codex-review" \
    PERFSEC_LABEL="codex-review-perf" \
    BUG_LABEL="codex-review-bug" \
    HIGH_LABEL="codex-review-high" \
    PR_NUMBER="334" \
    SKIP_REMOTE_CONTEXT="true" \
    "${ROOT_DIR}/scripts/run_review.sh"
  )

  test -s "${case_dir}/review.md"
  grep -q "Mock Review\|P[0-3]" "${case_dir}/review.md"
}

run_claude_case() {
  local label="$1"
  local case_dir="${TMP_DIR}/claude_$(echo "${label}" | tr -c 'a-zA-Z0-9' '_')"
  mkdir -p "${case_dir}"
  setup_fixtures "${case_dir}"

  (
    cd "${case_dir}"
    ACTION_DIR="${ROOT_DIR}" \
    WORKDIR="${case_dir}" \
    PROVIDER="claude" \
    ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-mock-key}" \
    CLAUDE_BIN="${CLAUDE_BIN}" \
    PYTHON_BIN="python3" \
    MODEL="claude-opus-4-6" \
    LANGUAGE="korean" \
    TRIGGER_LABEL="${label}" \
    DEFAULT_LABEL="codex-review" \
    SPEC_LABEL="codex-review" \
    PERFSEC_LABEL="codex-review-perf" \
    BUG_LABEL="codex-review-bug" \
    HIGH_LABEL="codex-review-high" \
    PR_NUMBER="334" \
    SKIP_REMOTE_CONTEXT="true" \
    "${ROOT_DIR}/scripts/run_review.sh"
  )

  test -s "${case_dir}/review.md"
  grep -q "Mock Review\|P[0-3]" "${case_dir}/review.md"
}

run_default_claude_case() {
  local case_dir="${TMP_DIR}/default_claude"
  local capture_bin
  mkdir -p "${case_dir}"
  setup_fixtures "${case_dir}"
  capture_bin="$(setup_capture_claude_bin "${case_dir}")"

  (
    cd "${case_dir}"
    ACTION_DIR="${ROOT_DIR}" \
    WORKDIR="${case_dir}" \
    ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-mock-key}" \
    CLAUDE_BIN="${capture_bin}" \
    PYTHON_BIN="python3" \
    LANGUAGE="korean" \
    TRIGGER_LABEL="codex-review" \
    DEFAULT_LABEL="codex-review" \
    SPEC_LABEL="codex-review" \
    PERFSEC_LABEL="codex-review-perf" \
    BUG_LABEL="codex-review-bug" \
    HIGH_LABEL="codex-review-high" \
    PR_NUMBER="334" \
    SKIP_REMOTE_CONTEXT="true" \
    "${ROOT_DIR}/scripts/run_review.sh"
  )

  test -s "${case_dir}/review.md"
  grep -q -- "--model" "${case_dir}/claude_invocation.txt"
  grep -q -- "claude-opus-4-6" "${case_dir}/claude_invocation.txt"
  grep -q -- "--effort" "${case_dir}/claude_invocation.txt"
  grep -q -- "high" "${case_dir}/claude_invocation.txt"
}

run_openai_provider_case() {
  local case_dir="${TMP_DIR}/openai_provider"
  local capture_bin
  mkdir -p "${case_dir}"
  setup_fixtures "${case_dir}"
  capture_bin="$(setup_capture_codex_bin "${case_dir}")"

  (
    cd "${case_dir}"
    ACTION_DIR="${ROOT_DIR}" \
    WORKDIR="${case_dir}" \
    PROVIDER="openai" \
    MODEL="claude-opus-4-6" \
    OPENAI_API_KEY="${OPENAI_API_KEY:-mock-key}" \
    CODEX_BIN="${capture_bin}" \
    PYTHON_BIN="python3" \
    LANGUAGE="korean" \
    TRIGGER_LABEL="codex-review" \
    DEFAULT_LABEL="codex-review" \
    SPEC_LABEL="codex-review" \
    PERFSEC_LABEL="codex-review-perf" \
    BUG_LABEL="codex-review-bug" \
    HIGH_LABEL="codex-review-high" \
    PR_NUMBER="334" \
    SKIP_REMOTE_CONTEXT="true" \
    "${ROOT_DIR}/scripts/run_review.sh"
  )

  test -s "${case_dir}/review.md"
  grep -q -- "-m" "${case_dir}/codex_invocation.txt"
  grep -q -- "gpt-5-mini" "${case_dir}/codex_invocation.txt"
}

if [ "${MODE}" != "--live-claude" ]; then
  run_case "codex-review"
  run_case "codex-review-perf"
  run_case "codex-review-bug"
  run_case "codex-review-high"
  run_openai_provider_case
  echo "openai smoke test passed"
fi

if [ "${MODE}" != "--live" ]; then
  run_default_claude_case
  run_claude_case "codex-review"
  run_claude_case "codex-review-high"
  echo "claude smoke test passed"
fi

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s "${ROOT_DIR}/scripts" \
  -p 'test_*.py'

echo "local smoke test passed (mode=${MODE})"
