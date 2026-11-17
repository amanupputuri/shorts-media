# Wit Wonderland — Studio growth playbook (run when Aman says "start improving my channel")

Aman runs this on demand while his laptop is on. Use the Claude desktop app's **built-in browser**
(tools `...Claude_Browser__...`), which is signed in to YouTube. Never sign out, never type passwords.
Set the tab viewport to 1400x900 while working; reset to preset "desktop" when done.
Channel id: UCl870UQHJt9aZCNW-IhK1gA. Studio: https://studio.youtube.com/channel/UCl870UQHJt9aZCNW-IhK1gA

Goal: monetization. Today: 1,000 subs + 4,000 long-form watch hours (12 months) OR 10M Shorts views (90 days).
From 1 Feb 2027: 8,000 hours OR 20M Shorts views. Shorts feed viewers into the long videos (watch hours).

Do the steps in order; skip what is already done. Log what you did at the bottom of this file (date + one line each).

## 1. Related video on every Short (biggest win)
Shorts list: /videos/short. For each public Short with "Related video: None": open /video/ID/edit → pencil on
"Related video" → pick the long video ("20 Eye & Brain Puzzles…") published the SAME day (else the newest one) → Save.

## 2. Pinned comment
For every public video without it: on youtube.com/watch?v=ID post "What was your score? 👇" as the channel and pin it.
Do not reply to viewer comments (Aman does that) unless he asks.

## 3. Playlists (watch time from long videos)
Keep playlists: "20 Eye & Brain Puzzles" (all long videos), and one per Shorts format family
("Memory Tests", "Spot the Difference", "Odd One Out", "Find It Puzzles", "Brain Math"). Add each video to the right one
(video details → Playlists). Create a playlist if missing (public, short description with search words).

## 4. Long videos: end screen + thumbnail
For each long video: Editor → End screen → "Video: best for viewer" + "Subscribe" element (last 10–20 s).
Thumbnail: if a file `thumbs/DATE-long.jpg` exists on the media branch, upload it.

## 5. Weekly review (once a week)
Analytics → Content: for Shorts, note "Viewed vs swiped away" and average % viewed per video; for long videos,
average view duration and CTR. Rank the formats (format = the Shorts format of that day, see tools.py day DATE).
Write the ranking to `pipeline/insights.json` ({"updated": DATE, "top_formats": [...], "weak_formats": [...],
"best_title_patterns": [...], "notes": "..."}), commit to main. Research tab: note rising searches about puzzles /
brain teasers / eye tests and add 5–10 theme ideas to insights.json "themes". The daily RUNBOOK reads it.
Report the findings to Aman in 5–8 short lines and suggest format changes (he decides).

## 6. Community posts — 2 per day, scheduled between 13:00 and 20:00 IST
Images: render a puzzle question frame with engine.py (spec: orientation "v", pill_text "WIT WONDERLAND DAILY PUZZLE",
mascot false, item fact ["",""], nudge "Answer in the comments!"), still at t=4.5, crop (0,120,1080,1650) → resize
1080x1530 → crop to 1080x1350 (4:5). Commit to main as posts/DATE-a.jpg / -b.jpg (public raw URL). Vary puzzle types.
Posting (built-in browser, youtube.com allowed): open https://www.youtube.com/channel/UCl870UQHJt9aZCNW-IhK1gA/posts →
click the text box, type the caption (question + "Comment your answer below! 👇" + 3 hashtags) → in JS fetch the raw
image URL, make a File, put it into the first `input[type=file][accept="image/*"]` via DataTransfer and dispatch
"change" → click "Image" (shows the preview) → click "Delete" on the preview and inject the file AGAIN (only the second
injection enables the Post button) → dropdown arrow next to Post → "Schedule post" → set date (calendar) and time
(e.g. 2:15 PM / 6:45 PM; use JS scrollIntoView on the [role=option] if the list is long) → Schedule → check the
SCHEDULED tab. Several days can be scheduled in one session.

