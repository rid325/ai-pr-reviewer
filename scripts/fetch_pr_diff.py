import os 
import json 
import requests
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash")

value = os.getenv("GITHUB_REPOSITORY")
token = os.getenv("GITHUB_TOKEN")

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
        "comment": "code improvements"
    }}
]
Severity must be one of: low, medium, high
Do not report speculative issues.
Only report issues you can justify from the diff.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside of json.
If no issues are found, return an empty JSON array [].
"""

final_prompt = reviewer_prompt + "\n\n" + all_diffs

print("Sending diffs to Gemini...")
try:
    response = model.generate_content(
        final_prompt,
        generation_config={
            "response_mime_type": "application/json"
        }
    )
    
    # Step 7: Parse the JSON response safely
    review_json = json.loads(response.text)
    
    print("\n" + "=" * 60)
    print("AI CODE REVIEW COMMENTS")
    print("=" * 60)
    print(json.dumps(review_json, indent=2))
    
except json.JSONDecodeError:
    print("Error: Gemini returned invalid JSON.")
    print("Raw response:")
    print(response.text)
except Exception as e:
    print(f"An error occurred while calling Gemini: {e}")
