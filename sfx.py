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


def make_music_upbeat(path, bpm=108, bars=8, seed=3):
    """bright, modern 'corporate / tech ad' loop: pluck chords, warm pad, bass, soft kick, clap and hats.
    Progression C - G - Am - F (uplifting pop). Generated here, so no copyright issues. Seamless loop."""
    if os.path.exists(path):
        return path
    import numpy as np
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm; bar = 4 * beat
    n = int(SR * bar * bars); L = np.zeros(n); R = np.zeros(n)
    hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    prog = [[60, 64, 67, 72], [59, 62, 67, 71], [57, 60, 64, 69], [57, 60, 65, 69]]  # C, G/B, Am, F
    roots = [36, 43, 45, 41]

    def add(sig, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR); j = min(n, i + len(sig))
        if i >= n:
            return
        s = sig[: j - i] * gain
        L[i:j] += s * (1 - pan) ** 0.5; R[i:j] += s * (1 + pan) ** 0.5

    def tone(f, dur, decay, harm=(1, .5, .25, .12), attack=0.004):
        t = np.arange(int(dur * SR)) / SR
        w = sum(a * np.sin(2 * np.pi * f * (k + 1) * t) for k, a in enumerate(harm))
        rel = np.minimum(1, (t[-1] - t) / 0.03 + 1e-9)  # 30 ms release, no clicks at note ends
        return w * np.exp(-t * decay) * np.minimum(1, t / attack) * rel

    def noise(dur, decay, hp=True):
        x = rng.uniform(-1, 1, int(dur * SR))
        if hp:
            x = np.diff(x, prepend=0)
        t = np.arange(len(x)) / SR
        return x * np.exp(-t * decay)

    kick_t = np.arange(int(0.35 * SR)) / SR
    kick = np.sin(2 * np.pi * (48 * kick_t + 90 * (1 - np.exp(-kick_t * 30)) / 30)) * np.exp(-kick_t * 9)
    for b in range(bars):
        c = b % 4; t_bar = b * bar
        # warm pad (whole bar)
        for m in prog[c]:
            add(tone(hz(m), bar, 0.6, harm=(1, .3, .1), attack=0.25), t_bar, pan=0.0, gain=0.035)
        # pluck pattern on 8ths: x . x x . x . x
        for k, on in enumerate([1, 0, 1, 1, 0, 1, 0, 1]):
            if on:
                for vi, m in enumerate(prog[c][1:] if k % 2 else prog[c][:3]):
                    add(tone(hz(m + 12), 0.5, 9), t_bar + k * beat / 2, pan=(-0.35 + 0.35 * vi), gain=0.09)
        # bass: root on 8ths with octave bounce
        for k in range(8):
            m = roots[c] + (12 if k % 4 == 3 else 0)
            add(tone(hz(m), beat / 2 * 0.95, 5, harm=(1, .35, .1), attack=0.01), t_bar + k * beat / 2, gain=0.16)
        # drums
        for q in range(4):
            add(kick, t_bar + q * beat, gain=0.4)
            if q in (1, 3):
                add(noise(0.12, 30), t_bar + q * beat, gain=0.06)
            add(noise(0.04, 90), t_bar + q * beat + beat / 2, pan=0.3, gain=0.025)
        if b % 4 == 3:  # little fill at phrase end
            for k in range(4):
                add(noise(0.04, 90), t_bar + 3 * beat + k * beat / 4, pan=-0.3, gain=0.02)
    peak = max(np.abs(L).max(), np.abs(R).max()) or 1
    st = (np.stack([L, R], 1) / peak * 0.85 * 32767).astype("<i2")
    raw = path + ".raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
                    "lowpass=f=10000,aecho=0.8:0.5:60|120:0.18|0.1,equalizer=f=250:t=q:w=1:g=-2,highshelf=f=6000:g=1.5,"
                    "acompressor=threshold=0.3:ratio=2:attack=10:release=150",
                    "-c:a", "pcm_s16le", path], check=True)
    os.remove(raw)
    return path
