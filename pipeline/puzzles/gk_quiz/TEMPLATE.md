# "GENERAL KNOWLEDGE QUIZ" template (GK quiz Short with stock photos)

This is the final approved style, first made 19–20 Nov 2026 as "General Knowledge Quiz 🧠 Only 3% Get 10/10! | GK Quiz with Answers".
When Aman says **"general knowledge quiz"** (or "gk quiz"), make a new video in exactly this style with NEW questions.

## Format
- **Video:** vertical 1080x1920, 30 fps, about 2:30, padded to the music bars so it loops.
- **10 questions**, easy to hard: 3 easy, 4 medium, 3 hard (Q8–10). Each question has **3 options (A/B/C)**, and the correct letter varies.
- **Sequence:**
  1. Hook screen: "STOP SCROLLING! QUESTION 10 FOOLED 97%! CAN YOU SCORE 10/10?"
  2. The questions.
  3. A comment screen before question 10.
  4. A "QUESTION 10 FOOLED 97%! ARE YOU READY?" teaser before question 10.
  5. Ending: "10/10? YOU'RE A GENIUS! CAN YOU DO IT AGAIN?", which loops back.
  - Aman **removed the "pause the video" screen and the "tap like & subscribe" screen**, so don't add them.
- **Question screen (`qd.py`, built on `_shared/design.py`):**
  - Small LIKE (Q1–5) or SUBSCRIBE (Q6–10) badge in the top-left, and "SCORE: ?/10" in the top-right.
  - A level chip ("EASY • QUESTION 1/10").
  - A **stock photo from Unsplash** in a rounded white frame. It must show the topic WITHOUT giving the answer away (for example, zebras rather than a cheetah, and a museum wall rather than the Mona Lisa).
  - The question card (balanced wrapping, fixed line spacing), then the A/B/C pills, then a ring timer (**3 s**).
  - **The answer is revealed:** the correct pill turns green with a tick, and "CORRECT ANSWER!" appears.
  - Each question has its own gradient background colour.
- **Hoot is STATIC.** He's smaller in the bottom-left so he doesn't cover "CORRECT ANSWER!".
- **Smooth transitions:** each screen pushes in from the right with a crossfade (0.55 s, smoothstep easing).
- **Smooth sound effects:** `_shared/audio_smooth.py` has soft long whooshes, light pops for the options, quiet ticks and a soft ding on the reveal.

## Photos
Search Unsplash with the Unsplash connector, free photos only (`plus: none`), and call `download_asset` for each.
- The sandbox blocks images.unsplash.com, so fetch the photos through the built-in browser (`fetch` + FileReader on any open page), then decode them.
- Save them as `photos/q01.jpg` … `q10.jpg`, and credit "Photos: Unsplash" in the description.

## Hoot voice
ElevenLabs voice `cPmGMZvsZ24aRiDy6Vc2`, model `eleven_v4`, one take. Split it with silencedetect, using pauses of 1.0 s or more as line breaks.
- **Hook (short, about 3 s):** "[excited] Question ten fooled 97%! Can you score ten out of ten?"
- **Each question:** one line reading the question **and its 3 options**, then one line with the answer ("Jupiter! It's HUGE!").
- **Q5:** add the re-hook "Halfway there! Still perfect? Watch out… question ten is coming!"
- **Q8:** add the re-hook "Only geniuses get this far!"
- **Before Q10:** the comment ask "How many did you get right so far? Tell me in the comments!"
- **Q10:** "Here it is… the one that fooled ninety-seven percent!" The answer line ends with "Can you do it again?" (loops back).
- Never say "first/last puzzle". No hook after the comment ask.

## Steps
1. Write the 10 questions (table: question, options, answer). Get Aman's approval.
2. Find a photo per question on Unsplash and send a contact sheet.
3. Write the voice script. Get approval, then generate the voice.
4. Update `qd.Q`, `qv.QL` (line map) and `qv.NOTES`. Then run `python3 mix.py`, then `python3 qv.py out.mp4`, then mux with loudnorm (I=-14, TP=-1.5).
5. Make the thumbnail: "ONLY 3% GET 10/10!", a "GENERAL KNOWLEDGE QUIZ" banner, 4 photos with "?" badges, Hoot, "CAN YOU?" (or make it in Google Flow).
6. Write the upload text from `upload_text.txt`: the answer key, "Photos: Unsplash", Education category, not made for kids.
7. Aman uploads it himself.
