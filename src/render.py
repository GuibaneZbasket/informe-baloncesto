"""Generación de la web estática: portada de jornada + página de cada partido."""

import json
import os
from html import escape as esc

from .analysis import period_label
from .cronica import write as write_cronica
from .teams import short_name

FOOTER = "Generado automáticamente a partir del play-by-play oficial de la Euroliga."

CSS = r"""
:root{--bg:#f9f9f7;--card:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;
--axis:#c3c2b7;--border:rgba(11,11,11,.10);--home:#2a78d6;--away:#eb6834;--chip:#efeee9;--hl:#f3f2ed}
@media (prefers-color-scheme:dark){:root{--bg:#0d0d0d;--card:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;
--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--home:#3987e5;--away:#d95926;
--chip:#262624;--hl:#222220}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
font-feature-settings:"tnum" 1}
a{color:inherit;text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 48px}
.demo{background:#fab219;color:#0b0b0b;text-align:center;font-size:12px;font-weight:600;padding:6px 12px;letter-spacing:.02em}
header.top{padding:28px 0 12px}
.kicker{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink2);font-weight:600}
h1{font-size:40px;line-height:1.05;margin:6px 0 4px;letter-spacing:-.02em}
h2{font-size:20px;margin:0 0 12px;letter-spacing:-.01em}
h3{font-size:15px;margin:0 0 8px}
.sub{color:var(--ink2);font-size:14px}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.pill{display:inline-block;padding:5px 11px;border-radius:999px;background:var(--chip);font-size:13px;color:var(--ink2);border:1px solid transparent}
.pill.on{background:var(--ink);color:var(--bg)}
section{margin-top:28px}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px}
a.card{display:block;transition:transform .12s,box-shadow .12s}
a.card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.08)}
.meta{display:flex;justify-content:space-between;gap:8px;font-size:12px;color:var(--muted);margin-bottom:8px}
.tags{display:flex;gap:4px;flex-wrap:wrap}
.tag{font-size:11px;padding:1px 7px;border-radius:999px;background:var(--chip);color:var(--ink2);font-weight:600}
.trow{display:flex;align-items:center;gap:10px;padding:3px 0}
.badge{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-size:10px;font-weight:700;
letter-spacing:.02em;flex:none;border:2px solid var(--c);color:var(--ink);background:var(--card)}
.tname{flex:1;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tscore{font-size:24px;font-weight:700;min-width:44px;text-align:right}
.lose .tscore,.lose .tname{color:var(--muted);font-weight:500}
.qs{font-size:11px;color:var(--muted);letter-spacing:.02em;text-align:right;white-space:nowrap}
.spark{margin:8px 0 6px;display:block;width:100%;height:44px}
.one{font-size:13px;color:var(--ink2);margin:4px 0 0}
.mvp{font-size:13px;margin-top:8px;padding-top:8px;border-top:1px solid var(--border);display:flex;justify-content:space-between;gap:8px}
.mvp b{font-weight:600}.muted{color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:13px}
th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600;text-align:right;padding:6px 6px;border-bottom:1px solid var(--axis);white-space:nowrap}
td{padding:6px 6px;text-align:right;border-bottom:1px solid var(--grid);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
tr.tot td{font-weight:700;border-top:1px solid var(--axis)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.sticky td:first-child,.sticky th:first-child{position:sticky;left:0;background:var(--card);z-index:1}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--c);margin-right:6px;vertical-align:1px}
.list{margin:0;padding:0;list-style:none}
.list li{display:flex;gap:10px;align-items:baseline;padding:8px 0;border-bottom:1px solid var(--grid)}
.list li:last-child{border-bottom:0}
.rank{font-weight:700;color:var(--muted);width:18px}
.big{font-size:22px;font-weight:700}
/* partido */
.hero{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:18px;margin-top:16px}
.score{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;text-align:center}
.score .team{display:flex;flex-direction:column;align-items:center;gap:6px;font-weight:600;font-size:14px}
.score .badge{width:52px;height:52px;font-size:14px;border-width:3px}
.score .num{font-size:46px;font-weight:800;letter-spacing:-.03em;line-height:1}
.score .num span.l{color:var(--muted)}
.status{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-top:6px}
.qtable{margin-top:14px}
.chips{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;display:flex;gap:6px;overflow-x:auto;margin:0 -16px;padding-left:16px;padding-right:16px}
.chips a{flex:none}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.tile{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px}
.tile .l{font-size:12px;color:var(--ink2)}.tile .v{font-size:24px;font-weight:700;line-height:1.2}
.tile .d{font-size:12px;color:var(--muted)}
.keys{display:grid;gap:8px}
.key{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 12px;font-size:14px}
.key b{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink2);margin-bottom:2px}
.cronica p{font-size:16px;line-height:1.65;margin:0 0 12px;max-width:68ch}
.cronica h2{font-size:24px}
.mvpcard{display:flex;gap:14px;align-items:center}
.mvpcard .badge{width:56px;height:56px;font-size:13px}
.mirror{display:grid;grid-template-columns:62px 1fr 1fr 62px;align-items:center;gap:0 6px;font-size:13px;margin:3px 0}
.mirror .lab{grid-column:1/5;text-align:center;font-size:12px;color:var(--ink2);margin-top:8px}
.mirror .va{text-align:right;font-weight:600}.mirror .vb{font-weight:600}.mirror small{display:block;font-weight:400;color:var(--muted);font-size:11px;line-height:1.2}
.bar{height:10px;background:var(--grid);border-radius:4px;position:relative;overflow:hidden}
.bar i{position:absolute;top:0;bottom:0;border-radius:4px}
.bar.a i{right:0;background:var(--home)}.bar.b i{left:0;background:var(--away)}
.legend{display:flex;gap:14px;font-size:12px;color:var(--ink2);margin-bottom:8px;flex-wrap:wrap}
.seg{display:flex;gap:2px;height:14px;border-radius:4px;overflow:hidden;margin:6px 0}
.seg i{display:block;height:100%}
.chartbox{position:relative}
.tip{position:absolute;pointer-events:none;background:var(--ink);color:var(--bg);font-size:12px;padding:5px 8px;border-radius:6px;
white-space:nowrap;transform:translate(-50%,-110%);opacity:0;transition:opacity .1s}
.tabs{display:flex;gap:6px;margin-bottom:10px}
.tabs button{font:inherit;font-size:13px;border:1px solid var(--border);background:var(--card);color:var(--ink2);padding:6px 12px;border-radius:999px;cursor:pointer}
.tabs button.on{background:var(--ink);color:var(--bg)}
th.s{cursor:pointer}th.s:hover{color:var(--ink)}
.lu{padding:10px 0;border-bottom:1px solid var(--grid)}.lu:last-child{border:0}
.lu .n{font-size:13px}.lu .m{font-size:12px;color:var(--muted)}
.pm{font-weight:700}
details{background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:8px}
summary{cursor:pointer;padding:10px 14px;font-weight:600}
.pbp td{white-space:normal}.pbp tr.sc td{font-weight:600}
.pbp .clk{color:var(--muted);width:48px}
.glos{font-size:12px;color:var(--ink2);margin-top:8px}
.glos dt{font-weight:700;display:inline}.glos dd{display:inline;margin:0 0 0 4px}
.glos div{margin:2px 0}
.heat td.h{font-weight:600}
footer{margin-top:40px;font-size:12px;color:var(--muted)}
@media (max-width:600px){h1{font-size:32px}.score .num{font-size:38px}.qs{display:none}}
"""

