"""Usage:
  python main.py "How AI agents work"                 # script + voice + video
  python main.py "How AI agents work" --upload        # ...and upload (private by default)
  python main.py "Topic" --upload --privacy public --publish-at 2026-11-02T12:00:00Z
  python main.py --from-script out/script.json        # re-render an edited script
"""
import argparse, json, os, re
import scriptgen, voice, visuals, render, upload, character, slides


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--from-script")
    ap.add_argument("--scenes", type=int, default=8)
    ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--music", default="music.mp3")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--privacy", default="private")
    ap.add_argument("--publish-at")
    ap.add_argument("--upload-only", action="store_true")
    ap.add_argument("--review", action="store_true", help="stop after script so you can edit it")
    a = ap.parse_args()

    if a.from_script:
        script = json.load(open(a.from_script))
        out_dir = os.path.splitext(a.from_script)[0] + "_out"
        os.makedirs(out_dir, exist_ok=True)
    else:
        script = scriptgen.generate_script(a.topic, a.scenes, a.seconds)
        out_dir = os.path.join("out", slug(script["title"]))
        os.makedirs(out_dir, exist_ok=True)
        json.dump(script, open(os.path.join(out_dir, "script.json"), "w"), indent=2)
        print("Script saved:", os.path.join(out_dir, "script.json"))
        if a.review:
            print("Edit it, then run: python main.py --from-script", os.path.join(out_dir, "script.json"))
            return

    if a.upload_only:
        print("Uploaded:", upload.upload(os.path.join(out_dir, "final.mp4"), script["title"],
              script["description"], script["tags"], a.privacy, a.publish_at))
        return

    work = os.path.join(out_dir, "work")
    os.makedirs(work, exist_ok=True)
    scenes = []
    for i, sc in enumerate(script["scenes"]):
        audio = os.path.join(work, f"voice{i}.mp3")
        dur = voice.synth(sc["narration"], audio)
        entry = dict(audio=audio, duration=dur, text=sc["narration"])
        if sc.get("screen"):  # relevant slide + animated presenter
            png = os.path.join(work, f"slide{i}.png")
            slides.render_slides([sc["screen"]], [png])
            entry.update(visual_path=png, is_video=False, static=True,
                         char_list=character.build_scene_frames(audio, dur + 0.25, work, i))
        else:
            vpath, is_vid = visuals.get_visual(sc["visual"], work, i, sc.get("headline", ""))
            entry.update(visual_path=vpath, is_video=is_vid)
        scenes.append(entry)
        print(f"scene {i + 1}/{len(script['scenes'])} ready ({dur:.1f}s)")

    video = render.render(scenes, work, os.path.join(out_dir, "final.mp4"), a.music)
    print("Video:", video)

    if a.upload:
        print("Uploaded:", upload.upload(video, script["title"], script["description"],
                                         script["tags"], a.privacy, a.publish_at))


if __name__ == "__main__":
    main()
