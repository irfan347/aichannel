"""Relevant on-screen slides per scene, rendered with headless Chromium.
Each screen is rendered as several *states* (text typing in, bullets appearing one by one) so the
slide animates in step with the narration. Supports landscape (1920x1080) and vertical Shorts (1080x1920)."""
import base64, html
from playwright.sync_api import sync_playwright

BASE_CSS = """
*{box-sizing:border-box;margin:0}
body{font-family:'DejaVu Sans',Arial,sans-serif;color:#fff;overflow:hidden;position:relative;
background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 55%,#312e81 100%)}
.glow{position:absolute;right:-200px;top:-200px;width:900px;height:900px;border-radius:50%;
background:radial-gradient(circle,rgba(99,102,241,.35),transparent 70%)}
.area{position:absolute;display:flex;flex-direction:column;justify-content:center}
.tag{font-size:30px;letter-spacing:4px;color:#a5b4fc;text-transform:uppercase;margin-bottom:28px}
h1{font-size:92px;line-height:1.1}
h2{font-size:64px;line-height:1.15;margin-bottom:40px}
.sub{font-size:44px;color:#c7d2fe;margin-top:30px}
.win{background:#111827;border:2px solid #374151;border-radius:28px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.5)}
.bar{background:#1f2937;padding:18px 26px;font-size:26px;color:#9ca3af;display:flex;gap:12px;align-items:center}
.dot{width:16px;height:16px;border-radius:50%}
.chat{padding:34px;display:flex;flex-direction:column;gap:26px;min-height:300px}
.u,.a{font-size:38px;line-height:1.35;padding:26px 32px;border-radius:26px;max-width:92%}
.u{background:#4f46e5;align-self:flex-end;border-bottom-right-radius:6px}
.a{background:#1f2937;align-self:flex-start;border-bottom-left-radius:6px;border:1px solid #374151}
.who{font-size:24px;color:#9ca3af;margin-bottom:8px}
.cur{display:inline-block;width:4px;height:40px;background:#fff;margin-left:4px;vertical-align:middle}
.typing{font-size:44px;letter-spacing:6px;color:#9ca3af}
ul{list-style:none;padding:0}
li{font-size:52px;line-height:1.25;margin:22px 0;display:flex;gap:26px;align-items:flex-start}
li.new{color:#fde68a}
.num{min-width:76px;height:76px;border-radius:20px;background:#6366f1;font-size:44px;font-weight:bold;
display:flex;align-items:center;justify-content:center;color:#fff}
.chk{min-width:76px;height:76px;border-radius:20px;background:#16a34a;font-size:50px;display:flex;align-items:center;justify-content:center;color:#fff}
"""
LAND = "body{width:1920px;height:1080px}.area{left:90px;top:50px;width:1210px;height:830px}"
VERT = ("body{width:1080px;height:1920px}.area{left:70px;top:120px;width:940px;height:1000px}"
        "h1{font-size:96px}h2{font-size:66px}li{font-size:54px}.u,.a{font-size:40px}")


def _e(t):
    return html.escape(str(t))


def _page(inner, vertical):
    return (f"<html><head><style>{BASE_CSS}{VERT if vertical else LAND}</style></head>"
            f"<body><div class='glow'></div><div class='area'>{inner}</div></body></html>")


def _chunks(text, n):
    w = text.split()
    if len(w) <= n:
        return [" ".join(w[:i]) for i in range(1, len(w) + 1)]
    return [" ".join(w[: round(len(w) * k / n)]) for k in range(1, n + 1)]