## 7. Long-video thumbnails
If a long video still has an auto thumbnail: make one with pipeline/thumb_long.py (or use thumbs/DATE-long.jpg), commit to main,
open /video/ID/edit, in JS fetch the raw URL → File → put into the only `input[type=file]` (accept image/jpeg,image/png) via
DataTransfer + "change" → Save (wait until Save greys out).

## Log
- 2026-11-17: related video → 16 Nov long ("Memory, Focus & IQ Test") set on uwxQXJoo4X0, E2qM9D5hePo, nWAZdGW0XWE. Save kept hanging on lbxkNwup954 (Studio was slow / 504) — still to do: lbxkNwup954 (16 Nov long), and the 15 Nov Shorts qW8--lvbzQg, ocdkD64Rxs4, zL6DCQVwDDg, BbnrciUKNoY → 15 Nov long ("How Many Can You Solve? (Memory, Spot It & More)"). Tip: after Save, wait until the dim overlay is gone before leaving the page.
- 2026-11-17: 2 image posts scheduled — Spot the difference (14:15) and Find the owl (18:45).
- 2026-11-17: new channel logo (Hoot on yellow), banner (brand/), puzzle-focused description and keywords published.
- 2026-11-17: custom thumbnails uploaded for long videos VEQQq8HeMoo (16 Nov) and E70jagKMdfc (15 Nov).
- 2026-11-17: related video set on lbxkNwup954 (16 Nov long) and all 4 of the 15 Nov Shorts (15 Nov long). Today's 5 Shorts still need one once live + today's long video is up.
- 2026-11-17: playlists created — "20 Eye & Brain Puzzles – Full Brain Workouts 🦉" (2 long), "What Changed? Memory Test Shorts 🧠" (4), "Odd One Out Challenges 👀" (4), "Quick Brain Quiz – 3 Questions 🧠" (8), "Did You Know? Everyday Science 🔬" (12). Method: Studio → Content → Playlists → New playlist → Add videos (picker checkboxes, aria-label "Select <title>") → Done → Create. Add each new long video / Short to the matching playlist.
- 2026-11-17: end screens (template "1 video, 1 subscribe": Best for viewer + Subscribe) on VEQQq8HeMoo and E70jagKMdfc. New long videos: End screen → "Import from latest video" → Save.
- 2026-11-17: "What was your score?" comment pinned on both long videos and the 8 Shorts of 15–16 Nov (youtube.com/watch → comment ⋮ → Pin → Pin).
- 2026-11-17: 6 image posts scheduled: 18 Nov 14:15 Christmas math, 18:45 find the owl; 19 Nov 13:45 odd pair, 19:15 finger count; 20 Nov 14:45 leg count, 18:15 board copy. Images posts/2026-11-18..20-a/b.jpg (crop now keeps the pill: frame crop y110..1450 (1540 for grid/board) on the frame background). Time list items use a narrow no-break space ("2:15 PM"); date: type into input#textbox in the calendar, Enter, click the selected day to close.

## 8. New-Short checklist (do once each Short is live — Buffer can't set these)
1. Custom thumbnail 1080x1920 (hard-level frame from the mp4 panels + "SPOT THE DIFFERENCE!" style title + pink badge + Hoot) → thumbs/DATE-sNN.jpg → upload via the file input on /video/ID/edit.
2. Related video → that day's long video (or latest long video until it's up; switch later).
3. Tags (Show more → Tags input: insertText "a, b, c," then Enter + blur; ~15 tags, <500 chars, format words + "wit wonderland, professor hoot").
4. Video language + Title/description language → "English".
5. Playlist → matching format playlist (Spot the Difference Challenges 🔍 / What Changed? / Odd One Out / Quick Brain Quiz / 20 Eye & Brain Puzzles).
6. Save (wait until Save greys out), then post + pin "What was your score? 👇" on youtube.com/watch?v=ID.
## 9. New-long-video checklist (Aman uploads it himself)
1. Thumbnail: thumbs/DATE-long.jpg if it exists (else make one with thumb_long.py) → upload on /video/ID/edit.
2. Tags (~15, puzzle words), Video language + Title/description language "English", playlist "20 Eye & Brain Puzzles – Full Brain Workouts 🦉", Save.
3. End screen: End screen → "Import from latest video" (or template "1 video, 1 subscribe": Best for viewer + Subscribe) → Save.
4. Post + pin "What was your score out of 20? 👇".
5. Re-point that day's live Shorts' related video to this long video.

