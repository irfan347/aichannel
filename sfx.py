"""Subtle sound design: pops when items appear, keyboard clicks while prompts type, a ding on results,
a whoosh on scene changes, and a soft generated background pad (if no music.mp3 is supplied).
Everything is generated here, so there are no copyright issues."""
import array, math, os, random, re, subprocess, wave

SR = 48000


def _env_tone(f0, f1, dur, amp, decay):
    n = int(SR * dur); out = []; ph = 0.0
    for i in range(n):
        t = i / SR
        f = f0 + (f1 - f0) * (t / dur)
        ph += 2 * math.pi * f / SR
        out.append(amp * math.sin(ph) * math.exp(-t * decay) * min(1, i / 60))
    return out


def _noise(dur, amp, decay, lp=0.5, seed=1):
    rnd = random.Random(seed); n = int(SR * dur); out = []; y = 0.0
    for i in range(n):
        y += lp * (rnd.uniform(-1, 1) - y)
        out.append(amp * y * math.exp(-i / SR * decay))
    return out


def _whoosh(dur=0.45, amp=0.22):
    rnd = random.Random(7); n = int(SR * dur); out = []; y = 0.0
    for i in range(n):
        p = i / n
        lp = 0.02 + 0.25 * math.sin(math.pi * p)        # filter opens then closes
        y += lp * (rnd.uniform(-1, 1) - y)
        out.append(amp * y * math.sin(math.pi * p) ** 1.5)
    return out


SOUNDS = None


def sounds():
    global SOUNDS
    if SOUNDS is None:
        SOUNDS = {
            "pop": _env_tone(900, 520, 0.09, 0.28, 38),
            "ding": [a + b for a, b in zip(_env_tone(1318, 1318, 0.6, 0.18, 7), _env_tone(1976, 1976, 0.6, 0.07, 9))],
            "whoosh": _whoosh(),
            "clicks": [_noise(0.018, 0.16 * (0.7 + 0.3 * k / 4), 260, lp=0.8, seed=k) for k in range(5)],
        }
    return SOUNDS


def events_from_html(html):
    """read the slide timeline from the generated HTML"""
    ev = []
    for tag in re.findall(r"<[^>]+>", html):
        attrs = dict(re.findall(r"(data-[\w-]+)=\"?([^\s\">]+)", tag))
        if attrs.get("data-sfx") == "type" and "data-type0" in attrs:
            a, b = float(attrs["data-type0"]), float(attrs["data-type1"])
            t = a
            rnd = random.Random(int(a * 100))
            while t < b:
                ev.append((t, "click")); t += rnd.uniform(0.07, 0.12)
        elif "data-t" in attrs:
            t = float(attrs["data-t"])
            kind = "ding" if attrs.get("data-sfx") == "ding" else "pop"
            if t >= 0.25 or kind == "ding":
                ev.append((t, kind))
    ev.sort()
    out, last = [], {}
    for t, k in ev:  # drop pops that land on top of each other
        if k == "pop" and t - last.get(k, -9) < 0.15:
            continue
        out.append((t, k)); last[k] = t
    return out


def render_track(events, total, path):
    """events: [(abs_time, kind)] -> mono 48k wav"""
    S = sounds()
    buf = [0.0] * (int(total * SR) + SR)
    rnd = random.Random(3)
    for t, k in events:
        snd = rnd.choice(S["clicks"]) if k == "click" else S[k]
        i0 = int(t * SR)
        for j, v in enumerate(snd):
            if i0 + j < len(buf):
                buf[i0 + j] += v
    data = array.array("h", (max(-32767, min(32767, int(v * 32767))) for v in buf[: int(total * SR)]))
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
    return path


def make_music(path):
    """16-second soft chord pad loop (Cmaj7 - Am7 - Fmaj7 - G6), warm and low-key"""
    if os.path.exists(path):
        return path
    chords = [[130.81, 164.81, 196.00, 246.94], [110.0, 130.81, 164.81, 196.0],
              [87.31, 110.0, 130.81, 164.81], [98.0, 123.47, 146.83, 164.81]]

    def chord_expr(fs):
        return "+".join(f"0.10*sin(2*PI*{f}*t)+0.03*sin(4*PI*{f}*t)" for f in fs) + f"+0.12*sin(2*PI*{fs[0] / 2}*t)"
    seg = "mod(t,16)"
    expr = (f"(if(lt({seg},4),{chord_expr(chords[0])},if(lt({seg},8),{chord_expr(chords[1])},"
            f"if(lt({seg},12),{chord_expr(chords[2])},{chord_expr(chords[3])}))))"
            f"*(0.55+0.45*sin(PI*mod(t,4)/4))")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s={SR}:d=16",
                    "-af", "lowpass=f=1400,aecho=0.8:0.6:90|170:0.25|0.15,volume=0.8",
                    "-ac", "1", "-c:a", "pcm_s16le", path], check=True)
    return path
