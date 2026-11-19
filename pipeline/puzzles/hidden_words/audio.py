"""Music + SFX for the word-search Short (synthesised, loop-safe). Voice files optional."""
import numpy as np, wave, sys, json, os
SR = 44100

def lp(x, k=8): return np.convolve(x, np.ones(k) / k, "same")

def build(total, events, out, voice=None):
    """events: list of (kind, t). voice: list of (wavpath, t)."""
    N = int(total * SR) + 2 * SR
    sfx = np.zeros(N); vo = np.zeros(N)
    def add(buf, sig, t, g=1.0):
        s = int(t * SR); e = min(N, s + len(sig))
        if e > s: buf[s:e] += sig[:e - s] * g
    tt = np.arange(int(0.09 * SR)) / SR
    pop = np.sin(2 * np.pi * (380 * tt + 1800 * tt * tt)) * np.exp(-30 * tt)
    tt = np.arange(int(0.12 * SR)) / SR
    tick = (np.sin(2 * np.pi * 620 * tt) + 0.2 * np.sin(2 * np.pi * 930 * tt)) * np.exp(-34 * tt)
    def mallet(f, d=0.7):
        t_ = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t_) + 0.18 * np.sin(2 * np.pi * f * 3.98 * t_) * np.exp(-30 * t_)) * np.exp(-7 * t_) * np.minimum(1, t_ / 0.012)
    ding = np.zeros(int(1.4 * SR))
    for off, f_, a_ in [(0.0, 783.99, 0.8), (0.09, 1046.5, 1.0), (0.18, 1567.98, 0.35)]:
        m = mallet(f_); o = int(off * SR); ding[o:o + len(m)] += m[:len(ding) - o] * a_
    # "draw the line" : rising marker swish (filtered noise + rising tone), 0.6 s
    n = int(0.6 * SR); t_ = np.arange(n) / SR
    rng = np.random.default_rng(4)
    swish = lp(rng.normal(0, 1, n), 6) - lp(rng.normal(0, 1, n), 40)
    swish = swish * np.sin(np.pi * t_ / 0.6) ** 1.5 * 0.9
    swish += 0.35 * np.sin(2 * np.pi * (500 * t_ + 900 * t_ * t_)) * np.sin(np.pi * t_ / 0.6) ** 2
    wh = lp(np.random.default_rng(1).normal(0, 1, int(0.45 * SR)), 40)
    whoosh = lp(wh, 12) * np.sin(np.linspace(0, np.pi, len(wh))) ** 2 * 3
    # bubbly "boop" for like/subscribe tap
    tt = np.arange(int(0.18 * SR)) / SR
    boop = np.sin(2 * np.pi * (900 * tt - 1500 * tt * tt)) * np.exp(-18 * tt)
    lib = dict(pop=(pop, 0.14), tick=(tick, 0.18), ding=(ding, 0.22), swish=(swish, 0.30), whoosh=(whoosh, 0.08), boop=(boop, 0.12))
    for k, t in events:
        s, g = lib[k]; add(sfx, s, t, g)
    for p, t in (voice or []):
        with wave.open(p) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
            if w.getnchannels() == 2: a = a[::2]
        add(vo, a, t)
    # music: bars fitted to total for a seamless loop
    bpm = 118; beat = 60 / bpm; bar = beat * 4
    nb = int(round(total / bar));
    chords = [[293.7, 370, 440], [246.9, 293.7, 370], [196, 246.9, 293.7], [220, 277.2, 329.6]]
    mus = np.zeros(N)
    def pluck(f, d=0.3, dec=11):
        t_ = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t_) + 0.3 * np.sin(4 * np.pi * f * t_) * np.exp(-14 * t_)) * np.exp(-dec * t_) * np.minimum(1, t_ / 0.006)
    def marimba(f, d=0.45):
        t_ = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * t_) + 0.12 * np.sin(2 * np.pi * f * 3.98 * t_) * np.exp(-25 * t_)) * np.exp(-8 * t_) * np.minimum(1, t_ / 0.008)
    nrng = np.random.default_rng(3)
    shk = np.diff(np.concatenate([[0], nrng.normal(0, 1, int(0.06 * SR))])) * np.exp(-np.arange(int(0.06 * SR)) / SR * 60)
    clap = lp(nrng.normal(0, 1, int(0.12 * SR)), 2) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30)
    riffs = [[0, 2, 1, 2, 0, 2, 1, None], [0, None, 2, 1, None, 2, 0, 1], [2, 1, 0, None, 2, None, 1, 0]]
    for b in range(nb):
        ch = chords[b % 4]; t0 = b * bar; riff = riffs[(b // 4) % 3]
        for q in range(4): add(mus, pluck(ch[0] / 2 * (1.5 if q % 2 else 1)) * 0.55, t0 + q * beat)
        for k, nn in enumerate(riff):
            if nn is not None: add(mus, marimba(ch[nn] * 2) * (0.32 if k % 2 == 0 else 0.24), t0 + k * beat / 2)
        for k in range(8): add(mus, shk * (0.05 if k % 2 else 0.025), t0 + k * beat / 2)
        for q in (1, 3): add(mus, clap * 0.08, t0 + q * beat)
    mus = lp(mus, 5)
    T = int(nb * bar * SR)
    venv = lp(np.abs(vo), int(0.25 * SR)); venv /= venv.max() + 1e-9
    mus *= 1 - 0.55 * np.clip(venv * 4, 0, 1)
    tail = mus[T:].copy(); mus[:len(tail)] += tail; mus[T:] = 0   # wrap tail to start -> loop
    mus /= np.max(np.abs(mus)) + 1e-9
    mix = (vo * 0.95 + lp(sfx, 4) * 0.9 + mus * 0.2)[:T]
    mix /= max(1, np.max(np.abs(mix)) / 0.95)
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return nb * bar
