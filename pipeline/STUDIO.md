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

## 6. Community posts (when Posts tab is available)
Create → Post: an image (a puzzle question frame from today's video) + "Can you find it? 👀 Answer in the comments!"
or a quiz post with 3 options. Max 2 per day.

## Log
- 2026-11-17: related video → 16 Nov long ("Memory, Focus & IQ Test") set on uwxQXJoo4X0, E2qM9D5hePo, nWAZdGW0XWE. Save kept hanging on lbxkNwup954 (Studio was slow / 504) — still to do: lbxkNwup954 (16 Nov long), and the 15 Nov Shorts qW8--lvbzQg, ocdkD64Rxs4, zL6DCQVwDDg, BbnrciUKNoY → 15 Nov long ("How Many Can You Solve? (Memory, Spot It & More)"). Tip: after Save, wait until the dim overlay is gone before leaving the page.
