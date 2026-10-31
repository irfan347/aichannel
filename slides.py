"""Renders a relevant on-screen slide per scene (chat mock-up, bullets, checklist, big title) to a 1920x1080 PNG.
The right ~560px is left free for the animated presenter."""
import html
from playwright.sync_api import sync_playwright

CSS = """
*{box-sizing:border-box;margin:0}
body{width:1920px;height:1080px;font-family:'DejaVu Sans',Arial,sans-serif;color:#fff;overflow:hidden;
background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 55%,#312e81 100%);position:relative}
.glow{position:absolute;right:-200px;top:-200px;width:900px;height:900px;border-radius:50%;
background:radial-gradient(circle,rgba(99,102,241,.35),transparent 70%)}
.area{position:absolute;left:90px;top:50px;width:1210px;height:830px;display:flex;flex-direction:column;justify-content:center}
.tag{font-size:30px;letter-spacing:4px;color:#a5b4fc;text-transform:uppercase;margin-bottom:28px}
h1{font-size:92px;line-height:1.1}
h2{font-size:64px;line-height:1.15;margin-bottom:40px}
.sub{font-size:44px;color:#c7d2fe;margin-top:30px}
.win{background:#111827;border:2px solid #374151;border-radius:28px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.5)}
.bar{background:#1f2937;padding:18px 26px;font-size:26px;color:#9ca3af;display:flex;gap:12px;align-items:center}
.dot{width:16px;height:16px;border-radius:50%}
.chat{padding:34px;display:flex;flex-direction:column;gap:26px}
.u,.a{font-size:38px;line-height:1.35;padding:26px 32px;border-radius:26px;max-width:1000px}
.u{background:#4f46e5;align-self:flex-end;border-bottom-right-radius:6px}
.a{background:#1f2937;align-self:flex-start;border-bottom-left-radius:6px;border:1px solid #374151}
.who{font-size:24px;color:#9ca3af;margin-bottom:8px}
ul{list-style:none;padding:0}
li{font-size:52px;line-height:1.25;margin:22px 0;display:flex;gap:26px;align-items:flex-start}
.num{min-width:76px;height:76px;border-radius:20px;background:#6366f1;font-size:44px;font-weight:bold;
display:flex;align-items:center;justify-content:center}
.chk{min-width:76px;height:76px;border-radius:20px;background:#16a34a;font-size:50px;display:flex;align-items:center;justify-content:center}
.hl{color:#fde68a}
"""


def _page(inner):
    return f"<html><head><style>{CSS}</style></head><body><div class='glow'></div><div class='area'>{inner}</div></body></html>"


def _e(t):
    return html.escape(str(t))


def build_html(sc: dict) -> str:
    t = sc.get("type", "title")
    tag = f"<div class='tag'>{_e(sc['tag'])}</div>" if sc.get("tag") else ""
    if t == "chat":
        chat = f"<div class='u'><div class='who'>You</div>{_e(sc['user'])}</div>"
        if sc.get("ai"):
            chat += f"<div class='a'><div class='who'>AI</div>{_e(sc['ai'])}</div>"
        head = f"<h2>{_e(sc['title'])}</h2>" if sc.get("title") else ""
        return _page(f"{tag}{head}<div class='win'><div class='bar'><span class='dot' style='background:#ef4444'></span>"
                     f"<span class='dot' style='background:#f59e0b'></span><span class='dot' style='background:#22c55e'></span>"
                     f"&nbsp; AI Assistant</div><div class='chat'>{chat}</div></div>")
    if t in ("bullets", "steps", "checklist"):
        items = ""
        for i, it in enumerate(sc["items"], 1):
            mark = f"<div class='num'>{i}</div>" if t == "steps" else ("<div class='chk'>&#10003;</div>" if t == "checklist" else "<div class='num'>&#8226;</div>")
            items += f"<li>{mark}<div>{_e(it)}</div></li>"
        return _page(f"{tag}<h2>{_e(sc['title'])}</h2><ul>{items}</ul>")
    # title
    sub = f"<div class='sub'>{_e(sc['subtitle'])}</div>" if sc.get("subtitle") else ""
    return _page(f"{tag}<h1>{_e(sc['title'])}</h1>{sub}")


def render_slides(screens: list, out_paths: list):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        for sc, out in zip(screens, out_paths):
            pg.set_content(build_html(sc))
            pg.screenshot(path=out)
        b.close()
