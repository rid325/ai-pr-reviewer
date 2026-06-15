import os
import json


print("=" * 60)
print("GITHUB ENVIRONMENT VARIABLES")
print("=" * 60)

for key, value in sorted(os.environ.items()):
    if key.startswith("GITHUB_"):
        print(f"{key} = {value}")


print("\n" + "=" * 60)
print("FULL EVENT PAYLOAD (from GITHUB_EVENT_PATH)")
print("=" * 60)

event_path = os.environ.get("GITHUB_EVENT_PATH")
if event_path:
    with open(event_path, "r") as f:
        event = json.load(f)
    print(json.dumps(event, indent=2))
else:
    print("GITHUB_EVENT_PATH not set — are you running outside of GitHub Actions?")


print("\n" + "=" * 60)
print("KEY PR DETAILS")
print("=" * 60)

if event_path and "pull_request" in event:
    pr = event["pull_request"]
    print(f"PR Number : #{pr.get('number')}")
    print(f"Title     : {pr.get('title')}")
    print(f"Author    : {pr['user'].get('login')}")
    print(f"Base      : {pr['base'].get('ref')}")
    print(f"Head      : {pr['head'].get('ref')}")
    print(f"Body      : {pr.get('body') or '(no description)'}")
else:
    print("No pull_request data found in event payload.")
