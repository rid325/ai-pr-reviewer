import os 
import json 
import fnmatch
import requests
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("INPUT_GEMINI_API_KEY"))

value = os.getenv("GITHUB_REPOSITORY")
token = os.getenv("INPUT_GITHUB_TOKEN")
max_diff_lines = int(os.getenv("INPUT_MAX_DIFF_LINES", "500"))
ignore_patterns = [p.strip() for p in os.getenv("INPUT_IGNORE_PATTERNS", "").split(",") if p.strip()]

owner, repo = value.split("/")

event_path = os.getenv("GITHUB_EVENT_PATH")

with open(event_path) as f:
    event = json.load(f)

pr_number = event["pull_request"]["number"]

url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

response = requests.get(url, headers=headers)
response.raise_for_status()
files = response.json()

def count_diff_lines(patch):
    count = 0
    for line in patch.splitlines():
        if (line.startswith("+") or line.startswith("-")) and not line.startswith("+++") and not line.startswith("---"):
            count += 1
    return count

skipped_files = []
valid_files = []
total_lines = 0

for file in files:
    filename = file["filename"]
    if ignore_patterns and any(fnmatch.fnmatch(filename, pattern) for pattern in ignore_patterns):
        print(f"Skipping {filename} (matched ignore pattern)")
        continue
    patch = file.get("patch")
    if not patch:
        print(f"WARNING: Skipping {filename} due to size (no patch returned by GitHub API)")
        skipped_files.append(filename)
        continue
    valid_files.append(file)
    total_lines += count_diff_lines(patch)

print(f"Total diff lines (+ and -) in all collected patches: {total_lines}")

# Sort files by changes descending
valid_files.sort(key=lambda f: f.get("changes", 0), reverse=True)

diff_chunks = []
current_chunk = ""
current_line_count = 0

max_total_lines = 4 * max_diff_lines
total_processed_lines = 0

for file in valid_files:
    filename = file["filename"]
    patch = file["patch"]
    file_lines = count_diff_lines(patch)

    if total_processed_lines + file_lines > max_total_lines:
        print(f"WARNING: Skipping {filename} because adding it would exceed the total budget of {max_total_lines} lines.")
        skipped_files.append(filename)
        continue

    total_processed_lines += file_lines
    file_diff = f"\n=== {filename} ===\n{patch}"

    if file_lines > max_diff_lines:
        if current_chunk:
            diff_chunks.append(current_chunk)
            current_chunk = ""
            current_line_count = 0
        lines = patch.splitlines()
        part = ""
        part_lines = 0
        for line in lines:
            is_diff_line = (line.startswith("+") or line.startswith("-")) and not line.startswith("+++") and not line.startswith("---")
            if part_lines + (1 if is_diff_line else 0) > max_diff_lines and part:
                diff_chunks.append(f"\n=== {filename} ===\n{part}")
                part = ""
                part_lines = 0
            part += line + "\n"
            if is_diff_line:
                part_lines += 1
        if part:
            diff_chunks.append(f"\n=== {filename} ===\n{part}")
        continue

    if current_line_count + file_lines > max_diff_lines:
        diff_chunks.append(current_chunk)
        current_chunk = file_diff
        current_line_count = file_lines
    else:
        current_chunk += file_diff
        current_line_count += file_lines

if current_chunk:
    diff_chunks.append(current_chunk)

if not diff_chunks:
    print("No valid diffs to review.")
    exit(0)

if skipped_files:
    print(f"\nWARNING: {len(skipped_files)} file(s) skipped due to size or budget limits:")
    for skipped in skipped_files:
        print(f"  - {skipped}")

print(f"Prepared {len(diff_chunks)} chunk(s) (max {max_diff_lines} diff lines per chunk).")

reviewer_prompt = f"""
You are an expert code reviewer.
You are gonna review bugs, security issues, performance problems, maintainability, missing error handling,
suggest improvements, logic errors and adherence to best practices.

Review the following diff:

For the Output give it as a JSON schema strictly like this example:
[
    {{
        "file": "path/to/file",
        "line": 21,
        "severity": "high",
        "comment": "code improvements",
        "suggestion": "print('this is the fixed code')"
    }}
]
Severity must be one of: low, medium, high
Do not report speculative issues.
Only report issues you can justify from the diff.

If there is a direct, actionable code fix, include it in the "suggestion" field. 
The "suggestion" field must contain ONLY the exact replacement code for that specific line. Do not wrap it in markdown ticks inside the JSON.
If no direct code fix is applicable, omit the "suggestion" field or leave it blank.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside of json.
If no issues are found, return an empty JSON array [].
"""

