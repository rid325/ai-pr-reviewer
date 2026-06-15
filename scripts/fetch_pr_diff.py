import os 
import json 

value= os.getenv("GITHUB_REPOSITORY")

owner, repo = value.split("/")

event_path= os.getenv("GITHUB_EVENT_PATH")

with open(event_path) as f:
    event = json.load(f)

pr_number=event["pull_request"]["number"]
    
