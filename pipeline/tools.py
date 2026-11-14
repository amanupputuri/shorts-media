"""Helpers for the daily run.

  python3 tools.py day DATE              -> format of the day + style for DATE (YYYY-MM-DD)
  python3 tools.py check SPEC            -> validate spec, print the true answer of every item
  python3 tools.py prompt SPEC [N]       -> print TTS prompt(s); long videos are split in N parts (default 1)
  python3 tools.py fill SPEC VOICE...    -> write voice paths + voice_counts into SPEC
"""
import sys, json, datetime, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

FORMATS = ["odd4", "changed", "maze", "keys", "glasses", "path", "shadow", "mirror", "blocks", "fit",
           "twins", "colortrap", "piece", "illusion", "rotate", "balance", "count", "order", "dots", "hidden"]
NAMES = {"odd4": "Find the Odd One Out", "changed": "What Changed?", "cups": "Follow the Ball", "keys": "Which Key Fits?",
         "glasses": "Which Glass Fills First?", "path": "Which Path Gets the Prize?", "shadow": "Shadow Match",
         "mirror": "Mirror Match", "jar": "Which Jar Has More?", "fit": "How Many Fit?", "twins": "Find the Twins",
         "gears": "Which Way Does the Last Gear Turn?", "piece": "Which Piece Fits?", "illusion": "Illusion Check",
         "rotate": "Rotate Match", "stack": "What's at the Bottom?", "count": "Quick Count", "order": "Remember the Order",
         "pattern": "Complete the Pattern", "hidden": "Find the Hidden One", "maze": "Mini Maze", "blocks": "Count the Blocks",
         "colortrap": "Colour Trap", "balance": "Balance the Scale", "dots": "Connect the Dots"}
START = datetime.date(2026, 11, 15)
PALETTES = [([20, 40, 110], [70, 20, 120], [230, 60, 90]), ([20, 90, 80], [10, 40, 90], [240, 120, 40]),
            ([60, 20, 100], [20, 30, 90], [230, 60, 120]), ([90, 30, 30], [40, 20, 80], [40, 160, 220]),
            ([20, 60, 100], [30, 20, 70], [250, 120, 40]), ([15, 70, 60], [20, 30, 70], [255, 90, 90]),
            ([80, 20, 70], [30, 20, 90], [60, 180, 120])]
BGS = ["bubbles", "stars", "grid", "waves", "confetti"]

def day_info(date):
    d = datetime.date.fromisoformat(date); n = (d - START).days
    fmt = FORMATS[n % 20]; p = PALETTES[n % len(PALETTES)]
    return {"day_index": n, "format": fmt, "format_name": NAMES[fmt],
            "style": {"palette": [p[0], p[1]], "accent": [255, 210, 60], "pill": p[2], "bg": BGS[n % len(BGS)]},
            "music_seed": n}

def answer(item):
    import eyebrain as E
    t = item.get("type")
    L = "ABCD"
    if t == "cups": return L[E.final_slot(item)]
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
        if t == "hidden" and it["base"] == it["odd"]: errs.append(f"item {i}: hidden base == odd")
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
        print("ERRORS:" if e else "OK", *e, sep="\n  ")
        sys.exit(1 if e else 0)
    elif cmd == "prompt":
        spec = json.load(open(sys.argv[2])); n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        for k, p in enumerate(prompt_parts(spec, n)):
            print(f"--- part {k + 1} ({len(p)} segments)"); print(" [long pause] ".join(p))
    elif cmd == "fill":
        sp = sys.argv[2]; spec = json.load(open(sp)); voices = sys.argv[3:]
        parts = prompt_parts(spec, len(voices))
        spec["voice"] = [os.path.abspath(v) for v in voices]; spec["voice_counts"] = [len(p) for p in parts]
        json.dump(spec, open(sp, "w"), indent=1, ensure_ascii=False); print("voice_counts", spec["voice_counts"])
