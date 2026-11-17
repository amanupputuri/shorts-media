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
- `python3 pipeline/tools.py day TARGET` → gives `short_formats` (5 DIFFERENT formats, one per Short), `short_themes`, `style`, `music_seed`, `long_formats`.
  **Aman, 18 Nov: every Short of the day is a DIFFERENT puzzle type** — Short k uses only `short_formats[k]` (never the same format in two Shorts of one day). The old single `format` field is no longer used for Shorts.

## 2. Write the content (the creative part — take care)
Read `pipeline/used.json` (list of short keys of puzzles already used). Never repeat one.
If `pipeline/insights.json` exists (weekly Studio review), use its `themes` and `best_title_patterns` for ideas and titles.
N = 5 Shorts. Write N+1 spec files in `work/TARGET/`:
- THEMES: if `short_themes[k]` is not empty, Short k uses that theme: every puzzle's emoji/pictures come from that
  theme (e.g. Christmas: 🎄🎅🎁⛄🔔🦌🍪🧦⭐), and the title names it ("Christmas Spot the Difference 🎄👀 #shorts").
  Formats built on numbers/letters/shapes have no theme (empty string) — keep them as they are.
- `s01.json … sNN.json` — Shorts. Each: **exactly 6 puzzles, all of that Short's own format (`short_formats[k]`): 2 EASY, 2 MEDIUM, 2 HARD, in that
  order** (badges are added automatically), orientation `"v"`, count_secs **4** (Aman, 18 Nov: 4-second timer; Shorts land ~60–75 s).
  HOOKS (most important — make viewers wait for the last puzzle):
  **HOOK STYLE — attractive + encouraging (Aman, 17 Nov; Shorts AND long videos).** Every hook must make the viewer
  WANT to keep watching and feel they CAN do it. Each hook does two things in a few words:
    1. *pull forward* — promise something good just ahead (a sneakier puzzle, a twist, a big finish, bragging rights), and
    2. *cheer them on* — warm, positive, second person ("you", "your"), like a friendly coach.
  Good: "You're on fire — the next one's sneaky!", "Halfway there, and you're crushing it!", "Ready for a twist?
  You've got this!", "Save your best for the last one!", "Only sharp eyes get all 6 — show me yours!",
  "Nice streak! Can you keep it going?", "The best puzzle is saved for last — stay with me!".
  Bad: anything that discourages or mocks ("Most people give up here", "You'll fail this", "Too hard for you"),
  flat labels ("Puzzle 5", "Next one"), or long sentences. Fear-of-failure stats ("99% fail") only when turned
  into a dare the viewer can win ("Only 1% get this — be the 1%!"). Simple words, ages 5–80, ≤ 7 words on screen.
  · `"hook"` (≤ 7 words) shown over puzzle 1 at second 0 and spoken by Hoot as say.intro. It must promise a payoff at
    the END and invite them in: "Can you beat all 6? Let's go!", "Stay for puzzle 6 — it's a beauty!",
    "Only sharp eyes get all 6 — you in?", "The last one is my favourite!".
    Read `pipeline/hooks_used.json` (list of {"date","hook","teasers"}). Do NOT reuse a hook from the last 30 days, and
    avoid the same opening words twice in a row. Rotate styles so it feels natural, not templated:
    dare ("Think you can get puzzle 6? Show me!"), curiosity ("Wait till you see the last one!"), stat ("Only 3% get
    6/6 — be one!"), personal ("Puzzle 4 got me — can you?"), speed ("5 seconds each. Ready? Go!"), story ("I saved a
    fun twist for last"), question ("Are your eyes sharper than an owl's?") — always in the HOOK STYLE. Fit that Short's format (memory, colours,
    numbers…). A favourite may come back after 30 days, slightly reworded.
  · **SPOKEN HOOKS — natural voice, no text cards (Aman, 18 Nov; Shorts too, same as the long video).** Give
    `say.items[2]`, `say.items[4]` and `say.items[5]` a `"hook"` (≤ 7 words, HOOK STYLE, sounds like a friend talking, e.g.
    "Ooh, you're good! This one's sneaky.", "Two left. You've totally got this!", "Last one — the best for last!").
    Hoot says it at the end of the previous answer screen. Make the voice for them with `tools.py hooks sNN.json` (one extra
    generate call per Short, voice cPmGMZvsZ24aRiDy6Vc2) and `tools.py fillhooks sNN.json work/TARGET/voice/sNN-hooks.mp3`.
    Do NOT write `"teaser"` (check fails) — with spoken hooks the old text cliff-hanger cards are switched off.
    The opening `"hook"` banner at second 0 stays (it is also said as say.intro). Reword hooks every Short, never the same twice in a day.
  · **PUZZLE STYLE = the latest long video's style (Aman, 18 Nov):** follow "Question first — FINAL FORMAT" below in every Short
    (prompt = Hoot's q words, `"hint": ""`, two-part questions with `"stack": true`, short answers, find-it reveals with the green ring),
    and for the HARD puzzles use the long video's bigger variants where the format has one (memgrid n 4, missing 9, cardflip 16, numflash 6 digits,
    spotdiff 16) — if a build looks cramped on the vertical frame, fall back to the 3x3 version for that puzzle only.
  · (old, now off when spoken hooks are present) Cliff-hanger cards appear automatically (before puzzle 3: "Great start! Now it gets tricky!", before puzzle 5:
    "Hard mode! You've got this!", before puzzle 6: "Final one! Go get all six!"). Write your own instead by giving
    items 2, 4 and 5 a `"teaser"` (≤ 7 words) — make them cheer the viewer on and build excitement toward puzzle 6 (HOOK STYLE), and differ across the day's
    Shorts (if you leave them out, varied defaults are picked automatically).
  · Puzzle 6 must be the hardest of the day (genuinely tricky) so the payoff is real and people rewatch.
  RETENTION RULES: no slow start, q lines ≤ 4 words,
  label `"PUZZLE"`. Vary difficulty: easy, medium, tricky.
- `long.json` — orientation `"h"`, count_secs 5, label `"PUZZLE"`, **20 puzzles = one each of the 20 formats in step 1's `long_formats` (in that order)**,
  shuffled order, easy → harder. **Long-video hooks are SPOKEN, never text (Aman, 17 Nov)** — see rule 6 below:
  `title_card` = {"emoji": "🦉", "line1": "20 PUZZLES", "line2": "", "tag": "Eye & Brain Workout"} (no hook question on the title card),
  `say.intro` = a natural, attractive spoken hook (≤ 14 words, HOOK STYLE) that ends with a warm-up line, e.g.
  "Hoo-hoo! Twenty puzzles, and the best one's at the end. Ready? Let's warm up!" — reword it every day.
- Every spec gets: `style` and `music_seed` from step 1 (long video: music_seed + 1), a `title_card`
  {emoji, line1, line2, tag} and `outro` exactly {"line1": "LIKE &", "line2": "SUBSCRIBE!", "line3": "", "cta": "SUBSCRIBE", "cta_sub": "Comment your score below!"},
  and a `say` block: `{"intro": "...", "items": [{"q": "...", "a": "..."}, ...], "outro": "..."}`.
  The voice is **Professor Hoot** (a wise, playful owl professor) and he only says SHORT catchphrases — the puzzle
  itself is carried by on-screen text, music and sound effects. intro ≤ 10 words (often starting "Hoo-hoo!"; long video: ≤ 14 words, ending with the warm-up line),
  q lines ≤ 6 words (e.g. "Which key fits? Think fast!"; **exception: the Bug puzzle's q reads out the moves**), a lines ≤ 10 words and state the answer first
  (e.g. "Key B! Every tooth matches."), outro is ALWAYS exactly "Like and subscribe! Comment your score below!" (Aman's wording — short, never change it). Vary the wording of all other lines every video;
  never the same line twice in a day. Simple words, fun tone, for ages 5–80.
- After writing each spec run `python3 pipeline/tools.py check FILE`. It prints the **true answer** of every
  puzzle (computed from the drawing data). Make every `a` line and the `fact` lines agree with it. Fix and re-check
  until it prints OK. Never ship a spec whose voice disagrees with `check`.

### Question first — FINAL FORMAT (Aman, 17 Nov; applies to every video from now on)
1. **On screen question = what Hoot says.** `prompt` is exactly Hoot's q line (same words). No "Answer: A, B or C"-style text on screen:
   set `"hint": ""` on every item. Never say or show "row and column" for a find-it puzzle — reveal with "Here it is! …" and the green ring
   (odd letter, crowd, mirrored emoji). Row/column only where the options ARE cells (Grid Finder "A, E2").
2. **Two-part questions** — BOTH lines are shown stacked at once (first line yellow, second white): set `"stack": true` with `prompt` + `prompt2`. `prompt` = first part ("Watch the flashes!", "Remember the cards.", "Add the dice.",
   "Remember all 6 digits OTP"), `prompt2` = second part ("Which number flashed last?", "Find the matching pair!", "What is the total?",
   "Can you tell the correct OTP?"). (without `stack` the screen would switch to prompt2 after the watch phase — not used any more). Hoot's q line says both sentences in order.
   Puzzles with no watch phase (e.g. What's Missing) put both sentences into one `prompt`.
3. **Answers**: the spoken answer is short and never says row/column or "Square N" for spot-the-difference
   ("The trumpet became a horn."). Memory Grid: "Number twelve flashed last."
4. **Bug**: `show_arrows: true`; q = "Where does the bug stop? Listen to Hoot! <moves spoken>".
5. **Fruit Math (long)**: EASY — two fruits only: two equations (A+A=n, A+B=m), ask B+B.
6. **Long videos — pop-up, spoken hooks, corner badge (Aman, 17 Nov)**:
   - spec `"midcta": {"idx": 4}` shows a LIKE + SUBSCRIBE pop-up (with bell) over the reveal of puzzle 5.
   - **Hooks are voice-over only — NO text banners**: never put `"teaser"` on long-video items (`check` fails; the engine ignores
     them for long videos). Instead give `say.items[10]`, `say.items[15]` and `say.items[19]` a `"hook"` (≤ 7 words, attractive + encouraging — see HOOK STYLE — e.g.
     "Halfway there — you're doing great!", "Tough ones now. You've got this!", "Last one! Finish strong!") — Hoot says it at the end of the previous puzzle's answer screen, which
     is held a little longer for it. The hook before puzzle 1 is the last part of `say.intro` ("…Ready? Let's warm up!").
     Reword the hooks every day; never the same set two days running.
   - **LIKE + SUBSCRIBE corner badge**: build.py adds it automatically to every long video — top-left, 10 times, 4 s each,
     spread from 0:08 to just before the outro (skips the title card and the ending screen). Nothing to write in the spec.
7. Voice reuse: when only some lines change, regenerate just those lines (generations_count 1, voice cPmGMZvsZ24aRiDy6Vc2) and splice them with
   spec `"voice_override": {"<segment index>": "path.mp3"}` (segment index: intro 0, puzzle i q = 2i-1, a = 2i, 1-based).

### Long-video difficulty rules (Aman's feedback, 17 Nov)
Puzzle 4 (Upside-Down One → mirrored odd emoji in a big grid) was far too easy; use the bigger/harder variants above for the long video:
Spot the Difference 4x4, Memory Grid 4x4 ("Watch the flashes"), What's Missing 3x3 (9), Number Flash 6 digits, Bug on voice, Card Flip 4x4, Zoom Out a bit wider.

### Puzzle schemas — the 26 formats (all items also have `prompt` (on-screen question, ≤ 32 characters) and `fact` [line1 ≤ 26 chars, line2 ≤ 34 chars])
Emoji must be single standard emoji (no flags, no skin tones, no ZWJ sequences). Each Short uses only its own format from `short_formats`;
the long video uses the 20 formats listed in `long_formats` for the day (one puzzle each); it rotates through all 26.
- **odd4** `{"type":"odd4","options":[[label,emoji]x4],"right":i}` — 4 things, one doesn't belong (reason in fact).
- **twins** `{"type":"twins","seed":n}` any int; answer = check output.
- **spotdiff** `{"type":"spotdiff","prompt":"Spot the difference!","scene":[9 emoji],"diff":0-8,"alt":e (similar-looking, e.g. 🌼→🌻)}` — **long video: 4x4 = `scene` of 16 different emoji, `diff` 0-15** (Shorts keep 3x3).
- **memgrid** `{"type":"memgrid","prompt":"Watch the squares!","prompt2":"Which square lit up LAST?","seq":[4-5 cell indexes 0-8, no repeats]}` — **long video: add `"n":4` (4x4 grid) and `seq` of 6-7 cells 0-15, no repeats**; prompt "Watch the flashes!" (Shorts keep 3x3).
- **missing** `{"type":"missing","prompt":"Remember these 6!","prompt2":"Which one is missing?","before":[6 emoji],"gone":i,"options":[3 emoji incl. before[gone]],"right":i}` — **long video: 3x3 = `before` of 9 different emoji, prompt "Remember these 9!"**.
- **flipped** `{"type":"flipped","prompt":"Find the upside-down one!","emoji":e (clearly not symmetric: 🐟🐌🦒🚗🐘),"pos":[row,col]}` — **now HARD**: the odd emoji is MIRRORED (not turned upside-down) inside a big grid (12x6 long / 7x9 Shorts; `pos` row 0-5 col 0-11 long, row 0-8 col 0-6 Shorts). Optional `"mode":"rot"` (upside-down, easy) and `"grid":[cols,rows]`.
- **bug** `{"type":"bug","prompt":"Where does the bug stop?","start":[r,c],"moves":"4-6 of U/D/L/R"}` must stay on the 4x4 grid; answer = check output. **VOICE-DRIVEN: no arrows on screen — Hoot SPEAKS the moves.** The bug's `say.items[i].q` must name the start square and every move in order ("Bug starts on ten. Up, up, left, down, right!") — `check` fails if the spoken moves differ from `moves`. (Optional `"show_arrows":true` brings the arrows back.)
- **countdiff** `{"type":"countdiff","prompt":"How many differences?","scene":[9 emoji],"diffs":[[cell,alt],...] (1-3),"options":["1","2","3"],"right":len(diffs)-1}`
- **cardflip** `{"type":"cardflip","prompt":"Remember the cards!","prompt2":"Find the matching pair!","cards":[9 emoji, exactly 2 == target] (**long video: 16 cards = 4x4, 15 different emoji + the target twice**),"target":e,"options":["a & b" strings, one is the true pair],"right":i}`
- **diceflash** `{"type":"diceflash","prompt":"Remember the dice!","prompt2":"What was the total?","dice":[2 values 1-6],"options":[3 strings],"right":i}`
- **zoom** `{"type":"zoom","prompt":"What is it? Guess early!","emoji":e,"focus":[0.3-0.7,0.3-0.7],"options":[3 names],"right":i}` — starts zoomed in 4.5x and zooms out to 2.4x while you guess (a little wider than before); optional `"zoom":[start,end]`.

- **shapemiss** `{"type":"shapemiss","prompt":"Watch closely!","prompt2":"Which one never appeared?","stack":true,"seq":[5 emoji],"options":[3 emoji: exactly one NOT in seq],"right":i}`
- **spotlight** `{"type":"spotlight","prompt":"What's in the dark?","emoji":e (big clear animal/object),"options":[3 names],"right":i}`
- **pixel** `{"type":"pixel","prompt":"Guess before it clears!","emoji":e,"options":[3 names],"right":i}`
- **colorcount** `{"type":"colorcount","prompt":"How many GREEN shapes?","counts":{"green":n,"red":n,"blue":n,"yellow":n} (total ≤ 30),"ask":colour,"seed":n,"options":[3 strings],"right":i}`

- **numflash** `{"type":"numflash","prompt":"Remember the number!","prompt2":"Which number did you see?","number":"5 digits (**long video: 6 digits**)","options":[5 different look-alike numbers of the same length incl. number (swap 2 digits, change 1 digit…)],"right":i}`
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
  Plus one more call per Short for its spoken hooks: `python3 pipeline/tools.py hooks sNN.json` → download to `work/TARGET/voice/sNN-hooks.mp3` → `tools.py fillhooks`.
- Long video: `python3 pipeline/tools.py prompt long.json 2` → 2 calls (part 1 and part 2), plus
  `python3 pipeline/tools.py hooks long.json` → 1 more call for the spoken hooks (download it to `work/TARGET/voice/hooks.mp3`,
  then `python3 pipeline/tools.py fillhooks long.json work/TARGET/voice/hooks.mp3`).
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
Use the **fixed Shorts slots 13:00, 15:00, 17:00, 19:00, 21:00 IST** (in that order; skip any slot earlier than 30 minutes
after now). They are fixed because the scheduled task "Wit Wonderland – new upload checklist" runs at :12 past each slot
to give every Short its thumbnail, tags, playlist, related video and pinned comment right after it goes live.
The long video is for **11:00 IST** (Aman's schedule: day runs 11 AM – 9 PM).
**Long-video thumbnail (high-CTR style, Aman 17 Nov):** `python3 pipeline/thumb_long4.py thumbs/TARGET-long.jpg "TOP LINE" "BIG" <common emoji> <odd emoji>`
(e.g. "99% CAN'T FIND IT" "1%" 🐼 🐨; yellow sunburst, huge outlined text, one big odd-one-out card, red arrow, big owl). Change the top line,
big word and emoji pair EVERY day (look-alike pairs: 🐼/🐨, 🍔/🥪, 🐶/🐺, 🍊/🍑, 🚗/🚕, ⚽/🏀) so no two days look the same; never reuse yesterday's.
Look at it at phone size (246x138) before using it. Look at it, commit it to **main** under thumbs/, and give Aman its raw URL
(https://raw.githubusercontent.com/amanupputuri/shorts-media/main/thumbs/TARGET-long.jpg) with the long video so he sets it as the
custom thumbnail when uploading.
**Buffer's YouTube channel only accepts Shorts** (vertical, ≤ 3 min) — do NOT send the long video to Buffer. Put only the
N Shorts in posts.json. For the long video, write its title, full description and the time 11:00 into
`pipeline/schedule/TARGET.json` and into the final report with its download URL, so Aman can upload it in the YouTube app.
Write `work/TARGET/posts.json` = list of {"url", "title", "text", "due_ist": "TARGET HH:MM"} and run
`python3 pipeline/buffer_post.py schedule work/TARGET/posts.json`. Every step must come back `PostActionSuccess`;
if one fails, fix it and schedule only that one again (never re-send ones that succeeded — that would post twice).
Buffer sets: public, category Education (27), not made for kids, notify subscribers. Buffer can't set tags or a
first comment — the evening Studio task pins the comment and sets the related video.
- Title: SHORT (3–7 words + 1–2 emoji, ≤ 60 chars), challenge or curiosity style, keep the searchable puzzle words
  (e.g. "Can You Spot the Difference? 🛁👀", "Only 1% Find the Owl 🦉"), then "#shorts". Use `insights.json` best_title_patterns
  and themes (seasonal: Christmas/winter from late Nov). Never long vague titles.
- Description (text): 1 hook line; "Can you get all 6?" style challenge; the puzzles in plain words (no answers in
  the first lines; answers after "ANSWERS (no peeking!)"); comment-your-score line; subscribe line with
  https://www.youtube.com/channel/UCl870UQHJt9aZCNW-IhK1gA?sub_confirmation=1 ; a "Search: …" line with 10–14 search
  phrases separated by commas (brain teaser, eye test, puzzle game, iq test, can you solve this, wit wonderland, the
  puzzle type names…) in place of tags; then 6–10 hashtags.
  Long video: list the 20 puzzle types.
- Save the Buffer post ids + titles + times to `work/TARGET/scheduled.json` and also commit a copy to **main** as
  `pipeline/schedule/TARGET.json` (the evening Studio task reads it).

## 7. Wrap up
- Append every Short's hook and its spoken hooks (as "teasers") to `pipeline/hooks_used.json` ({"date": TARGET, "hook": ..., "teasers": [...]}).
- Append the new puzzle keys (e.g. "cups:1:0-1,1-2,0-2", "odd4:penguin") to `pipeline/used.json` on **main**, commit,
  push (use `git -c push.negotiate=true push`).
- Send a short report (SendUserMessage + PushNotification if available): date, the 5 Short formats, how many
  posts scheduled, any failures.
