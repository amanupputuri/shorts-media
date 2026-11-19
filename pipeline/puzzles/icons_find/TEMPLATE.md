# "CROSS WORDS ICONS PUZZLE" template: Find All Matching Icons (Wit Wonderland emoji Short)

This is the final approved style, first made 19 Nov 2026 as "Find All Matching Icons! 🦉 Only Owl Eyes Get 10/10".
When Aman says **"cross words icons puzzle"**, make a new video in exactly this style with NEW icon sets.

## Format
- **Video:** vertical 1080x1920, 30 fps, about 2:00, padded to the music bars so it loops.
- **Intro, "HOW TO PLAY" example:** a 4x4 fruit grid. Red circles draw around the 4 🍎 one by one, then "4 APPLES FOUND!" appears. Hoot says the hook, then the how-to line.

### The 10 puzzles
Each puzzle is an **8x9 grid (72 boxes)**, smaller and centred (CELL 94, GAP 6, GY 540). That keeps it clear of YouTube's like/comment/share buttons on the right and the title area at the bottom.

| Puzzles | Level | Find | Icon types | Leftover | Timer |
|---|---|---|---|---|---|
| 1–2 | Easy | 5 | 14 × 5 = 70 | 2 icons that appear once | 4 s |
| 3–6 | Medium | 8 | 9 × 8 = 72 | none | 5 s |
| 7–10 | Hard | 10 | 7 × 10 = 70 | 2 icons that appear once | 6 s |

- Easy needs 16 emoji, medium 9, hard 9.
- **Every icon type appears exactly as many times as the target**, so counting doesn't give the answer away.
- **One colour per puzzle.** Every icon matches the target's colour (orange, green, yellow, red, blue, purple, brown, pink, grey, black). Check the colours with `hue.py` or by eye. Some Noto emoji look the wrong colour: the butterfly and bat render brown, and the pig face is pale (recolour it with `pinkify` in grids.py).
- **Different icons for every puzzle**, with no repeats inside a video. Use a new set and new targets for each new video.
- **Fully scattered.** The `g2.scatter` simulated annealing makes sure no two matching icons touch, including diagonally.
- **Every icon stays inside its box.** Easy icons are straight at 86% of the box. Medium icons tilt ±10° and hard icons ±20°, at 74–86% of the box.
- **Header** (centred, equal 30 px gaps): level pill "EASY • 1/10", then "FIND N", then a white box with the target icon.
- **Below the grid:** timer bar and countdown, "GET READY…", then "TIME'S UP!".
  - Puzzle 5 adds an "II PAUSE FOR MORE TIME" pill.
  - **No answer reveal.** The answers go in the description as Row/Column (`key.txt`).
- **Animation:**
  - Hoot sits bottom-left, bobbing to his voice: think while getting ready, magnify during the countdown, cheer after.
  - LIKE badge on puzzles 1–5 and SUBSCRIBE badge on 6–10, top-left.
  - Puzzles slide in (ease-back) and slide out to the left.
- **Audio:** 118 bpm music fitted to the bar length, pop/tick/ding/whoosh sound effects, voice ducking, then mix with loudnorm I=-14, TP=-1.5 and AAC 192k.

## Hoot voice
ElevenLabs voice `cPmGMZvsZ24aRiDy6Vc2`, model `eleven_v4`, one take. Don't use the whispers tag (Aman's rule).
- 22 lines separated by `[long pause]`. Split them with silencedetect at `n=-35dB:d=0.45`, using every pause of 1.0 s or more.
- **Line 0, hook:** "[excited] Psst! Only one in a hundred can find them ALL… are you one of them?"
- **Line 1:** "[cheerful] Here's how to play: find every matching icon, like these four apples! [excited] Let's go!"
- **Each puzzle** gets an announce line, a mid line on puzzles 2 and 5, and an end line. `vid2.LINES` maps them.
  - Puzzle 2 mid line: the like/subscribe ask, early, played straight after the announce line.
  - Puzzle 5 mid line: "Need more time? Pause the video. I won't tell!"
  - Puzzle 9 end line: "How many did you find? Tell me in the comments!"
  - Puzzles 8 and 10 have no end line.
- Puzzle 10 ends with "…can you?", which loops back into the hook.
- Never say "first puzzle" or "last puzzle". No hook after the comment ask.
- Show Aman the script first, with the targets table. Generate the voice only after he approves it.

## How to make a new one
1. Write a new `plan.py`: 10 (level, emoji string) entries, target first. Use colour-matched sets that are new for this video.
2. Build the grids and save the layouts and answer key (see the step-2 code in this file's history: `g2.make` → `lays.pkl` + `key.txt`). Send a contact sheet for approval.
3. Write the voice script (format above) and get it approved. Then generate the voice into `VOICE_DIR`, split it to `l00..l21.wav` and update `segs.json`.
4. Run `python3 mix.py` (makes mix.wav), then `python3 vid2.py silent.mp4`, then the ffmpeg mux (loudnorm) to make the final MP4.
5. Make the thumbnail in **Google Flow** (9:16): "FIND 10 <TARGET>!", a red "99% FAIL" banner, a glowing icon board with one target circled and a "?", and shocked Hoot (brown owl, gold glasses, graduation cap, red scarf, magnifying glass). Keep the right edge clear.
6. Write the upload text from `upload_text.txt` (SEO version):
   - Title: "Find the Emoji Puzzle 🔍 Only 1% Find All 10! | Eye Test Brain Teaser #shorts"
   - Description: keywords in the first 2 lines, then the level list, then the answer key, then the subscribe link.
   - Hashtags: #findtheemoji #emojipuzzle #eyetest first.
   - About 25 tags.
   - Pinned comment: "Be honest 👀 How many did you find out of 10?"
   - Category Entertainment, not made for kids, English, related video set to the long quiz.
7. Aman uploads it himself unless he asks for it to be uploaded.
