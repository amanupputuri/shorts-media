"""Helpers for the daily run.

  python3 tools.py day DATE              -> format of the day + style for DATE (YYYY-MM-DD)
  python3 tools.py check SPEC            -> validate spec, print the true answer of every item
  python3 tools.py prompt SPEC [N]       -> print TTS prompt(s); long videos are split in N parts (default 1)
  python3 tools.py fill SPEC VOICE...    -> write voice paths + voice_counts into SPEC
  python3 tools.py hooks SPEC            -> TTS prompt for the long video's spoken hooks (say.items[i].hook)
  python3 tools.py fillhooks SPEC VOICE  -> write that hook voice file into SPEC ("hook_voice")
"""
import sys, json, datetime, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

FORMATS = ["odd4", "twins", "spotdiff", "memgrid", "missing", "flipped", "numflash",
           "bug", "rowdiff", "countdiff", "letterhunt", "cardflip", "diceflash", "zoom",
           "shapemiss", "spotlight", "pixel", "crowd", "colorcount", "dupnum",
           "fruitmath", "gridfind", "patmatch", "fingers", "analogy", "oddpair"]
NAMES = {"odd4": "Find the Odd One Out", "changed": "What Changed?", "cups": "Follow the Ball", "keys": "Which Key Fits?",
         "glasses": "Which Glass Fills First?", "path": "Which Path Gets the Prize?", "shadow": "Shadow Match",
         "mirror": "Mirror Match", "jar": "Which Jar Has More?", "fit": "How Many Fit?", "twins": "Find the Twins",
         "gears": "Which Way Does the Last Gear Turn?", "piece": "Which Piece Fits?", "illusion": "Illusion Check",
         "rotate": "Rotate Match", "stack": "What's at the Bottom?", "count": "Quick Count", "order": "Remember the Order",
         "pattern": "Complete the Pattern", "hidden": "Find the Hidden One", "maze": "Mini Maze", "blocks": "Count the Blocks",
         "colortrap": "Colour Trap", "balance": "Balance the Scale", "dots": "Connect the Dots",
         "spotdiff": "Spot the Difference", "oddcolor": "Odd Colour Out", "memgrid": "Memory Grid", "missing": "What's Missing?",
         "flipped": "Upside-Down One", "numflash": "Number Flash", "whereflash": "Where Was It?", "bug": "Bug Arrows",
         "rowdiff": "Which Row Is Different?", "countdiff": "How Many Differences?", "arrowout": "Arrow Out", "letterhunt": "Odd Letter Out", "fruitmath": "Fruit Math", "gridfind": "Grid Finder", "patmatch": "Board Copy", "fingers": "Finger Count", "analogy": "Goes With", "oddpair": "Odd Pair Out",
         "cardflip": "Card Flip Memory", "diceflash": "Dice Flash", "zoom": "Zoom Out", "lightorder": "Light Order", "split": "Split Picture",
         "shapemiss": "Which One Didn't Appear?", "spotlight": "Spotlight", "pixel": "Pixel Guess", "crowd": "Find It in the Crowd",
         "colorcount": "Colour Count", "moved": "What Moved?", "dupnum": "Number Twice"}
START = datetime.date(2026, 11, 15)
THEMES = ["Bath Time", "Breakfast Table", "Christmas", "Winter Snow", "Ocean Life", "Farm Animals", "Jungle Safari",
          "Sweet Treats", "Fruit Market", "Space Adventure", "School Bag", "Birthday Party", "Sports Day", "Toy Box",
          "Bugs & Garden", "Pets at Home"]
THEMABLE = {"odd4", "spotdiff", "missing", "flipped", "bug", "rowdiff", "countdiff", "cardflip", "zoom", "shapemiss",
            "spotlight", "pixel", "crowd", "fruitmath", "gridfind", "analogy", "oddpair", "twins"}
