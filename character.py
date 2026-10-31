"""Animated cartoon presenter: mouth follows the voice loudness, eyes blink, body bobs slightly.
Produces a list of PNG frames (transparent) per scene, played via ffmpeg concat."""
import array, os, random, subprocess
from PIL import Image, ImageDraw

FPS = 30
CW, CH = 560, 700  # character canvas
S = 2  # supersample


def _base(eyes_open: bool, mouth: int) -> Image.Image:
    im = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = lambda *v: [x * S for x in v]
    # body / hoodie
    d.rounded_rectangle(s(60, 470, 500, 760), radius=120 * S, fill=(52, 99, 235))
    d.polygon(s(220, 470, 340, 470, 280, 560), fill=(235, 190, 150))   # neckline
    d.rectangle(s(240, 400, 320, 480), fill=(235, 190, 150))           # neck
    # head + ears
    d.ellipse(s(70, 230, 130, 330), fill=(235, 190, 150))
    d.ellipse(s(430, 230, 490, 330), fill=(235, 190, 150))
    d.ellipse(s(100, 70, 460, 450), fill=(245, 205, 165))
    # hair
    d.pieslice(s(90, 50, 470, 380), 180, 360, fill=(45, 35, 40))
    d.ellipse(s(90, 120, 190, 230), fill=(45, 35, 40))
    d.ellipse(s(370, 120, 470, 230), fill=(45, 35, 40))
    d.rectangle(s(150, 140, 410, 190), fill=(245, 205, 165))
    d.pieslice(s(100, 70, 460, 330), 180, 360, fill=(45, 35, 40))
    d.chord(s(150, 150, 410, 260), 0, 180, fill=(245, 205, 165))
    # glasses
    for cx in (210, 350):
        d.ellipse(s(cx - 52, 235, cx + 52, 330), outline=(30, 30, 40), width=7 * S, fill=(255, 255, 255, 235))
    d.line(s(262, 275, 298, 275), fill=(30, 30, 40), width=7 * S)
    # eyes
    for cx in (210, 350):
        if eyes_open:
            d.ellipse(s(cx - 14, 262, cx + 14, 300), fill=(30, 30, 40))
            d.ellipse(s(cx - 5, 268, cx + 3, 277), fill=(255, 255, 255))
        else:
            d.line(s(cx - 18, 285, cx + 18, 285), fill=(30, 30, 40), width=6 * S)
    # brows
    d.line(s(165, 215, 255, 208), fill=(45, 35, 40), width=9 * S)
    d.line(s(305, 208, 395, 215), fill=(45, 35, 40), width=9 * S)
    # nose
    d.arc(s(268, 300, 292, 350), 20, 160, fill=(200, 150, 115), width=5 * S)
    # mouth (0 closed, 1 small, 2 medium, 3 wide)
    mx, my = 280, 385
    if mouth == 0:
        d.arc(s(mx - 40, my - 20, mx + 40, my + 15), 20, 160, fill=(150, 60, 70), width=7 * S)
    else:
        h = {1: 14, 2: 28, 3: 44}[mouth]
        w = {1: 26, 2: 34, 3: 40}[mouth]
        d.ellipse(s(mx - w, my - 6, mx + w, my - 6 + h * 2 // 1 // 2 + h), fill=(110, 30, 45))
        if mouth >= 2:
            d.ellipse(s(mx - w + 12, my + h - 4, mx + w - 12, my + h + 18), fill=(220, 100, 110))
        d.rectangle(s(mx - w + 8, my - 6, mx + w - 8, my + 4), fill=(255, 255, 255))
    return im.resize((CW, CH), Image.LANCZOS)


_cache = {}


def frame(eyes_open, mouth):
    k = (eyes_open, mouth)
    if k not in _cache:
        _cache[k] = _base(eyes_open, mouth)
    return _cache[k]


def loudness(audio_path, fps=FPS):
    """RMS loudness per video frame, normalised 0..1"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", audio_path, "-f", "s16le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True, check=True).stdout
    a = array.array("h"); a.frombytes(raw[: len(raw) // 2 * 2])
    win = 16000 // fps
    vals = []
    for i in range(0, len(a) - win + 1, win):
        seg = a[i:i + win]
        vals.append((sum(x * x for x in seg) / win) ** 0.5)
    if not vals:
        return []
    peak = sorted(vals)[int(len(vals) * 0.95)] or 1
    return [min(v / peak, 1.0) for v in vals]


def build_scene_frames(audio_path, total_seconds, workdir, idx, seed=0):
    """writes PNGs for each distinct state + a concat list file; returns list path"""
    rnd = random.Random(seed + idx)
    loud = loudness(audio_path)
    n = int(total_seconds * FPS) + 1
    loud += [0.0] * (n - len(loud))
    states, blink_left, next_blink = [], 0, rnd.randint(60, 120)
    prev = 0
    for i in range(n):
        if blink_left > 0:
            blink_left -= 1; eyes = False
        else:
            eyes = True; next_blink -= 1
            if next_blink <= 0:
                blink_left, next_blink = 4, rnd.randint(60, 140)
        l = loud[i]
        m = 0 if l < 0.12 else 1 if l < 0.4 else 2 if l < 0.7 else 3
        m = round(0.5 * m + 0.5 * prev) if m != prev else m  # smooth
        prev = m
        states.append((eyes, m))
    paths = {}
    for st in set(states):
        p = os.path.join(workdir, f"char_{int(st[0])}{st[1]}.png")
        if not os.path.exists(p):
            frame(*st).save(p)
        paths[st] = os.path.abspath(p)
    lst = os.path.join(workdir, f"char{idx}.txt")
    with open(lst, "w") as f:
        for st in states:
            f.write(f"file '{paths[st]}'\nduration {1 / FPS:.5f}\n")
    return lst
