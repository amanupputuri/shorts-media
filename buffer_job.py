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
BLOCK_DATES = ("2026-11-16T18:3", "2026-11-16T18:4", "2026-11-16T18:5", "2026-11-16T19", "2026-11-16T2", "2026-11-17T0", "2026-11-17T1")  # 17 Nov IST: stopped by Aman
for st in job["steps"]:
    due = json.dumps(st.get("variables", {}))
    if "createPost" in st["query"] and any('"dueAt": "' + b in due for b in BLOCK_DATES):
        out["steps"].append({"name": st.get("name"), "result": {"data": {"createPost": {"__typename": "MutationError", "message": "Blocked: Aman stopped all 17 Nov videos"}}}})
        continue
    out["steps"].append({"name": st.get("name"), "result": gql(st["query"], st.get("variables"))})
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
