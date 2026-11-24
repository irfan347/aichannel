"""Animated cartoon presenter: mouth follows the voice loudness, eyes blink, body bobs slightly.
Produces a list of PNG frames (transparent) per scene, played via ffmpeg concat."""
import array, os, random, subprocess
from PIL import Image, ImageDraw

FPS = 30
CW, CH = 680, 700  # character canvas
OX = 60  # horizontal margin so gestures fit
S = 2  # supersample


def _base(eyes_open: bool, mouth: int, pose: int = 0) -> Image.Image:
    im = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = lambda *v: [(x + (OX if k % 2 == 0 else 0)) * S for k, x in enumerate(v)]

    def limb(pts, w, col):
        for a, b in zip(pts, pts[1:]):
            d.line(s(*a, *b), fill=col, width=w * S)
        for p in pts[:-1]:
            d.ellipse(s(p[0] - w // 2, p[1] - w // 2, p[0] + w // 2, p[1] + w // 2), fill=col)
    # body / hoodie
    d.rounded_rectangle(s(60, 470, 500, 760), radius=120 * S, fill=(52, 99, 235))
    sleeve, skin = (40, 85, 215), (235, 190, 150)
    if pose == 1:   # arm raised, pointing at the slide on the left
        limb([(130, 560), (40, 470), (-10, 360)], 64, sleeve)
        d.ellipse(s(-48, 300, 28, 376), fill=skin)                       # fist
        d.rounded_rectangle(s(-60, 318, 0, 346), radius=14 * S, fill=skin)  # index finger pointing left
    elif pose == 2:  # open hand explaining
        limb([(430, 600), (530, 560), (560, 470)], 64, sleeve)
        d.ellipse(s(520, 390, 600, 470), fill=skin)
        for fx in (528, 548, 568, 588):
            d.rounded_rectangle(s(fx - 8, 360, fx + 8, 420), radius=8 * S, fill=skin)
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


STYLE = "classic"  # "pro": young man in a navy blazer, shirt and tie (set by main.py from the script)


def _base_pro(eyes_open: bool, mouth: int, pose: int = 0) -> Image.Image:
    """professional young presenter: neat dark hair, clean-shaven, navy blazer, white shirt, green tie"""
    im = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = lambda *v: [(x + (OX if k % 2 == 0 else 0)) * S for k, x in enumerate(v)]
    skin, skin_d, hair = (214, 162, 122), (190, 138, 100), (24, 20, 22)
    navy, navy_l, shirt, tie = (20, 33, 56), (31, 48, 78), (244, 246, 248), (58, 110, 18)

    def limb(pts, w, col):
        for a, b in zip(pts, pts[1:]):
            d.line(s(*a, *b), fill=col, width=w * S)
        for q in pts[:-1]:
            d.ellipse(s(q[0] - w // 2, q[1] - w // 2, q[0] + w // 2, q[1] + w // 2), fill=col)
    # blazer body, shirt, tie, lapels
    d.rounded_rectangle(s(50, 480, 510, 780), radius=110 * S, fill=navy)
    d.polygon(s(200, 478, 360, 478, 280, 640), fill=shirt)
    d.polygon(s(268, 500, 292, 500, 300, 520, 290, 620, 280, 640, 270, 620, 260, 520), fill=tie)
    d.polygon(s(262, 486, 298, 486, 292, 506, 268, 506), fill=(46, 90, 12))          # knot
    d.polygon(s(200, 478, 236, 470, 280, 640, 250, 600), fill=navy_l)                 # left lapel
    d.polygon(s(360, 478, 324, 470, 280, 640, 310, 600), fill=navy_l)                 # right lapel
    d.polygon(s(232, 470, 262, 486, 252, 500), fill=shirt)                            # collar
    d.polygon(s(328, 470, 298, 486, 308, 500), fill=shirt)
    d.rounded_rectangle(s(395, 560, 445, 574), radius=4 * S, fill=(191, 255, 118))   # pocket square
    if pose == 1:   # pointing at the slide on the left
        limb([(130, 590), (50, 530), (20, 450)], 66, navy)
        d.rectangle(s(-4, 414, 44, 434), fill=shirt)                                   # cuff
        d.ellipse(s(-20, 350, 56, 426), fill=skin)                                     # palm
        for fy in (356, 374, 392, 410):                                                # fingers toward the slide
            d.rounded_rectangle(s(-56, fy - 8, 0, fy + 8), radius=8 * S, fill=skin)
        d.rounded_rectangle(s(24, 322, 42, 366), radius=9 * S, fill=skin)              # thumb
    elif pose == 2:  # open hand explaining
        limb([(430, 610), (530, 570), (560, 480)], 66, navy)
        d.rectangle(s(536, 456, 584, 476), fill=shirt)
        d.ellipse(s(520, 390, 600, 470), fill=skin)
        for fx in (528, 548, 568, 588):
            d.rounded_rectangle(s(fx - 8, 360, fx + 8, 420), radius=8 * S, fill=skin)
    # neck, ears, head
    d.rectangle(s(242, 400, 318, 486), fill=skin_d)
    d.ellipse(s(92, 250, 146, 340), fill=skin_d)
    d.ellipse(s(414, 250, 468, 340), fill=skin_d)
    d.ellipse(s(110, 80, 450, 460), fill=skin)
    # hair: neat, side part
    d.pieslice(s(100, 50, 460, 330), 180, 360, fill=hair)
    d.ellipse(s(100, 120, 170, 250), fill=hair)
    d.ellipse(s(390, 120, 460, 250), fill=hair)
    d.chord(s(150, 120, 420, 250), 0, 180, fill=skin)
    d.polygon(s(150, 180, 210, 110, 330, 96, 420, 150, 420, 180, 330, 140, 220, 150), fill=hair)
    d.line(s(205, 108, 236, 150), fill=(60, 50, 52), width=4 * S)                     # part line
    # eyes
    for cx in (210, 350):
        if eyes_open:
            d.ellipse(s(cx - 30, 262, cx + 30, 298), fill=(255, 255, 255))
            d.ellipse(s(cx - 15, 264, cx + 15, 296), fill=(70, 44, 30))
            d.ellipse(s(cx - 8, 271, cx + 8, 289), fill=(18, 14, 14))
            d.ellipse(s(cx + 2, 268, cx + 9, 276), fill=(255, 255, 255))
            d.arc(s(cx - 32, 258, cx + 32, 300), 200, 340, fill=(40, 30, 28), width=4 * S)
        else:
            d.arc(s(cx - 30, 262, cx + 30, 296), 20, 160, fill=(40, 30, 28), width=5 * S)
    # brows
    d.line(s(172, 238, 250, 232), fill=hair, width=12 * S)
    d.line(s(310, 232, 388, 238), fill=hair, width=12 * S)
    # nose
    d.arc(s(262, 300, 298, 350), 30, 150, fill=skin_d, width=5 * S)
    # mouth (0 closed smile, 1 small, 2 medium, 3 wide)
    mx, my = 280, 398
    if mouth == 0:
        d.arc(s(mx - 34, my - 18, mx + 34, my + 10), 20, 160, fill=(130, 60, 60), width=6 * S)
    else:
        h = {1: 10, 2: 20, 3: 30}[mouth]
        w = {1: 22, 2: 28, 3: 32}[mouth]
        d.ellipse(s(mx - w, my - 6, mx + w, my + h), fill=(100, 34, 40))
        d.rectangle(s(mx - w + 8, my - 6, mx + w - 8, my + 2), fill=(250, 250, 250))
        if mouth >= 2:
            d.ellipse(s(mx - w + 10, my + h - 12, mx + w - 10, my + h + 2), fill=(200, 100, 105))
    return im.resize((CW, CH), Image.LANCZOS)


_cache = {}


BOB = 8  # px of head/body bob while talking


def frame(eyes_open, mouth, pose=0, bob=0):
    k = (STYLE, eyes_open, mouth, pose, bob)
    if k not in _cache:
        im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        base = _base_pro if STYLE == "pro" else _base
        im.alpha_composite(base(eyes_open, mouth, pose), (0, BOB - bob))
        _cache[k] = im
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


def build_scene_frames(audio_path, total_seconds, workdir, idx, seed=0, gesture_at_start=True):
    """writes PNGs for each distinct state + a concat list file; returns list path"""
    rnd = random.Random(seed + idx)
    loud = loudness(audio_path)
    n = int(total_seconds * FPS) + 1
    loud += [0.0] * (n - len(loud))
    states, blink_left, next_blink = [], 0, rnd.randint(60, 120)
    prev, pose, pose_left, next_pose = 0, 0, 0, rnd.randint(45, 90)
    first_point = gesture_at_start
    for i in range(n):
        if blink_left > 0:
            blink_left -= 1; eyes = False
        else:
            eyes = True; next_blink -= 1
            if next_blink <= 0:
                blink_left, next_blink = 4, rnd.randint(60, 140)
        l = loud[i]
        m = 0 if l < 0.12 else 1 if l < 0.4 else 2 if l < 0.7 else 3
        m = round(0.5 * m + 0.5 * prev) if m != prev else m
        prev = m
        # gestures: point at the slide when it changes, otherwise occasional explaining hand
        if first_point and i > 8 and l > 0.2:
            pose, pose_left, first_point = 1, 45, False
        if pose_left > 0:
            pose_left -= 1
            if pose_left == 0:
                pose = 0
        else:
            next_pose -= 1
            if next_pose <= 0 and l > 0.25:
                pose, pose_left, next_pose = rnd.choice([2, 2, 1]), rnd.randint(30, 50), rnd.randint(70, 140)
        bob = round(min(l, 1.0) * 2) * (BOB // 2)
        states.append((eyes, m, pose, bob))
    paths = {}
    for st in set(states):
        p = os.path.join(workdir, "char_%s_%d%d%d%d.png" % (STYLE, int(st[0]), st[1], st[2], st[3]))
        if not os.path.exists(p):
            frame(*st).save(p)
        paths[st] = os.path.abspath(p)
    lst = os.path.join(workdir, f"char{idx}.txt")
    with open(lst, "w") as f:
        for st in states:
            f.write(f"file '{paths[st]}'\nduration {1 / FPS:.5f}\n")
    return lst


def bubble(eyes_open, mouth, bob=0, size=340):
    """presenter inside a round 'facecam' bubble with an accent ring"""
    k = ("bubble", eyes_open, mouth, bob, size)
    if k in _cache:
        return _cache[k]
    SS = 3
    big = size * SS
    bg = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    g = ImageDraw.Draw(bg)
    for y in range(big):  # indigo gradient inside the circle
        t = y / big
        g.line([(0, y), (big, y)], fill=(int(67 + (30 - 67) * t), int(56 + (27 - 56) * t), int(202 + (75 - 202) * t), 255))
    ch = frame(eyes_open, mouth, 0, bob).crop((20, 0, 660, 700))
    cw = int(big * 0.92)
    ch = ch.resize((cw, int(cw * ch.height / ch.width)), Image.LANCZOS)
    bg.alpha_composite(ch, ((big - cw) // 2, int(big * 0.12)))
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    out = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    d = ImageDraw.Draw(out)
    ring = int(big * 0.03)
    d.ellipse((ring // 2, ring // 2, big - ring // 2, big - ring // 2), outline=(250, 204, 21, 255), width=ring)
    out = out.resize((size, size), Image.LANCZOS)
    _cache[k] = out
    return out


def build_bubble_frames(audio_path, total_seconds, workdir, idx, size=340, seed=0):
    """lip-sync + blink + slight bob inside the facecam bubble; returns concat list path"""
    rnd = random.Random(seed + idx)
    loud = loudness(audio_path)
    n = int(round(total_seconds * FPS))
    loud += [0.0] * (n - len(loud))
    states, blink_left, next_blink, prev = [], 0, rnd.randint(60, 120), 0
    for i in range(n):
        if blink_left > 0:
            blink_left -= 1; eyes = False
        else:
            eyes = True; next_blink -= 1
            if next_blink <= 0:
                blink_left, next_blink = 4, rnd.randint(70, 150)
        l = loud[i]
        m = 0 if l < 0.12 else 1 if l < 0.4 else 2 if l < 0.7 else 3
        m = round(0.5 * m + 0.5 * prev) if m != prev else m
        prev = m
        states.append((eyes, m, round(min(l, 1.0) * 2) * (BOB // 2)))
    lst = os.path.join(workdir, f"bub{size}_{idx}.txt")
    with open(lst, "w") as f:
        run_st, run_n = states[0], 0
        def flush(st, c):
            p = os.path.abspath(os.path.join(workdir, "bub%d_%s_%d%d%d.png" % (size, STYLE, int(st[0]), st[1], st[2])))
            if not os.path.exists(p):
                bubble(st[0], st[1], st[2], size).save(p)
            f.write(f"file '{p}'\nduration {c / FPS:.5f}\n")
            return p
        last = None
        for st in states:
            if st == run_st:
                run_n += 1
            else:
                last = flush(run_st, run_n); run_st, run_n = st, 1
        last = flush(run_st, run_n)
        f.write(f"file '{last}'\n")
    return lst
