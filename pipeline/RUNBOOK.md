# Wit Wonderland — daily puzzle run

Every day this run makes **4 vertical Shorts + 1 horizontal 20-puzzle video** for the YouTube channel
Wit Wonderland and schedules them in Metricool. Work unattended: never stop to ask questions; if a step fails,
retry once, skip that video, and carry on. Report at the end.

## 0. Setup
- Repo: `amanupputuri/shorts-media` (attach with add_repo, push access; clone to `/home/claude/shorts-media`).
- `pip install numpy pillow --break-system-packages` if missing; ffmpeg must exist.
- All times are **Asia/Kolkata (IST)**.

## 1. Pick the target date
- If TARGET is listed in `pipeline/skip_dates.txt` → it is PAUSED: do nothing else, report "paused for TARGET".
- If IST time now is before 11:00 → TARGET = today, else TARGET = tomorrow.
- Metricool: `getBrandSettings` → blogId **8098288**. `getScheduledPosts` for TARGET 00:00–23:59 IST
  (timezone `Asia/Calcutta`). If **3 or more** YouTube posts already exist that day → it is already done:
  stop and report "already scheduled".
- `python3 pipeline/tools.py day TARGET` → gives `format` (the Shorts format of the day), `style`, `music_seed`.

## 2. Write the content (the creative part — take care)
Read `pipeline/used.json` (list of short keys of puzzles already used). Never repeat one.
N = 4 Shorts. Write N+1 spec files in `work/TARGET/`:
- `s01.json … sNN.json` — Shorts. Each: **3 puzzles, all of the day's format**, orientation `"v"`, count_secs 3,
  label `"PUZZLE"`. Vary difficulty: easy, medium, tricky.
- `long.json` — orientation `"h"`, count_secs 5, label `"PUZZLE"`, **20 puzzles = one each of 20 different formats (all 20)**,
  shuffled order, easy → harder.
- Every spec gets: `style` and `music_seed` from step 1 (long video: music_seed + 1), a `title_card`
  {emoji, line1, line2, tag} and `outro` exactly {"line1": "LIKE &", "line2": "SUBSCRIBE!", "line3": "", "cta": "SUBSCRIBE", "cta_sub": ""},
  and a `say` block: `{"intro": "...", "items": [{"q": "...", "a": "..."}, ...], "outro": "..."}`.
  The voice is **Professor Hoot** (a wise, playful owl professor) and he only says SHORT catchphrases — the puzzle
  itself is carried by on-screen text, music and sound effects. intro ≤ 10 words (often starting "Hoo-hoo!"),
  q lines ≤ 6 words (e.g. "Which key fits? Think fast!"), a lines ≤ 10 words and state the answer first
  (e.g. "Key B! Every tooth matches."), outro is ALWAYS exactly "Like and subscribe!" (nothing else — keep the ending short). Vary the wording of all other lines every video;
  never the same line twice in a day. Simple words, fun tone, for ages 5–80.
- After writing each spec run `python3 pipeline/tools.py check FILE`. It prints the **true answer** of every
  puzzle (computed from the drawing data). Make every `a` line and the `fact` lines agree with it. Fix and re-check
  until it prints OK. Never ship a spec whose voice disagrees with `check`.

