![Demo](assets/demo.gif)

# AI PR Reviewer

A GitHub Action that reviews pull requests with AI — flags bugs, security issues, and complexity hotspots as inline PR comments.

[![Review PRs](https://img.shields.io/github/actions/workflow/status/rid325/ai-pr-reviewer/review.yml?label=review)](https://github.com/rid325/ai-pr-reviewer/actions/workflows/review.yml)
[![License: MIT](https://img.shields.io/github/license/rid325/ai-pr-reviewer)](LICENSE)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)

## What it does

- **Null pointer / missing checks** — catches dereferences and division-by-zero when guards are absent from the diff
- **Hardcoded secrets** — flags API keys, passwords, and tokens committed as string literals
- **SQL injection patterns** — detects string-concatenated queries instead of parameterized statements
- **Performance hotspots** — surfaces nested loops and other O(n²) patterns in changed code
- **Actionable fixes** — posts GitHub suggestion blocks you can apply in one click

## Setup

1. Add a `GEMINI_API_KEY` secret to your repository (**Settings → Secrets and variables → Actions**).
2. Create `.github/workflows/ai-review.yml` in your repo:

```yaml
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: AI Code Review
        uses: rid325/ai-pr-reviewer@v1.0.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
```

3. Open a pull request — the workflow runs automatically.
4. Wait ~30 seconds for inline comments and a summary to appear on the PR.
5. Merge the suggested fixes or dismiss false positives.

## Configuration

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `github_token` | Yes | — | GitHub token with `pull-requests: write` permission |
| `gemini_api_key` | Yes | — | Google Gemini API key |
| `ignore_patterns` | No | `*.lock,package-lock.json,*.generated.*` | Comma-separated [fnmatch](https://docs.python.org/3/library/fnmatch.html) patterns for files to skip |
| `max_diff_lines` | No | `500` | Max added/removed lines per Gemini call; larger diffs are split into chunks |

Example with all options:

```yaml
- uses: rid325/ai-pr-reviewer@v1.0.0
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
    ignore_patterns: '*.lock,*.generated.js,migrations/*'
    max_diff_lines: 500
```

## How it works

```
PR opened
    │
    ▼
workflow triggers (review.yml)
    │
    ▼
fetch diff via GitHub API
    │
    ▼
filter ignored files → sort by size → chunk if needed
    │
    ▼
Gemini API (one call per chunk)
    │
    ▼
parse JSON review results
    │
    ▼
post inline comments + PR summary
```

## Limitations

- **Max diff size:** Files with more than ~300 changed lines may not include a patch from the GitHub API and are skipped with a warning. Larger diffs are chunked at `max_diff_lines` (default 500) across multiple Gemini calls.
- **Languages:** Works best with Python, JavaScript/TypeScript, Go, and Java. Shell, YAML, and config files often produce noise.
- **False positives:** Expect roughly 10–20% false positives on stylistic or context-dependent findings. The bot only sees the diff, not full repo context.
- **Rate limits:** Very large PRs (50+ files) may take several minutes due to sequential Gemini calls.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
