import os 
import json 
import requests
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("INPUT_GEMINI_API_KEY"))

value = os.getenv("GITHUB_REPOSITORY")
token = os.getenv("INPUT_GITHUB_TOKEN")

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

all_diffs = ""
total_chars = 0

for file in files:
    filename = file["filename"]
    if filename.endswith(".lock") or ".generated" in filename or filename == "package-lock.json":
        print(f"Skipping {filename}")
        continue
    patch = file.get("patch")
    if not patch:
        print(f"No patch available for {filename}")
        continue

    if total_chars + len(patch) > 30000:
        print("\nDiff length limit reached, skipping remaining files.")
        break
    total_chars += len(patch)
    all_diffs += f"\n=== {filename} ===\n{patch}"

if not all_diffs:
    print("No valid diffs to review.")
    exit(0)

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

final_prompt = reviewer_prompt + "\n\n" + all_diffs

print("Sending diffs to Gemini...")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=final_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    
    review_json = json.loads(response.text)
    if not review_json:    
        print("No issues found in the PR.")
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
    
    if review_response.status_code == 200:
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
        
        if fallback_response.status_code == 200:
            print("Successfully posted fallback general review!")
        else:
            print(f"Failed to post fallback review. Status code: {fallback_response.status_code}")
            print(fallback_response.text)
            
    else:
        print(f"Failed to post review. Status code: {review_response.status_code}")
        print("GitHub API Response:")
        print(review_response.text)

except json.JSONDecodeError:
    print("Error: Gemini returned invalid JSON.")
    print("Raw response:")
    print(response.text)
except Exception as e:
    print(f"An error occurred while calling Gemini or GitHub: {e}")