PLAY_ES = {
    "2FGM": "Canasta de 2", "2FGA": "Fallo de 2", "3FGM": "Triple", "3FGA": "Fallo de 3",
    "FTM": "Tiro libre anotado", "FTA": "Tiro libre fallado", "O": "Rebote ofensivo",
    "D": "Rebote defensivo", "AS": "Asistencia", "ST": "Robo", "TO": "Pérdida", "FV": "Tapón",
    "AG": "Tapón recibido", "CM": "Falta personal", "CMU": "Falta antideportiva",
    "CMD": "Falta descalificante", "CMT": "Técnica", "CMTI": "Técnica", "OF": "Falta en ataque",
    "RV": "Falta recibida", "IN": "Entra a pista", "OUT": "Sale de pista", "TOUT": "Tiempo muerto",
    "TOUT_TV": "Tiempo muerto TV", "BP": "Inicio del periodo", "EP": "Fin del periodo",
    "EG": "Final del partido", "JB": "Salto inicial", "CCH": "Challenge del entrenador",
}

TAG_ES = {"prorroga": "Prórroga", "remontada": "Remontada", "paliza": "Paliza",
          "final_apretado": "Final apretado", "de_principio_a_fin": "Siempre por delante"}


def _short(n):
    parts = n.split()
    return f"{parts[0][0]}. {' '.join(parts[1:])}" if len(parts) > 1 else n


def tname(g, s):
    t = g["teams"][s]
    return t.get("short") or short_name(t["code"], t["name"])


def badge(code, side):
    return f'<span class="badge" style="--c:var(--{"home" if side == "A" else "away"})">{esc(code)}</span>'


def pct(x, d=0):
    return "–" if x is None else f"{100 * x:.{d}f}%"


def page(title, body, demo=False, depth=0):
    banner = ('<div class="demo">DEMO · Datos ficticios generados para probar el diseño. '
              'Los equipos son reales, los jugadores y resultados no.</div>') if demo else ""
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style></head>
<body>{banner}<div class="wrap">{body}
<footer>{FOOTER}</footer>
</div></body></html>"""


# ---------------------------------------------------------------- gráficos

def margin_path(timeline, total, w, h, pad_y, ymax):
    def X(t):
        return t / total * w

    def Y(d):
        return h / 2 - d / ymax * (h / 2 - pad_y)

    pts = [(X(0), Y(0))]
    prev = 0
    for p in timeline[1:]:
        x = X(p["t"])
        pts.append((x, Y(prev)))
        pts.append((x, Y(p["d"])))
        prev = p["d"]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = line + f" L{X(total):.1f},{Y(0):.1f} L0,{Y(0):.1f} Z"
    return line, area, Y(0)


def sparkline(g, uid):
    w, h = 300, 44
    tl = g["timeline"]
    ymax = max(8, max(abs(p["d"]) for p in tl))
    line, area, y0 = margin_path(tl, g["game_seconds"], w, h, 3, ymax)
    qlines = "".join(
        f'<line x1="{t / g["game_seconds"] * w:.1f}" x2="{t / g["game_seconds"] * w:.1f}" y1="0" y2="{h}" stroke="var(--grid)" stroke-width="1"/>'
        for t in _period_bounds(g)[1:-1])
    return f"""<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">
