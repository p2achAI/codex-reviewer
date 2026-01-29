# Codex Reviewer

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Codex%20Reviewer-brightgreen.svg?colorA=24292e&colorB=0366d6)](https://github.com/marketplace/actions/codex-reviewer)

An automated GitHub Action that reviews pull requests and provides AI-powered code feedback. It leverages OpenAI's powerful models to generate summaries, improvement suggestions, and detect potential bugs in your PRs.

## Key Features

- 💬 **PR Summary**: Clearly explains what the PR does and its purpose
- 🔍 **Code Review**: Provides suggestions to improve code quality
- 🐛 **Bug Detection**: Identifies potential issues and bugs
- 🌎 **Multilingual Support**: Generate reviews in multiple languages
- 🧠 **Multi-Agent Review**: Specialized agents review different concerns and aggregate into one PR comment
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
          enable_multi_agent: "true"
          agents_path: "agents.json"
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
| `perfsec_label` | Label for performance/security review | ❌ | `codex-review-spec` |
| `bug_label` | Label for correctness/bug review | ❌ | `codex-review-bug` |
| `model` | OpenAI model to use | ❌ | `codex-mini-latest` |
| `language` | Review language | ❌ | `english` |
| `custom_prompt` | Custom review prompt | ❌ | |
| `enable_multi_agent` | Enable multi-agent review | ❌ | `true` |
| `agents_path` | Path to `agents.json` | ❌ | `agents.json` |
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

### Label-based Agents

- `spec_label` (default `codex-review`): runs **Spec + Tests** agents
- `perfsec_label` (default `codex-review-spec`): runs **Performance/Security** agent
- `bug_label` (default `codex-review-bug`): runs **Correctness/Bug** agent

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

PR 코멘트 전문은 `comments.md`로 저장되며, 에이전트들이 참고 컨텍스트로 사용할 수 있습니다.
PR 설명은 `pr_description.md`로 저장되어 기획문서 준수 에이전트가 함께 참고합니다.

## License

MIT

## Contributing

Issues and pull requests are welcome! Help us improve this action.
