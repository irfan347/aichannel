"""Step 4: assemble scenes + narration + burned-in captions + music into final mp4 with ffmpeg."""
import os, subprocess

W, H, FPS = 1920, 1080, 30


def _ass_time(t):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def make_ass(scene_texts, durations, path, words_per_chunk=4):
    """Caption file: each scene's text split into short chunks timed evenly."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Outline,Shadow,Alignment,MarginV
Style: Default,DejaVu Sans,64,&H00FFFFFF,&H00000000,&H80000000,1,5,2,2,110

[Events]
Format: Layer,Start,End,Style,Text
"""
    lines, t0 = [], 0.0
    for text, d in zip(scene_texts, durations):
        words = text.split()
        chunks = [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
        step = d / max(len(chunks), 1)
        for i, c in enumerate(chunks):
            lines.append(f"Dialogue: 0,{_ass_time(t0 + i * step)},{_ass_time(t0 + (i + 1) * step)},Default,{c}")
        t0 += d
    open(path, "w").write(head + "\n".join(lines) + "\n")


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def render(scenes, workdir, out_path, music=None):
    """scenes: list of dict(visual_path, is_video, audio, duration, text)"""
    segs = []
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},format=yuv420p")
    for i, s in enumerate(scenes):
        seg = os.path.join(workdir, f"seg{i}.mp4")
        d = f"{s['duration'] + 0.25:.2f}"  # tiny pause between scenes
        if s["is_video"]:
            inp = ["-stream_loop", "-1", "-i", s["visual_path"]]
            filt = vf
        else:  # slow zoom on still image
            inp = ["-loop", "1", "-framerate", str(FPS), "-i", s["visual_path"]]
            filt = (f"scale=2400:-1,zoompan=z='min(zoom+0.0008,1.2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p")
        run(["ffmpeg", "-y", *inp, "-i", s["audio"], "-t", d, "-vf", filt,
             "-af", "apad", "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
             "-c:a", "aac", "-ar", "44100", "-ac", "2", seg])
        segs.append(seg)

    lst = os.path.join(workdir, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in segs))
    joined = os.path.join(workdir, "joined.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

    ass = os.path.join(workdir, "captions.ass")
    make_ass([s["text"] for s in scenes], [s["duration"] + 0.25 for s in scenes], ass)

    cmd = ["ffmpeg", "-y", "-i", joined]
    if music and os.path.exists(music):
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                f"[0:v]ass={ass}[v];[1:a]volume=0.08[m];[0:a][m]amix=inputs=2:duration=first[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", f"ass={ass}"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", out_path]
    run(cmd)
    return out_path
