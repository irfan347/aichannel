"""Step 4: assemble scenes into the final video with frame-exact audio sync.
Every scene lasts exactly N frames; its voice is padded to exactly N/FPS seconds, so picture and sound
never drift. Captions are timed per word, with the spoken word highlighted."""
import os, re, subprocess
import sfx

FPS = 30
YELLOW = "&H0015CCFA&"   # #FACC15 in ASS BGR
WHITE = "&H00FFFFFF&"


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode:
        raise RuntimeError("ffmpeg failed:\n" + r.stderr.decode()[-2500:])


def _t(x):
    x = max(x, 0)
    h, rem = divmod(x, 3600); m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def make_ass(words, path, W, H, vertical):
    """words: [[start, end, text]] absolute seconds"""
    if vertical:
        fs, ml, mr, mv, wpc = 78, 70, 70, 560, 3
    else:
        fs, ml, mr, mv, wpc = 64, 110, 470, 64, 4
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Inter,{fs},&H00FFFFFF,&H000000FF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,5,2,2,{ml},{mr},{mv},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= wpc or w[0] - cur[-1][1] > 0.45):
            groups.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.!?,;:]$", w[2]):
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    clean = lambda s: s.replace("{", "(").replace("}", ")")
    ev = []
    for gi, g in enumerate(groups):
        nxt = groups[gi + 1][0][0] if gi + 1 < len(groups) else g[-1][1] + 0.6
        for k, w in enumerate(g):
            start = w[0]
            end = g[k + 1][0] if k + 1 < len(g) else min(w[1] + 0.35, nxt)
            if end <= start:
                end = start + 0.08
            txt = " ".join((f"{{\\c{YELLOW}}}{clean(x[2])}{{\\c{WHITE}}}" if j == k else clean(x[2]))
                           for j, x in enumerate(g))
            ev.append(f"Dialogue: 0,{_t(start)},{_t(end)},Default,,0,0,0,,{txt}")
    open(path, "w").write(head + "\n".join(ev) + "\n")


def render(scenes, workdir, out_path, music=None, vertical=False):
    """scenes: list of dict(frames=N, wav, words(scene-relative), slide(concat list), clip(optional stock mp4),
    char(optional concat list))"""
    W, H = (1080, 1920) if vertical else (1920, 1080)
    tag = "v" if vertical else "h"
    bub = 420 if vertical else 340
    cx, cy = ((W - bub) // 2, H - bub - 90) if vertical else (W - bub - 60, H - bub - 50)
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
    vsegs, asegs, all_words, t0, events = [], [], [], 0.0, []
    for i, s in enumerate(scenes):
        N = s["frames"]; T = N / FPS
        seg = os.path.join(workdir, f"seg{i}_{tag}.mp4")
        ins, fc = [], []
        if s.get("clip"):
            ins += ["-stream_loop", "-1", "-i", s["clip"], "-f", "concat", "-safe", "0", "-i", s["slide"]]
            fc += [f"[0:v]{cover},eq=brightness=-0.08:saturation=0.95,format=rgba[b0]",
                   f"[1:v]fps={FPS},format=rgba[o]", "[b0][o]overlay=0:0[b]"]
        else:
            ins += ["-f", "concat", "-safe", "0", "-i", s["slide"]]
            fc += [f"[0:v]fps={FPS},scale={W}:{H}[b]"]
        if s.get("char"):
            k = 2 if s.get("clip") else 1
            ins += ["-f", "concat", "-safe", "0", "-i", s["char"]]
            fc += [f"[{k}:v]fps={FPS},format=rgba[c]", f"[b][c]overlay={cx}:{cy}:eof_action=repeat,format=yuv420p[v]"]
        else:
            fc += ["[b]format=yuv420p[v]"]
        run(["ffmpeg", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[v]", "-frames:v", str(N), "-an",
             "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", seg])
        vsegs.append(seg)
        aseg = os.path.join(workdir, f"aud{i}_{tag}.wav")
        run(["ffmpeg", "-y", "-i", s["wav"], "-af", "apad", "-t", f"{T:.6f}", "-ar", "48000", "-ac", "1",
             "-c:a", "pcm_s16le", aseg])
        asegs.append(aseg)
        all_words += [[w[0] + t0, w[1] + t0, w[2]] for w in s["words"]]
        if i > 0:
            events.append((max(t0 - 0.2, 0), "whoosh"))
        events += [(t0 + et, k) for et, k in s.get("events", []) if et < T]
        t0 += T

    def concat(paths, out):
        lst = out + ".txt"
        open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in paths))
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
        return out
    joined = concat(vsegs, os.path.join(workdir, f"joined_{tag}.mp4"))
    voice = concat(asegs, os.path.join(workdir, f"voice_{tag}.wav"))

    ass = os.path.join(workdir, f"captions_{tag}.ass")
    make_ass(all_words, ass, W, H, vertical)
    total = t0
    fx_wav = sfx.render_track(events, total, os.path.join(workdir, f"sfx_{tag}.wav"))
    if not (music and os.path.exists(music)):
        music = sfx.make_music(os.path.join(workdir, "pad.wav"))
    fc = (f"[0:v]ass={ass},fade=t=in:st=0:d=0.35,fade=t=out:st={total - 0.45:.3f}:d=0.45[v];"
          f"[1:a]loudnorm=I=-15:TP=-2:LRA=9,aresample=48000,asplit=2[vo][vsc];"
          f"[2:a]aresample=48000,volume=0.55[sx];"
          f"[3:a]aresample=48000,volume=0.16,afade=t=in:st=0:d=1.5[m0];"
          f"[m0][vsc]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=500[m];"
          f"[vo][sx][m]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95,"
          f"afade=t=out:st={total - 0.8:.3f}:d=0.8[a]")
    cmd = ["ffmpeg", "-y", "-i", joined, "-i", voice, "-i", fx_wav, "-stream_loop", "-1", "-i", music,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.6f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out_path]
    run(cmd)
    return out_path