<defs><clipPath id="u{uid}"><rect x="0" y="0" width="{w}" height="{y0:.1f}"/></clipPath>
<clipPath id="d{uid}"><rect x="0" y="{y0:.1f}" width="{w}" height="{h}"/></clipPath></defs>{qlines}
<line x1="0" x2="{w}" y1="{y0:.1f}" y2="{y0:.1f}" stroke="var(--axis)" stroke-width="1"/>
<path d="{area}" fill="var(--home)" opacity=".22" clip-path="url(#u{uid})"/>
<path d="{area}" fill="var(--away)" opacity=".22" clip-path="url(#d{uid})"/>
<path d="{line}" fill="none" stroke="var(--home)" stroke-width="1.6" clip-path="url(#u{uid})" vector-effect="non-scaling-stroke"/>
<path d="{line}" fill="none" stroke="var(--away)" stroke-width="1.6" clip-path="url(#d{uid})" vector-effect="non-scaling-stroke"/>
</svg>"""


def _period_bounds(g):
    b = [0]
    for p in range(1, g["periods"] + 1):
        b.append(b[-1] + (600 if p <= 4 else 300))
    return b


def margin_chart(g):
    w, h, padl, padb = 800, 300, 34, 22
    iw, ih = w - padl, h - padb
    tl = g["timeline"]
    total = g["game_seconds"]
    ymax = max(10, max(abs(p["d"]) for p in tl))
    ymax = ((ymax + 4) // 5) * 5
    line, area, y0 = margin_path(tl, total, iw, ih, 8, ymax)
    bounds = _period_bounds(g)
    grid = ""
    for v in range(-ymax, ymax + 1, 5 if ymax <= 20 else 10):
        y = ih / 2 - v / ymax * (ih / 2 - 8)
        grid += (f'<line x1="0" x2="{iw}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--grid)" stroke-width="{1 if v else 0}"/>'
                 f'<text x="-6" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="var(--muted)">{abs(v)}</text>')
    for i, t in enumerate(bounds[:-1]):
        x = t / total * iw
        x2 = bounds[i + 1] / total * iw
        if i:
            grid += f'<line x1="{x:.1f}" x2="{x:.1f}" y1="0" y2="{ih}" stroke="var(--axis)" stroke-dasharray="3 3" stroke-width="1"/>'
        grid += f'<text x="{(x + x2) / 2:.1f}" y="{ih + 16}" text-anchor="middle" font-size="11" fill="var(--muted)">{period_label(i + 1)}</text>'
    # bandas de los parciales más grandes
    bands = ""
    for s in "AB":
        st = g["best_stretch"].get(s)
        if st and st["net"] >= 8:
            x1, x2 = st["t0"] / total * iw, st["t1"] / total * iw
            bands += (f'<rect x="{x1:.1f}" y="0" width="{max(2, x2 - x1):.1f}" height="{ih}" fill="var(--{"home" if s == "A" else "away"})" opacity=".07"/>'
                      f'<text x="{(x1 + x2) / 2:.1f}" y="{12 if s == "A" else ih - 6}" text-anchor="middle" font-size="11" font-weight="600" fill="var(--ink2)">{st["for"]}-{st["against"]}</text>')
    data = json.dumps([[p["t"], p["d"], p["a"], p["b"]] for p in tl], separators=(",", ":"))
    return f"""<div class="legend"><span><i class="dot" style="--c:var(--home)"></i>Ventaja {esc(tname(g, "A"))} (arriba)</span>
<span><i class="dot" style="--c:var(--away)"></i>Ventaja {esc(tname(g, "B"))} (abajo)</span><span>Zonas sombreadas: mejor parcial de cada equipo</span></div>
<div class="chartbox" id="mc" data-total="{total}" data-pl="{padl}" data-w="{w}" data-iw="{iw}">
<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Evolución de la diferencia en el marcador">
<defs><clipPath id="cu"><rect x="0" y="-10" width="{iw}" height="{y0 + 10:.1f}"/></clipPath>
<clipPath id="cd"><rect x="0" y="{y0:.1f}" width="{iw}" height="{ih}"/></clipPath></defs>
<g transform="translate({padl},0)">{grid}{bands}
<path d="{area}" fill="var(--home)" opacity=".18" clip-path="url(#cu)"/>
<path d="{area}" fill="var(--away)" opacity=".18" clip-path="url(#cd)"/>
<path d="{line}" fill="none" stroke="var(--home)" stroke-width="2" clip-path="url(#cu)"/>
<path d="{line}" fill="none" stroke="var(--away)" stroke-width="2" clip-path="url(#cd)"/>
<line id="mcx" x1="0" x2="0" y1="0" y2="{ih}" stroke="var(--ink2)" stroke-width="1" opacity="0"/>
<circle id="mcd" r="4" fill="var(--ink)" stroke="var(--card)" stroke-width="2" opacity="0"/>
</g></svg><div class="tip" id="mct"></div></div>
<script>(function(){{var D={data},box=document.getElementById('mc'),svg=box.querySelector('svg'),T=+box.dataset.total,
pl=+box.dataset.pl,W=+box.dataset.w,iw=+box.dataset.iw,ih={ih},ym={ymax},A={json.dumps(g["teams"]["A"]["code"])},B={json.dumps(g["teams"]["B"]["code"])},
tip=document.getElementById('mct'),lx=document.getElementById('mcx'),dt=document.getElementById('mcd');
function lab(t){{var p=1,s=0;while(true){{var L=p<=4?600:300;if(t<=s+L||p>8)break;s+=L;p++}}var r=Math.round(s+(p<=4?600:300)-t);
return (p<=4?p+'C':'PR'+(p>5?(p-4):''))+' '+String(Math.floor(r/60)).padStart(2,'0')+':'+String(r%60).padStart(2,'0')}}
function mv(e){{var r=svg.getBoundingClientRect(),cx=(e.touches?e.touches[0].clientX:e.clientX)-r.left,sx=cx*W/r.width-pl;
var t=Math.max(0,Math.min(T,sx/iw*T)),k=0;for(var i=0;i<D.length;i++){{if(D[i][0]<=t)k=i}}var d=D[k],x=t/T*iw,y=ih/2-d[1]/ym*(ih/2-8);
lx.setAttribute('x1',x);lx.setAttribute('x2',x);lx.setAttribute('opacity',1);dt.setAttribute('cx',x);dt.setAttribute('cy',y);dt.setAttribute('opacity',1);
tip.style.left=((x+pl)*r.width/W)+'px';tip.style.top=(y*r.width/W)+'px';tip.style.opacity=1;
tip.textContent=lab(t)+' · '+A+' '+d[2]+'-'+d[3]+' '+B+(d[1]?' ('+(d[1]>0?A:B)+' +'+Math.abs(d[1])+')':' (empate)')}}
function out(){{tip.style.opacity=0;lx.setAttribute('opacity',0);dt.setAttribute('opacity',0)}}
svg.addEventListener('mousemove',mv);svg.addEventListener('touchmove',mv,{{passive:true}});svg.addEventListener('mouseleave',out);svg.addEventListener('touchend',out)}})();</script>"""


def mirror(label, a, b, fa=None, fb=None, ratio=False):
    fa = fa if fa is not None else str(a)
    fb = fb if fb is not None else str(b)
    m = max(a or 0, b or 0) or 1
    wa, wb = 100 * (a or 0) / m, 100 * (b or 0) / m
    if ratio:
        wa, wb = 100 * (a or 0), 100 * (b or 0)
    return (f'<div class="mirror"><div class="lab">{esc(label)}</div><div class="va">{fa}</div>'
            f'<div class="bar a"><i style="width:{wa:.0f}%"></i></div><div class="bar b"><i style="width:{wb:.0f}%"></i></div>'
            f'<div class="vb">{fb}</div></div>')


# ---------------------------------------------------------------- portada

def game_card(g, c, idx):
    w = g["winner"]
    rows = ""
    for s in "AB":
        q = " ".join(str(x) for x in g["quarters"][s])
        rows += (f'<div class="trow {"" if s == w else "lose"}">{badge(g["teams"][s]["code"], s)}'
                 f'<span class="tname">{esc(tname(g, s))}</span><span class="qs">{q}</span>'
                 f'<span class="tscore">{g["score"][s]}</span></div>')
    tags = "".join(f'<span class="tag">{TAG_ES[t]}</span>' for t in c["tags"] if t in TAG_ES and t != "ajustada")
    mvp = g["mvp"]
    mvp_html = (f'<div class="mvp"><span><span class="muted">MVP</span> <b>{esc(mvp["name"])}</b> '
                f'<span class="muted">· {esc(g["teams"][mvp["side"]]["code"])}</span></span>'
                f'<span>{mvp["PTS"]} pts · {mvp["REB"]} reb · <b>{mvp["PIR"]}</b> val</span></div>') if mvp else ""
    when = " · ".join(x for x in [g.get("date"), g.get("hour")] if x)
    return f"""<a class="card" href="partidos/{g['season']}-{g['game_code']}.html">
