"""Step 4: assemble scenes + narration + presenter + burned-in captions + music into an mp4 with ffmpeg.
Works for landscape (1920x1080) and vertical Shorts (1080x1920)."""
import os, subprocess

FPS = 30
CHAR_W, CHAR_H = 680, 700


def _ass_time(t):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def make_ass(scene_texts, durations, path, W, H, vertical):
    """Captions: each scene's text split into short chunks timed by word count."""
    if vertical:  # above the presenter, centred
        style, wpc = f"DejaVu Sans,74,&H00FFFFFF,&H00000000,&H80000000,1,6,2,2,60,60,{CHAR_H + 40}", 3
    else:         # bottom-left, clear of the presenter
        style, wpc = "DejaVu Sans,64,&H00FFFFFF,&H00000000,&H80000000,1,5,2,2,90,720,60", 4
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Outline,Shadow,Alignment,MarginL,MarginR,MarginV
Style: Default,{style}
Style: Hi,{style.replace('&H00FFFFFF', '&H0000E5FF', 1)}

[Events]
Format: Layer,Start,End,Style,Text
"""
    lines, t0 = [], 0.0
    for text, d in zip(scene_texts, durations):
        words = text.split()
        chunks = [words[i:i + wpc] for i in range(0, len(words), wpc)]
        speak = d - 0.25
        total_chars = sum(len(" ".join(c)) for c in chunks) or 1
        t = t0
        for c in chunks:
            dur = speak * len(" ".join(c)) / total_chars
            lines.append(f"Dialogue: 0,{_ass_time(t)},{_ass_time(t + dur)},Default,{' '.join(c)}")
            t += dur
        t0 += d
    open(path, "w").write(head + "\n".join(lines) + "\n")


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode:
        raise RuntimeError("ffmpeg failed:\n" + r.stderr.decode()[-2000:])


def render(scenes, workdir, out_path, music=None, vertical=False):
    """scenes: list of dict(audio, duration, text, and one of:
         slide_list (concat file of animated slide states) | visual_path + is_video,
       optional char_list (presenter frames))"""
    W, H = (1080, 1920) if vertical else (1920, 1080)
    tag = "v" if vertical else "h"
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p"
    cx, cy = ((W - CHAR_W) // 2, H - CHAR_H) if vertical else (W - CHAR_W - 20, H - CHAR_H)
    segs = []
    for i, s in enumerate(scenes):
        seg = os.path.join(workdir, f"seg{i}_{tag}.mp4")
        d = f"{s['duration'] + 0.25:.2f}"
        if s.get("slide_list"):
            inp = ["-f", "concat", "-safe", "0", "-i", s["slide_list"]]
            filt = f"scale={W}:{H},fps={FPS},format=yuv420p"
        elif s.get("is_video"):  # stock footage, darkened so text/presenter pop
            inp = ["-stream_loop", "-1", "-i", s["visual_path"]]
            filt = cover + ",eq=brightness=-0.12:saturation=0.9"
        else:  # still image with slow zoom
            inp = ["-loop", "1", "-framerate", str(FPS), "-i", s["visual_path"]]
            filt = f"scale={W * 5 // 4}:-1,zoompan=z='min(zoom+0.0008,1.2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p"
        enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-ar", "44100", "-ac", "2"]
        if s.get("char_list"):
            run(["ffmpeg", "-y", *inp, "-i", s["audio"], "-f", "concat", "-safe", "0", "-i", s["char_list"],
                 "-t", d, "-filter_complex",
                 f"[0:v]{filt}[bg];[2:v]format=rgba[c];[bg][c]overlay={cx}:{cy}:eof_action=repeat,format=yuv420p[v];"
                 f"[1:a]apad[a]", "-map", "[v]", "-map", "[a]", *enc, seg])
        else:
            run(["ffmpeg", "-y", *inp, "-i", s["audio"], "-t", d, "-filter_complex",
                 f"[0:v]{filt}[v];[1:a]apad[a]", "-map", "[v]", "-map", "[a]", *enc, seg])
        segs.append(seg)

    lst = os.path.join(workdir, f"list_{tag}.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in segs))
    joined = os.path.join(workdir, f"joined_{tag}.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

    ass = os.path.join(workdir, f"captions_{tag}.ass")
    make_ass([s["text"] for s in scenes], [s["duration"] + 0.25 for s in scenes], ass, W, H, vertical)

    cmd = ["ffmpeg", "-y", "-i", joined]
    if music and os.path.exists(music):
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                f"[0:v]ass={ass}[v];[1:a]volume=0.07[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", f"ass={ass}"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-movflags", "+faststart", out_path]
    run(cmd)
    return out_path
