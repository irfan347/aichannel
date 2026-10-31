"""Usage:
  python main.py --from-script scripts/video01.json                  # landscape video + Short + thumbnail
  python main.py --from-script scripts/video01.json --format landscape
  python main.py --from-script scripts/video01.json --upload --privacy public
  python main.py "Topic" --review     # (needs ANTHROPIC_API_KEY) draft a script with Claude, then edit it

Scene "screen" types: title, chat, steps, bullets, checklist, stock (stock footage, needs PEXELS_API_KEY).
"""
import argparse, json, os, re
import voice, visuals, render, character, slides


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def build(script, out_dir, music, vertical):
    work = os.path.join(out_dir, "work")
    os.makedirs(work, exist_ok=True)
    # make all voice files first, before the browser starts
    for i, sc in enumerate(script["scenes"]):
        audio = os.path.join(work, f"voice{i}.mp3")
        if not os.path.exists(audio):
            voice.synth(sc["narration"], audio)
    scenes = []
    with slides.Renderer(vertical) as R:
        for i, sc in enumerate(script["scenes"]):
            audio = os.path.join(work, f"voice{i}.mp3")
            if not os.path.exists(audio):  # voice is shared by landscape + vertical
                voice.synth(sc["narration"], audio)
            dur = voice.duration(audio)
            total = dur + 0.25
            entry = dict(audio=audio, duration=dur, text=sc["narration"])
            screen = sc.get("screen") or {"type": "title", "title": sc.get("headline", "")}
            if screen.get("type") == "stock":
                clip = os.path.join(work, f"stock{i}.mp4")
                if os.path.exists(clip) or visuals.pexels_video(screen.get("query", sc.get("visual", "technology")), clip):
                    entry.update(visual_path=clip, is_video=True)
                else:  # no Pexels key / no result -> title slide instead
                    screen = {"type": "title", "tag": screen.get("tag"), "title": screen.get("title", sc.get("headline", ""))}
            if "visual_path" not in entry:
                entry["slide_list"] = R.scene(screen, total, work, i)
            if sc.get("presenter", True):
                entry["char_list"] = character.build_scene_frames(
                    audio, total, work, i, gesture_at_start=screen.get("type") in ("steps", "bullets", "checklist", "chat"))
            scenes.append(entry)
            print(f"[{'short' if vertical else 'video'}] scene {i + 1}/{len(script['scenes'])} ready ({dur:.1f}s)")
    name = "short.mp4" if vertical else "final.mp4"
    return render.render(scenes, work, os.path.join(out_dir, name), music, vertical)


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
    os.makedirs(out_dir, exist_ok=True)

    if not a.upload_only:
        print("Thumbnail:", make_thumbnail(script, out_dir))
        if a.format in ("both", "landscape"):
            print("Video:", build(script, out_dir, a.music, vertical=False))
        if a.format in ("both", "vertical"):
            print("Short:", build(script, out_dir, a.music, vertical=True))

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