<div class="meta"><span>{esc(when)}</span><span class="tags">{tags}</span></div>{rows}
{sparkline(g, idx)}<p class="one"><b>{esc(c["title"])}.</b> {esc(c["summary"])}</p>{mvp_html}</a>"""


def round_page(games, crons, round_label, rounds_all, demo=False, competition="Euroliga"):
    cards = "".join(game_card(g, c, i) for i, (g, c) in enumerate(zip(games, crons)))
    dates = sorted({g.get("date") for g in games if g.get("date")}, key=_date_key)
    # destacados
    allp = [(r, g) for g in games for s in "AB" for r in g["box"][s]]
    top = sorted(allp, key=lambda x: -x[0]["PIR"])[:6]
    tops = "".join(
        f'<li><span class="rank">{i + 1}</span><span style="flex:1"><b>{esc(r["name"])}</b> '
        f'<span class="muted">· {esc(tname(g, r["side"]))}</span><br><span class="muted" style="font-size:13px">'
        f'{r["PTS"]} pts · {r["REB"]} reb · {r["AST"]} as · {r["MIN"]} min</span></span><span class="big">{r["PIR"]}</span></li>'
        for i, (r, g) in enumerate(top))
    # equipos
    trs = []
    for g in games:
        for s in "AB":
            o = "B" if s == "A" else "A"
            trs.append((g["adv"][s]["net"], g, s, o))
    trs.sort(key=lambda x: -(x[0] or 0))
    teams_rows = "".join(
        f'<tr><td><b>{esc(tname(g, s))}</b></td>'
        f'<td>{"G" if g["winner"] == s else "P"} {g["score"][s]}-{g["score"][o]}</td>'
        f'<td>{g["adv"][s]["ortg"]}</td><td>{g["adv"][s]["drtg"]}</td><td><b>{net:+.1f}</b></td>'
        f'<td>{g["adv"][s]["pace"]}</td><td>{pct(g["adv"][s]["efg"])}</td><td>{pct(g["adv"][s]["tov_pct"])}</td>'
        f'<td>{pct(g["adv"][s]["orb_pct"])}</td></tr>'
        for net, g, s, o in trs)
    # récords
    rec = []
    run = max(((r, g) for g in games for r in g["runs"]), key=lambda x: x[0]["pts"], default=None)
    if run:
        r, g = run
        rec.append(("Mayor parcial", f'{r["pts"]}-0', f'{tname(g, r["side"])} ante {tname(g, "B" if r["side"] == "A" else "A")}'))
    com = max(games, key=lambda g: g["biggest_lead"]["B" if g["winner"] == "A" else "A"].get("lead", 0))
    d = com["biggest_lead"]["B" if com["winner"] == "A" else "A"].get("lead", 0)
    if d >= 6:
        rec.append(("Mayor remontada", f"-{d}", f'{tname(com, com["winner"])} ({com["score"]["A"]}-{com["score"]["B"]})'))
    sc = max(allp, key=lambda x: x[0]["PTS"])
    rec.append(("Máximo anotador", f'{sc[0]["PTS"]} pts', f'{sc[0]["name"]} ({tname(sc[1], sc[0]["side"])})'))
    tr = max(allp, key=lambda x: (x[0]["3PM"], -x[0]["3PA"]))
    rec.append(("Más triples", f'{tr[0]["3PM"]}/{tr[0]["3PA"]}', f'{tr[0]["name"]} ({tname(tr[1], tr[0]["side"])})'))
    rb = max(allp, key=lambda x: x[0]["REB"])
    rec.append(("Más rebotes", f'{rb[0]["REB"]}', f'{rb[0]["name"]} ({tname(rb[1], rb[0]["side"])})'))
    asx = max(allp, key=lambda x: x[0]["AST"])
    rec.append(("Más asistencias", f'{asx[0]["AST"]}', f'{asx[0]["name"]} ({tname(asx[1], asx[0]["side"])})'))
    recs = "".join(f'<div class="tile"><div class="l">{esc(a)}</div><div class="v">{esc(b)}</div><div class="d">{esc(c)}</div></div>'
                   for a, b, c in rec)
    nav = "".join(f'<a class="pill{" on" if r == round_label else ""}" href="{_round_file(r)}">J{esc(str(r))}</a>'
                  for r in rounds_all)
    extra_nav = ('<div class="nav"><a class="pill" href="app/">📋 App Banquillo</a>'
                 '<a class="pill" href="equipo/">Nuestro equipo</a></div>') if competition == "Euroliga" else \
        '<div class="nav"><a class="pill" href="../app/">📋 App Banquillo</a><a class="pill" href="../">Euroliga</a></div>'
    body = f"""<header class="top"><div class="kicker">Informe {competition}</div>
