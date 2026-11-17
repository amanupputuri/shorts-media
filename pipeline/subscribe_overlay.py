"""Add an animated "LIKE & SUBSCRIBE" badge in the top-left corner of a finished video.

usage: python3 subscribe_overlay.py IN.mp4 OUT.mp4 [TIMES] [SECS]
  TIMES  number of appearances (default 10), spread evenly between the intro and the outro
  SECS   seconds on screen each time (default 4)
"""
import sys, os, subprocess, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
EXTRA = 90  # room for the slide-in overshoot

def probe(f):
    o = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                            "stream=width,height:format=duration", "-of", "json", f]))
    return o["streams"][0]["width"], o["streams"][0]["height"], float(o["format"]["duration"])

def emoji(e, size):
    f = ImageFont.truetype(os.path.join(HERE, "fonts", "NotoColorEmoji.ttf"), 109)
    im = Image.new("RGBA", (180, 170), (0, 0, 0, 0)); ImageDraw.Draw(im).text((20, 15), e, font=f, embedded_color=True)
    im = im.crop(im.getbbox()); return im.resize((int(im.width * size / im.height), size), Image.LANCZOS)

def badge(scale):
    """LIKE pill + SUBSCRIBE pill, drawn once at full size."""
    s = scale; fnt = ImageFont.truetype(os.path.join(HERE, "fonts", "Fredoka-SemiBold.ttf"), int(44 * s))
    W, H = int(640 * s), int(110 * s); im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    lw = int(220 * s); sw = W - lw - int(30 * s)
    for x0, w in ((int(6 * s), lw), (lw + int(26 * s), sw)):
        sd.rounded_rectangle((x0, int(14 * s), x0 + w, H - int(2 * s)), radius=int(46 * s), fill=(0, 0, 0, 70))
    im.alpha_composite(sh)
    # LIKE pill (white)
    d.rounded_rectangle((0, int(6 * s), lw, H - int(10 * s)), radius=int(46 * s), fill=(255, 255, 255, 255))
    th = emoji("👍", int(56 * s)); im.alpha_composite(th, (int(22 * s), int((H - 4 * s - th.height) / 2)))
    d.text((int(92 * s), int((H - 4 * s) / 2)), "LIKE", font=fnt, fill=(40, 40, 60), anchor="lm")
    # SUBSCRIBE pill (red)
    x0 = lw + int(20 * s)
    d.rounded_rectangle((x0, int(6 * s), x0 + sw, H - int(10 * s)), radius=int(46 * s), fill=(235, 45, 60, 255))
    bl = emoji("🔔", int(52 * s)); im.alpha_composite(bl, (x0 + int(24 * s), int((H - 4 * s - bl.height) / 2)))
    d.text((x0 + int(92 * s), int((H - 4 * s) / 2)), "SUBSCRIBE", font=fnt, fill=(255, 255, 255), anchor="lm")
    return im

def ease_out_back(t):
    t = max(0.0, min(1.0, t)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def frame(b, pad, t, secs):
    """badge state at t seconds into one appearance -> RGBA image of the overlay box"""
    Wb, Hb = b.size; box = Image.new("RGBA", (Wb + 2 * pad + EXTRA, Hb + 2 * pad), (0, 0, 0, 0))
    if t < 0.45: x = -Wb - pad + (Wb + 2 * pad) * ease_out_back(t / 0.45); a = 1
    elif t > secs - 0.35: x = pad - (Wb + 2 * pad) * ((t - (secs - 0.35)) / 0.35) ** 2; a = 1
    else: x = pad; a = 1
    sc = 1.0
    for pt in (1.3, 2.6):  # two gentle "tap" pulses
        if pt <= t < pt + 0.3: sc = 1 + 0.07 * math.sin(math.pi * (t - pt) / 0.3)
    bb = b if sc == 1 else b.resize((int(Wb * sc), int(Hb * sc)), Image.LANCZOS)
    box.paste(bb, (int(x - (bb.width - Wb) / 2), int(pad - (bb.height - Hb) / 2)), bb)
    return box

def main():
    src, out = sys.argv[1], sys.argv[2]
    times = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    secs = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
    W, H, D = probe(src)
    scale = W / 1920 if W > H else W / 1080 * 0.9
    b = badge(scale); pad = int(14 * scale)
    first, last = 8.0, D - 8.0 - secs  # skip the title card and the outro (it already says like & subscribe)
    starts = [round(first + k * (last - first) / (times - 1), 2) for k in range(times)]
    bw, bh = b.width + 2 * pad + EXTRA, b.height + 2 * pad
    bw += bw % 2; bh += bh % 2
    mx, my = int(28 * scale), int(26 * scale)
    # one small transparent track covering the whole video, badge drawn only inside the windows
    track = out + ".badge.mov"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{bw}x{bh}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", track], stdin=subprocess.PIPE)
    empty = np.zeros((bh, bw, 4), np.uint8).tobytes(); cache = {}
    for k in range(int(D * FPS) + 1):
        t = k / FPS; s = next((s for s in starts if s <= t < s + secs), None)
        if s is None: p.stdin.write(empty); continue
        key = round((t - s) * FPS)
        if key not in cache:
            fr = frame(b, pad, key / FPS, secs); c = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); c.alpha_composite(fr)
            cache[key] = np.asarray(c).tobytes()
        p.stdin.write(cache[key])
    p.stdin.close(); p.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", track, "-filter_complex", f"[0:v][1:v]overlay={mx}:{my}:eof_action=pass[v]",
                    "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart", out], check=True)
    os.remove(track)
    print(out, "badge at", ", ".join(f"{s:.1f}s" for s in starts))

if __name__ == "__main__":
    main()
