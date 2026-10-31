"""Step 3: get a background clip/image per scene. Pexels if key set, else gradient card."""
import os, random, requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
PALETTES = [((20, 30, 70), (90, 40, 140)), ((10, 60, 80), (20, 20, 60)),
            ((60, 20, 60), (20, 40, 90)), ((15, 15, 35), (40, 90, 120))]


def pexels_video(query: str, out: str) -> bool:
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return False
    try:
        r = requests.get("https://api.pexels.com/videos/search",
                         headers={"Authorization": key},
                         params={"query": query, "per_page": 8, "orientation": "landscape"}, timeout=20)
        vids = r.json().get("videos", [])
        if not vids:
            return False
        v = random.choice(vids)
        files = sorted([f for f in v["video_files"] if f["file_type"] == "video/mp4"],
                       key=lambda f: abs((f.get("width") or 0) - 1920))
        data = requests.get(files[0]["link"], timeout=60).content
        open(out, "wb").write(data)
        return True
    except Exception as e:
        print("pexels failed:", e)
        return False


def gradient_card(text: str, out: str, idx: int):
    text = text or ""
    a, b = PALETTES[idx % len(PALETTES)]
    img = Image.new("RGB", (W, H))
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        px.line([(0, y), (W, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 110)
    except OSError:
        font = ImageFont.load_default()
    import textwrap
    for n, line in enumerate(textwrap.wrap(text, 22)[:3]):
        px.text((W // 2, H // 2 - 200 + n * 130), line, font=font, fill=(255, 255, 255), anchor="mm")
    img.save(out)


def get_visual(query: str, workdir: str, idx: int, headline: str = "") -> tuple[str, bool]:
    """returns (path, is_video)"""
    v = os.path.join(workdir, f"bg{idx}.mp4")
    if pexels_video(query, v):
        return v, True
    p = os.path.join(workdir, f"bg{idx}.png")
    gradient_card(headline, p, idx)
    return p, False