### Puzzle schemas — the 20 formats (all items also have `prompt` (on-screen question, ≤ 32 characters) and `fact` [line1 ≤ 26 chars, line2 ≤ 34 chars])
Emoji must be single standard emoji (no flags, no skin tones, no ZWJ sequences). Shorts use only the format of the day;
the long video uses 20 different formats (one puzzle each), one puzzle from each of the 20.
- **odd4** `{"type":"odd4","options":[[label,emoji]x4],"right":i}` — 4 things, one doesn't belong (reason in fact).
- **twins** `{"type":"twins","seed":n}` any int; answer = check output.
- **spotdiff** `{"type":"spotdiff","prompt":"Spot the difference!","scene":[9 emoji],"diff":0-8,"alt":e (similar-looking, e.g. 🌼→🌻)}`
- **memgrid** `{"type":"memgrid","prompt":"Watch the squares!","prompt2":"Which square lit up LAST?","seq":[4-5 cell indexes 0-8, no repeats]}`
- **missing** `{"type":"missing","prompt":"Remember these 6!","prompt2":"Which one is missing?","before":[6 emoji],"gone":i,"options":[3 emoji incl. before[gone]],"right":i}`
- **flipped** `{"type":"flipped","prompt":"Find the upside-down one!","emoji":e (clearly not symmetric: 🐟🐌🦒🚗🐘),"pos":[row,col],"mode":"rot"}`
- **bug** `{"type":"bug","prompt":"Where does the bug stop?","start":[r,c],"moves":"4-6 of U/D/L/R"}` must stay on the 4x4 grid; answer = check output.
- **countdiff** `{"type":"countdiff","prompt":"How many differences?","scene":[9 emoji],"diffs":[[cell,alt],...] (1-3),"options":["1","2","3"],"right":len(diffs)-1}`
- **cardflip** `{"type":"cardflip","prompt":"Remember the cards!","prompt2":"Find the matching pair!","cards":[9 emoji, exactly 2 == target],"target":e,"options":["a & b" strings, one is the true pair],"right":i}`
- **diceflash** `{"type":"diceflash","prompt":"Remember the dice!","prompt2":"What was the total?","dice":[2 values 1-6],"options":[3 strings],"right":i}`
- **zoom** `{"type":"zoom","prompt":"What is it? Guess early!","emoji":e,"focus":[0.3-0.7,0.3-0.7],"options":[3 names],"right":i}`

- **shapemiss** `{"type":"shapemiss","prompt":"Watch closely!","prompt2":"Which one did NOT appear?","seq":[5 emoji],"options":[3 emoji: exactly one NOT in seq],"right":i}`
- **spotlight** `{"type":"spotlight","prompt":"What's in the dark?","emoji":e (big clear animal/object),"options":[3 names],"right":i}`
- **pixel** `{"type":"pixel","prompt":"Guess before it clears!","emoji":e,"options":[3 names],"right":i}`
- **colorcount** `{"type":"colorcount","prompt":"How many GREEN shapes?","counts":{"green":n,"red":n,"blue":n,"yellow":n} (total ≤ 30),"ask":colour,"seed":n,"options":[3 strings],"right":i}`

- **numflash** `{"type":"numflash","prompt":"Remember the number!","prompt2":"Which number did you see?","number":"5 digits","options":[5 different look-alike numbers incl. number (swap 2 digits, change 1 digit…)],"right":i}`
- **rowdiff** `{"type":"rowdiff","prompt":"Which row is different?","seq":[7 DIFFERENT, easy-to-tell-apart emoji of one theme, e.g. 🍎🍌🍇🍓🍊🍉🍍 or 🐶🐱🐭🐰🦊🐻🐼],"rows":4,"odd_row":0-3,"swap":[k,k+1]}` MEDIUM (two neighbours swapped; never use look-alike faces).
- **letterhunt** `{"type":"letterhunt","prompt":"Find the odd letter!","base":"O","odd":"Q","pos":[row 0-9,col 0-15]}` — dense grid; use look-alike pairs and vary daily: O/Q, M/N, E/F, P/R, C/G, 8/B, 5/S, 0/O, V/Y, I/T, 3/8, U/V.
- **crowd** `{"type":"crowd","prompt":"Find it in the crowd!","target":e,"pool":[8+ emoji that look very similar to the target — same colour/shape family, e.g. 🐧 among 🐦🕊️🦅🦆🦉🐓🦜🐤],"pos":[row 0-8,col 0-15],"seed":n}` HARD (dense grid).
- **dupnum** `{"type":"dupnum","prompt":"Which number appears twice?","nums":[30 two-digit numbers, exactly one repeated once, include near-twins like 47/74/41/17]}` HARD.

