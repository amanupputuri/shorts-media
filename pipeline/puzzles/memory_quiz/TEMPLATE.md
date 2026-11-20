# "CAN YOU REMEMBER EVERYTHING?" template (Watch & Answer memory quiz Short)

This is the final approved style, first made 19 Nov 2026 as "Can You Remember Everything? 🧠 Memory Test Only 1% Pass! | Watch & Answer".
When Aman says **"can you remember everything"** (or "memory quiz" / "watch and answer"), make a new video in exactly this style with NEW clips and questions.

## Format
- **Video:** vertical 1080x1920, 30 fps, about 2:30, padded to the music bars so it loops.
- **Order:** Intro, then 3 rounds (EASY, MEDIUM, HARD). Each round goes: round title, then an ~8 s cartoon clip, then its questions.
  - Questions per round: 3 / 4 / 4 (11 in total). Each question has its own gradient background colour; never use a blurred clip still, because it gives the colours away.
  - A comment-ask screen comes before the final question.
- **Clips:** made with **Google Flow → Veo**: vertical 9:16, a 3D Pixar-style sunny park, a static camera (so things can be counted), and the same girl Mia (brown pigtail buns, pink ribbons, pink dress).
  - Easy: Mia jumps, with family nearby.
  - Medium: ball, dog, people walking past.
  - Hard: a busy park (balloons, birds, cats, ice-cream cart).
  - Download them at 720p through Flow's "Download media" button. They land in ~/Downloads; stage them from there.
  - Veo Quality costs 100 credits per clip and Lite costs 10. Check the Flow credits and ask Aman which model to use.
- **Questions:** written from what is actually in the clips. **Each question is different** (no repeats across rounds). Each one has **3 options (A/B/C)**. Aman supplies or confirms the answers.
- **No answer reveal in the video.** The answers go in the description.
- **Look (`_shared/design.py`):**
  - Fonts: Lilita One for headings, Fredoka for text.
  - Question text: balanced line wrapping with fixed line spacing.
  - A/B/C pill options, a ring timer (3 s), then "TIME'S UP!".
  - "WATCH CAREFULLY!" chip and a progress bar on the clips.
- **Hoot is STATIC** (no animation; Aman's rule).
- **Transitions:** slide-in screens, and a white flash plus zoom into each clip. Sound effects: whoosh, pop, tick, ding.
- **The clips' own audio plays at 0.35 volume** under Hoot.

## Hoot voice
ElevenLabs voice `cPmGMZvsZ24aRiDy6Vc2`, model `eleven_v4`, one take. **No whispers.** Split the take with silencedetect.
- **Hook:** "[excited] Can you remember EVERYTHING? We'll ask questions like… what colour was the dress? Or how many birds were there? [excited] Let's go!"
- **Each round:** an intro line, then 2 short lines during the clip (never giving an answer away), then each question read aloud **with its 3 options**.
- **Like/subscribe:** Aman removed the like/subscribe screen from later videos, so ask before adding it.
- **Ending:** a comment ask, then the final question ends with "…can you?", which loops back to the hook.
- Never say "first/last puzzle". No hook after the comment ask.

## Steps
1. Make 3 Veo clips in Flow, download them, and send a contact sheet.
2. Write the questions and options. Get Aman's approval and the answers.
3. Make the stills (contact sheet), then the voice script. Get approval, then generate the voice.
4. Put the voice lines and timings in `final.py` (ROUNDS), then run `python3 mix.py`, then `python3 final.py out.mp4`, then mux with loudnorm (I=-14, TP=-1.5).
5. Make the thumbnail in Google Flow (9:16): "CAN YOU REMEMBER EVERYTHING?", "99% FAIL", the park scene, Hoot with his magnifier.
6. Write the upload text from `upload_text.txt`: the answer key with A/B/C letters. If YouTube asks about AI/synthetic content for the Veo clips, tick it.
7. Aman uploads it himself.
