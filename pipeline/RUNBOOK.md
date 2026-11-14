# Wit Wonderland — daily puzzle run

Every day this run makes **6–10 vertical Shorts (random count) + 1 horizontal 20-puzzle video** for the YouTube channel
Wit Wonderland and schedules them in Metricool. Work unattended: never stop to ask questions; if a step fails,
retry once, skip that video, and carry on. Report at the end.

## 0. Setup
- Repo: `amanupputuri/shorts-media` (attach with add_repo, push access; clone to `/home/claude/shorts-media`).
- `pip install numpy pillow --break-system-packages` if missing; ffmpeg must exist.
- All times are **Asia/Kolkata (IST)**.

## 1. Pick the target date
- If IST time now is before 11:00 → TARGET = today, else TARGET = tomorrow.
- Metricool: `getBrandSettings` → blogId **8098288**. `getScheduledPosts` for TARGET 00:00–23:59 IST
  (timezone `Asia/Calcutta`). If **4 or more** YouTube posts already exist that day → it is already done:
  stop and report "already scheduled".
- `python3 pipeline/tools.py day TARGET` → gives `format` (the Shorts format of the day), `style`, `music_seed`.

## 2. Write the content (the creative part — take care)
Read `pipeline/used.json` (list of short keys of puzzles already used). Never repeat one.
Pick the number of Shorts N = random 6–10 (Python `random` seeded by TARGET). Write N+1 spec files in `work/TARGET/`:
- `s01.json … sNN.json` — Shorts. Each: **3 puzzles, all of the day's format**, orientation `"v"`, count_secs 3,
  label `"PUZZLE"`. Vary difficulty: easy, medium, tricky.
- `long.json` — orientation `"h"`, count_secs 5, label `"PUZZLE"`, **20 puzzles = one of each of the 20 formats**,
  shuffled order, easy → harder.
- Every spec gets: `style` and `music_seed` from step 1 (long video: music_seed + 1), a `title_card`
  {emoji, line1, line2, tag} and `outro` {line1, line2, line3, cta ("FOLLOW" Shorts / "SUBSCRIBE" long), cta_sub},
  and a `say` block: `{"intro": "...", "items": [{"q": "...", "a": "..."}, ...], "outro": "..."}`.
  Write fresh intro/outro lines every video (never the same wording twice in a day). Simple words, fun tone,
  for ages 5–80. q lines ≤ 14 words; a lines ≤ 22 words and must state the answer first.
- After writing each spec run `python3 pipeline/tools.py check FILE`. It prints the **true answer** of every
  puzzle (computed from the drawing data). Make every `a` line and the `fact` lines agree with it. Fix and re-check
  until it prints OK. Never ship a spec whose voice disagrees with `check`.

### Puzzle schemas (all items also have `prompt` (on-screen question) and `fact` [line1 ≤ 26 chars, line2 ≤ 34 chars])
Emoji must be single standard emoji (no flags, no skin tones, no ZWJ sequences).
- **odd4** `{"type":"odd4","options":[[label,emoji]x4],"right":i}` — 4 things, one doesn't belong (reason in fact).
- **changed** `{"type":"changed","prompt":"Remember these 6!","prompt2":"Which one changed?","before":[6 emoji],"changed":i,"after_emoji":e}`
- **keys** `{"type":"keys","lock":[5 ints 1-3],"keys":[3 lists],"right":i}` keys[right] == lock; others differ in 1–2 teeth.
- **glasses** `{"type":"glasses","pipes":{"1":[[child,height0-1,blocked]],...}}` glasses 1→2,3; 2→4,5; 3→5,6 (any subset,
  some blocked). Answer = check output (water takes the lowest open pipe).
- **path** `{"type":"path","starters":[3 emoji],"prize":e,"prize_slot":0-2,"rows":8,"rungs":[[row 0.8-7.2, left_lane 0|1],...]}`
  4–7 rungs, rows ≥ 1 apart for the same lane pair. Answer = check output.
- **shadow** `{"type":"shadow","object":e,"shadows":[3 entries, one == object, others similar animals/objects or "e|flip"],"right":i}`
- **mirror** `{"type":"mirror","kind":"text"|"emoji","content":"WORD" (A–Z, 4–6 letters, not symmetric) or emoji string,"opts":[permutation of "h","v","r"],"right": index of "h"}`
- **fit** `{"type":"fit","item":e,"grid":[cols 3-5,rows 2-4],"options":[3 numbers as strings],"right":i}` options[right] == cols*rows.
- **twins** `{"type":"twins","seed":n}` any int; answer = check output.
- **piece** `{"type":"piece","emoji":e (big animal/object face),"missing":0-8,"options":[3 of: the missing index, another index, "<missing>r"],"right":i,"bg":[r,g,b] pale}`
- **illusion** `{"type":"illusion","kind":"lines"|"circles","diff":-1|0|1}` (0 = same — use 0 most of the time, ±1 sometimes).
- **rotate** `{"type":"rotate","cells":[[r,c] 5 cells in 4x4, asymmetric],"opts":[[angle 90|180|270, mirrored bool] x3],"right":i,"color":[r,g,b]}` exactly one opt not mirrored.
- **count** `{"type":"count","target":e,"others":[2-3 emoji],"n":4-9,"m":8-12,"seed":k,"options":[3 strings],"right":i}` n+m ≤ 20, options[right] == n.
- **order** `{"type":"order","prompt":"Remember the order!","prompt2":"Which one came SECOND?","seq":[4 emoji],"ask_pos":1-4,"options":[3 emoji incl. seq[ask_pos-1]],"right":i}`
- **maze** `{"type":"maze","starters":[3 emoji],"prize":e,"seed":n,"goal_col":0-6 (optional, default 3)}` answer = check output (each animal has its own sealed area; one contains the prize).
- **blocks** `{"type":"blocks","heights":[[3x3 column heights 0-4]],"options":[3 strings],"right":i}` options[right] == total; taller columns at the back-left so hidden blocks are implied; total 5-14.
- **colortrap** `{"type":"colortrap","prompt":"Say the COLOUR, not the word!","word":colour name,"ink":one of red|blue|green|yellow|purple|orange|pink (≠ word),"options":[3 colour names incl. ink and word],"right":index of ink}`
- **balance** `{"type":"balance","rule":[[emojiA,a],[emojiB,b]],"q_n":n,"options":[3 strings],"right":i}` means a×A = b×B; question: n×B = ? A. Answer n·a/b must be a whole number ≤ 9; options[right] equals it.
- **dots** `{"type":"dots","prompt":"Connect the dots... what is it?","shape":one of star|house|fish|heart|boat|arrow|tree|rocket|crown|cat|kite|umbrella,"options":[3 names incl. the shape],"right":i}`
- **hidden** `{"type":"hidden","base":e,"odd":very similar emoji (😀/😃, 🕐/🕑, 🐻/🐨, 🍎/🍅, 🌕/🌝),"pos":[row 0-5,col 0-11]}`

## 3. Voice (ElevenLabs connector)
- `creative_create_flow` once (name "Wit Wonderland TARGET").
- For each Short: `python3 pipeline/tools.py prompt sNN.json` → one `creative_generate_speech` call
  (model `eleven_v4`, voice_id `c6SfcYrb2t09NHXiT80T` (Jarnathan), generations_count 1, same flow_id).
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
Pick N+1 **random** times on TARGET between 13:00 and 23:00 IST (random minutes, not round numbers, at least 35 minutes apart,
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
