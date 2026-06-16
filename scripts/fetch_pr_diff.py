import os 
import json 
import requests

value= os.getenv("GITHUB_REPOSITORY")
token= os.getenv("GITHUB_TOKEN")

owner, repo = value.split("/")

event_path= os.getenv("GITHUB_EVENT_PATH")

with open(event_path) as f:
    event = json.load(f)

pr_number=event["pull_request"]["number"]

url=f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

headers={
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

response = requests.get(url, headers=headers)
response.raise_for_status()
files= response.json()


for file in files:
    filename= file["filename"]
    if (filename.endswith(".lock") or (".generated" in filename) or filename=="package-lock.json" ):
        print(f"Skipping {filename}")
        continue
    patch=file.get("patch")
    if not patch:
        print(f"No patch available for {filename}")
        continue
    if patch:
        print(f"\n=== {filename} ===")
        print(patch)

    
    
 