## 10. Auto-check (scheduled task "Wit Wonderland – new upload checklist")
Runs daily at 13:12, 15:12, 17:12, 19:12 and 21:12 IST (12 min after each fixed Shorts slot) on Aman's computer (built-in browser). Each run: list Studio Shorts + Videos published in the last 3 days;
a video counts as DONE when it has tags (not 0/500), a playlist, language English, a related video (Shorts) / end screen (long), a custom
thumbnail and a pinned score comment. Do sections 8/9 for anything not done. Never change titles/descriptions, never delete anything.
If the browser/computer is unreachable, stop and say so (the next run catches up).

- 2026-11-17: Cz6U2tdEm6A (17 Nov s04) fully done with the checklist above; new playlist "Spot the Difference Challenges 🔍" created.
- 2026-11-17 (auto-check 15:38): ykbrvOcy-PQ (17 Nov s05) — full checklist: thumbs/2026-11-17-s05.jpg, related → 16 Nov long VEQQq8HeMoo (17 Nov long not uploaded yet), 15 tags, English ×2, playlist Spot the Difference, pinned score comment.
- 2026-11-17 (auto-check): uwxQXJoo4X0 (16 Nov) — custom thumbnail (thumbs/2026-11-16-uwxQXJoo4X0.jpg) + English languages.
- 2026-11-17 (auto-check): E2qM9D5hePo (16 Nov) — custom thumbnail + English languages.
- 2026-11-17 (auto-check): nWAZdGW0XWE (16 Nov) — custom thumbnail + English languages.
- 2026-11-17 (auto-check): lbxkNwup954 (16 Nov) — custom thumbnail + English languages.
- 2026-11-17 (auto-check): qW8--lvbzQg (15 Nov) — custom thumbnail + English languages.
- 2026-11-17 (auto-check): ocdkD64Rxs4 (15 Nov) — custom thumbnail + English languages.
- 2026-11-17 (auto-check): zL6DCQVwDDg (15 Nov) — custom thumbnail + English languages.
- 2026-11-17 (auto-check): BbnrciUKNoY (15 Nov) — custom thumbnail + English languages.
- 2026-11-17 (auto-check): VEQQq8HeMoo (16 Nov long) and E70jagKMdfc (15 Nov long) — English languages (tags/playlist/thumbnail/end screen/pin already done).
- Method note: 15/16 Nov mp4s are no longer on `media`, so panel frames were grabbed from the youtube.com watch page (canvas drawImage of the MSE <video> at puzzle 3, shown full-window, screenshot) and composed with pipeline/thumb_short.py. Language dropdowns: open with a real click on the field, then JS-click the visible tp-yt-paper-item "English" (clicking refs after scroll_to picks the wrong language). Playlist checkbox refs can also land on the wrong row — verify with a screenshot.
- 2026-11-17 (manual, 17:40): Gf1iTueoGxo (17 Nov s02 Food spot-diff) — thumbnail, 17 tags, English languages, playlist Spot the Difference Challenges, related video (16 Nov long), pinned score comment. The 17:12 auto-run had only made the thumbnail file and never applied it, so check that runs finish all steps. ykbrvOcy-PQ (s05) was already complete.
- 2026-11-17 (manual, 19:00): V29VJ5NU4hE (17 Nov s03 Animal spot-diff) — thumbnail (thumb_short.py on hard-level frame 46s), 17 tags, English languages, playlist Spot the Difference Challenges, related video (16 Nov long), pinned score comment; verified after reload.
- 2026-11-17 (manual, 22:35): eKPtZicQUBU (17 Nov s01 sweets spot-diff, last Short of the day) — thumbnail, 17 tags, English languages, playlist Spot the Difference Challenges, related video (16 Nov long), pinned score comment. 9:12 auto-run had not done it. Long video for 17 Nov still not uploaded.
