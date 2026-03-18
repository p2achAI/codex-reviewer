# Codex Reviewer

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Codex%20Reviewer-brightgreen.svg?colorA=24292e&colorB=0366d6)](https://github.com/marketplace/actions/codex-reviewer)

An automated GitHub Action that reviews pull requests and provides AI-powered code feedback. It leverages OpenAI's powerful models to generate summaries, improvement suggestions, and detect potential bugs in your PRs.

## Key Features

- 💬 **PR Summary**: Clearly explains what the PR does and its purpose
- 🔍 **Code Review**: Provides suggestions to improve code quality
- 🐛 **Bug Detection**: Identifies potential issues and bugs
- 🌎 **Multilingual Support**: Generate reviews in multiple languages
- 🎯 **Single-Agent Review**: One review prompt runs per label and writes a single PR comment
- 📋 **Spec Compliance**: Optional ClickUp spec agent checks alignment with planned requirements

## Usage

### Basic Setup

Create a workflow file in your repository's `.github/workflows` directory:

```yaml
name: Codex PR Review

on:
  pull_request:
    types: [labeled] # add synchronize if you want to trigger the action when the PR is synchronized

jobs:
  review:
    permissions:
      contents: read
      pull-requests: write
      issues: write
    runs-on: ubuntu-latest
    if: github.event.label.name == 'codex-review'
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
      - uses: p2achAI/codex-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          label: 'codex-review'
          model: "o4-mini"
          language: "korean"
          custom_prompt: "Please review the code"
          clickup_api_token: ${{ secrets.CLICKUP_API_TOKEN }}
          clickup_url: "https://app.clickup.com/t/ABC-123"
          clickup_team_id: "90144302619"
          clickup_custom_task_ids: "true"
          spec_comment_marker: "SPEC:"
```

### Input Parameters

| Input | Description | Required | Default |
|------|------|:----:|--------|
| `github_token` | GitHub token | ✅ | |
| `openai_api_key` | OpenAI API Key | ✅ | |
| `label` | Review trigger label | ✅ | `codex-review` |
| `spec_label` | Label for spec+tests review | ❌ | `codex-review` |
| `perfsec_label` | Label for performance/security review | ❌ | `codex-review-perf` |
| `bug_label` | Label for correctness/bug review | ❌ | `codex-review-bug` |
| `model` | OpenAI model to use | ❌ | `codex-mini-latest` |
| `codex_version` | Pinned `@openai/codex` version installed in GitHub Actions | ❌ | `0.115.0-alpha.27` |
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
3. Using an OpenAI model, it generates a comprehensive code review.
4. The review is automatically posted as a comment on the PR.

### Local Smoke Test

로컬에서도 액션과 같은 리뷰 경로를 검증할 수 있습니다.

```bash
bash ./scripts/local_smoke_test.sh
```

- 기본값은 `scripts/mock_codex.sh`를 사용하므로 API 키 없이도 실행됩니다.
- 실제 Codex까지 포함해 확인하려면 `OPENAI_API_KEY`를 설정한 뒤 `bash ./scripts/local_smoke_test.sh --live` 를 실행하세요.
- 현재 고정 버전은 `@openai/codex@0.115.0-alpha.27` 입니다.
- GitHub Actions에서는 중첩 샌드박스 오류를 피하기 위해 `--dangerously-bypass-approvals-and-sandbox` 로 실행합니다. 러너 자체가 격리 환경이므로 CI에서만 이 모드를 사용합니다.

### Label-based Review Modes

- `spec_label` (default `codex-review`): runs the **Spec + Tests** review prompt
- `perfsec_label` (default `codex-review-perf`): runs the **Performance/Security** review prompt
- `bug_label` (default `codex-review-bug`): runs the **Correctness/Bug** review prompt

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