<h1>Jornada {esc(str(round_label))}</h1><div class="sub">{esc(" y ".join(dates))} · {len(games)} partidos</div>
<div class="nav">{nav}</div>{extra_nav}</header>
<section><h2>Resultados</h2><div class="grid">{cards}</div></section>
<section><h2>Récords de la jornada</h2><div class="tiles">{recs}</div></section>
<section><div class="card"><h2>Mejores valoraciones</h2><ul class="list" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));column-gap:28px">{tops}</ul></div></section>
<section><div class="card"><h2>Equipos de la jornada</h2><div class="scroll"><table class="sticky">
<tr><th>Equipo</th><th>Res.</th><th>ORtg</th><th>DRtg</th><th>Net</th><th>Ritmo</th><th>eFG%</th><th>PER%</th><th>RO%</th></tr>
{teams_rows}</table></div><p class="glos">ORtg/DRtg: puntos anotados/recibidos por cada 100 posesiones. Net: diferencia. PER%: pérdidas por posesión. RO%: rebotes ofensivos capturados sobre los disponibles.</p></div>
</section>"""
    return page(f"{competition} · Jornada {round_label}", body, demo)


def _date_key(d):
    try:
        dd, mm, yy = d.split("/")
        return (int(yy), int(mm), int(dd))
    except Exception:
        return (0, 0, 0)


def _round_file(r):
    return f"jornada-{r}.html"


# ---------------------------------------------------------------- partido

def box_table(g, s):
    rows = ""
    for r in g["box"][s]:
        star = "*" if r["starter"] else ""
        label = r["name"] if r["name"].startswith("#") else f'{r["num"]} {r["name"]}'
        rows += (f'<tr><td>{esc(label)}{star}</td><td data-v="{r["SEC"]}">{r["MIN"]}</td>'
                 f'<td>{r["PTS"]}</td><td data-v="{r["2PM"]}">{r["2PM"]}/{r["2PA"]}</td>'
                 f'<td data-v="{r["3PM"]}">{r["3PM"]}/{r["3PA"]}</td><td data-v="{r["FTM"]}">{r["FTM"]}/{r["FTA"]}</td>'
                 f'<td>{r["OREB"]}</td><td>{r["DREB"]}</td><td>{r["REB"]}</td><td>{r["AST"]}</td><td>{r["STL"]}</td>'
                 f'<td>{r["TOV"]}</td><td>{r["BLK"]}</td><td>{r["PF"]}</td><td>{r["FD"]}</td><td><b>{r["PIR"]}</b></td>'
                 f'<td>{r["PM"]:+d}</td><td data-v="{r["TS"] or 0}">{pct(r["TS"])}</td><td data-v="{r["USG"] or 0}">{"–" if r["USG"] is None else r["USG"]}</td></tr>')
    t = g["team_box"][s]
    rows += (f'<tr class="tot"><td>Total</td><td></td><td>{t["PTS"]}</td><td>{t["2PM"]}/{t["2PA"]}</td>'
             f'<td>{t["3PM"]}/{t["3PA"]}</td><td>{t["FTM"]}/{t["FTA"]}</td><td>{t["OREB"]}</td><td>{t["DREB"]}</td>'
             f'<td>{t["REB"]}</td><td>{t["AST"]}</td><td>{t["STL"]}</td><td>{t["TOV"]}</td><td>{t["BLK"]}</td>'
             f'<td>{t["PF"]}</td><td>{t["FD"]}</td><td>{t["PIR"]}</td><td></td><td>{pct(t["TS"])}</td><td></td></tr>')
    head = "".join(f'<th class="s">{h}</th>' for h in
                   ["Jugador", "Min", "Pts", "T2", "T3", "TL", "RO", "RD", "RT", "As", "Rob", "Pér", "Tap", "FC", "FR", "Val", "+/-", "TS%", "Uso%"])
    return f'<div class="scroll"><table class="sticky box"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def quarter_heat(g, s):
    n = g["periods"]
    head = "".join(f"<th>{period_label(p)}</th>" for p in range(1, n + 1))
    mx = max([max(r["q_pts"]) for r in g["box"][s]] + [1])
    rows = ""
    for r in sorted(g["box"][s], key=lambda r: -r["PTS"]):
        if not r["PTS"]:
            continue
        cells = ""
        for v in r["q_pts"]:
            a = 0.08 + 0.55 * v / mx if v else 0
            cells += (f'<td class="h" style="background:color-mix(in srgb,var(--{"home" if s == "A" else "away"}) {a * 100:.0f}%,transparent)">'
                      f'{v or "·"}</td>')
        rows += f'<tr><td>{esc(r["name"])}</td>{cells}<td><b>{r["PTS"]}</b></td></tr>'
    return f'<div class="scroll"><table class="heat"><tr><th>{esc(tname(g, s))}</th>{head}<th>Tot</th></tr>{rows}</table></div>'


def match_page(g, c, demo=False):
    A, B = "A", "B"
    w = g["winner"]
    status = "Final" + (" · prórroga" if g["periods"] == 5 else f" · {g['periods'] - 4} prórrogas" if g["periods"] > 5 else "")
    qhead = "".join(f"<th>{period_label(p)}</th>" for p in range(1, g["periods"] + 1))
    qrows = "".join(
        f'<tr><td><span class="dot" style="--c:var(--{"home" if s == "A" else "away"})"></span><b>{esc(g["teams"][s]["code"])}</b></td>'
        + "".join(f"<td>{x}</td>" for x in g["quarters"][s]) + f'<td><b>{g["score"][s]}</b></td></tr>'
        for s in "AB")
    hero = f"""<div class="hero"><div class="score">
