"""Usage:
  python main.py --from-script scripts/video02.json                  # landscape video + Short + thumbnail
  python main.py --from-script scripts/video02.json --format landscape
  python main.py --from-script scripts/video02.json --upload --privacy public

Scene "screen" types: title, chat, steps, bullets, checklist, stock (stock footage, needs PEXELS_API_KEY).
Use **word** in titles/items to highlight a word in yellow.
"""
import argparse, json, math, os, re
import voice, visuals, render, character, slides, anim

FPS = 30
GAP = 0.35  # breath between scenes (seconds)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def prepare_audio(script, work):
    """voice for every scene (shared by landscape + vertical): cleaned wav + word timings"""
    out = []
    for i, sc in enumerate(script["scenes"]):
        wav, wj = os.path.join(work, f"voice{i}.wav"), os.path.join(work, f"voice{i}.json")
        if not (os.path.exists(wav) and os.path.exists(wj)):
            raw = os.path.join(work, f"voice{i}_raw.mp3")
            words = voice.synth(sc["narration"], raw)
            voice.clean(raw, wav)
            json.dump(voice.align(sc["narration"], words, voice.duration(wav)), open(wj, "w"))
        out.append((wav, voice.duration(wav), json.load(open(wj))))
        print(f"voice {i + 1}/{len(script['scenes'])} ready")
    return out


def build(script, out_dir, music, vertical, audio):
    work = os.path.join(out_dir, "work")
    tag = "v" if vertical else "h"
    n = len(script["scenes"])
    scenes = []
    with anim.Renderer(vertical) as R:
        for i, (sc, (wav, dur, words)) in enumerate(zip(script["scenes"], audio)):
            frames = math.ceil((dur + GAP) * FPS)
            sp = words[-1][1] if words else dur
            screen = dict(sc.get("screen") or {"type": "title", "title": sc.get("headline", "")})
            clip = None
            if screen.get("type") == "stock":
                c = os.path.join(work, f"stock{i}.mp4")
                if os.path.exists(c) or visuals.pexels_video(screen.get("query", "technology office"), c):
                    clip = c
                screen["type"] = "title"
            html = anim.build_html(screen, words, sp, i, n, vertical, clear=bool(clip))
            slide = R.frames(html, frames, work, f"s{i}{tag}", transparent=bool(clip))
            char = (character.build_bubble_frames(wav, frames / FPS, work, i, 420 if vertical else 340)
                    if sc.get("presenter", True) else None)
            scenes.append(dict(frames=frames, wav=wav, words=words, slide=slide, clip=clip, char=char))
            print(f"[{'short' if vertical else 'video'}] scene {i + 1}/{n} ready ({frames / FPS:.1f}s)")
    return render.render(scenes, work, os.path.join(out_dir, "short.mp4" if vertical else "final.mp4"),
                         music, vertical)


def make_thumbnail(script, out_dir):
    work = os.path.join(out_dir, "work"); os.makedirs(work, exist_ok=True)
    face = os.path.join(work, "thumb_char.png")
    character.frame(True, 3, 1, 0).save(face)
    out = os.path.join(out_dir, "thumbnail.png")
    if script.get("thumbnail"):  # before-vs-after style
        return slides.thumbnail_vs(script["thumbnail"], face, out)
    text = script.get("thumbnail_text") or " ".join(script["title"].split()[:4])
    return slides.thumbnail(text, face, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--from-script")
    ap.add_argument("--format", default="both", choices=["both", "landscape", "vertical"])
    ap.add_argument("--music", default="music.mp3")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--upload-only", action="store_true")
    ap.add_argument("--privacy", default="private")
    ap.add_argument("--publish-at")
    ap.add_argument("--review", action="store_true")
    a = ap.parse_args()

    if a.from_script:
        script = json.load(open(a.from_script))
        out_dir = os.path.splitext(a.from_script)[0] + "_out"
    else:
        import scriptgen
        script = scriptgen.generate_script(a.topic)
        out_dir = os.path.join("out", slug(script["title"]))
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "script.json")
        json.dump(script, open(path, "w"), indent=2)
        print("Script saved:", path)
        if a.review:
            return
    os.makedirs(os.path.join(out_dir, "work"), exist_ok=True)

    if not a.upload_only:
        print("Thumbnail:", make_thumbnail(script, out_dir))
        audio = prepare_audio(script, os.path.join(out_dir, "work"))
        if a.format in ("both", "landscape"):
            print("Video:", build(script, out_dir, a.music, False, audio))
        if a.format in ("both", "vertical"):
            idx = script.get("short_scenes") or list(range(len(script["scenes"])))
            short = dict(script, scenes=[script["scenes"][i] for i in idx])
            print("Short:", build(short, out_dir, a.music, True, [audio[i] for i in idx]))

    if a.upload or a.upload_only:
        import upload
        thumb = os.path.join(out_dir, "thumbnail.png")
        main_vid = os.path.join(out_dir, "final.mp4")
        if os.path.exists(main_vid):
            print("Uploaded video:", upload.upload(main_vid, script["title"], script["description"],
                                                   script["tags"], a.privacy, a.publish_at, thumbnail=thumb))
        short = os.path.join(out_dir, "short.mp4")
        if os.path.exists(short):
            title = script.get("short_title", script["title"])[:90] + " #Shorts"
            print("Uploaded short:", upload.upload(short, title, script["description"], script["tags"],
                                                   a.privacy, a.publish_at))


if __name__ == "__main__":
    main()