## 3. Voice (ElevenLabs connector)
- `creative_create_flow` once (name "Wit Wonderland TARGET").
- For each Short: `python3 pipeline/tools.py prompt sNN.json` → one `creative_generate_speech` call
  (model `eleven_v4`, voice_id `cPmGMZvsZ24aRiDy6Vc2` (**Professor Hoot**, the channel's owl mascot), generations_count 1, same flow_id).
- Long video: `python3 pipeline/tools.py prompt long.json 2` → 2 calls (part 1 and part 2).
- Never call generate twice for the same text. Collect generation_ids; read URLs with `creative_get_generations`
  (wait ~20 s first; up to 4 ids per call) and download each with curl to `work/TARGET/voice/`.
- `python3 pipeline/tools.py fill sNN.json work/TARGET/voice/sNN.mp3` (long: two files in order).

## 4. Render
`python3 pipeline/build.py SPEC work/TARGET/build_NAME out/NAME.mp4` — run at most 2 builds at once.
Check each output exists, Shorts 40–80 s, long 5–12 min. Grab 3 frames of 2 videos and look at them.
If a split fails ("split failed"), regenerate that one voice once.

## 5. Host the files
Commit the mp4s to the orphan branch **media** (it only ever holds the current day — force push):
```
cd /home/claude/shorts-media && git checkout --orphan media-tmp && git rm -rf --cached . -q
mkdir -p media && cp out/*.mp4 media/ && git add media && git commit -qm "media TARGET"
git branch -D media 2>/dev/null; git branch -m media && git push -f origin media && git checkout -f main
```
Name files `TARGET-s01.mp4 … TARGET-sNN.mp4`, `TARGET-long.mp4`. URL:
`https://raw.githubusercontent.com/amanupputuri/shorts-media/media/media/FILE` — curl -sI each, must be 200.
(Metricool copies the file when the post is created, so replacing the branch next day is safe.)

## 6. Schedule in Metricool (createScheduledPost, blogId 8098288, timezone Asia/Calcutta)
Pick N+1 **random** times on TARGET between 13:00 and 23:00 IST (random minutes, not round numbers, at least 90 minutes apart,
and never earlier than 30 minutes after now). Generate them with Python `random` seeded by TARGET. N go to the Shorts in random
order; the long video gets one of the times between 16:00 and 21:00.
info: autoPublish true, draft false, providers [{"network":"youtube"}], media [URL], firstCommentText
"What was your score? 👇", youtubeData {title, type "short" (long: "video"), privacy "public", tags,
category "EDUCATION", madeForKids false, isAiGeneratedContent false}.
- Title ≤ 90 chars, catchy, different every video, ends with "#shorts" for Shorts. Mention the puzzle type.
- Description (text): 1 hook line; "Can you solve all 3?" style challenge; the 3 puzzles in plain words (no answers in
  the first lines; answers after "ANSWERS (no peeking!)"); comment-your-score line; subscribe line with
  https://www.youtube.com/channel/UCl870UQHJt9aZCNW-IhK1gA?sub_confirmation=1 ; 6–10 hashtags.
  Long video: list "0:00 Intro" style is NOT needed; list the 20 puzzle types.
- Tags: 12–18 search phrases (puzzle type names, "brain teaser", "eye test", "puzzle game", "iq test",
  "can you solve this", "wit wonderland", …). No single-word tags only.

## 7. Wrap up
- Append the new puzzle keys (e.g. "cups:1:0-1,1-2,0-2", "odd4:penguin") to `pipeline/used.json` on **main**, commit,
  push (use `git -c push.negotiate=true push`).
- Send a short report (SendUserMessage + PushNotification if available): date, format of the day, how many
  posts scheduled, any failures.
