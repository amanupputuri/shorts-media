# SPOTLIGHT — "What's hiding in the dark?" (Wit Wonderland)
Trigger: Aman says "SPOTLIGHT".

## Format (final approved style, 20 Nov 2026)
- 6 puzzles, no intro slide, no outro slide. 1080x1920, 30 fps, ~62 s.
- Each puzzle: 0.6 s in + 6 s explore (ring countdown 6..1) + 0.7 s hole grows to full + 3 s hold on answer.
- Close-up animal/bird photos from Unsplash (search with plus:none, call download_asset, fetch via built-in browser JS -> base64, 900x900).
- Spotlight hole (radius 118 -> 70 from EASY to HARD) travels ONLY over the animal: per-photo waypoints WP[i] (Catmull-Rom loop, 1.4 s per segment). Check a frame sheet that no waypoint lands on empty background.
- Levels: 2 EASY, 2 MEDIUM, 2 HARD. 3 options each (A/B/C pills), names NEVER repeat across puzzles.
- Warm smooth gradient backgrounds (warm(i)), glowing red "LIKE" pill top-left on every puzzle, static Hoot bottom-left (magnify, cheer on reveal), right side clear.
- Even spacing: chip 150, heading 250, stage 90..990 x 330..1230, pills 104 tall / 26 gap, timer 44 below pills.
- Voice: Hoot (ElevenLabs cPmGMZvsZ24aRiDy6Vc2, eleven_v4, 1 take, [long pause] between lines, split with silencedetect). Per puzzle: question line at +0.5 s, answer line at +6.75 s. Puzzle 5 question starts "Two more to go!". No intro/outro voice, no whispers, never "first/last puzzle".
- Audio: audio_smooth (ticks each second, swish on reveal, ding, whoosh transitions), loudnorm I=-14.
- Thumbnail: Google Flow (Nano Banana) vertical, warm gradient, golden spotlight on an animal eye, big title, red "ONLY 1% GET 6/6!" badge, Hoot bottom-left.

## Run
1. Put photos in a folder as s1..s6.jpg; export SPOT_PH=<folder>. Edit P (options/answer/radius/level) and WP in sp.py.
2. Preview: python3 -c "import sp" + render screen(i,2,(4,.4)) and screen(i,reveal=True) sheet -> show Aman first.
3. Voice -> vo/l00..l11.wav (q,a pairs); python3 mixsp.py; python3 fin.py 0 2 & python3 fin.py 1 2 (parallel, ~7 min); concat parts; mux mix.wav with apad + loudnorm.
