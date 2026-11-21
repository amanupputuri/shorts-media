# WHICH ONE WILL STAY TILL THE END? — Wit Wonderland Short
Trigger: Aman says "which one will stay till the end".

## Format (approved 21 Nov 2026)
- 6 rounds (2 EASY, 2 MEDIUM, 2 HARD), 14.5 s each (1.5 s intro + 10 s play + 3 s reveal) ≈ 87 s, 1080x1920 30 fps, slide transitions.
- Each round uses a TOTALLY different set of 4 Microsoft Fluent 3D icons (e.g. animals / fruit / sea / vehicles / sweets / weather).
- 7x7 board: winner x13, the 3 others x12. A 3D pointing hand swaps two tiles; exactly one line of 4 identical tiles (horizontal or vertical) flashes gold and bursts. 12 moves per round, no gravity, no accidental extra lines (m3.py builds this backwards and verifies forward). Decoys survive until the last moves; one tile left, glowing.
- Question: "WHICH ONE WILL / STAY TILL THE END?" (gold 2nd line). Level pill "EASY • ROUND 1/6". 4 big answer buttons under the board; reveal = winner button green + "THE ___!".
- Board slightly left of centre (right edge clear for YouTube buttons), glowing LIKE pill, static Hoot (think/cheer), warm gradient bg.
- Audio: ticks each second, swish per swap, pop per burst, ding on reveal, whoosh between rounds.
- Voice (Hoot cPmGMZvsZ24aRiDy6Vc2, eleven_v4, 1 take, [long pause] split): hook "Good luck will follow you… if you guess even one right!", question line at round start, answer at reveal; "getting harder" at round 3, "Only two left" at round 5. No like/subscribe line.
- Thumbnail: Google Flow (pane must be visible) — board of 3D tiles, a row of 4 bursting, hand swiping, one gold "?" tile, "GOOD LUCK IF YOU GET ONE!" badge, Hoot; never show winners.

## Run
1. New icon sets: download Fluent 3D PNGs into ic/, add names to AN in cc.py.
2. Rounds: edit R in gen.py (level, 4 icons, winner) and run `python3 gen.py <i>` for i=0..5 (writes rounds/r{i}.json). Existing jsons can be reused by renaming icons (structure only depends on order).
3. Preview frames with ccv3.frame(t); show Aman. Render: python3 ccv3.py 0 2 & python3 ccv3.py 1 2; concat; mix with audio_smooth (EV + voice lines) and loudnorm I=-14.