# modern, bright, kid-friendly flat colours: (top, bottom, pill)
PALETTES = [([66, 133, 244], [44, 104, 222], [255, 92, 120]),    # sky blue
            ([124, 92, 255], [100, 66, 230], [255, 176, 32]),    # violet
            ([20, 184, 166], [13, 148, 136], [255, 92, 120]),    # teal
            ([240, 91, 166], [214, 64, 140], [70, 110, 255]),    # bubblegum pink
            ([34, 170, 95], [22, 140, 78], [255, 92, 120]),      # leaf green
            ([255, 107, 107], [235, 80, 90], [60, 100, 240]),    # coral
            ([56, 189, 248], [14, 150, 220], [255, 92, 120])]    # aqua
BGS = ["blobs", "dots"]

def day_info(date):
    d = datetime.date.fromisoformat(date); n = (d - START).days
    fmt = FORMATS[n % len(FORMATS)]; p = PALETTES[n % len(PALETTES)]
    return {"day_index": n, "format": fmt, "format_name": NAMES[fmt],
            "style": {"palette": [p[0], p[1]], "accent": [255, 210, 60], "pill": p[2], "bg": BGS[n % len(BGS)]},
            "music_seed": n,
            "themes": ([THEMES[(n * 5 + k) % len(THEMES)] for k in range(5)] if fmt in THEMABLE else []),
            "long_formats": [FORMATS[(n + k) % len(FORMATS)] for k in range(20)],
            # Aman, 18 Nov: every Short of the day is a DIFFERENT puzzle format (5 per day, rotating, no overlap with yesterday)
            "short_formats": [FORMATS[(n * 5 + k) % len(FORMATS)] for k in range(5)],
            "short_themes": [THEMES[(n * 5 + k) % len(THEMES)] if FORMATS[(n * 5 + k) % len(FORMATS)] in THEMABLE else ""
                             for k in range(5)]}

