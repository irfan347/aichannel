"""A phone mock-up showing the Rabta app as it really looks (near-black canvas, amber accent, white active chip,
tabs Chats / Status / Spaces / Nearby / Calls), animated with the same data-t timeline as the slides.
Screens: chats, status, chat, nearby, drop, locked, call. UI labels are English like the app; text can be Urdu."""
import html

AMBER, SEC, GREEN = "#f5b841", "#9a9994", "#3ddc97"

CSS = """
.ph-split{display:flex;align-items:center;gap:70px;height:100%}
.ph-text{flex:1;display:flex;flex-direction:column;justify-content:center;min-width:0}
.ph-scale{flex:none;align-self:center}
body.vert.phv .area{top:170px;height:1720px;justify-content:flex-start}
body.vert.phv h2{text-align:center;align-self:center;margin-bottom:40px}body.vert.phv .tag{align-self:center}
.phone{width:390px;height:800px;border-radius:58px;background:#050506;padding:13px;position:relative;
 box-shadow:0 0 0 2px #34373f,0 0 0 9px #111216,0 0 0 11px #4a4d56,0 50px 110px rgba(0,0,0,.7),0 0 90px rgba(245,184,65,.16)}
.scr{width:100%;height:100%;border-radius:46px;overflow:hidden;background:#0e0f12;position:relative;direction:ltr;
 font-family:'Inter','DejaVu Sans',sans-serif;color:#f4f2ee;letter-spacing:0}
.scr *{letter-spacing:0!important;text-transform:none!important;line-height:1.25}
.isl{position:absolute;top:10px;left:50%;width:110px;height:30px;margin-left:-55px;background:#000;border-radius:20px;z-index:5}
.sb{display:flex;justify-content:space-between;padding:14px 28px 0;font-size:15px;font-weight:700;height:44px}
.sb i{font-style:normal;opacity:.9}
.hd{display:flex;align-items:center;justify-content:space-between;padding:6px 18px 10px}
.hd b{font-size:30px;font-weight:800}
.hd b .urt{color:#f5b841;font-size:21px;font-weight:400;margin-left:6px}
.hd .r{display:flex;gap:18px;font-size:20px;color:#f4f2ee}
.srch{margin:2px 14px 10px;height:42px;border-radius:12px;background:#17191e;display:flex;align-items:center;gap:10px;
 padding:0 16px;color:#9a9994;font-size:15px}
.chips{display:flex;gap:7px;padding:0 14px 8px}
.chip{padding:7px 13px;border-radius:999px;border:1.5px solid #3a3d45;font-size:14px;font-weight:600;color:#f4f2ee}
.chip.on{background:#f4f2ee;color:#0e0f12;border-color:#f4f2ee}
.onl{font-size:12px;color:#9a9994;padding:0 18px 6px;display:flex;align-items:center;gap:6px}
.onl:before{content:'';width:8px;height:8px;border-radius:50%;background:#3ddc97}
.sec{font-size:13px;color:#9a9994;font-weight:600;padding:10px 18px 4px}
.row{display:flex;align-items:center;gap:13px;padding:8px 16px}
.row .mid{flex:1;min-width:0}
.row .nm{font-size:16px;font-weight:700}
.row .ms{font-size:14px;color:#9a9994;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:3px}
.row .ms.ty{color:#3ddc97}
.row .ms b{color:#51aad0;font-weight:400}
.row .tm{font-size:12px;color:#9a9994;text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:7px;min-width:52px}
.row .tm.new{color:#f5b841}
.av{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:17px;
 color:#f4f2ee;flex:none}
.ring{padding:3px;border-radius:50%;border:2.5px solid #f5b841}
.ring.seen{border-color:#3a3d45}
.badge{background:#f5b841;color:#0e0f12;font-size:12px;font-weight:800;border-radius:999px;min-width:22px;height:22px;
 display:flex;align-items:center;justify-content:center;padding:0 6px}
.fab{position:absolute;right:16px;bottom:92px;width:58px;height:58px;border-radius:18px;background:#f5b841;color:#0e0f12;
 font-size:24px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(0,0,0,.5)}
.nav{position:absolute;left:0;right:0;bottom:0;height:76px;background:#0e0f12;border-top:1px solid #23252b;display:flex;
 justify-content:space-around;align-items:center;padding-bottom:8px}
.nav span{display:flex;flex-direction:column;align-items:center;gap:5px;font-size:12px;color:#9a9994;font-weight:500;position:relative;width:64px}
.nav span i{font-style:normal;font-size:20px;height:24px;display:flex;align-items:center;justify-content:center}
.nav span.on{color:#f5b841}
.nav span.on:before{content:'';position:absolute;top:-13px;width:30px;height:3px;border-radius:2px;background:#f5b841}
.nav .nb{position:absolute;top:-6px;left:36px;background:#f5b841;color:#0e0f12;font-size:10px;font-weight:800;border-radius:999px;
 min-width:17px;height:17px;display:flex;align-items:center;justify-content:center}
.nav .nd{position:absolute;top:-2px;left:38px;width:7px;height:7px;border-radius:50%;background:#f5b841}
.urt{font-family:'UrduNastaliq',sans-serif;direction:rtl;line-height:1.9!important}
.ch-hd{display:flex;align-items:center;gap:12px;padding:4px 14px 12px;border-bottom:1px solid #23252b}
.ch-hd .nm{font-size:17px;font-weight:700}.ch-hd .st{font-size:13px;color:#3ddc97;margin-top:2px}
.note{margin:14px auto 6px;width:max-content;max-width:88%;background:#17191e;color:#9a9994;font-size:13px;
 font-weight:500;padding:7px 14px;border-radius:12px}
.note b{color:#f5b841;font-weight:600}
.msgs{display:flex;flex-direction:column;gap:9px;padding:8px 12px}
.bb{max-width:80%;padding:3px 13px 6px;border-radius:18px;font-size:19px}
.bb.out{align-self:flex-end;background:#3a2f17;border:1px solid rgba(245,184,65,.35);border-bottom-right-radius:5px}
.bb.in{align-self:flex-start;background:#17191e;border-bottom-left-radius:5px}
.bb .mt{font-family:'Inter','DejaVu Sans',sans-serif;direction:ltr;font-size:11px;color:#9a9994;text-align:right;line-height:1!important}
.bb .mt b{color:#51aad0;font-weight:400}
.inp{position:absolute;left:10px;right:10px;bottom:16px;height:50px;border-radius:25px;background:#17191e;display:flex;
 align-items:center;padding:0 6px 0 18px;color:#9a9994;font-size:15px;justify-content:space-between}
.inp i{font-style:normal;width:40px;height:40px;border-radius:50%;background:#f5b841;color:#0e0f12;display:flex;
 align-items:center;justify-content:center;font-size:17px}
.tog{display:flex;justify-content:space-between;align-items:center;margin:4px 14px 6px;padding:12px 16px;border-radius:16px;
 background:#17191e;font-size:16px;font-weight:600}
.sw{width:48px;height:28px;border-radius:14px;background:#f5b841;position:relative}
.sw:after{content:'';position:absolute;right:3px;top:3px;width:22px;height:22px;border-radius:50%;background:#0e0f12}
.orbit{position:relative;width:330px;height:330px;margin:8px auto}
.orb{position:absolute;border-radius:50%;border:1.5px solid rgba(245,184,65,.22)}
.me{position:absolute;left:50%;top:50%;width:68px;height:68px;margin:-34px;border-radius:50%;background:#f5b841;color:#0e0f12;
 display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;box-shadow:0 0 40px rgba(245,184,65,.5)}
.pn{position:absolute;display:flex;flex-direction:column;align-items:center;gap:4px;font-size:12px;font-weight:700;width:84px;margin-left:-42px}
.pn .av{width:46px;height:46px;font-size:16px}
.pn small{font-size:10px;font-weight:600}
.tools{display:grid;grid-template-columns:1fr 1fr;gap:9px;padding:6px 14px}
.tool{background:#17191e;border-radius:14px;padding:12px;font-size:14px;font-weight:600;display:flex;gap:10px;align-items:center}
.tool i{font-style:normal;width:32px;height:32px;border-radius:10px;background:#23252b;color:#f5b841;display:flex;align-items:center;justify-content:center}
.card{margin:9px 14px;background:#17191e;border-radius:18px;padding:16px}
.fi{display:flex;gap:14px;align-items:center}
.fi .ic2{width:52px;height:52px;border-radius:14px;background:rgba(245,184,65,.14);color:#f5b841;font-size:24px;display:flex;
 align-items:center;justify-content:center;flex:none}
.fi b{font-size:16px}.fi div div{font-size:13px;color:#9a9994;margin-top:4px}
.pb{height:10px;border-radius:5px;background:#23252b;margin:16px 0 9px;overflow:hidden}
.pb div{height:100%;width:0;border-radius:5px;background:#f5b841}
.pr{display:flex;justify-content:space-between;font-size:13px;color:#9a9994}
.ok{margin-top:13px;background:rgba(61,220,151,.12);color:#3ddc97;font-weight:700;font-size:15px;padding:10px 14px;border-radius:12px}
.ntf{position:absolute;left:10px;right:10px;top:50px;background:rgba(30,32,38,.98);border-radius:22px;padding:13px 15px;
 display:flex;gap:12px;align-items:center;box-shadow:0 12px 40px rgba(0,0,0,.6);border:1px solid #34373f;z-index:6}
.ntf .ap{width:40px;height:40px;border-radius:12px;background:#f5b841;display:flex;align-items:center;justify-content:center;
 color:#0e0f12;font-weight:900;font-size:21px}
.ntf b{font-size:15px}.ntf div div{font-size:13px;color:#9a9994;margin-top:3px}
.call{position:absolute;inset:0;background:radial-gradient(circle at 50% 35%,#3a2f17,#0e0f12 70%)}
.call .big{width:150px;height:150px;font-size:54px;margin:110px auto 20px;box-shadow:0 0 0 10px rgba(245,184,65,.12),0 0 0 22px rgba(245,184,65,.06)}
.call .cn{text-align:center;font-size:28px;font-weight:800}.call .cs{text-align:center;color:#3ddc97;font-size:15px;margin-top:8px}
.pip{position:absolute;right:18px;top:64px;width:96px;height:140px;border-radius:18px;background:linear-gradient(160deg,#3b5b7a,#17191e);
 border:2px solid #34373f;display:flex;align-items:flex-end;justify-content:center;padding-bottom:8px;font-size:11px;color:#c9c7c2}
.cbtn{position:absolute;bottom:50px;left:0;right:0;display:flex;justify-content:center;gap:16px}
.cbtn i{font-style:normal;width:58px;height:58px;border-radius:50%;background:#23252b;display:flex;align-items:center;justify-content:center;font-size:22px}
.cbtn i.end{background:#e5484d;color:#fff}
.foot{font-size:12px;color:#9a9994;padding:14px 18px}
"""

