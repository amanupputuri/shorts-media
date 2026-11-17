# Wit Wonderland — daily puzzle run

Every day this run makes **5 vertical Shorts + 1 horizontal 20-puzzle video** for the YouTube channel
Wit Wonderland and schedules them in **Buffer** (through `pipeline/buffer_post.py`; Metricool is no longer used). Work unattended: never stop to ask questions; if a step fails,
retry once, skip that video, and carry on. Report at the end.

## 0. Setup
- Repo: `amanupputuri/shorts-media` (attach with add_repo, push access; clone to `/home/claude/shorts-media`).
- `pip install numpy pillow --break-system-packages` if missing; ffmpeg must exist.
- All times are **Asia/Kolkata (IST)**.

## 1. Pick the target date
- If TARGET is listed in `pipeline/skip_dates.txt` → it is PAUSED: do nothing else, report "paused for TARGET".
- If the message that started this run names a TARGET date, use exactly that date (it overrides everything here).
- Otherwise: if IST time now is before 11:00 → TARGET = today, else TARGET = tomorrow.
- Already done? `python3 pipeline/buffer_post.py list <TARGET 00:00 IST in UTC> <TARGET 23:59 IST in UTC>`
  (e.g. TARGET 2026-11-18 → `2026-11-17T18:30:00.000Z 2026-11-18T18:29:00.000Z`). If **3 or more** posts exist → stop, report "already scheduled".
- `python3 pipeline/tools.py day TARGET` → gives `format` (the Shorts format of the day), `style`, `music_seed`.