def states_html(sc: dict, vertical=False) -> list:
    """returns list of HTML pages; shown one after another across the scene"""
    t = sc.get("type", "title")
    tag = f"<div class='tag'>{_e(sc['tag'])}</div>" if sc.get("tag") else ""
    P = lambda inner: _page(inner, vertical)
    if t == "chat":
        head = f"<h2>{_e(sc['title'])}</h2>" if sc.get("title") else ""
        win = lambda body: (f"{tag}{head}<div class='win'><div class='bar'><span class='dot' style='background:#ef4444'></span>"
                            f"<span class='dot' style='background:#f59e0b'></span><span class='dot' style='background:#22c55e'></span>"
                            f"&nbsp; AI Assistant</div><div class='chat'>{body}</div></div>")
        out = []
        for part in _chunks(sc["user"], 4):  # user prompt types in
            out.append(P(win(f"<div class='u'><div class='who'>You</div>{_e(part)}<span class='cur'></span></div>")))
        user = f"<div class='u'><div class='who'>You</div>{_e(sc['user'])}</div>"
        if sc.get("ai"):
            out.append(P(win(user + "<div class='a'><div class='who'>AI</div><span class='typing'>&#9679; &#9679; &#9679;</span></div>")))
            for part in _chunks(sc["ai"], 3):
                out.append(P(win(user + f"<div class='a'><div class='who'>AI</div>{_e(part)}</div>")))
        return out
    if t in ("bullets", "steps", "checklist"):
        out = [P(f"{tag}<h2>{_e(sc['title'])}</h2><ul></ul>")]
        for k in range(1, len(sc["items"]) + 1):
            items = ""
            for i, it in enumerate(sc["items"][:k], 1):
                mark = (f"<div class='num'>{i}</div>" if t == "steps" else
                        "<div class='chk'>&#10003;</div>" if t == "checklist" else "<div class='num'>&#8226;</div>")
                items += f"<li class='{'new' if i == k else ''}'>{mark}<div>{_e(it)}</div></li>"
            out.append(P(f"{tag}<h2>{_e(sc['title'])}</h2><ul>{items}</ul>"))
        return out
    sub = f"<div class='sub'>{_e(sc['subtitle'])}</div>" if sc.get("subtitle") else ""
    out = [P(f"{tag}<h1>{_e(sc['title'])}</h1>")]
    if sub:
        out.append(P(f"{tag}<h1>{_e(sc['title'])}</h1>{sub}"))
    return out


def schedule(n_states, total, kind):
    """seconds each state is shown. Typing/reveals happen in the first ~75% then the final state holds."""
    if n_states == 1:
        return [total]
    active = total * (0.6 if kind == "chat" else 0.75)
    step = active / (n_states - 1)
    return [step] * (n_states - 1) + [total - active]


def render_scene(sc, total, workdir, idx, vertical=False, page=None):
    """renders states to PNGs and writes an ffmpeg concat list; returns its path"""
    htmls = states_html(sc, vertical)
    durs = schedule(len(htmls), total, sc.get("type", "title"))
    paths = []
    for k, h in enumerate(htmls):
        p = f"{workdir}/slide{idx}_{'v' if vertical else 'h'}{k}.png"
        page.set_content(h)
        page.screenshot(path=p)
        paths.append(p)
    lst = f"{workdir}/slide{idx}_{'v' if vertical else 'h'}.txt"
    import os
    with open(lst, "w") as f:
        for p, d in zip(paths, durs):
            f.write(f"file '{os.path.abspath(p)}'\nduration {d:.3f}\n")
        f.write(f"file '{os.path.abspath(paths[-1])}'\n")
    return lst


class Renderer:
    def __init__(self, vertical=False):
        self.vertical = vertical

    def __enter__(self):
        self._p = sync_playwright().start()
        self._b = self._p.chromium.launch()
        size = {"width": 1080, "height": 1920} if self.vertical else {"width": 1920, "height": 1080}
        self.page = self._b.new_page(viewport=size)
        return self

    def scene(self, sc, total, workdir, idx):
        return render_scene(sc, total, workdir, idx, self.vertical, self.page)

    def screenshot_html(self, html_str, out, size):
        self.page.set_viewport_size(size)
        self.page.set_content(html_str)
        self.page.screenshot(path=out)

    def __exit__(self, *a):
        self._b.close(); self._p.stop()