def answer(item):
    import eyebrain as E
    t = item.get("type")
    L = "ABCD"
    if t == "cups": return L[E.final_slot(item)]
    import eyebrain3 as E3
    if t == "fruitmath": return "%s (values %s)" % (E3.fruitmath_answer(item), E3.fruitmath_values(item))
    if t == "gridfind": return E3.gridfind_answer(item)
    if t == "fingers": return str(E3.fingers_answer(item))
    if t in ("patmatch", "oddpair"): return L[item["right"]]
    if t == "analogy": return item["options"][item["right"]]
    if t == "glasses": return "glass %d" % E.glass_path(item)[-1][0]
    if t == "path":
        rows = item.get("rows", 8)
        for l in range(len(item["starters"])):
            _, end = E.path_trace(item, l, rows)
            if end == item["prize_slot"]: return "%s (%s)" % (L[l], item["starters"][l])
        return "NO WINNER - fix rungs"
    if t == "twins":
        _, pair = E.twins_set(item["seed"]); return "numbers %d and %d" % (pair[0] + 1, pair[1] + 1)
    if t == "gears": return ["A clockwise", "B anticlockwise"][E.gears_answer(item)]
    if t == "illusion": return ["A", "B", "same"][E.illusion_answer(item)]
    if t == "spotdiff": return "cell %d changed to %s" % (item["diff"] + 1, item["alt"])
    if t == "oddcolor": return "row %d col %d" % (item["pos"][0] + 1, item["pos"][1] + 1)
    if t == "memgrid": return "square %d" % (item["seq"][-1] + 1)
    if t == "missing": return "%s = %s (gone %s)" % (L[item["right"]], item["options"][item["right"]], item["before"][item["gone"]])
    if t in ("flipped", "arrowout", "letterhunt", "oddsize"): return "row %d col %d" % (item["pos"][0] + 1, item["pos"][1] + 1)
    if t == "numflash": return "%s = %s (shown %s)" % (L[item["right"]], item["options"][item["right"]], item["number"])
    if t == "whereflash": return "square %d (%s)" % (item["target_idx"] + 1, item["grid"][item["target_idx"]])
    if t == "bug":
        p = E.bug_path(item); return "OFF GRID - fix" if p is None else "square %d" % (p[-1][0] * 4 + p[-1][1] + 1)
    if t == "rowdiff": return "row %s" % "ABCDE"[item["odd_row"]]
    if t == "countdiff": return "%s = %s (true %d)" % (L[item["right"]], item["options"][item["right"]], len(item["diffs"]))
    if t == "cardflip": return "%s = %s (true %s)" % (L[item["right"]], item["options"][item["right"]], " & ".join(map(str, E.cardflip_pair(item))))
    if t == "diceflash": return "%s = %s (true %d)" % (L[item["right"]], item["options"][item["right"]], sum(item["dice"]))
    if t == "zoom": return "%s = %s" % (L[item["right"]], item["options"][item["right"]])
    if t == "lightorder": return "%s = %s (true %s)" % (L[item["right"]], item["options"][item["right"]], item["seq"][item["ask_pos"] - 1])
    if t == "split": return "bottom %d" % (E.split_answer(item) + 1)
    if t == "shapemiss": return "%s = %s" % (L[item["right"]], item["options"][item["right"]])
    if t in ("spotlight", "pixel"): return "%s = %s" % (L[item["right"]], item["options"][item["right"]])
    if t == "crowd": return "row %d col %d" % (item["pos"][0] + 1, item["pos"][1] + 1)
    if t == "colorcount": return "%s = %s (true %d %s)" % (L[item["right"]], item["options"][item["right"]], item["counts"][item["ask"]], item["ask"])
    if t == "moved": return "%s = %s (moved %s)" % (L[item["right"]], item["options"][item["right"]], item["slots"][item["move"][0]])
    if t == "dupnum": a = E.dupnum_answer(item); return "NO DUPLICATE - fix" if a is None else "%d" % a[0]
    if t == "maze": w = E.maze_answer(item); return "%s (%s)" % (L[w], item["starters"][w])
    if t == "blocks": return "%s = %s (true total %d)" % (L[item["right"]], item["options"][item["right"]], E.blocks_total(item))
    if t == "balance": return "%s = %s (true %g)" % (L[item["right"]], item["options"][item["right"]], E.balance_answer(item))
    if t == "colortrap": return "%s = %s (ink %s)" % (L[item["right"]], item["options"][item["right"]], item["ink"])
    if t == "dots": return "%s = %s (shape %s)" % (L[item["right"]], item["options"][item["right"]], item["shape"])
    if t == "jar": return "A" if item["counts"][0] > item["counts"][1] else "B"
    if t == "changed": return "number %d (%s became %s)" % (item["changed"] + 1, item["before"][item["changed"]], item["after_emoji"])
    if t == "hidden": return "the odd emoji %s" % item["odd"]
    if t == "fit": return "%s = %s (grid %dx%d = %d)" % (L[item["right"]], item["options"][item["right"]], item["grid"][0], item["grid"][1], item["grid"][0] * item["grid"][1])
    if t == "count": return "%s = %s (true count %d)" % (L[item["right"]], item["options"][item["right"]], item["n"])
    if "right" in item:
        o = item.get("options") or item.get("opts")
        return "%s = %s" % (L[item["right"]], o[item["right"]] if o else "")
    return "?"

