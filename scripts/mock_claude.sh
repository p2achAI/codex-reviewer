#!/bin/bash
set -euo pipefail

if [ "${1:-}" = "--version" ] || [ "${1:-}" = "-v" ]; then
  echo "2.1.105 (Claude Code)"
  exit 0
fi

# Parse flags, ignore all of them
while [ "$#" -gt 0 ]; do
  case "$1" in
    -p|--print|--dangerously-skip-permissions)
      shift
      ;;
    --model|--output-format|--permission-mode)
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      # positional prompt argument — ignore
      shift
      ;;
  esac
done

# Consume stdin
cat >/dev/null

# Output mock review to stdout
cat <<'EOF'
## Mock Review

- P2 `apps/example.py:10-12` 예시 이슈: 로컬 스모크 테스트용 출력입니다.
EOF