<div class="team">{badge(g["teams"][A]["code"], A)}<span>{esc(tname(g, A))}</span></div>
<div><div class="num"><span class="{'' if w == A else 'l'}">{g["score"][A]}</span> <span class="l">–</span> <span class="{'' if w == B else 'l'}">{g["score"][B]}</span></div>
<div class="status">{status}</div></div>
<div class="team">{badge(g["teams"][B]["code"], B)}<span>{esc(tname(g, B))}</span></div></div>
<div class="sub" style="text-align:center;margin-top:8px">{esc(" · ".join(x for x in [g.get("date"), g.get("hour"), g.get("venue")] if x))}</div>
<div class="scroll qtable"><table><tr><th></th>{qhead}<th>Total</th></tr>{qrows}</table></div></div>"""

    chips = "".join(f'<a class="pill" href="#{a}">{b}</a>' for a, b in [
        ("resumen", "Resumen"), ("jugadores", "Jugadores"), ("cronica", "Crónica"), ("marcador", "Marcador"), ("momentos", "Rachas"),
        ("equipos", "Equipos"), ("avanzada", "Avanzada"), ("cuartos", "Por cuartos"),
        ("quintetos", "Quintetos"), ("pbp", "Jugada a jugada")])

    # ---- resumen
    mvp = g["mvp"]
    l = "B" if w == "A" else "A"
    mvp_html = ""
    if mvp:
        mvp_html = f"""<div class="card mvpcard">{badge(g["teams"][mvp["side"]]["code"], mvp["side"])}
<div style="flex:1"><div class="kicker">MVP del partido</div><div class="big">{esc(mvp["name"])}</div>
<div class="sub">{mvp["PTS"]} pts · {mvp["REB"]} reb · {mvp["AST"]} as · {mvp["FGM"]}/{mvp["FGA"]} TC · {mvp["MIN"]} min · {mvp["PM"]:+d}</div></div>
<div style="text-align:center"><div class="big" style="font-size:34px">{mvp["PIR"]}</div><div class="muted" style="font-size:11px">VAL</div></div></div>"""
    bl = {s: g["biggest_lead"][s].get("lead", 0) for s in "AB"}
    st_w = g["best_stretch"].get(w) or {}
    tiles = [
        ("Mayor ventaja", f'{tname(g, A)} +{bl[A]} · {tname(g, B)} +{bl[B]}', ""),
        ("Cambios de líder", str(g["lead_changes"]), f'{g["ties"]} empates'),
        ("Mejor parcial ganador", f'{st_w.get("for", 0)}-{st_w.get("against", 0)}', f'en 5 min · {tname(g, w)}'),
        ("Ritmo", f'{g["adv"][A]["pace"]}', "posesiones por 40 min"),
    ]
    tiles_html = "".join(f'<div class="tile"><div class="l">{a}</div><div class="v" style="font-size:{18 if len(b) > 12 else 24}px">{esc(b)}</div><div class="d">{esc(d)}</div></div>'
                         for a, b, d in tiles)
    keys = "".join(f'<div class="key"><b>{esc(k["label"])}</b>{esc(k["text"])}</div>' for k in c["keys"])

    # ---- momentos
    def run_txt(r):
        return (f'{r["pts"]}-0 {esc(tname(g, r["side"]))}', f'{period_label(r["start"]["period"])} {r["start"]["clock"]} → '
                f'{period_label(r["end"]["period"])} {r["end"]["clock"]} · de {r["start"]["a"]}-{r["start"]["b"]} a {r["end"]["a"]}-{r["end"]["b"]}', r["side"])
    items = [run_txt(r) for r in g["runs"][:6]]
    runs_html = "".join(f'<li><span class="dot" style="--c:var(--{"home" if s == "A" else "away"})"></span><span style="flex:1"><b>{a}</b><br>'
                        f'<span class="muted" style="font-size:13px">{b}</span></span></li>' for a, b, s in items) or "<li>Sin rachas de 7-0 o más</li>"
    tot = g["game_seconds"]
    tlA, tlB = g["adv"][A]["time_leading"], g["adv"][B]["time_leading"]
    tie = max(0, tot - tlA - tlB)
    seg = (f'<div class="seg"><i style="width:{100 * tlA / tot:.1f}%;background:var(--home)"></i>'
           f'<i style="width:{100 * tie / tot:.1f}%;background:var(--axis)"></i><i style="width:{100 * tlB / tot:.1f}%;background:var(--away)"></i></div>')
    mm = lambda s: f"{int(s) // 60}:{int(s) % 60:02d}"
    lead_html = f"""<div class="legend"><span><i class="dot" style="--c:var(--home)"></i>{esc(tname(g, A))} {mm(tlA)}</span>