def check(spec):
    import eyebrain as E2
    import eyebrain3 as E3
    errs = []
    for i, it in enumerate(spec["items"]):
        t = it.get("type")
        if t == "fit" and int(it["options"][it["right"]]) != it["grid"][0] * it["grid"][1]: errs.append(f"item {i}: fit right option != grid count")
        if t == "count" and int(it["options"][it["right"]]) != it["n"]: errs.append(f"item {i}: count right option != n")
        if t == "jar" and it["counts"][0] == it["counts"][1]: errs.append(f"item {i}: jar counts equal")
        if t == "order" and it["options"][it["right"]] != it["seq"][it["ask_pos"] - 1]: errs.append(f"item {i}: order right option mismatch")
        if t == "pattern" and len(it["options"]) != 3: errs.append(f"item {i}: pattern needs 3 options")
        if t == "count" and it["n"] + it["m"] > 20: errs.append(f"item {i}: count n+m must be <= 20")
        if t == "path" and "NO WINNER" in answer(it): errs.append(f"item {i}: path has no winner")
        if t == "changed" and len(it["before"]) != 6: errs.append(f"item {i}: changed needs 6 emojis")
        if t == "blocks" and int(it["options"][it["right"]]) != E2.blocks_total(it): errs.append(f"item {i}: blocks right option != total")
        if t == "balance" and float(it["options"][it["right"]]) != E2.balance_answer(it): errs.append(f"item {i}: balance right option wrong")
        if t == "balance" and E2.balance_answer(it) != int(E2.balance_answer(it)): errs.append(f"item {i}: balance answer not whole")
        if t == "colortrap" and it["options"][it["right"]].lower() != it["ink"]: errs.append(f"item {i}: colortrap right must be the ink colour")
        if t == "colortrap" and it["word"].lower() == it["ink"]: errs.append(f"item {i}: colortrap word must differ from ink")
        if t == "dots" and it["shape"] not in E2.DOT_SHAPES: errs.append(f"item {i}: unknown dots shape")
        if t == "missing" and it["options"][it["right"]] != it["before"][it["gone"]]: errs.append(f"item {i}: missing right option wrong")
        if t == "numflash" and it["options"][it["right"]] != it["number"]: errs.append(f"item {i}: numflash right option wrong")
        if t == "numflash" and (len(it["options"]) != 5 or len(set(it["options"])) != 5): errs.append(f"item {i}: numflash needs 5 different options")
        if t == "rowdiff" and (len(it["seq"]) != 7 or len(set(it["seq"])) != 7 or it.get("rows", 4) != 4): errs.append(f"item {i}: rowdiff needs 7 different items per row and 4 rows")
        if t == "fruitmath" and (E3.fruitmath_values(it) is None or str(E3.fruitmath_answer(it)) != str(it["options"][it["right"]])): errs.append(f"item {i}: fruitmath has no whole-number solution or right option wrong")
        if t == "gridfind" and (it["options"][it["right"]] != E3.gridfind_answer(it) or it["target"] in it["pool"]): errs.append(f"item {i}: gridfind right option wrong or target in pool")
        if t == "fingers" and (any(h not in E3.FINGERS for h in it["hands"]) or str(E3.fingers_answer(it)) != str(it["options"][it["right"]])): errs.append(f"item {i}: fingers right option wrong (hands only ✋ ✌️ ☝️ 🤟)")
        if t == "patmatch" and (len(it["diffs"]) != 2 or any(it["grid"][r][q] == col for r, q, col in it["diffs"])): errs.append(f"item {i}: patmatch needs 2 diffs that really change a peg")
        if t == "oddpair" and len(it["pairs"]) != 4: errs.append(f"item {i}: oddpair needs 4 pairs")
        if t == "analogy" and len(it["options"]) != 3: errs.append(f"item {i}: analogy needs 3 options")
        if t == "letterhunt" and (len(it["base"]) != 1 or len(it["odd"]) != 1 or it["base"] == it["odd"]): errs.append(f"item {i}: letterhunt needs two different single characters")
        if t == "crowd" and len(it["pool"]) < 8: errs.append(f"item {i}: crowd pool needs 8+ look-alikes")
        if t == "arrowout" and not (10 <= abs((it["odd_angle"] - it["angle"] + 180) % 360 - 180) <= 25): errs.append(f"item {i}: arrowout odd angle must differ by 10-25 degrees")
        if t == "dupnum" and len(it["nums"]) != 30: errs.append(f"item {i}: dupnum needs 30 numbers")
        if t == "bug" and E2.bug_path(it) is None: errs.append(f"item {i}: bug walks off the 4x4 grid")
        if t == "countdiff" and int(it["options"][it["right"]]) != len(it["diffs"]): errs.append(f"item {i}: countdiff right option wrong")
        if t == "cardflip" and (len(E2.cardflip_pair(it)) != 2 or it["options"][it["right"]] != " & ".join(map(str, E2.cardflip_pair(it)))): errs.append(f"item {i}: cardflip needs exactly 2 targets and matching right option")
        if t == "diceflash" and int(it["options"][it["right"]]) != sum(it["dice"]): errs.append(f"item {i}: diceflash right option wrong")
        if t == "lightorder" and it["options"][it["right"]].lower() != it["seq"][it["ask_pos"] - 1]: errs.append(f"item {i}: lightorder right option wrong")
        if t == "rowdiff" and abs(it["swap"][0] - it["swap"][1]) != 1: errs.append(f"item {i}: rowdiff swap must be neighbours")
        if t == "shapemiss" and (it["options"][it["right"]] in it["seq"] or any(o not in it["seq"] for k, o in enumerate(it["options"]) if k != it["right"])): errs.append(f"item {i}: shapemiss right option must be the only one not in seq")
        if t == "colorcount" and int(it["options"][it["right"]]) != it["counts"][it["ask"]]: errs.append(f"item {i}: colorcount right option wrong")
        if t == "colorcount" and sum(it["counts"].values()) > 30: errs.append(f"item {i}: colorcount total must be <= 30")
        if t == "moved" and (it["slots"][it["move"][1]] != "" or it["options"][it["right"]] != it["slots"][it["move"][0]]): errs.append(f"item {i}: moved target slot must be empty and right option = moved emoji")
        if t == "dupnum":
            from collections import Counter
            cnt = Counter(it["nums"])
            if sorted(cnt.values())[-1] != 2 or list(cnt.values()).count(2) != 1: errs.append(f"item {i}: dupnum needs exactly one number twice")
        if t == "hidden" and it["base"] == it["odd"]: errs.append(f"item {i}: hidden base == odd")
        # --- long-video upgrades (grids / digits / voice-driven bug) ---
        if t == "spotdiff" and (len(it["scene"]) not in (9, 16) or not 0 <= it["diff"] < len(it["scene"])): errs.append(f"item {i}: spotdiff scene must have 9 or 16 emoji and diff inside it")
        if t == "memgrid" and (it.get("n", 3) not in (3, 4) or any(not 0 <= k < it.get("n", 3) ** 2 for k in it["seq"])): errs.append(f"item {i}: memgrid n must be 3 or 4 and seq cells inside the grid")
        if t == "missing" and len(it["before"]) not in (6, 9): errs.append(f"item {i}: missing needs 6 or 9 emoji (long video: 9 = 3x3)")
        if t == "numflash" and len(set(len(o) for o in it["options"] + [it["number"]])) != 1: errs.append(f"item {i}: numflash options must all have the same number of digits as the number")
        if t == "cardflip" and len(it["cards"]) not in (9, 10, 16): errs.append(f"item {i}: cardflip needs 9, 10 or 16 cards (long video: 16 = 4x4)")
        if t == "flipped" and not (0 <= it["pos"][0] and 0 <= it["pos"][1]): errs.append(f"item {i}: flipped pos must be >= 0")
        if t == "bug" and not it.get("show_arrows"):
            q = (spec.get("say", {}).get("items", [{}] * (i + 1))[i] or {}).get("q", "").lower()
            words = [w for w in re.findall(r"[a-z]+", q) if w in ("up", "down", "left", "right")]
            want = [{"U": "up", "D": "down", "L": "left", "R": "right"}[m] for m in it["moves"]]
            if words != want: errs.append(f"item {i}: bug is voice-driven - say.items[{i}].q must say the moves in order {want} (found {words})")
    return errs

