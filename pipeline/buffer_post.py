"""Send Buffer API calls through the repo's GitHub Action (branch `buffer`), which holds the BUFFER_API_KEY secret.

  python3 buffer_post.py schedule POSTS.json      -> create YouTube posts, print result
  python3 buffer_post.py list FROM_ISO TO_ISO     -> list scheduled/sent posts between two UTC times
  python3 buffer_post.py delete POST_ID           -> delete one post

POSTS.json: [{"url": "...mp4", "title": "...", "text": "description", "due_ist": "2026-11-18 14:37", "thumb": optional}]
The Action writes its answer to branch `buffer-result`; this script waits for it (up to ~6 min).
"""
import json, os, subprocess, sys, tempfile, time, datetime, uuid

REPO = "https://github.com/amanupputuri/shorts-media.git"
ORG = "6afbdb5edb9ae616ed8a7467"
CHANNEL = "6afbdbb4ece6dfde5ff1432b"  # Wit Wonderland (youtube)
ENV = {k: v for k, v in os.environ.items() if k != "GH_TOKEN"}

def git(*a, cwd=None, check=True):
    return subprocess.run(["git", *a], cwd=cwd, env=ENV, check=check, capture_output=True, text=True)

def run_job(steps):
    jid = "job-" + uuid.uuid4().hex[:10]
    d = tempfile.mkdtemp()
    git("clone", "-q", "--depth", "1", "--branch", "buffer", REPO, d)
    json.dump({"id": jid, "steps": steps}, open(os.path.join(d, "job.json"), "w"), indent=1, ensure_ascii=False)
    git("add", "job.json", cwd=d)
    git("-c", "user.name=amanupputuri", "-c", "user.email=amanupputuri@users.noreply.github.com", "commit", "-qm", jid, cwd=d)
    for _ in range(3):
        if git("-c", "push.negotiate=true", "push", "-q", "origin", "buffer", cwd=d, check=False).returncode == 0: break
        git("pull", "-q", "--rebase", "origin", "buffer", cwd=d, check=False)
    for _ in range(45):
        time.sleep(8)
        if git("fetch", "-q", "origin", "buffer-result", cwd=d, check=False).returncode: continue
        r = git("show", "FETCH_HEAD:result.json", cwd=d, check=False).stdout
        try: res = json.loads(r)
        except Exception: continue
        if res.get("job_id") == jid: return res
    return {"error": "timed out waiting for the Buffer Action", "job_id": jid}

CREATE = """mutation($input: CreatePostInput!) { createPost(input: $input) { __typename
  ... on PostActionSuccess { post { id dueAt status } } ... on MutationError { message } } }"""

def to_utc(due_ist):
    t = datetime.datetime.strptime(due_ist, "%Y-%m-%d %H:%M") - datetime.timedelta(hours=5, minutes=30)
    return t.strftime("%Y-%m-%dT%H:%M:00.000Z")

def schedule(posts):
    steps = []
    for p in posts:
        vid = {"url": p["url"]}
        if p.get("thumb"): vid["thumbnailUrl"] = p["thumb"]
        steps.append({"name": p["title"], "query": CREATE, "variables": {"input": {
            "channelId": CHANNEL, "schedulingType": "automatic", "mode": "customScheduled", "dueAt": to_utc(p["due_ist"]),
            "needsApproval": False, "text": p["text"], "assets": [{"video": vid}],
            "metadata": {"youtube": {"title": p["title"][:100], "privacy": "public", "categoryId": "27", "madeForKids": False,
                                     "notifySubscribers": True, "license": "youtube", "embeddable": True, "isAiGenerated": False}}}}})
    return run_job(steps)

def list_posts(a, b):
    q = """query($i: PostsInput!) { posts(first: 50, input: $i) { edges { node { id dueAt status text } } } }"""
    return run_job([{"name": "posts", "query": q, "variables": {"i": {"organizationId": ORG, "filter": {"channelIds": [CHANNEL],
                    "dueAt": {"start": a, "end": b}}}}}])

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "schedule": out = schedule(json.load(open(sys.argv[2])))
    elif cmd == "list": out = list_posts(sys.argv[2], sys.argv[3])
    elif cmd == "delete": out = run_job([{"name": "delete", "query": 'mutation($i: DeletePostInput!) { deletePost(input:$i) { __typename ... on MutationError { message } } }', "variables": {"i": {"id": sys.argv[2]}}}])
    else: sys.exit(__doc__)
    print(json.dumps(out, indent=1, ensure_ascii=False))
