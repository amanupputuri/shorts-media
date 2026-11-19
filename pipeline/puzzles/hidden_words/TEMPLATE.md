# "PUZZLES CROSS WORD" template: "Find All 10 Hidden ___" (Wit Wonderland word-search Short)

The final, approved style (first published as https://youtube.com/shorts/DpuDss7tRHk).
When Aman says **"puzzles cross word"**, make a new video in exactly this style with a new theme.

## Format
- Vertical 1080x1920, 30 fps, about 1:40 (99.7 s), padded to the music bars so it loops.
- 10 puzzles, each on a 6x6 grid with one 4-letter word to find, easy to hard:
  - Puzzles 1–3 (lvl 0): horizontal or vertical, forwards. The filler letters exclude the target's letters.
  - Puzzles 4–6 (lvl 1): adds backwards words. The filler uses the full alphabet.
  - Puzzles 7–10 (lvl 2): diagonals and diagonal-backwards. The filler is heavy with the target's letters.
  - Each answer appears exactly once (`ws.build()` checks this).
- Intro "HOW TO PLAY": the word ANIMAL hidden diagonally backwards, crossed with a red line plus a sound effect, then the caption "DIAGONAL + BACKWARDS!".
- For each puzzle:
  1. slide in (ease_back, 0.5 s)
  2. announce line
  3. "GET READY…" and a countdown with a pulse (4 s for puzzles 1–4, 5 s for 5–10) and ticks
  4. "TIME'S UP!"
  5. end line
  6. slide out to the left
- **No answer reveal.** The answers go in the description.
- Chip at the top shows the word plus an animated Flow icon. A progress pill and dots sit top-right.
- An animated LIKE badge (Flow) on puzzles 1–5 and SUBSCRIBE on 6–10, both top-left.
- On puzzle 5, a pill: "Need more time? Pause the video!"
- Animated Hoot (brown owl: gold glasses, graduation cap, red scarf) bobs to the voice envelope. Poses: think, magnify, cheer.
- Equal spacing throughout. Layout constants are in `ws.py`.
- Audio (`audio.py`):
  - music: 118 bpm, D-Bm-G-A, bars fitted to the length for looping
  - sound effects: pop, tick, ding, swish, whoosh, boop
  - voice ducking
  - mix: loudnorm I=-14, TP=-1.5, AAC

## Voice (Hoot, ElevenLabs voice `cPmGMZvsZ24aRiDy6Vc2`, model `eleven_v4`). Generate it LAST.
29 lines in one take, separated by `[long pause]`. Split them with ffmpeg silencedetect (`n=-35dB:d=0.45`) into `l00..l28.wav` and `segs.json`.
- Line 0 is the hook: "Only owl eyes can find all ten hidden <theme>!"
- Line 1: "Like this! The word <EXAMPLE>, hiding diagonally, backwards!"
- Line 2: "Ready? Let's go!"
- Then one announce line, an optional middle line and one end line per puzzle (mapping in `ws2.LINES`):
  - announce lines like "Here comes the X!" or "Next is the X!"
  - the middle line on puzzle 2 is the like/subscribe ask (it comes early)
  - the middle line on puzzle 5 is "Need more time? Pause the video!"
  - the middle line on puzzle 9 is "Comment how many you found!" (it comes late)
  - end lines like "I hope you found this one!" or "Did you spot it?"
  - the last end line is "Answers are in the description!"
- Never say "first puzzle" or "last puzzle". No hook after the comment ask.

## How to make a new one
1. Pick a theme (fruits, colours, countries, ocean animals…) and 10 four-letter words. Edit `PUZ` in `ws.py` (placements and levels as above) and the example word.
2. Make the icons in Google Flow, one per word, in the same 3D cute style. Cut them out with rembg (`isnet-anime`) and crop to the alpha bbox (threshold 60). Save them as `fl/i_<word>.png`.
3. Render a silent draft (`python3 ws2.py draft.mp4`) and show Aman frames or the draft first.
4. After approval, generate the voice (29 lines) and set `VOICE_DIR`. Then run `final2.py` to make the mix and render the final with the mux.
5. Make the thumbnail in Google Flow at 9:16: "FIND 10 <THEME>!", a "99% FAIL" badge, the grid, Hoot with his magnifier.
6. Upload (see RUNBOOK):
   - title: "Find All 10 Hidden <Theme>! 🦉 Only Owl Eyes Can | Word Search Puzzle #shorts"
   - description: answer key, comment ask, subscribe link, hashtags (template in `description.txt`)
   - 15 tags, not made for kids, public
   - then pin "How many <theme> did you find? 👇", set the related video to the long quiz, set the language to English, add it to a playlist
