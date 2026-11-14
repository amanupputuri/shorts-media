# Wit Wonderland — daily puzzle run

Every day this run makes **4 vertical Shorts + 1 horizontal 20-puzzle video** for the YouTube channel
Wit Wonderland and schedules them in Metricool. Work unattended: never stop to ask questions; if a step fails,
retry once, skip that video, and carry on. Report at the end.

## 0. Setup
- Repo: `amanupputuri/shorts-media` (attach with add_repo, push access; clone to `/home/claude/shorts-media`).
- `pip install numpy pillow --break-system-packages` if missing; ffmpeg must exist.
- All times are **Asia/Kolkata (IST)**.

## 1. Pick the target date
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
- `long.json` — orientation `"h"`, count_secs 5, label `"PUZZLE"`, **20 puzzles = one each of 20 of the 21 formats**,
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

### Puzzle schemas — the 21 formats (all items also have `prompt` (on-screen question, ≤ 32 characters) and `fact` [line1 ≤ 26 chars, line2 ≤ 34 chars])
Emoji must be single standard emoji (no flags, no skin tones, no ZWJ sequences). Shorts use only the format of the day;
the long video uses all 21 (one each; drop one so it is 20).
- **odd4** `{"type":"odd4","options":[[label,emoji]x4],"right":i}` — 4 things, one doesn't belong (reason in fact).
- **changed** `{"type":"changed","prompt":"Remember these 6!","prompt2":"Which one changed?","before":[6 emoji],"changed":i,"after_emoji":e}`
- **twins** `{"type":"twins","seed":n}` any int; answer = check output.
- **count** `{"type":"count","target":e,"others":[2-3 emoji],"n":4-9,"m":8-12,"seed":k,"options":[3 strings],"right":i}` n+m ≤ 20, options[right] == n.
- **order** `{"type":"order","prompt":"Remember the order!","prompt2":"Which one came SECOND?","seq":[4 emoji],"ask_pos":1-4,"options":[3 emoji incl. seq[ask_pos-1]],"right":i}`
- **spotdiff** `{"type":"spotdiff","prompt":"Spot the difference!","scene":[9 emoji],"diff":0-8,"alt":e (similar-looking, e.g. 🌼→🌻)}`
- **oddcolor** `{"type":"oddcolor","prompt":"Find the different colour!","color":[r,g,b],"delta":14-26 (smaller = harder),"pos":[row 0-5,col 0-8]}`
- **memgrid** `{"type":"memgrid","prompt":"Watch the squares!","prompt2":"Which square lit up LAST?","seq":[4-5 cell indexes 0-8, no repeats]}`
- **missing** `{"type":"missing","prompt":"Remember these 6!","prompt2":"Which one is missing?","before":[6 emoji],"gone":i,"options":[3 emoji incl. before[gone]],"right":i}`
- **flipped** `{"type":"flipped","prompt":"Find the upside-down one!","emoji":e (clearly not symmetric: 🐟🐌🦒🚗🐘),"pos":[row,col],"mode":"rot"}`
- **numflash** `{"type":"numflash","prompt":"Remember the number!","prompt2":"Which number did you see?","number":"4-5 digits","options":[3 look-alike numbers incl. number],"right":i}`
- **whereflash** `{"type":"whereflash","prompt":"Remember where they are!","prompt2":"Where was the X?","grid":[9 distinct emoji],"target_idx":0-8}`
- **bug** `{"type":"bug","prompt":"Where does the bug stop?","start":[r,c],"moves":"4-6 of U/D/L/R"}` must stay on the 4x4 grid; answer = check output.
- **rowdiff** `{"type":"rowdiff","prompt":"Which row is different?","seq":[5 look-alike emoji, e.g. 😀😃😄😁😆 or 🐶🐕🐩🐺🦊],"rows":5,"odd_row":0-4,"swap":[k,k+1]}`
- **countdiff** `{"type":"countdiff","prompt":"How many differences?","scene":[9 emoji],"diffs":[[cell,alt],...] (1-3),"options":["1","2","3"],"right":len(diffs)-1}`
- **arrowout** `{"type":"arrowout","prompt":"Find the odd arrow!","angle":0|90|180|270,"odd_angle":angle±90 or +180 (or ±30 to be hard),"pos":[row,col]}`
- **cardflip** `{"type":"cardflip","prompt":"Remember the cards!","prompt2":"Find the matching pair!","cards":[9 emoji, exactly 2 == target],"target":e,"options":["a & b" strings, one is the true pair],"right":i}`
- **diceflash** `{"type":"diceflash","prompt":"Remember the dice!","prompt2":"What was the total?","dice":[2 values 1-6],"options":[3 strings],"right":i}`
- **zoom** `{"type":"zoom","prompt":"What is it? Guess early!","emoji":e,"focus":[0.3-0.7,0.3-0.7],"options":[3 names],"right":i}`
- **lightorder** `{"type":"lightorder","prompt":"Watch the lights!","prompt2":"Which colour lit up THIRD?","seq":[4-5 of red|blue|green|yellow],"ask_pos":n,"options":[3 colour names],"right":i}`
- **split** `{"type":"split","prompt":"Match the halves!","emojis":[3 animal faces],"order":[permutation of 0,1,2 ≠ identity],"ask":0-2}` answer = check output.

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
