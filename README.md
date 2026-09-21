# Codex Reviewer

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Codex%20Reviewer-brightgreen.svg?colorA=24292e&colorB=0366d6)](https://github.com/marketplace/actions/codex-reviewer)

An automated GitHub Action that reviews pull requests and provides AI-powered code feedback. It supports both Claude and OpenAI models to generate summaries, improvement suggestions, and detect potential bugs in your PRs.

## Key Features

- 💬 **PR Summary**: Clearly explains what the PR does and its purpose
- 🔍 **Code Review**: Provides suggestions to improve code quality
- 🐛 **Bug Detection**: Identifies potential issues and bugs
- 🌎 **Multilingual Support**: Generate reviews in multiple languages
- 🎯 **Single-Agent Review**: At most one review attempt per PR across all labels and commits
- 📋 **Spec Compliance**: Optional ClickUp spec agent checks alignment with planned requirements

## Usage

### Basic Setup

For organization repositories, call the reusable workflow. It centralizes the
runner, permissions, trigger filtering, and composite action implementation:

```yaml
name: Codex PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review, labeled]

permissions: {}

jobs:
  codex_review:
    permissions:
      contents: read
      pull-requests: write
    uses: p2achAI/codex-reviewer/.github/workflows/review.yml@<release-commit-sha>
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      CLICKUP_API_TOKEN: ${{ secrets.CLICKUP_API_TOKEN }}
      CLICKUP_TEAM_ID: ${{ secrets.CLICKUP_TEAM_ID }}
```

Use the full commit SHA behind a release, not a mutable tag. Enable Dependabot
for `github-actions` in each consumer repository so these immutable references
are updated by reviewable pull requests instead of manual edits:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

The reusable workflow automatically reviews non-draft PRs on `opened` and
`ready_for_review`. The exact labels `codex-review`, `codex-review-perf`,
`codex-review-bug`, and `codex-review-high` trigger explicit review modes.
`synchronize` and `reopened` keep the check current without generating a new
review. Fork pull requests never run on the self-hosted reviewer.

Use the composite action directly only when a repository needs a custom runner
or trigger policy. Direct consumers must pin this repository and every nested
action to full commit SHAs.

### PR당 1회 비용 제한

모든 provider와 리뷰 모드를 합쳐 PR당 최초 1회만 실행합니다. 모델 호출 전에
PR 댓글에 실행권 사용 기록을 저장하므로 실패·취소·새 커밋·라벨 재부착·Actions
재실행도 추가 리뷰를 실행하지 않습니다. 조회/기록 API 오류 시 호출하지 않습니다.
기록 댓글을 삭제/수정하면 제한이 해제될 수 있으므로 보존해야 합니다.
도입 이전의 마커 없는 리뷰는 소급 집계하지 않습니다. 한 번의 리뷰 안에서 발생하는
여러 모델 요청이나 토큰 비용 자체를 제한하는 기능은 아닙니다.

재사용 workflow에는 직렬화가 포함되어 있습니다. **composite action 직접 호출자는
모두 같은 PR 단위 concurrency를 반드시 설정해야 합니다.** 댓글 확인/작성 자체는
원자적 잠금이 아니므로 이 설정 없이 동시에 호출하면 1회 제한을 보장하지 못합니다.
SHA·리뷰 모드·workflow 이름을 group에 추가하지 마세요.

```yaml
jobs:
  codex_review:
    concurrency:
      group: codex-review-${{ github.repository }}-${{ github.event.pull_request.number }}
      cancel-in-progress: false
    # runs-on, permissions, steps ...
```

새 action 릴리스를 사용하도록 호출 저장소의 `uses` 참조도 함께 갱신해야 합니다.

### Input Parameters

| Input | Description | Required | Default |
|------|------|:----:|--------|
| `github_token` | GitHub token | ✅ | |
| `provider` | AI provider (`claude` or `openai`) | ❌ | `claude` |
| `anthropic_api_key` | Anthropic API Key | Claude 사용 시 필요 | |
| `openai_api_key` | OpenAI API Key | OpenAI 사용 시 필요 | |
| `label` | Review trigger label | ✅ | `codex-review` |
| `spec_label` | Label for spec+tests review | ❌ | `codex-review` |
| `perfsec_label` | Label for performance/security review | ❌ | `codex-review-perf` |
| `bug_label` | Label for correctness/bug review | ❌ | `codex-review-bug` |
| `model` | Review model to use | ❌ | `claude-opus-4-6` |
| `effort` | Claude Code effort level (`low`, `medium`, `high`, `xhigh`, `max`) | ❌ | `high` |
| `codex_version` | Pinned `@openai/codex` version installed in GitHub Actions | ❌ | `0.115.0-alpha.27` |
| `claude_code_version` | Pinned `@anthropic-ai/claude-code` version installed in GitHub Actions | ❌ | `2.1.150` |
| `language` | Review language | ❌ | `english` |
| `custom_prompt` | Custom review prompt | ❌ | |
| `enable_multi_agent` | Deprecated. Multi-agent review is no longer used | ❌ | `false` |
| `agents_path` | Deprecated. Multi-agent config path is no longer used | ❌ | `agents.json` |
| `clickup_api_token` | ClickUp API token for spec agent | ❌ | |
| `clickup_url` | ClickUp task URL for spec agent | ❌ | |
| `clickup_team_id` | ClickUp team/workspace ID (for custom task IDs) | ❌ | |
| `clickup_custom_task_ids` | Use custom task IDs (`true`/`false`) | ❌ | `false` |
| `spec_source` | Spec URL source (`input`, `comment`, `auto`) | ❌ | `auto` |
| `spec_comment_marker` | Marker used to find spec URL in PR comments | ❌ | `SPEC:` |

## How It Works

1. The action is triggered when a PR is labeled with the specified label (default: `codex-review`).
2. It analyzes the code changes in the PR.
3. Using the configured AI provider and model, it generates a comprehensive code review.
4. The review is automatically posted as a comment on the PR.

### Local Smoke Test

로컬에서도 액션과 같은 리뷰 경로를 검증할 수 있습니다.

```bash
bash ./scripts/local_smoke_test.sh
```

- 기본 모드에서는 mock Codex/Claude 바이너리를 사용하므로 API 키 없이도 실행됩니다.
- 실제 Codex까지 포함해 확인하려면 `OPENAI_API_KEY`를 설정한 뒤 `bash ./scripts/local_smoke_test.sh --live` 를 실행하세요.
- 실제 Claude Code까지 포함해 확인하려면 `ANTHROPIC_API_KEY`를 설정한 뒤 `bash ./scripts/local_smoke_test.sh --live-claude` 를 실행하세요.
- 현재 고정 버전은 `@anthropic-ai/claude-code@2.1.150`, `@openai/codex@0.115.0-alpha.27` 입니다.
- GitHub Actions에서는 중첩 샌드박스 오류를 피하기 위해 `--dangerously-bypass-approvals-and-sandbox` 로 실행합니다. 러너 자체가 격리 환경이므로 CI에서만 이 모드를 사용합니다.

### Label-based Review Modes

- `spec_label` (default `codex-review`): runs the **Spec + Tests** review prompt
- `perfsec_label` (default `codex-review-perf`): runs the **Performance/Security** review prompt
- `bug_label` (default `codex-review-bug`): runs the **Correctness/Bug** review prompt

All built-in review modes apply the same blocking-severity contract. P0-P2
findings must identify a concrete trigger, affected execution path, and
incorrect observable outcome. Suggestions about readability, type hints,
comments, defensive cleanup, or micro-optimization are P3 at most, and are
omitted when they are not actionable. The reviewer also self-audits blocking
findings before returning the final review.

### Spec Compliance (ClickUp)

If `clickup_api_token` is provided, the action can fetch a ClickUp task and compare the PR with the planned requirements. You can pass the ClickUp task URL via `clickup_url` input, or add a PR comment like:

```
SPEC: https://app.clickup.com/t/ABC-123
```

Note: ClickUp Docs content is not currently accessible via the public API, so the spec agent expects a ClickUp task URL (or a summary in PR comments).
If the URL follows `https://app.clickup.com/t/{workspace_id}/{task_id_or_custom}`, the fetcher will infer the workspace ID and automatically enable custom task IDs when the ID is non-numeric. You can still force behavior with `clickup_team_id` and `clickup_custom_task_ids`.

The action also scans PR comments for ClickUp links without a marker. For example:

```
Task linked: [PR-1588 Wifi 대시보드 기술 기획](https://app.clickup.com/t/9014951824/PR-1588)
```

PR 코멘트 전문은 `comments.md`로 저장되며, 단일 리뷰 프롬프트의 참고 컨텍스트로 사용됩니다.
PR 설명은 `pr_description.md`로 저장되어 해당 라벨의 리뷰 프롬프트가 함께 참고합니다.

## License

MIT

## Contributing

Issues and pull requests are welcome! Help us improve this action.

### Amazon Bedrock (Codex CLI)

AWS credentials must be configured before this action. OpenAI and Anthropic API
keys are not needed for this provider:

```yaml
with:
  github_token: ${{ secrets.GITHUB_TOKEN }}
  provider: bedrock
  model: global.openai.gpt-5.6-terra
  effort: medium
  aws_region: ap-northeast-2
```

Uses Codex CLI 0.155.1 with `amazon-bedrock-runtime`, not the Mantle provider
`amazon-bedrock`. The Runtime provider was verified in Seoul with the existing
GitHub IAM credentials. The global inference profile does not guarantee that
inference stays in Seoul. High-review labels preserve the configured Bedrock
model and effort. Provider errors fail without falling back to a direct API.

Provider regression tests: `python3 scripts/test_bedrock_provider.py`.
