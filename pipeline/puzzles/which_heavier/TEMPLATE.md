# WHICH IS HEAVIER — Wit Wonderland Short
Trigger: Aman says "which is heavy" / "which is heavier".

## Format (approved 20 Nov 2026)
- 6 pairs (2 EASY, 2 MEDIUM, 2 HARD), ~80 s, 1080x1920 30 fps. No intro/outro slides, no like/subscribe voice.
- Polished gold balance scale on a glowing stage with sparkles + white podium; 3D Microsoft Fluent emoji icons (MIT) on the pans (whole watermelon drawn in code); glowing red VS badge.
- Even ~70 px spacing: level gradient pill 140 → gradient title "WHICH IS HEAVIER?" 240 → scale (PY=450) → A/B (C=SAME for the trick) options PY+795 → 3 s timer / answer word PY+1045. Glowing LIKE pill top-left, static Hoot bottom-left, right edge clear.
- Reveal: scale tips with bounce toward heavier side (golden glow), "Avg ___ kg" tags under both items, correct option green, big green answer word. Weights never on question screens.
- Mix answer sides (A/B/C). Last question = trick (1 kg feathers vs 1 kg bricks → SAME).
- Script: hook "Most people failed this quiz… let's see if you can beat it!", "now it gets tricky" after Q2, "Only two left… this one splits everyone" before Q5, "the one most people fail" on Q6; every answer line = one wow fact. Hoot voice cPmGMZvsZ24aRiDy6Vc2, eleven_v4, 1 take, [long pause] between lines.
- Thumbnail: Google Flow (pane must be visible), 9:16, level scale with two items NOT in the video + "?" marks, "MOST PEOPLE FAIL!" badge, Hoot thinking.

## Run
1. Edit Q in hv.py (left icon, label, right icon, label, 'L'/'R'/'S', left avg, right avg, level). Icons from raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/<Name>/3D/<name>_3d.png into ic/.
2. Preview sheet (screen(i,1,(3,.6)) and screen(i,1,tilt=1,reveal=True)) → show Aman.
3. Voice → split with silencedetect into vo/l00..l12.wav + vo/lens.json; python3 mixhv.py; python3 hvv.py 0 2 & python3 hvv.py 1 2; concat parts; mux mix.wav (apad, loudnorm I=-14).
