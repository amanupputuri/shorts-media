"""Runs Buffer GraphQL calls listed in job.json. Never prints the API key."""
import json, os, sys, urllib.request

KEY = os.environ.get("BUFFER_API_KEY", "")

def gql(query, variables=None):
    req = urllib.request.Request("https://api.buffer.com", method="POST",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode()[:3000]}

job = json.load(open(sys.argv[1])); out = {"job_id": job.get("id"), "key_present": bool(KEY), "steps": []}
for st in job["steps"]:
    out["steps"].append({"name": st.get("name"), "result": gql(st["query"], st.get("variables"))})
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