<span><i class="dot" style="--c:var(--axis)"></i>Empate {mm(tie)}</span><span><i class="dot" style="--c:var(--away)"></i>{esc(tname(g, B))} {mm(tlB)}</span></div>{seg}"""
    moments = []
    for s in "AB":
        b = g["biggest_lead"][s]
        if b.get("lead"):
            moments.append((s, f"Máxima ventaja {tname(g, s)}: +{b['lead']}", f"{period_label(b['period'])} {b['clock']} · {b['a']}-{b['b']}"))
        st = g["best_stretch"].get(s)
        if st and st["net"] > 0:
            moments.append((s, f"Mejor tramo de 5' {tname(g, s)}: {st['for']}-{st['against']}",
                            f"{period_label(st['from']['period'])} {st['from']['clock']} → {period_label(st['to']['period'])} {st['to']['clock']}"))
        d = g["droughts"][s]
        moments.append((s, f"Mayor sequía {tname(g, s)}: {mm(d['seconds'])} sin anotar",
                        f"{period_label(d['from']['period'])} {d['from']['clock']} → {period_label(d['to']['period'])} {d['to']['clock']}"))
    mom_html = "".join(f'<li><span class="dot" style="--c:var(--{"home" if s == "A" else "away"})"></span><span style="flex:1"><b>{esc(a)}</b><br>'
                       f'<span class="muted" style="font-size:13px">{esc(b)}</span></span></li>' for s, a, b in moments)

    # ---- comparativa
    ta, tb = g["team_box"][A], g["team_box"][B]
    aa, ab = g["adv"][A], g["adv"][B]

    def frac(m, a):
        return f"{m}/{a}"
    def shot(label, m, a):
        va = ta[m] / ta[a] if ta[a] else None
        vb = tb[m] / tb[a] if tb[a] else None
        return mirror(label, va, vb, f'{pct(va)}<small>{ta[m]}/{ta[a]}</small>',
                      f'{pct(vb)}<small>{tb[m]}/{tb[a]}</small>', ratio=True)
    comp = (shot("Tiros de campo", "FGM", "FGA") + shot("Tiros de 2", "2PM", "2PA")
            + shot("Triples", "3PM", "3PA") + shot("Tiros libres", "FTM", "FTA")
            + mirror("Rebotes", ta["REB"], tb["REB"])
            + mirror("Rebotes ofensivos", ta["OREB"], tb["OREB"])
            + mirror("Asistencias", ta["AST"], tb["AST"])
            + mirror("Pérdidas", ta["TOV"], tb["TOV"])
            + mirror("Robos", ta["STL"], tb["STL"])
            + mirror("Tapones", ta["BLK"], tb["BLK"])
            + mirror("Puntos tras pérdida", aa["pts_off_to"], ab["pts_off_to"])
            + mirror("Puntos de 2ª oportunidad", aa["second_chance"], ab["second_chance"])
            + mirror("Puntos en transición (<8 s)", aa["fast_break"], ab["fast_break"])
            + mirror("Puntos del banquillo", aa["bench"], ab["bench"])
            + mirror("Puntos en clutch", aa["clutch"], ab["clutch"]))
    leg = (f'<div class="legend" style="justify-content:space-between"><span><i class="dot" style="--c:var(--home)"></i>{esc(tname(g, A))}</span>'
           f'<span>{esc(tname(g, B))}<i class="dot" style="--c:var(--away);margin:0 0 0 6px"></i></span></div>')

    # ---- avanzada
    def arow(label, k, f=lambda x: str(x), better="high"):
        va, vb = aa[k], ab[k]
        bold_a = bold_b = ""
        if va is not None and vb is not None and va != vb:
            hi = va > vb
            if better == "low":
                hi = not hi
            bold_a, bold_b = ("b", "") if hi else ("", "b")
        wrap = lambda v, b: f"<b>{f(v)}</b>" if b else f(v)
        return f"<tr><td>{label}</td><td>{wrap(va, bold_a)}</td><td>{wrap(vb, bold_b)}</td></tr>"
    adv_rows = (arow("Posesiones", "poss") + arow("Ritmo (pos./40 min)", "pace")
                + arow("Rating ofensivo (ORtg)", "ortg") + arow("Rating defensivo (DRtg)", "drtg", better="low")
                + arow("Net rating", "net", lambda x: f"{x:+.1f}")
                + arow("eFG% (tiro efectivo)", "efg", pct) + arow("TS% (tiro real)", "ts", pct)
                + arow("Pérdidas por posesión (TOV%)", "tov_pct", pct, "low")
                + arow("Rebote ofensivo (ORB%)", "orb_pct", pct) + arow("Rebote defensivo (DRB%)", "drb_pct", pct)
                + arow("Tiros libres por tiro (FTr)", "ftr", pct) + arow("Canastas asistidas (%AST)", "ast_pct", pct)
                + arow("Tiros que son triples (3PAr)", "three_rate", pct))
    glos = """<dl class="glos"><div><dt>Posesiones</dt><dd>estimadas como TC intentados − rebotes ofensivos + pérdidas + 0,44 × TL intentados.</dd></div>
<div><dt>ORtg / DRtg</dt><dd>puntos anotados / recibidos por cada 100 posesiones.</dd></div>
<div><dt>eFG%</dt><dd>acierto de campo dando 1,5 veces más valor al triple.</dd></div>
<div><dt>TS%</dt><dd>eficiencia de tiro incluyendo los tiros libres.</dd></div>
<div><dt>Los cuatro factores</dt><dd>(Dean Oliver): eFG%, TOV%, ORB% y FTr explican la mayor parte de cualquier resultado.</dd></div>
<div><dt>Uso%</dt><dd>porcentaje de jugadas del equipo que termina un jugador mientras está en pista.</dd></div>
<div><dt>Clutch</dt><dd>últimos 5 minutos del 4º cuarto y prórrogas con diferencia de 5 o menos.</dd></div></dl>"""

    # ---- quintetos
    def lu_html(s):
        out = ""
        for lu in g["lineups"][s]:
            out += (f'<div class="lu"><div class="n">{esc(" · ".join(_short(n) for n in lu["players"]))}</div>'
                    f'<div class="m">{lu["min"]} min · {lu["pf"]}-{lu["pa"]} · <span class="pm" style="color:var(--ink)">{lu["pm"]:+d}</span></div></div>')
        return out or '<div class="muted">Sin datos suficientes</div>'
    asis = "".join(f'<li><span class="dot" style="--c:var(--{"home" if a["side"] == "A" else "away"})"></span>'
                   f'<span style="flex:1">{esc(a["from"])} → {esc(a["to"])}</span><b>×{a["n"]}</b></li>' for a in g["assists"])

    # ---- on/off
    def onoff(s):
        rows = sorted(g["box"][s], key=lambda r: -(r["PM"] - r["OFF_PM"]))
        return "".join(f'<tr><td>{esc(r["name"])}</td><td>{r["MIN"]}</td><td>{r["PM"]:+d}</td><td>{r["OFF_PM"]:+d}</td>'
                       f'<td><b>{r["PM"] - r["OFF_PM"]:+d}</b></td></tr>' for r in rows if r["SEC"] >= 120)

    # ---- PBP
    pbp_html = ""
    for p in range(1, g["periods"] + 1):
        rows = ""
        for e in g["pbp"]:
            if e["period"] != p:
                continue
            side = e["side"]
            desc = PLAY_ES.get(e["type"], e["info"] or e["type"])
            who = esc(e["player"]) if e["player"] else (esc(tname(g, side)) if side else "")
            dot = f'<span class="dot" style="--c:var(--{"home" if side == "A" else "away"})"></span>' if side else ""
            cls = "sc" if e["pts"] else ("sub" if e["type"] in ("IN", "OUT") else "")
            scr = f'{e["a"]}-{e["b"]}' if e["pts"] else ""
            rows += f'<tr class="{cls}"><td class="clk">{e["clock"]}</td><td>{dot}{desc}{" · " + who if who else ""}</td><td>{scr}</td></tr>'
        pbp_html += (f'<details{" open" if p == g["periods"] else ""}><summary>{period_label(p)} · {g["quarters"]["A"][p - 1]}-{g["quarters"]["B"][p - 1]}</summary>'
                     f'<div class="scroll" style="padding:0 10px 10px"><table class="pbp">{rows}</table></div></details>')

    cron = "".join(f"<p>{esc(x)}</p>" for x in c["paragraphs"])
    body = f"""<header class="top" style="padding-top:18px"><a class="pill" href="../{_round_file(g.get('round') or 'x')}">← Jornada {esc(str(g.get('round') or ''))}</a></header>
{hero}
<nav class="chips">{chips}</nav>
<section id="resumen"><h2>Resumen</h2>{mvp_html}<div class="tiles" style="margin-top:10px">{tiles_html}</div>
<h3 style="margin-top:16px">Claves del partido</h3><div class="keys">{keys}</div></section>
<section id="jugadores"><h2>Estadísticas de jugadores</h2><div class="card">
<div class="tabs" data-tabs="box"><button class="on" data-t="0">{esc(tname(g, A))}</button><button data-t="1">{esc(tname(g, B))}</button></div>
<div data-pane="box">{box_table(g, A)}</div><div data-pane="box" hidden>{box_table(g, B)}</div>
<p class="glos">* titular. Pulsa una cabecera para ordenar. Minutos y +/- calculados siguiendo los cambios del play-by-play.</p></div>
</div></section>
<section id="cronica" class="cronica"><div class="kicker">Crónica</div><h2>{esc(c["title"])}</h2>{cron}</section>
<section id="marcador"><h2>Evolución del marcador</h2><div class="card">{margin_chart(g)}</div></section>
<section id="momentos" class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr));align-items:start">
<div class="card"><h2>Rachas (parciales sin respuesta)</h2><ul class="list">{runs_html}</ul></div>
<div class="card"><h2>Tiempo por delante</h2>{lead_html}<ul class="list" style="margin-top:8px">{mom_html}</ul></div></section>
<section id="equipos"><h2>Comparativa de equipos</h2><div class="card">{leg}{comp}</div></section>
<section id="avanzada"><h2>Estadística avanzada</h2><div class="card"><div class="scroll"><table>
<tr><th>Métrica</th><th>{esc(g["teams"][A]["code"])}</th><th>{esc(g["teams"][B]["code"])}</th></tr>{adv_rows}</table></div>{glos}</div></section>

