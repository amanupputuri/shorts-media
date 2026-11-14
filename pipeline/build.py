"""Build one finished video from a content spec + voice file(s).

usage: python3 build.py SPEC.json WORKDIR OUT.mp4

SPEC fields (content written by the daily run):
  orientation  "v" (Short 1080x1920) or "h" (long 1920x1080)
  label        pill word, e.g. "PUZZLE" / "QUESTION"
  count_secs   countdown length (3 for Shorts, 5 for long)
  style        {palette:[[r,g,b],[r,g,b]], accent:[r,g,b], pill:[r,g,b], bg:"bubbles|stars|grid|waves|confetti", card:[r,g,b]}
  title_card   {emoji, line1, line2, tag}
  outro        {line1, line2, line3, cta, cta_sub}
  items        list of {prompt, display?, options?, right?, letters?, fact:[l1,l2], nudge?}
  voice        list of mp3 paths; their segments, in order, must be:
               intro, q0, a0, q1, a1, ..., outro   (segments separated by "[long pause]")
               "voice_counts" gives the number of segments in each file.
"""
import sys, os, json, re, subprocess
import numpy as np, wave

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100

def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))

def split(src, n, outdir, start_idx):
    """cut src into n segments at the n-1 longest silences -> outdir/seg{start_idx+k}.wav"""
    d = dur(src)
    log = subprocess.run(["ffmpeg", "-i", src, "-af", "silencedetect=noise=-38dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True, stdin=subprocess.DEVNULL).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    sil = [(a, b) for a, b in zip(st, en) if a > 0.3 and b < d - 0.3]
    if len(sil) < n - 1:
        raise SystemExit(f"split failed for {src}: need {n-1} gaps, found {len(sil)}")
    top = sorted(sorted(sil, key=lambda x: x[1] - x[0], reverse=True)[:n - 1])
    cuts = [0.0] + [(a + b) / 2 for a, b in top] + [d]
    out = []
    for k in range(n):
        f = os.path.join(outdir, f"seg{start_idx + k:03d}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cuts[k]), "-to", str(cuts[k + 1]), "-i", src,
                        "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", str(SR), "-ac", "1", f], check=True, stdin=subprocess.DEVNULL)
        if dur(f) < 0.6:
            raise SystemExit(f"segment too short: {f}")
        out.append(f)
    return out

def load(f):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", f, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], stdin=subprocess.DEVNULL)
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768

def tone(f, d, decay=8):
    t = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.exp(-decay * t)
def mixs(*a):
    n = max(len(x) for x in a); o = np.zeros(n)
    for x in a: o[:len(x)] += x
    return o

def main():
    spec_path, work, out = sys.argv[1:4]
    os.makedirs(work, exist_ok=True)
    spec = json.load(open(spec_path))
    n_items = len(spec["items"])
    need = 2 + 2 * n_items
    counts = spec.get("voice_counts", [need])
    assert sum(counts) == need, f"voice segments {sum(counts)} != needed {need}"
    segs = []
    for f, n in zip(spec["voice"], counts):
        segs += split(f, n, work, len(segs))
    cs = spec["count_secs"]
    timing = {"intro": {"dur": round(dur(segs[0]) + 0.4, 3)}}
    for i in range(n_items):
        q, a = segs[1 + 2 * i], segs[2 + 2 * i]
        sys.path.insert(0, HERE); import eyebrain
        ask = max(round(dur(q) + 0.5, 3), 3.0 if spec["orientation"] == "v" else 3.4, eyebrain.min_ask(spec["items"][i]))
        timing[f"i{i}"] = {"ask": ask, "dur": round(ask + cs + dur(a) + 0.8, 3), "q": q, "a": a}
    timing["outro"] = {"dur": round(dur(segs[-1]) + 1.2, 3)}
    spec["timing"] = timing
    sp = os.path.join(work, "spec_timed.json"); json.dump(spec, open(sp, "w"), indent=1)

    order = ["intro"] + [f"i{i}" for i in range(n_items)] + ["outro"]
    # render scenes, at most 6 in parallel
    procs = []
    for g in order:
        o = os.path.join(work, f"{g}.mp4")
        if os.path.exists(o): os.remove(o)
        procs.append(subprocess.Popen([sys.executable, os.path.join(HERE, "engine.py"), sp, "video", g, o], stdin=subprocess.DEVNULL))
        if len(procs) >= 6:
            procs.pop(0).wait()
    for p in procs: p.wait()
    for g in order:
        if not os.path.exists(os.path.join(work, f"{g}.mp4")): raise SystemExit(f"render failed: {g}")

    # audio
    total = sum(timing[g]["dur"] for g in order); N = int(total * SR) + SR
    voice = np.zeros(N); sfx = np.zeros(N)
    def add(buf, sig, t, g=1.0):
        s = int(t * SR); e = min(N, s + len(sig)); buf[s:e] += sig[:e - s] * g
    pop = mixs(tone(880, 0.12, 30), 0.5 * tone(1320, 0.12, 35)); tick = tone(1800, 0.05, 80)
    ding = mixs(tone(1046.5, 0.9, 4), 0.6 * tone(1568, 0.9, 5), 0.3 * tone(2093, 0.9, 6))
    rng = np.random.default_rng(1); wh = rng.normal(0, 1, int(0.4 * SR))
    whoosh = np.convolve(wh, np.ones(60) / 60, 'same') * np.sin(np.linspace(0, np.pi, len(wh))) * 2
    t0 = 0.0
    for g in order:
        add(sfx, whoosh, t0, 0.22)
        if g == "intro": add(voice, load(segs[0]), t0 + 0.15)
        elif g == "outro": add(voice, load(segs[-1]), t0 + 0.15)
        else:
            tm = timing[g]; item = spec["items"][int(g[1:])]
            add(voice, load(tm["q"]), t0 + 0.15)
            for k in range(len(item.get("options", []))): add(sfx, pop, t0 + 0.8 + 0.35 * k + (0.2 if item.get("display") else 0), 0.35)
            for k in range(cs): add(sfx, tick, t0 + tm["ask"] + k, 0.5)
            r = t0 + tm["ask"] + cs
            add(sfx, ding, r, 0.45); add(voice, load(tm["a"]), r + 0.25)
        t0 += timing[g]["dur"]
    # music bed (key/tempo vary by day via spec["music_seed"])
    ms = spec.get("music_seed", 0)
    bpm = [104, 112, 120, 96, 116][ms % 5]; beat = 60 / bpm
    progs = [[[261.6, 329.6, 392], [220, 261.6, 329.6], [174.6, 220, 261.6], [196, 246.9, 293.7]],
             [[293.7, 370, 440], [246.9, 293.7, 370], [196, 246.9, 293.7], [220, 277.2, 329.6]],
             [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]]
    chords = progs[ms % 3]
    mus = np.zeros(N); i = 0; t = 0.0
    while t < total:
        ch = chords[(i // 8) % 4]; f = ch[i % 3] * (2 if i % 4 == 3 else 1)
        add(mus, mixs(tone(f, beat * 0.9, 6) * 0.5, tone(f / 2, beat * 0.9, 5) * 0.3 * (i % 2 == 0)), t); t += beat / 2; i += 1
    mix = (voice * 0.95 + sfx + mus * 0.055)[:int(total * SR)]
    mix = mix / max(1, np.max(np.abs(mix)) / 0.95)
    wav = os.path.join(work, "mix.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{g}.mp4'\n" for g in order))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest",
                    "-movflags", "+faststart", out], check=True, stdin=subprocess.DEVNULL)
    print(out, round(dur(out), 2), "s", round(os.path.getsize(out) / 1e6, 1), "MB")

if __name__ == "__main__":
    main()