review_json = []

print("Sending diffs to Gemini...")
try:
    for i, chunk in enumerate(diff_chunks, start=1):
        print(f"Sending chunk {i}/{len(diff_chunks)} to Gemini...")
        final_prompt = reviewer_prompt + "\n\n" + chunk
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=final_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        chunk_reviews = json.loads(response.text)
        if chunk_reviews:
            review_json.extend(chunk_reviews)

    if not review_json:    
        print("No issues found in the PR.")
        summary_body = "### 🤖 AI Review Summary\n\nNo issues found. Estimated review time saved: ~5 mins."
        if skipped_files:
            summary_body += "\n\n**Skipped files (exceeded size or budget limits):**\n"
            for skipped in skipped_files:
                summary_body += f"- `{skipped}`\n"
        comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        requests.post(comment_url, headers=headers, json={"body": summary_body})
        exit(0) 

    github_comments = []
    for review in review_json:
        body_text = f"**[{review.get('severity', 'COMMENT').upper()}]** {review['comment']}"
        if "suggestion" in review and review["suggestion"]:
            body_text += f"\n\n```suggestion\n{review['suggestion']}\n```"

        github_comment = {
            "path": review["file"],
            "line": int(review["line"]), 
            "side": "RIGHT",
            "body": body_text
        }
        github_comments.append(github_comment)

    payload = {
        "event": "COMMENT",
        "comments": github_comments
    }   

    print("\n" + "=" * 60)
    print("AI CODE REVIEW COMMENTS")
    print("=" * 60)
    print(json.dumps(review_json, indent=2))
    
    review_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    print(f"\nPosting review to {review_url}...")
    
    review_response = requests.post(review_url, headers=headers, json=payload)
    
    if review_response.status_code in (200, 201):
        print("Successfully posted inline review!")
    elif review_response.status_code == 422:
        print("GitHub rejected inline comments (422: Line could not be resolved).")
        print("Falling back to a general PR comment...")
        
        fallback_body = "### 🤖 AI Code Review Comments\n\n"
        for comment in github_comments:
            fallback_body += f"**File:** `{comment['path']}` (Line {comment['line']})\n"
            fallback_body += f"{comment['body']}\n\n---\n"
            
        fallback_payload = {
            "body": fallback_body,
            "event": "COMMENT"
        }
        
        fallback_response = requests.post(review_url, headers=headers, json=fallback_payload)
        
        if fallback_response.status_code in (200, 201):
            print("Successfully posted fallback general review!")
        else:
            print(f"Failed to post fallback review. Status code: {fallback_response.status_code}")
            print(fallback_response.text)
            
    else:
        print(f"Failed to post review. Status code: {review_response.status_code}")
        print("GitHub API Response:")
        print(review_response.text)

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for review in review_json:
        sev = review.get("severity", "low").lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    total_issues = sum(severity_counts.values())
    parts = []
    for sev in ("high", "medium", "low"):
        if severity_counts[sev]:
            parts.append(f"{severity_counts[sev]} {sev} severity" if severity_counts[sev] == 1 else f"{severity_counts[sev]} {sev} severities")

    summary_body = f"### 🤖 AI Review Summary\n\n**{total_issues} issue{'s' if total_issues != 1 else ''} found:** "
    summary_body += ", ".join(parts) + ".\n"
    summary_body += f"Estimated review time saved: ~{max(5, total_issues * 5)} mins."
    if len(diff_chunks) > 1:
        summary_body += f"\n\nReviewed diff in {len(diff_chunks)} chunks."
    if skipped_files:
        summary_body += "\n\n**Skipped files (exceeded size or budget limits):**\n"
        for skipped in skipped_files:
            summary_body += f"- `{skipped}`\n"

    comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    print(f"\nPosting summary comment to {comment_url}...")
    summary_response = requests.post(comment_url, headers=headers, json={"body": summary_body})
    if summary_response.status_code in (200, 201):
        print("Successfully posted PR summary comment!")
    else:
        print(f"Failed to post summary comment. Status code: {summary_response.status_code}")
        print(summary_response.text)

except json.JSONDecodeError:
    print("Error: Gemini returned invalid JSON.")
    print("Raw response:")
    print(response.text)
except Exception as e:
    print(f"An error occurred while calling Gemini or GitHub: {e}")