## 2. Write the content (the creative part — take care)
Read `pipeline/used.json` (list of short keys of puzzles already used). Never repeat one.
If `pipeline/insights.json` exists (weekly Studio review), use its `themes` and `best_title_patterns` for ideas and titles.
N = 5 Shorts. Write N+1 spec files in `work/TARGET/`:
- `s01.json … sNN.json` — Shorts. Each: **exactly 6 puzzles, all of the day's format: 2 EASY, 2 MEDIUM, 2 HARD, in that
  order** (badges are added automatically), orientation `"v"`, count_secs **3** (Shorts land ~55–65 s).
  HOOKS (most important — make viewers wait for the last puzzle):
  · `"hook"` (≤ 7 words) shown over puzzle 1 at second 0 and spoken by Hoot as say.intro. It must promise a payoff at
    the END: "Puzzle 6 fools 99% of people", "Wait for the last one…", "Only geniuses get all 6", "Level 6 broke my brain".
    Read `pipeline/hooks_used.json` (list of {"date","hook","teasers"}). Do NOT reuse a hook from the last 30 days, and
    avoid the same opening words twice in a row. Rotate styles so it feels natural, not templated:
    dare ("Bet you can't get puzzle 6"), curiosity ("The last one is impossible... or is it?"), stat ("Only 3% get 6/6"),
    personal ("My mom failed puzzle 4 😅" — no emoji on screen), speed ("You have 5 seconds. Go!"), story ("I made the
    last one extra sneaky"), question ("Are your eyes sharper than an owl's?"). Fit the day's format (memory, colours,
    numbers…). A favourite may come back after 30 days, slightly reworded.
  · Cliff-hanger cards appear automatically (before puzzle 3: "Warm-up done. Now it gets tricky!", before puzzle 5:
    "HARD MODE! Only 1% get these", before puzzle 6: "FINAL PUZZLE! Don't blink..."). Write your own instead by giving
    items 2, 4 and 5 a `"teaser"` (≤ 7 words) — make them build tension toward puzzle 6 and differ across the day's
    Shorts (if you leave them out, varied defaults are picked automatically).
  · Puzzle 6 must be the hardest of the day (genuinely tricky) so the payoff is real and people rewatch.
  RETENTION RULES: no slow start, q lines ≤ 4 words,
  label `"PUZZLE"`. Vary difficulty: easy, medium, tricky.
- `long.json` — orientation `"h"`, count_secs 5, label `"PUZZLE"`, **20 puzzles = one each of the 20 formats in step 1's `long_formats` (in that order)**,
  shuffled order, easy → harder.
- Every spec gets: `style` and `music_seed` from step 1 (long video: music_seed + 1), a `title_card`
  {emoji, line1, line2, tag} and `outro` exactly {"line1": "LIKE &", "line2": "SUBSCRIBE!", "line3": "", "cta": "SUBSCRIBE", "cta_sub": "Comment your score below!"},
  and a `say` block: `{"intro": "...", "items": [{"q": "...", "a": "..."}, ...], "outro": "..."}`.
  The voice is **Professor Hoot** (a wise, playful owl professor) and he only says SHORT catchphrases — the puzzle
  itself is carried by on-screen text, music and sound effects. intro ≤ 10 words (often starting "Hoo-hoo!"),
  q lines ≤ 6 words (e.g. "Which key fits? Think fast!"), a lines ≤ 10 words and state the answer first
  (e.g. "Key B! Every tooth matches."), outro is ALWAYS exactly "Like and subscribe! Comment your score below!" (Aman's wording — short, never change it). Vary the wording of all other lines every video;
  never the same line twice in a day. Simple words, fun tone, for ages 5–80.
- After writing each spec run `python3 pipeline/tools.py check FILE`. It prints the **true answer** of every
  puzzle (computed from the drawing data). Make every `a` line and the `fact` lines agree with it. Fix and re-check
  until it prints OK. Never ship a spec whose voice disagrees with `check`.

### Puzzle schemas — the 26 formats (all items also have `prompt` (on-screen question, ≤ 32 characters) and `fact` [line1 ≤ 26 chars, line2 ≤ 34 chars])
Emoji must be single standard emoji (no flags, no skin tones, no ZWJ sequences). Shorts use only the format of the day;
the long video uses the 20 formats listed in `long_formats` for the day (one puzzle each); it rotates through all 26.
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

- **fruitmath** `{"type":"fruitmath","prompt":"Solve the fruit math!","eqs":[[["🍎","🍎"],10],[["🍎","🍌"],8]],"ask":["🍌","🍌"],"options":[3 strings],"right":i}` — 2-3 equations with whole-number values 1-20; vary fruits and totals daily.
- **gridfind** `{"type":"gridfind","prompt":"Where is the strawberry?","target":"🍓","pool":[6 look-alike emoji NOT incl. target],"pos":[row 0-4,col 0-4],"seed":n,"options":[3 like "D3","C4","D2"],"right":i}` — answer is column letter + row number.
- **patmatch** `{"type":"patmatch","prompt":"Which board is an exact copy?","grid":[4x4 of "r","b","y","g","w"],"diffs":[[r,c,colour],[r,c,colour]],"right":0-2}` — the two wrong boards each have one peg changed.
- **fingers** `{"type":"fingers","prompt":"How many fingers are up?","hands":[3-5 of ✋ ✌️ ☝️ 🤟],"options":[3 strings],"right":i}` (✋=5 ✌️=2 ☝️=1 🤟=3).
- **analogy** `{"type":"analogy","prompt":"What goes with the bunny?","pair":["🐶","🦴"],"ask":"🐰","options":[3 emoji],"right":i}` — clear everyday links (bee→honey, cow→milk, key→lock…).
- **oddpair** `{"type":"oddpair","prompt":"Which pair doesn't belong?","pairs":[4 pairs of emoji, 3 that go together, 1 that doesn't],"right":0-3}` — fact explains the odd pair.

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
Check each output exists, Shorts 55–90 s, long 5–12 min. Grab 3 frames of 2 videos and look at them.
If a split fails ("split failed"), regenerate that one voice once.

## 5. Host the files
Commit the mp4s to the orphan branch **media**. Buffer downloads each video only when it publishes, so the branch keeps
**yesterday's and today's** files (force push; drop anything older):
```
cd /home/claude/shorts-media && git fetch -q origin media && mkdir -p /tmp/keep && git archive FETCH_HEAD media | tar -x -C /tmp/keep
git checkout --orphan media-tmp && git rm -rf --cached . -q && rm -rf media && mkdir -p media
cp /tmp/keep/media/YESTERDAY-* media/ 2>/dev/null; cp out/*.mp4 media/ && git add media && git commit -qm "media TARGET"
git branch -D media 2>/dev/null; git branch -m media && env -u GH_TOKEN git -c push.negotiate=true push -f origin media && git checkout -f main
```
Name files `TARGET-s01.mp4 … TARGET-sNN.mp4`, `TARGET-long.mp4`. URL:
`https://raw.githubusercontent.com/amanupputuri/shorts-media/media/media/FILE` — curl -sI each, must be 200.

## 6. Schedule in Buffer (`pipeline/buffer_post.py`)
Pick N+1 **random** times on TARGET between 11:00 and 23:00 IST — the last one no later than 23:00 (random minutes, not round numbers, at least 90 minutes apart,
and never earlier than 30 minutes after now). Generate them with Python `random` seeded by TARGET. N go to the Shorts in random
order; the long video gets one of the times between 16:00 and 21:00.
**Buffer's YouTube channel only accepts Shorts** (vertical, ≤ 3 min) — do NOT send the long video to Buffer. Put only the
N Shorts in posts.json. For the long video, write its title, full description and the suggested time (16:00–21:00) into
`pipeline/schedule/TARGET.json` and into the final report with its download URL, so Aman can upload it in the YouTube app.
Write `work/TARGET/posts.json` = list of {"url", "title", "text", "due_ist": "TARGET HH:MM"} and run
`python3 pipeline/buffer_post.py schedule work/TARGET/posts.json`. Every step must come back `PostActionSuccess`;
if one fails, fix it and schedule only that one again (never re-send ones that succeeded — that would post twice).
Buffer sets: public, category Education (27), not made for kids, notify subscribers. Buffer can't set tags or a
first comment — the evening Studio task pins the comment and sets the related video.
- Title ≤ 90 chars, catchy, different every video, ends with "#shorts" for Shorts. Mention the puzzle type.
- Description (text): 1 hook line; "Can you get all 6?" style challenge; the puzzles in plain words (no answers in
  the first lines; answers after "ANSWERS (no peeking!)"); comment-your-score line; subscribe line with
  https://www.youtube.com/channel/UCl870UQHJt9aZCNW-IhK1gA?sub_confirmation=1 ; a "Search: …" line with 10–14 search
  phrases separated by commas (brain teaser, eye test, puzzle game, iq test, can you solve this, wit wonderland, the
  puzzle type names…) in place of tags; then 6–10 hashtags.
  Long video: list the 20 puzzle types.
- Save the Buffer post ids + titles + times to `work/TARGET/scheduled.json` and also commit a copy to **main** as
  `pipeline/schedule/TARGET.json` (the evening Studio task reads it).

## 7. Wrap up
- Append every Short's hook and teasers to `pipeline/hooks_used.json` ({"date": TARGET, "hook": ..., "teasers": [...]}).
- Append the new puzzle keys (e.g. "cups:1:0-1,1-2,0-2", "odd4:penguin") to `pipeline/used.json` on **main**, commit,
  push (use `git -c push.negotiate=true push`).
- Send a short report (SendUserMessage + PushNotification if available): date, format of the day, how many
  posts scheduled, any failures.
