"""Build one finished video from a content spec + voice file(s).

usage: python3 build.py SPEC.json WORKDIR OUT.mp4

SPEC fields (content written by the daily run):
  orientation  "v" (Short 1080x1920) or "h" (long 1920x1080)
  label        pill word, e.g. "PUZZLE" / "QUESTION"
  count_secs   countdown length (4 for Shorts and long videos)
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
    for k, f in (spec.get("voice_override") or {}).items(): segs[int(k)] = f
    cs = spec["count_secs"]
    timing = {"intro": {"dur": round(dur(segs[0]) + 0.4, 3)}}
    for i in range(n_items):
        q, a = segs[1 + 2 * i], segs[2 + 2 * i]
        sys.path.insert(0, HERE); import eyebrain
        ask = max(round(dur(q) + 0.5, 3), 3.0 if spec["orientation"] == "v" else 3.4, eyebrain.min_ask(spec["items"][i]))
        timing[f"i{i}"] = {"ask": ask, "dur": round(ask + cs + dur(a) + 0.8, 3), "q": q, "a": a}
    hook_mode = spec["orientation"] == "v" and spec.get("hook_mode", True)
    if hook_mode:
        # retention: no title card — puzzle 1 starts at frame 0 with the hook banner while Hoot says the intro line
        hd = round(dur(segs[0]) + 0.25, 3)
        t0_ = timing["i0"]; t0_["hook"] = hd; t0_["qoff"] = hd
        t0_["ask"] = round(max(t0_["ask"], hd + dur(t0_["q"]) + 0.6), 3)
        t0_["dur"] = round(t0_["ask"] + cs + dur(t0_["a"]) + 0.8, 3)
    timing["outro"] = {"dur": round(max(dur(segs[-1]) + 0.5, 1.8) if hook_mode else max(dur(segs[-1]) + 0.8, 2.2), 3)}
    # spoken hooks (long videos): say.items[i].hook is said by Hoot at the end of puzzle i-1's reveal (no text banner);
    # all hook lines come from ONE extra voice file, spec "hook_voice", segments in item order.
    hook_idx = [i for i, it in enumerate(spec.get("say", {}).get("items", [])) if it.get("hook")]
    if hook_idx:
        assert spec.get("hook_voice"), "say.items have hooks but spec has no hook_voice (run tools.py hooks / fillhooks)"
        assert hook_idx[0] >= 1, "puzzle 1 has no hook slot: put the warm-up line into say.intro"
        hsegs = split(spec["hook_voice"], len(hook_idx), work, 900)
        for i, hf in zip(hook_idx, hsegs):
            pv = timing[f"i{i - 1}"]
            pv["hook_at"] = round(pv["dur"] - 0.2, 3); pv["hook_seg"] = hf
            pv["dur"] = round(pv["dur"] + dur(hf) + 0.55, 3)
    spec["timing"] = timing
    sp = os.path.join(work, "spec_timed.json"); json.dump(spec, open(sp, "w"), indent=1)

    order = ([] if hook_mode else ["intro"]) + [f"i{i}" for i in range(n_items)] + ["outro"]
    spec["timing"]["order"] = order; json.dump(spec, open(sp, "w"), indent=1)
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
        s = int(t * SR); e = min(N, s + len(sig))
        if e > s: buf[s:e] += sig[:e - s] * g
    # --- smooth sound design ---
    def env(n, a=0.005, r=None):
        e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
        if r: nr = min(n, int(r * SR)); e[-nr:] *= np.linspace(1, 0, nr) ** 2
        return e
    def lp(x, k=8): return np.convolve(x, np.ones(k) / k, "same")
    tt = np.arange(int(0.09 * SR)) / SR
    pop = np.sin(2 * np.pi * (380 * tt + 1800 * tt * tt)) * np.exp(-30 * tt) * env(len(tt), 0.012)          # soft bubble
    tt = np.arange(int(0.12 * SR)) / SR
    tick = (np.sin(2 * np.pi * 620 * tt) + 0.2 * np.sin(2 * np.pi * 930 * tt)) * np.exp(-34 * tt) * env(len(tt), 0.008)  # woodblock tock
    # modern "success" sound: soft marimba two-note rise (G5 → C6) + airy sparkle tail
    def mallet(f, d=0.7):
        t_ = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t_) + 0.18 * np.sin(2 * np.pi * f * 3.98 * t_) * np.exp(-30 * t_)) * np.exp(-7 * t_) * np.minimum(1, t_ / 0.012)
    ding = np.zeros(int(1.4 * SR))
    for off, f_, a_ in [(0.0, 783.99, 0.8), (0.09, 1046.5, 1.0), (0.18, 1567.98, 0.35)]:
        m = mallet(f_); o = int(off * SR); ding[o:o + len(m)] += m[:len(ding) - o] * a_
    tsp = np.arange(len(ding)) / SR
    sparkle = lp(np.random.default_rng(9).normal(0, 1, len(ding)), 3) - lp(np.random.default_rng(9).normal(0, 1, len(ding)), 30)
    ding += sparkle * np.exp(-4 * np.maximum(0, tsp - 0.15)) * (tsp > 0.12) * 0.05
    ding = lp(ding, 3)
    rng = np.random.default_rng(1); wh = lp(rng.normal(0, 1, int(0.45 * SR)), 40)
    whoosh = lp(wh, 12) * np.sin(np.linspace(0, np.pi, len(wh))) ** 2 * 3                                    # airy swoosh
    t0 = 0.0
    for g in order:
        add(sfx, whoosh, t0, 0.08)
        if g == "intro": add(voice, load(segs[0]), t0 + 0.15)
        elif g == "outro": add(voice, load(segs[-1]), t0 + 0.15)
        else:
            tm = timing[g]; item = spec["items"][int(g[1:])]
            if tm.get("qoff"): add(voice, load(segs[0]), t0 + 0.1)
            add(voice, load(tm["q"]), t0 + 0.15 + tm.get("qoff", 0))
            for k in range(len(item.get("options", []))): add(sfx, pop, t0 + 0.8 + 0.35 * k + (0.2 if item.get("display") else 0), 0.14)
            for k in range(cs): add(sfx, tick, t0 + tm["ask"] + k, 0.18)
            r = t0 + tm["ask"] + cs
            add(sfx, ding, r, 0.2); add(voice, load(tm["a"]), r + 0.25)
            if tm.get("hook_seg"): add(voice, load(tm["hook_seg"]), t0 + tm["hook_at"])
        t0 += timing[g]["dur"]
    # music bed: playful "puzzle / quiz" style (pizzicato bass, marimba riff, soft shaker + clap); key & tempo vary by day
    ms = spec.get("music_seed", 0)
    bpm = [116, 120, 112, 124, 118][ms % 5]; beat = 60 / bpm
    progs = [[[261.6, 329.6, 392], [220, 261.6, 329.6], [174.6, 220, 261.6], [196, 246.9, 293.7]],      # C Am F G
             [[293.7, 370, 440], [246.9, 293.7, 370], [196, 246.9, 293.7], [220, 277.2, 329.6]],      # D Bm G A
             [[196, 246.9, 293.7], [164.8, 196, 246.9], [130.8, 164.8, 196], [146.8, 185, 220]]]      # G Em C D
    chords = progs[ms % 3]
    mus = np.zeros(N); bar = beat * 4; nb = int(total / bar) + 2
    def pluck(f, d=0.35, dec=9, att=0.006):
        t_ = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t_) + 0.3 * np.sin(4 * np.pi * f * t_) * np.exp(-14 * t_)) * np.exp(-dec * t_) * np.minimum(1, t_ / att)
    def marimba(f, d=0.45):
        t_ = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t_) + 0.12 * np.sin(2 * np.pi * f * 3.98 * t_) * np.exp(-25 * t_)) * np.exp(-8 * t_) * np.minimum(1, t_ / 0.008)
    nrng = np.random.default_rng(3)
    shk = np.diff(np.concatenate([[0], nrng.normal(0, 1, int(0.06 * SR))])) * np.exp(-np.arange(int(0.06 * SR)) / SR * 60)
    clap = lp(nrng.normal(0, 1, int(0.12 * SR)), 2) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30)
    riffs = [[0, 2, 1, 2, 0, 2, 1, None], [0, None, 2, 1, None, 2, 0, 1], [2, 1, 0, None, 2, None, 1, 0]]
    for b in range(nb):
        ch = chords[b % 4]; t0b = b * bar; riff = riffs[(b // 4 + ms) % 3]
        for q in range(4):  # pizzicato bass: root / fifth bounce
            add(mus, pluck(ch[0] / 2 * (1.5 if q % 2 else 1), 0.3, 11) * 0.55, t0b + q * beat)
        for k, n in enumerate(riff):  # marimba riff on 8ths, octave up
            if n is None: continue
            add(mus, marimba(ch[n] * 2) * (0.32 if k % 2 == 0 else 0.24), t0b + k * beat / 2)
        for k in range(8):  # soft shaker on 8ths, accent off-beats
            add(mus, shk * (0.05 if k % 2 else 0.025), t0b + k * beat / 2)
        for q in (1, 3):  # gentle clap on 2 and 4
            add(mus, clap * 0.08, t0b + q * beat)
    mus = lp(mus, 5)
    # soft room reverb (decaying noise impulse) for a smooth, dreamy bed
    ir_n = int(1.4 * SR); ir = np.random.default_rng(5).normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 3.2); ir = lp(ir, 20); ir /= np.abs(ir).sum() / 6
    from numpy.fft import rfft, irfft
    L_ = len(mus) + ir_n; nf = 1 << (L_ - 1).bit_length()
    wet = irfft(rfft(mus, nf) * rfft(ir, nf), nf)[:len(mus)]
    mus = 0.85 * mus + 0.15 * wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(mus))
    venv = lp(np.abs(voice), int(0.25 * SR)); venv = venv / (venv.max() + 1e-9)
    mus = mus * (1 - 0.55 * np.clip(venv * 4, 0, 1))  # sidechain duck under Professor Hoot
    fade = int(0.8 * SR); mus[int(total * SR) - fade:int(total * SR)] *= np.linspace(1, 0, fade)
    mus = mus / (np.max(np.abs(mus)) + 1e-9)
    sfx = lp(sfx, 4)
    mix = (voice * 0.95 + sfx * 0.9 + mus * 0.17)[:int(total * SR)]
    mix = mix / max(1, np.max(np.abs(mix)) / 0.95)
    wav = os.path.join(work, "mix.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{g}.mp4'\n" for g in order))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest",
                    "-movflags", "+faststart", out], check=True, stdin=subprocess.DEVNULL)
    if spec["orientation"] == "h" and spec.get("badge", True):
        # LIKE + SUBSCRIBE badge in the top-left corner, 10 times x 4 s (Aman, 17 Nov)
        raw = out[:-4] + ".nobadge.mp4"; os.replace(out, raw)
        subprocess.run([sys.executable, os.path.join(HERE, "subscribe_overlay.py"), raw, out,
                        str(spec.get("badge_times", 10)), str(spec.get("badge_secs", 4))], check=True, stdin=subprocess.DEVNULL)
        os.remove(raw)
    print(out, round(dur(out), 2), "s", round(os.path.getsize(out) / 1e6, 1), "MB")

if __name__ == "__main__":
    main()