def prompt_parts(spec, n):
    say = spec["say"]
    segs = ["[excited] " + say["intro"]]
    for it in say["items"]:
        segs += ["[curious] " + it["q"], "[excited] " + it["a"]]
    segs.append("[cheerful] " + say["outro"])
    if n == 1: return [segs]
    per = -(-len(segs) // n); return [segs[k:k + per] for k in range(0, len(segs), per)]

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "day":
        print(json.dumps(day_info(sys.argv[2]), indent=1))
    elif cmd == "check":
        spec = json.load(open(sys.argv[2]))
        for i, it in enumerate(spec["items"]): print(i, it.get("type"), "->", answer(it))
        e = check(spec)
        if len(spec.get("say", {}).get("items", [])) != len(spec["items"]): e.append("say.items count != items count")
        if True:  # Aman, 18 Nov: Shorts AND long videos use spoken (voice) hooks, no text teasers
            if spec.get("orientation") == "v" and spec.get("count_secs") != 4: e.append("Shorts use count_secs 4 (Aman, 18 Nov)")
            if spec.get("orientation") == "v" and len([1 for si in spec.get("say", {}).get("items", []) if si.get("hook")]) < 4:
                e.append("Shorts need 4 spoken hooks: say.items[2], [4], [5] (<= 7 words) + the LIKE ask on say.items[3]")
            # Aman, 18 Nov: once in the middle of EVERY video Hoot asks for a like so he can keep making puzzles
            mid = 3 if spec.get("orientation") == "v" else 10
            sit = spec.get("say", {}).get("items", [])
            if len(sit) > mid and "like" not in sit[mid].get("hook", "").lower():
                e.append(f"say.items[{mid}].hook must be the mid-video LIKE ask (<= 12 words), e.g. \"Enjoying this? Tap like so I can make more puzzles!\"")
            for i, it in enumerate(spec["items"]):
                if it.get("teaser"): e.append(f"item {i}: NO text teasers any more - put the line in say.items[{i}].hook (spoken)")
                if it.get("prompt2") and not it.get("stack"): e.append(f"item {i}: two-part question needs \"stack\": true (both lines on screen)")
            for i, si in enumerate(spec.get("say", {}).get("items", [])):
                if si.get("hook") and i == 0: e.append("say.items[0].hook: puzzle 1 has no hook slot - end say.intro with the warm-up line")
                if si.get("hook") and len(si["hook"].split()) > (12 if "like" in si["hook"].lower() else 7): e.append(f"say.items[{i}].hook must be <= 7 words")
        print("ERRORS:" if e else "OK", *e, sep="\n  ")
        sys.exit(1 if e else 0)
    elif cmd == "prompt":
        spec = json.load(open(sys.argv[2])); n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        for k, p in enumerate(prompt_parts(spec, n)):
            print(f"--- part {k + 1} ({len(p)} segments)"); print(" [long pause] ".join(p))
    elif cmd == "hooks":  # TTS prompt for the spoken hooks (Shorts and long videos) (one generate call)
        spec = json.load(open(sys.argv[2])); hs = [it["hook"] for it in spec["say"]["items"] if it.get("hook")]
        print(" [long pause] ".join("[excited] " + h for h in hs) if hs else "(no hooks)")
    elif cmd == "fillhooks":
        sp = sys.argv[2]; spec = json.load(open(sp)); spec["hook_voice"] = os.path.abspath(sys.argv[3])
        json.dump(spec, open(sp, "w"), indent=1, ensure_ascii=False); print("hook_voice", spec["hook_voice"])
    elif cmd == "fill":
        sp = sys.argv[2]; spec = json.load(open(sp)); voices = sys.argv[3:]
        parts = prompt_parts(spec, len(voices))
        spec["voice"] = [os.path.abspath(v) for v in voices]; spec["voice_counts"] = [len(p) for p in parts]
        json.dump(spec, open(sp, "w"), indent=1, ensure_ascii=False); print("voice_counts", spec["voice_counts"])
