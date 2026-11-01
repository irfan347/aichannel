"""Animated, professional slides synced to the narration.
Each scene is an HTML page whose elements appear at the moment the voice talks about them
(fade + slide-in, typing prompts, streaming AI replies). Frames are rendered deterministically with
headless Chromium (only changed frames are captured) so timing is exact."""
import base64, html, os, re
from playwright.sync_api import sync_playwright

FPS = 30
STOP = set("the a an and or to of for in on with your you is are it this that what from them they their just "
           "then any your how use using make makes more most only every never".split())

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter','DejaVu Sans',Arial,sans-serif;color:#f8fafc;overflow:hidden;position:relative;background:#0b1020}
.bg{position:absolute;inset:0;background:
 radial-gradient(1200px 700px at 88% -10%,rgba(99,102,241,.38),transparent 60%),
 radial-gradient(900px 600px at -10% 112%,rgba(250,204,21,.12),transparent 60%),
 radial-gradient(rgba(255,255,255,.06) 1.6px,transparent 1.6px) 0 0/38px 38px}
body.clear{background:transparent}
body.clear .bg{background:linear-gradient(180deg,rgba(0,0,0,.15) 0%,rgba(0,0,0,.25) 40%,rgba(0,0,0,.7) 100%)}
.brand{position:absolute;top:42px;right:56px;display:flex;align-items:center;gap:14px;font-weight:800;font-size:24px;
 letter-spacing:3px;color:#e2e8f0}
.brand img{height:48px}
.prog{position:absolute;top:60px;left:110px;display:flex;gap:8px}
.prog i{display:block;width:44px;height:7px;border-radius:4px;background:rgba(255,255,255,.16)}
.prog i.on{background:#facc15}
.area{position:absolute;display:flex;flex-direction:column;justify-content:center}
.tag{align-self:flex-start;font-size:24px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#0b1020;
 background:#facc15;padding:10px 20px;border-radius:999px;margin-bottom:28px}
h1{font-size:98px;line-height:1.04;font-weight:800;letter-spacing:-2px}
h2{font-size:64px;line-height:1.1;font-weight:800;letter-spacing:-1px;margin-bottom:36px}
.sub{font-size:44px;color:#a5b4fc;margin-top:28px;font-weight:500}
.hl{color:#facc15}
.win{background:#0f172a;border:1.5px solid rgba(255,255,255,.12);border-radius:26px;overflow:hidden;
 box-shadow:0 40px 90px rgba(0,0,0,.55)}
.bar{background:#111a2e;padding:18px 24px;font-size:22px;color:#94a3b8;display:flex;gap:11px;align-items:center;
 border-bottom:1px solid rgba(255,255,255,.08)}
.dot{width:14px;height:14px;border-radius:50%}
.chat{padding:30px;display:flex;flex-direction:column;gap:22px}
.u,.a{font-size:35px;line-height:1.42;padding:22px 28px;border-radius:24px;max-width:94%}
.u{background:#4f46e5;align-self:flex-end;border-bottom-right-radius:6px}
.a{background:#1e293b;align-self:flex-start;border-bottom-left-radius:6px;border:1px solid rgba(255,255,255,.08)}
.who{font-size:20px;font-weight:800;color:rgba(255,255,255,.6);margin-bottom:6px;letter-spacing:2px}
.tw{position:relative}
.ghost{visibility:hidden}
.txt{position:absolute;left:0;top:0;right:0}
.caret{display:inline-block;width:3px;height:36px;background:#fff;margin-left:3px;vertical-align:-6px}
.dots{position:absolute;left:0;top:4px}
.dots span{display:inline-block;width:14px;height:14px;border-radius:50%;background:#94a3b8;margin-right:9px}
.list{display:flex;flex-direction:column;gap:20px}
.item{display:flex;align-items:center;gap:24px;font-size:46px;font-weight:600;padding:20px 26px;border-radius:22px;
 background:rgba(255,255,255,.04);border:1.5px solid rgba(255,255,255,.08)}
.item.act{background:rgba(250,204,21,.10);border-color:rgba(250,204,21,.6)}
.ic{min-width:66px;height:66px;border-radius:18px;background:#4f46e5;font-size:36px;font-weight:800;display:flex;
 align-items:center;justify-content:center}
.ic.ok{background:#16a34a}
.sheet{background:#fff;color:#111827;border-radius:22px;overflow:hidden;box-shadow:0 40px 90px rgba(0,0,0,.55);font-size:32px}
.fx{display:flex;align-items:center;gap:18px;padding:16px 22px;background:#f1f5f9;border-bottom:2px solid #cbd5e1;
 font-family:'DejaVu Sans Mono',monospace;font-size:31px;min-height:76px}
.fx b{font-family:'Inter',sans-serif;color:#16a34a;font-size:30px;font-style:italic}
.fx .tw{flex:1}
.fx .caret{background:#111827;height:32px}
table{border-collapse:collapse;width:100%}
td,th{border:1.5px solid #e2e8f0;padding:14px 20px;text-align:left;white-space:nowrap;color:#111827;font-size:34px}
th{background:#f8fafc;color:#64748b;font-weight:700;font-size:28px}
td.res{background:#dcfce7;font-weight:800;color:#166534}
td.target{outline:4px solid #16a34a;outline-offset:-4px}
"""
LAND = "body{width:1920px;height:1080px}.area{left:110px;top:110px;width:1290px;height:800px}"
VERT = ("body{width:1080px;height:1920px}.area{left:70px;top:190px;width:940px;height:1060px}"
        ".prog{left:70px;top:112px}.brand{top:96px;right:60px}h1{font-size:96px}h2{font-size:66px}"
        ".item{font-size:46px}.u,.a{font-size:38px}")

JS = """
function ease(p){return 1-Math.pow(1-p,3)}
function clamp(x){return Math.max(0,Math.min(1,x))}
function render(t){
 const sig=[];
 document.querySelectorAll('[data-t]').forEach(el=>{
  let p=ease(clamp((t-(+el.dataset.t))/0.4)); const a=el.dataset.a||'up';
  el.style.opacity=p;
  el.style.transform=a==='pop'?`scale(${0.92+0.08*p})`:a==='left'?`translateX(${(1-p)*-46}px)`:`translateY(${(1-p)*34}px)`;
  sig.push(Math.round(p*60));
 });
 document.querySelectorAll('[data-act0]').forEach(el=>{
  const on=t>=+el.dataset.act0&&t<+el.dataset.act1; el.classList.toggle('act',on); sig.push(on?1:0);
 });
 document.querySelectorAll('[data-hide]').forEach(el=>{
  const h=t>=+el.dataset.hide; el.style.display=h?'none':''; sig.push(h?1:0);
  if(!h){el.querySelectorAll('span').forEach((s,i)=>{s.style.opacity=(Math.floor(t*4)%3===i)?1:.35});sig.push(Math.floor(t*4)%3)}
 });
 document.querySelectorAll('[data-type0]').forEach(el=>{
  const a=+el.dataset.type0,b=+el.dataset.type1,full=el.dataset.full;
  const n=Math.round(full.length*clamp((t-a)/Math.max(b-a,.01)));
  const c=el.querySelector('.caret');
  el.querySelector('.tt').textContent=full.slice(0,n);
  let on=false; if(c){on=t>=a-0.3&&t<b+0.5&&(t<b||Math.floor(t*2.5)%2===0); c.style.opacity=on?1:0}
  sig.push(n,on?1:0);
 });
 return sig.join(',');
}
"""

_LOGO = None


def _logo():
    global _LOGO
    if _LOGO is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand", "logo.png")
        _LOGO = base64.b64encode(open(p, "rb").read()).decode() if os.path.exists(p) else ""
    return _LOGO


def _e(t):
    """escape + **word** highlight"""
    return re.sub(r"\*\*(.+?)\*\*", r"<span class=hl>\1</span>", html.escape(str(t)))


def _plain(t):
    return html.escape(re.sub(r"\*\*", "", str(t)), quote=True)


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _kw_time(words, text, after):
    keys = {_norm(w) for w in text.split() if len(_norm(w)) > 3 and _norm(w) not in STOP}
    for s, e, w in words:
        if s >= after and _norm(w) in keys:
            return s
    return None


def _list_times(words, items, sp):
    times, after = [], 0.4
    for k, it in enumerate(items):
        even = sp * (0.15 + 0.6 * k / max(len(items) - 1, 1))
        t = _kw_time(words, it, after)
        if t is None or t > sp - 0.2 or t - after > sp * 0.6:
            t = even
        t = max(t, after)
        times.append(t); after = t + 0.45
    return times


def _typing(cls, who, text, t0, t1, appear, caret=True, dots_until=None):
    dots = (f"<div class=dots data-hide={dots_until:.2f}><span></span><span></span><span></span></div>"
            if dots_until else "")
    c = "<span class=caret></span>" if caret else ""
    return (f"<div class={cls} data-t={appear:.2f}><div class=who>{who}</div>"
            f"<div class=tw data-type0={t0:.2f} data-type1={t1:.2f} data-full=\"{_plain(text)}\">"
            f"<span class=ghost>{_plain(text)}</span><span class=txt><span class=tt></span>{c}</span>{dots}</div></div>")


def build_html(sc, words, sp, idx, n, vertical=False, clear=False):
    """sc: screen spec; words: [[s,e,w]] scene-relative; sp: time speech ends"""
    t = sc.get("type", "title")
    tag = f"<div class=tag data-t=0.05 data-a=left>{_e(sc['tag'])}</div>" if sc.get("tag") else ""
    if t == "chat":
        head = f"<h2 data-t=0.1>{_e(sc['title'])}</h2>" if sc.get("title") else ""
        u, a = sc["user"], sc.get("ai", "")
        u0 = 0.45; u1 = u0 + min(len(u) / 38, max(sp * 0.45, 1.2))
        body = _typing("u", "YOU", u, u0, u1, 0.3)
        if a:
            a0 = u1 + 0.9; a1 = a0 + min(len(a) / 70, max(sp - a0 - 0.2, 1.0))
            body += _typing("a", "AI", a, a0, a1, u1 + 0.2, caret=False, dots_until=a0)
        inner = (f"{tag}{head}<div class=win data-t=0.15 data-a=pop><div class=bar>"
                 "<span class=dot style='background:#ef4444'></span><span class=dot style='background:#f59e0b'></span>"
                 f"<span class=dot style='background:#22c55e'></span>&nbsp; AI Assistant</div><div class=chat>{body}</div></div>")
    elif t in ("bullets", "steps", "checklist"):
        items = sc["items"]; ts = _list_times(words, items, sp)
        rows = ""
        for k, (it, t0) in enumerate(zip(items, ts)):
            t1 = ts[k + 1] if k + 1 < len(ts) else 999
            ic = (f"<div class=ic>{k + 1}</div>" if t == "steps" else
                  "<div class='ic ok'>&#10003;</div>" if t == "checklist" else "<div class=ic>&#8226;</div>")
            rows += f"<div class=item data-t={t0:.2f} data-a=left data-act0={t0:.2f} data-act1={t1:.2f}>{ic}<div>{_e(it)}</div></div>"
        inner = f"{tag}<h2 data-t=0.1>{_e(sc['title'])}</h2><div class=list>{rows}</div>"
    elif t == "formula":
        f = sc["formula"]
        f0 = 0.6; f1 = f0 + min(len(f) / 22, max(sp * 0.5, 1.2))
        r0 = f1 + 0.4
        cols = "".join(f"<th>{_e(c)}</th>" for c in sc["cols"])
        rows = ""
        for ri, row in enumerate(sc["rows"]):
            cells = ""
            for ci, v in enumerate(row):
                if v == "?":
                    cells += (f"<td class='res target'><span style='opacity:0' data-t={r0:.2f} data-a=pop>"
                              f"{_e(sc['result'])}</span></td>")
                else:
                    cells += f"<td>{_e(v)}</td>"
            rows += f"<tr>{cells}</tr>"
        head = f"<h2 data-t=0.1>{_e(sc['title'])}</h2>" if sc.get("title") else ""
        fx = (f"<div class=fx><b>fx</b><div class=tw data-type0={f0:.2f} data-type1={f1:.2f} data-full=\"{_plain(f)}\">"
              f"<span class=ghost>{_plain(f)}</span><span class=txt><span class=tt></span><span class=caret></span></span></div></div>")
        inner = f"{tag}{head}<div class=sheet data-t=0.15 data-a=pop>{fx}<table><tr>{cols}</tr>{rows}</table></div>"
    else:  # title (also used over stock footage)
        sub = ""
        if sc.get("subtitle"):
            st = _kw_time(words, sc["subtitle"], 0.6) or sp * 0.45
            sub = f"<div class=sub data-t={min(st, max(sp - 0.5, 0.8)):.2f}>{_e(sc['subtitle'])}</div>"
        inner = f"{tag}<h1 data-t=0.12>{_e(sc.get('title', ''))}</h1>{sub}"
    prog = "".join(f"<i class={'on' if k <= idx else ''}></i>" for k in range(n))
    logo = f"<img src='data:image/png;base64,{_logo()}'>" if _logo() else ""
    return (f"<html><head><style>{CSS}{VERT if vertical else LAND}</style><script>{JS}</script></head>"
            f"<body class='{'clear' if clear else ''}'><div class=bg></div><div class=prog>{prog}</div>"
            f"<div class=brand>{logo}WORK HACKED</div><div class=area>{inner}</div></body></html>")


class Renderer:
    def __init__(self, vertical=False):
        self.vertical = vertical

    def __enter__(self):
        self._p = sync_playwright().start()
        self._b = self._p.chromium.launch()
        size = {"width": 1080, "height": 1920} if self.vertical else {"width": 1920, "height": 1080}
        self.page = self._b.new_page(viewport=size)
        return self

    def frames(self, html_str, n_frames, workdir, name, transparent=False):
        """render n_frames at FPS; only changed frames are captured. returns ffmpeg concat list path"""
        self.page.set_content(html_str)
        self.page.evaluate("document.fonts.ready")
        ext = "png" if transparent else "jpg"
        runs, prev = [], None
        for f in range(n_frames):
            sig = self.page.evaluate(f"render({f / FPS:.4f})")
            if sig != prev:
                p = os.path.abspath(os.path.join(workdir, f"{name}_{f:05d}.{ext}"))
                if transparent:
                    self.page.screenshot(path=p, omit_background=True)
                else:
                    self.page.screenshot(path=p, type="jpeg", quality=92)
                runs.append([p, 1]); prev = sig
            else:
                runs[-1][1] += 1
        lst = os.path.join(workdir, f"{name}.txt")
        with open(lst, "w") as fh:
            for p, c in runs:
                fh.write(f"file '{p}'\nduration {c / FPS:.5f}\n")
            fh.write(f"file '{runs[-1][0]}'\n")
        return lst

    def __exit__(self, *a):
        self._b.close(); self._p.stop()