AV = {"AK": "#7a3e55", "GW": "#3e6b4a", "BA": "#3b5b7a", "HR": "#8a5a3c", "SM": "#6b4e8c", "OT": "#2f6670",
      "ZA": "#5a6b2f", "UT": "#4a4f8c", "IR": "#2f6670"}


def _e(s):
    return html.escape(str(s))


def _ini(name):
    w = str(name).split()
    return (w[0][:2] if len(w) == 1 else w[0][0] + w[1][0]).upper()


def _av(name, cls="av"):
    i = _ini(name)
    return f"<div class='{cls}' style='background:{AV.get(i, '#3b5b7a')}'>{_e(i)}</div>"


def _txt(text):
    """Urdu text in Nastaliq, everything else plain"""
    if any("؀" <= c <= "ۿ" for c in str(text)):
        return f"<span class=urt>{_e(text)}</span>"
    return _e(text)


def _status():
    return "<div class=isl></div><div class=sb><span>9:41</span><span><i>&#9679;&#9679;&#9679;</i> <i>&#9650;</i> <i>&#9646;</i></span></div>"


def _nav(on):
    items = [("Chats", "&#9993;", "<b class=nb>8</b>"), ("Status", "&#9678;", "<b class=nd></b>"),
             ("Spaces", "&#9737;&#9737;", ""), ("Nearby", "&#10687;", ""), ("Calls", "&#9742;", "")]
    return "<div class=nav>" + "".join(
        f"<span class='{'on' if n == on else ''}'>{extra}<i>{ic}</i>{n}</span>" for n, ic, extra in items) + "</div>"


