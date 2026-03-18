#!/bin/bash
set -euo pipefail

if [ "${1:-}" = "--version" ]; then
  echo "codex-cli 0.115.0-alpha.27"
  exit 0
fi

if [ "${1:-}" != "exec" ]; then
  echo "mock_codex only supports 'exec'" >&2
  exit 2
fi
shift

output_file=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o|--output-last-message)
      output_file="$2"
      shift 2
      ;;
    -m|--model|-C|--cd|-c|--config)
      shift 2
      ;;
    --full-auto|--skip-git-repo-check|--ephemeral|--json|--dangerously-bypass-approvals-and-sandbox|--)
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

if [ -z "${output_file}" ]; then
  echo "mock_codex requires -o <file>" >&2
  exit 2
fi

cat >/dev/null

cat > "${output_file}" <<'EOF'
## Mock Review

- P2 `apps/example.py:10-12` 예시 이슈: 로컬 스모크 테스트용 출력입니다.
EOF