<section id="cuartos"><h2>Puntos por cuarto</h2><div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
<div class="card">{quarter_heat(g, A)}</div><div class="card">{quarter_heat(g, B)}</div></div></section>
<section id="quintetos"><h2>Quintetos y conexiones</h2><div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr));align-items:start">
<div class="card"><h3><span class="dot" style="--c:var(--home)"></span>Quintetos más usados · {esc(tname(g, A))}</h3>{lu_html(A)}</div>
<div class="card"><h3><span class="dot" style="--c:var(--away)"></span>Quintetos más usados · {esc(tname(g, B))}</h3>{lu_html(B)}</div>
<div class="card"><h3>Conexiones de asistencia</h3><ul class="list">{asis}</ul></div></div></section>
<section id="pbp"><h2>Jugada a jugada</h2><div class="tabs" data-filter><button class="on" data-f="all">Todo</button><button data-f="sc">Solo canastas</button><button data-f="nosub">Sin cambios</button></div>{pbp_html}</section>
<script>
document.querySelectorAll('[data-tabs]').forEach(function(t){{var k=t.dataset.tabs,ps=document.querySelectorAll('[data-pane="'+k+'"]');
t.querySelectorAll('button').forEach(function(b){{b.onclick=function(){{t.querySelectorAll('button').forEach(function(x){{x.classList.remove('on')}});b.classList.add('on');
ps.forEach(function(p,i){{p.hidden=i!=+b.dataset.t}})}}}})}});
document.querySelectorAll('table.box').forEach(function(tb){{tb.querySelectorAll('th').forEach(function(th,ci){{if(!ci)return;th.onclick=function(){{
var body=tb.tBodies[0],rows=[].slice.call(body.rows),tot=rows.pop(),dir=th.dataset.d=th.dataset.d==='-1'?'1':'-1';
rows.sort(function(a,b){{function v(r){{var c=r.cells[ci];return parseFloat(c.dataset.v!==undefined?c.dataset.v:c.textContent)||0}}return (v(a)-v(b))*dir}});
rows.forEach(function(r){{body.appendChild(r)}});body.appendChild(tot)}}}})}});
var fb=document.querySelector('[data-filter]');fb.querySelectorAll('button').forEach(function(b){{b.onclick=function(){{
fb.querySelectorAll('button').forEach(function(x){{x.classList.remove('on')}});b.classList.add('on');var f=b.dataset.f;
document.querySelectorAll('table.pbp tr').forEach(function(r){{r.hidden=(f==='sc'&&!r.classList.contains('sc'))||(f==='nosub'&&r.classList.contains('sub'))}})}}}});
</script>"""
    return page(f"{tname(g, A)} {g['score'][A]}-{g['score'][B]} {tname(g, B)}", body, demo)


# ---------------------------------------------------------------- sitio

def build_site(games, out_dir, demo=False, competition="Euroliga", footer=None):
    """games: lista de análisis (salida de analysis.analyze)."""
    global FOOTER
    FOOTER = footer or "Generado automáticamente a partir del play-by-play oficial de la Euroliga."
    os.makedirs(os.path.join(out_dir, "partidos"), exist_ok=True)
    by_round = {}
    for g in games:
        by_round.setdefault(str(g.get("round") or "?"), []).append(g)

    def rkey(r):
        try:
            return int(r)
        except ValueError:
            return 9999
    rounds = sorted(by_round, key=rkey)
    latest = None
    for r in rounds:
        gs = sorted(by_round[r], key=lambda g: (_date_key(g.get("date") or ""), g.get("hour") or "", g["game_code"]))
        crons = [write_cronica(g) for g in gs]
        for g, c in zip(gs, crons):
            with open(os.path.join(out_dir, "partidos", f"{g['season']}-{g['game_code']}.html"), "w", encoding="utf-8") as f:
                f.write(match_page(g, c, demo))
        html = round_page(gs, crons, r, rounds, demo, competition)
        with open(os.path.join(out_dir, _round_file(r)), "w", encoding="utf-8") as f:
            f.write(html)
        latest = html
    if latest:
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(latest)
    return rounds