def thumbnail(text, char_png, out, accent="#facc15"):
    """1280x720 click-worthy thumbnail: huge 2-5 word text + presenter."""
    b64 = base64.b64encode(open(char_png, "rb").read()).decode()
    import os
    lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand", "logo.png")
    logo = (f"<img src='data:image/png;base64,{base64.b64encode(open(lp, 'rb').read()).decode()}'>"
            if os.path.exists(lp) else "")
    words = _e(text).split()
    hi = " ".join(words[-2:]); lo = " ".join(words[:-2])
    page = f"""<html><head><style>*{{margin:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;font-family:'DejaVu Sans',Arial,sans-serif;
background:radial-gradient(circle at 75% 40%,#4f46e5 0%,#1e1b4b 55%,#0b0f24 100%);position:relative}}
.t{{position:absolute;left:50px;top:60px;width:700px;overflow:hidden;white-space:normal;word-break:keep-all;font-weight:900;font-size:120px;overflow-wrap:normal;line-height:1.02;color:#fff;
text-transform:uppercase;text-shadow:0 8px 0 #000,0 0 30px rgba(0,0,0,.6)}}
.t span{{color:{accent}}}
.badge{{position:absolute;left:50px;bottom:50px;background:#ef4444;color:#fff;font-weight:900;font-size:44px;
padding:10px 26px 10px 12px;border-radius:14px;transform:rotate(-3deg);display:flex;align-items:center;gap:14px}}
.badge img{{position:static;height:64px}}
body>img{{position:absolute;right:-60px;bottom:-30px;height:660px}}</style></head>
<body><div class='t'>{lo} <span>{hi}</span></div><div class='badge'>{logo}WORK HACKED</div>
<img src='data:image/png;base64,{b64}'>
<script>const t=document.querySelector('.t');let f=120;
while((t.scrollWidth>t.clientWidth||t.scrollHeight>520)&&f>50){{f-=4;t.style.fontSize=f+'px'}}</script></body></html>"""
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 720})
        pg.set_content(page); pg.screenshot(path=out); b.close()
    return out


def thumbnail_vs(spec, char_png, out):
    """'Before vs after' thumbnail (style A): grey manual side, green AI side, presenter, channel logo."""
    import os
    b64 = base64.b64encode(open(char_png, "rb").read()).decode()
    lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand", "logo.png")
    logo = (f"<img class=logo src='data:image/png;base64,{base64.b64encode(open(lp, 'rb').read()).decode()}'>"
            if os.path.exists(lp) else "")
    e = lambda k: _e(spec[k])
    page = f"""<html><head><style>*{{margin:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;font-family:'DejaVu Sans',sans-serif;position:relative}}
.s{{text-shadow:6px 6px 0 #000,-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000}}
.l{{position:absolute;left:0;top:0;width:640px;height:720px;background:#3f3f46}}
.r{{position:absolute;left:640px;top:0;width:640px;height:720px;background:#16a34a}}
.lab{{position:absolute;left:60px;top:40px;font-weight:900;font-size:62px;color:#fff}}
.big{{position:absolute;left:60px;top:140px;white-space:nowrap;font-weight:900;font-size:140px;line-height:1;color:#fff}}
.x{{position:absolute;left:60px;top:200px;width:520px;height:22px;background:#ef4444;transform:rotate(-12deg)}}
.doc{{position:absolute;left:70px;top:390px;width:400px;height:260px;background:#fff;border-radius:22px;padding:30px}}
.doc div{{height:22px;background:#d4d4d8;border-radius:11px;margin:16px 0}}
.c{{position:absolute;right:-20px;bottom:-50px;height:400px}}
.vs{{position:absolute;left:585px;top:300px;width:110px;height:110px;border-radius:50%;background:#facc15;font-weight:900;
font-size:48px;display:flex;align-items:center;justify-content:center;border:6px solid #000}}
.logo{{position:absolute;left:684px;bottom:40px;height:90px}}</style></head><body>
<div class=l><div class="lab s">{e('left_label')}</div><div class="big s">{e('left')}</div><div class=x></div>
<div class=doc><div style="width:60%"></div><div></div><div></div><div style="width:80%"></div></div></div>
<div class=r><div class="lab s">{e('right_label')}</div><div class="big s" style="color:#facc15">{e('right')}</div></div>
<img class=c src='data:image/png;base64,{b64}'><div class=vs>VS</div>{logo}
<script>for(const b of document.querySelectorAll('.big')){{let f=140;while(b.scrollWidth>540&&f>60){{f-=6;b.style.fontSize=f+'px'}}}}</script>
</body></html>"""
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1280, "height": 720})
        pg.set_content(page); pg.screenshot(path=out); br.close()
    return out
