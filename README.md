# Codex Reviewer

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Codex%20Reviewer-brightgreen.svg?colorA=24292e&colorB=0366d6)](https://github.com/marketplace/actions/codex-reviewer)

An automated GitHub Action that reviews pull requests and provides AI-powered code feedback. It leverages OpenAI's powerful models to generate summaries, improvement suggestions, and detect potential bugs in your PRs.

## Key Features

- 💬 **PR Summary**: Clearly explains what the PR does and its purpose
- 🔍 **Code Review**: Provides suggestions to improve code quality
- 🐛 **Bug Detection**: Identifies potential issues and bugs
- 🌎 **Multilingual Support**: Generate reviews in multiple languages

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
```

### Input Parameters

| Input | Description | Required | Default |
|------|------|:----:|--------|
| `github_token` | GitHub token | ✅ | |
| `openai_api_key` | OpenAI API Key | ✅ | |
| `label` | Review trigger label | ✅ | `codex-review` |
| `model` | OpenAI model to use | ❌ | `o4-mini` |
| `language` | Review language | ❌ | `english` |
| `custom_prompt` | Custom review prompt | ❌ | |

## How It Works

1. The action is triggered when a PR is labeled with the specified label (default: `codex-review`).
2. It analyzes the code changes in the PR.
3. Using an OpenAI model, it generates a comprehensive code review.
4. The review is automatically posted as a comment on the PR.

## License

MIT

## Contributing

Issues and pull requests are welcome! Help us improve this action.
