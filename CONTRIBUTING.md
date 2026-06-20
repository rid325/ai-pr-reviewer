# Contributing to AI PR Reviewer

Thanks for helping improve this project. Keep PRs focused and small.

## Local development setup

1. Clone the repo and install dependencies:

```bash
git clone https://github.com/rid325/ai-pr-reviewer.git
cd ai-pr-reviewer
pip install -r requirements.txt
```

2. Set the required environment variables:

```bash
export INPUT_GITHUB_TOKEN="ghp_..."
export INPUT_GEMINI_API_KEY="..."
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_EVENT_PATH="./test-event.json"
export INPUT_IGNORE_PATTERNS="*.lock,package-lock.json"
export INPUT_MAX_DIFF_LINES="500"
```

3. Create a `test-event.json` from a real PR webhook payload (or copy the `pull_request` object from a GitHub delivery log). At minimum it needs:

```json
{ "pull_request": { "number": 42 } }
```

4. Run the reviewer locally without triggering the full Action:

```bash
python scripts/fetch_pr_diff.py
```

Use a draft PR in your fork so you can test against a real diff without spamming production repos.

## How to test

Open a **draft PR** in this repo (or your fork) with intentional test bugs. The workflow in `.github/workflows/review.yml` runs on `opened` and `synchronize`. Draft PRs still trigger the workflow, but reviewers are less likely to be notified.

To avoid posting comments while iterating, temporarily comment out the GitHub posting block in `fetch_pr_diff.py` or point `GITHUB_REPOSITORY` at a private test repo.

## Adding support for a new LLM

The Gemini API call is located in `scripts/fetch_pr_diff.py` where `client.models.generate_content(...)` is called. To swap providers (OpenAI, Claude, etc.):

1. Replace the Google `genai.Client` setup with your provider client setup at the top of the file.
2. Update the prompt generation and model API call block to use your provider's SDK.
3. Ensure your provider client returns a response in the same JSON array schema, using JSON mode or equivalent structured output.

The rest of the pipeline (diff fetching, chunking, comment posting) is provider-agnostic.

## Commit message format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `refactor:` code change that neither fixes a bug nor adds a feature

Example: `feat: add ignore_patterns input for fnmatch filtering`

## Opening issues

Include:

- **Repo language/stack** (e.g. Python 3.10, Node 20)
- **Diff size** (files changed, approximate lines)
- **What the bot said** (copy the comment or summary)
- **What it should have said** (expected behavior)
- **Action logs** (relevant lines showing skipped files or chunk counts)

Screenshots of inline comments help a lot.