def _times(sp, k, start=0.6, end_frac=0.75):
    end = max(sp * end_frac, start + 0.4 * k)
    return [start + (end - start) * i / max(k - 1, 1) for i in range(k)]


def screen(app, sp, spec=None):
    """inner HTML of the phone screen for one Rabta screen; sp = when the narration ends"""
    spec = spec or {}
    if app == "chats":
        chats = spec.get("chats") or [
            ["Ayesha Khan", "Kal subah 10 baje theek hai?", "9:41", 2, ""],
            ["Ghar Wale", "Ammi: Khana tayyar hai, jaldi aao", "9:12", 5, ""],
            ["Bilal Ahmed", "typing...", "8:55", 0, "ty"],
            ["Hamza Raza", "<b>&#10003;&#10003;</b> &#127897; Voice message · 0:42", "Yesterday", 0, "raw"],
            ["Sana Malik", "<b>&#10003;&#10003;</b> &#128247; Photo", "Yesterday", 0, "raw"],
            ["Office Team", "Usman: Report bhej di hai", "Tue", 1, ""],
            ["Zainab Ali", "&#10003; &#10687; Sent over Nearby, no internet", "Mon", 0, "raw"]]
        ts = _times(sp, len(chats), 0.9, 0.6)
        rows = ""
        for (nm, ms, tm, n, kind), t in zip(chats, ts):
            msg = ms if kind == "raw" else _txt(ms)
            badge = f"<div class=badge>{n}</div>" if n else ""
            rows += (f"<div class=row data-t={t:.2f} data-a=left>{_av(nm)}<div class=mid><div class=nm>{_e(nm)}</div>"
                     f"<div class='ms {'ty' if kind == 'ty' else ''}'>{msg}</div></div>"
                     f"<div class='tm {'new' if n else ''}'>{_e(tm)}{badge}</div></div>")
        return (_status() + "<div class=hd><b>Rabta<span class=urt>رابطہ</span></b><div class=r><span>&#9673;</span><span>&#8942;</span></div></div>"
                "<div class=srch data-t=0.2>&#9906; Search</div>"
                "<div class=chips data-t=0.4><span class='chip on'>All</span><span class=chip>Unread 3</span>"
                "<span class=chip>Groups</span><span class=chip>Nearby</span></div>"
                "<div class=onl data-t=0.5>Online · 3 phones nearby</div>" + rows
                + "<div class=fab data-t=1.2 data-a=pop>&#10010;</div>" + _nav("Chats"))
    if app == "status":
        recent = [["Ayesha Khan", "12 minutes ago"], ["Bilal Ahmed", "Today, 8:10 am"], ["Sana Malik", "Today, 7:45 am"]]
        seen = [["Hamza Raza", "Yesterday, 10:02 pm"], ["Usman Tariq", "Yesterday, 6:30 pm"]]
        ts = _times(sp, 5, 0.9, 0.6)

        def row(nm, tm, t, cls):
            return (f"<div class=row data-t={t:.2f} data-a=left><div class='{cls}'>{_av(nm)}</div>"
                    f"<div class=mid><div class=nm>{_e(nm)}</div><div class=ms>{_e(tm)}</div></div></div>")
        return (_status() + "<div class=hd><b>Status</b><div class=r><span>&#9673;</span><span>&#8942;</span></div></div>"
                f"<div class=row data-t=0.3>{_av('IR')}<div class=mid><div class=nm>My status</div>"
                "<div class=ms>Add a photo, video or text · 24 hours</div></div></div><div class=sec>Recent</div>"
                + "".join(row(n, tm, t, "ring") for (n, tm), t in zip(recent, ts[:3]))
                + "<div class=sec>Viewed</div>" + "".join(row(n, tm, t, "ring seen") for (n, tm), t in zip(seen, ts[3:]))
                + "<div class=foot>&#128274; Only the people you choose see your status.</div>"
                + "<div class=fab data-t=1.2 data-a=pop>&#9673;</div>" + _nav("Status"))
    if app == "chat":
        name = spec.get("name", "Ghar Wale")
        msgs = spec.get("messages") or [["out", "امی، نیٹ بند ہے لیکن میں خیریت سے ہوں"], ["in", "شکر الحمدللہ بیٹا!"],
                                        ["out", "دس منٹ میں گھر پہنچ رہا ہوں"], ["in", "ٹھیک ہے، احتیاط سے آنا"]]
        ts = _times(sp, len(msgs), 1.0, 0.8)
        body = ""
        for k, ((side, txt), t) in enumerate(zip(msgs, ts)):
            ticks = " <b>&#10003;&#10003;</b>" if side == "out" else ""
            body += (f"<div class='bb {side}' data-t={t:.2f} data-a=pop {'data-sfx=ding ' if side == 'in' else ''}>"
                     f"{_txt(txt)}<div class=mt>9:4{k + 1}{ticks}</div></div>")
        return (_status() + f"<div class=ch-hd><span>&#8249;</span>{_av(name)}<div><div class=nm>{_e(name)}</div>"
                "<div class=st>&#10687; Nearby · no internet</div></div></div>"
                "<div class=note data-t=0.5>Sent over <b>Nearby</b> · Bluetooth / Wi-Fi</div>"
                f"<div class=msgs>{body}</div><div class=inp>Message<i>&#10148;</i></div>")
    if app == "nearby":
        nodes = [("Bilal Ahmed", "Connected", GREEN, 50, 6), ("Sana Malik", "Waiting", AMBER, 86, 58),
                 ("Usman Tariq", "Discovered", SEC, 14, 64)]
        ts = _times(sp, len(nodes), 1.0, 0.6)
        pn = "".join(f"<div class=pn style='left:{x}%;top:{y}%' data-t={t:.2f} data-a=pop>{_av(nm)}{_e(nm.split()[0])}"
                     f"<small style='color:{col}'>&#9679; {st}</small></div>" for (nm, st, col, x, y), t in zip(nodes, ts))
        rings = "".join(f"<div class=orb style='inset:{p}%'></div>" for p in (0, 16, 32))
        tools = "".join(f"<div class=tool><i>{i}</i>{n}</div>" for i, n in
                        [("&#8659;", "Rabta Drop"), ("&#9641;", "Instant QR"), ("&#9678;", "Network Vision"), ("&#9900;", "NFC pair")])
        return (_status() + "<div class=hd><b>Nearby</b></div>"
                "<div class=tog data-t=0.3>Discoverable<div class=sw></div></div>"
                f"<div class=orbit>{rings}<div class=me>You</div>{pn}</div><div class=tools data-t={sp * 0.7:.2f}>{tools}</div>"
                + _nav("Nearby"))
    if app == "drop":
        f0, f1 = 1.0, max(sp * 0.8, 2.0)
        return (_status() + "<div class=hd><b>Rabta Drop</b><div class=r><span>&#8942;</span></div></div>"
                "<div class=note data-t=0.3>&#128274; Encrypted · <b>no internet needed</b></div>"
                "<div class=card data-t=0.5 data-a=pop><div class=fi><div class=ic2>&#9654;</div><div><b>Family_Wedding.mp4</b>"
                "<div>2.4 GB · to Bilal Ahmed</div></div></div>"
                f"<div class=pb><div data-w0={f0:.2f} data-w1={f1:.2f}></div></div>"
                f"<div class=pr><span><span data-pct0={f0:.2f} data-pct1={f1:.2f}>0</span>%</span><span>18.6 MB/s</span></div>"
                f"<div class=ok data-t={f1 + 0.1:.2f} data-a=pop data-sfx=ding>&#10003; Delivered · verified</div></div>"
                "<div class=card data-t=0.8><div class=fi><div class=ic2>&#9636;</div>"
                "<div><b>Report.pdf</b><div>3.1 MB · Delivered &#10003;</div></div></div></div>" + _nav("Nearby"))
    if app == "locked":
        ts = _times(sp, 3, 0.8, 0.75)
        return (_status() + "<div class=hd><b>Privacy</b></div>"
                f"<div class=card data-t={ts[0]:.2f} data-a=left><div class=fi><div class=ic2>&#128274;</div>"
                "<div><b>Locked chats</b><div>Only you and them can read</div></div></div></div>"
                f"<div class=card data-t={ts[1]:.2f} data-a=left><div class=fi><div class=ic2>&#9729;</div>"
                "<div><b>Backup to Google Drive</b><div>Every night · password protected</div></div></div>"
                f"<div class=pb style='margin-bottom:4px'><div data-w0={ts[1]:.2f} data-w1={ts[1] + 1.2:.2f}></div></div>"
                "<div class=pr><span>Last backup: today 2:00 am</span><span style='color:#3ddc97'>&#10003;</span></div></div>"
                f"<div class=card data-t={ts[2]:.2f} data-a=left><div class=fi><div class=ic2>&#9873;</div>"
                "<div><b>Pahunch gaya</b><div>Family hears when you arrive</div></div></div></div>"
                f"<div class=ntf data-t={ts[2] + 0.5:.2f} data-sfx=ding><div class=ap>R</div><div><b>Bilal · Pahunch gaya &#10003;</b>"
                "<div>Reached home just now</div></div></div>" + _nav("Chats"))
    if app == "call":
        return (_status() + f"<div class=call>{_av('Ayesha Khan', 'av big')}<div class=cn>Ayesha Khan</div>"
                "<div class=cs>Video call · 02:14 · HD</div><div class=pip>You</div>"
                "<div class=cbtn data-t=0.6><i>&#127908;</i><i>&#127909;</i><i>&#9641;</i><i class=end>&#9990;</i></div></div>")
    raise ValueError(f"unknown phone app screen: {app}")


def phone(app, sp, spec=None, scale=1.0):
    return (f"<div class=ph-scale style='zoom:{scale}'><div class=phone data-t=0.15 data-a=pop>"
            f"<div class=scr>{screen(app, sp, spec)}</div></div></div>")
