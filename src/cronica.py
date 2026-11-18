"""Crónicas en castellano generadas con plantillas a partir del análisis.

Todo es determinista (la variedad de frases depende del código del partido),
así que el mismo partido siempre produce el mismo texto.
"""

import random

from .teams import short_name

FEMININE = {"VIR"}
QNAME = {1: "primer cuarto", 2: "segundo cuarto", 3: "tercer cuarto", 4: "último cuarto"}


class T:
    """Ayudante para nombrar equipos con artículo y contracciones."""

    def __init__(self, g):
        self.g = g

    def name(self, s):
        t = self.g["teams"][s]
        return t.get("short") or short_name(t["code"], t["name"])

    def art(self, s):
        return "la" if self.g["teams"][s]["code"] in FEMININE else "el"

    def el(self, s, cap=False):
        a = self.art(s)
        r = f"{a} {self.name(s)}"
        return r[0].upper() + r[1:] if cap else r

    def de(self, s):
        return f"del {self.name(s)}" if self.art(s) == "el" else f"de la {self.name(s)}"

    def a(self, s):
        return f"al {self.name(s)}" if self.art(s) == "el" else f"a la {self.name(s)}"


def qname(p):
    return QNAME.get(p, "la prórroga" if p == 5 else f"la {p - 4}ª prórroga")


def del_q(p):
    return f"del {qname(p)}" if p <= 4 else f"de {qname(p)}"


def stat_line(r, long=False):
    parts = [f"{r['PTS']} puntos"]
    if r["REB"] >= 5 or long:
        parts.append(f"{r['REB']} rebotes")
    if r["AST"] >= 4 or long:
        parts.append(f"{r['AST']} asistencias")
    if r["3PM"] >= 3:
        parts.append(f"{r['3PM']} triples")
    return ", ".join(parts[:-1]) + (" y " + parts[-1] if len(parts) > 1 else parts[0]) + f" ({r['PIR']} de valoración)"


def classify(g):
    w = g["winner"]
    l = "B" if w == "A" else "A"
    margin = abs(g["score"]["A"] - g["score"]["B"])
    deficit = g["biggest_lead"][l].get("lead", 0)
    tags = []
    if g["periods"] > 4:
        tags.append("prorroga")
    if deficit >= 10:
        tags.append("remontada")
    if margin >= 20:
        tags.append("paliza")
    elif margin >= 11:
        tags.append("comoda")
    elif margin <= 5:
        tags.append("ajustada")
    total = g["game_seconds"]
    if deficit <= 2 and g["adv"][w]["time_leading"] >= 0.8 * total:
        tags.append("de_principio_a_fin")
    if g["clutch"] and margin <= 5:
        tags.append("final_apretado")
    return tags


def write(g):
    rng = random.Random(f"{g.get('season')}-{g.get('game_code')}")
    t = T(g)
    w = g["winner"]
    l = "B" if w == "A" else "A"
    sw, sl = g["score"][w], g["score"][l]
    margin = sw - sl
    tags = classify(g)
    home_won = w == "A"
    box = g["box"]
    best = {s: max(box[s], key=lambda r: (r["PIR"], r["PTS"])) for s in "AB" if box[s]}
    top_scorer = {s: max(box[s], key=lambda r: (r["PTS"], r["PIR"])) for s in "AB" if box[s]}
    mvp = g["mvp"]
    deficit = g["biggest_lead"][l].get("lead", 0)
    where = "en casa" if home_won else "a domicilio"
    venue = f" en el {g['venue']}" if g.get("venue") else ""

    # ---------------- Titular
    if "remontada" in tags and "prorroga" in tags:
        title = rng.choice([
            f"{t.el(w, True)} remonta {deficit} puntos y gana en la prórroga",
            f"{t.el(w, True)} levanta un -{deficit} y se lo lleva en la prórroga",
        ])
    elif "remontada" in tags:
        title = rng.choice([
            f"{t.el(w, True)} remonta {deficit} puntos para ganar {where}",
            f"{t.el(w, True)} levanta un -{deficit} y tumba {t.a(l)}",
            f"Remontada {t.de(w)}, que llegó a perder de {deficit}",
        ])
    elif "prorroga" in tags:
        title = rng.choice([
            f"{t.el(w, True)} gana {t.a(l)} tras una prórroga",
            f"Hizo falta prórroga: {t.el(w)} se impone {t.a(l)}",
        ])
    elif "paliza" in tags:
        title = rng.choice([
            f"Exhibición {t.de(w)}, que arrolla {t.a(l)} (+{margin})",
            f"{t.el(w, True)} pasa por encima {t.de(l)}",
            f"{t.el(w, True)} no da opción {t.a(l)}: +{margin}",
        ])
    elif "final_apretado" in tags or "ajustada" in tags:
        title = rng.choice([
            f"{t.el(w, True)} gana un final apretado ante {t.el(l)}",
            f"{t.el(w, True)} resiste y gana por {margin}",
            f"Triunfo por la mínima {t.de(w)} ante {t.el(l)}",
        ])
    elif "de_principio_a_fin" in tags:
        title = rng.choice([
            f"{t.el(w, True)} manda de principio a fin",
            f"{t.el(w, True)} controla el partido y vence {t.a(l)}",
        ])
    else:
        title = rng.choice([
            f"{t.el(w, True)} se impone {t.a(l)}",
            f"Victoria {t.de(w)} ante {t.el(l)}",
            f"{t.el(w, True)} gana {where} {t.a(l)}" if not home_won else f"{t.el(w, True)} hace valer su pista ante {t.el(l)}",
        ])

    # ---------------- Entradilla
    mvp_side = mvp["side"] if mvp else w
    lead = rng.choice([
        f"{t.el(w, True)} ganó {sw}-{sl} {t.a(l)}{venue if home_won else ''}",
        f"{t.el(w, True)} se impuso por {sw}-{sl} {t.a(l)}{venue if home_won else ''}",
    ])
    if not home_won:
        lead += f" a domicilio{venue}"
    if "remontada" in tags:
        lead += f" tras llegar a ir perdiendo de {deficit} puntos"
    elif "paliza" in tags:
        lead += " en un partido sin historia"
    elif "de_principio_a_fin" in tags:
        lead += " en un partido que controló de principio a fin"
    if "prorroga" in tags:
        lead += f" y después de {g['periods'] - 4 if g['periods'] > 5 else 'una'} prórroga{'s' if g['periods'] > 5 else ''}"
    lead += "."
    if mvp:
        lead += " " + rng.choice([
            f"{mvp['name']} fue el mejor del partido con {stat_line(mvp)}.",
            f"El MVP fue {mvp['name']}: {stat_line(mvp)}.",
        ])
        if mvp_side != w:
            lead = lead[:-1] + ", aunque no le bastó a su equipo."

    # ---------------- Desarrollo por cuartos
    qa, qb = g["quarters"]["A"], g["quarters"]["B"]
    cum = []
    a = b = 0
    for x, y in zip(qa, qb):
        a += x
        b += y
        cum.append((a, b))
    runs_by_q = {}
    for r in g["runs"]:
        if r["start"]["period"] == r["end"]["period"]:
            runs_by_q.setdefault(r["end"]["period"], r)
    mentioned = set()

    def q_sentence(i):
        p = i + 1
        x, y = qa[i], qb[i]
        ca, cb = cum[i]
        qw = "A" if x > y else "B" if y > x else None
        s = ""
        if qw:
            s = rng.choice([
                f"{t.el(qw, True)} ganó el {qname(p)} ({max(x, y)}-{min(x, y)})",
                f"En el {qname(p)}, {t.el(qw)} fue mejor ({max(x, y)}-{min(x, y)})",
            ]) if p <= 4 else f"{t.el(qw, True)} se llevó la prórroga ({max(x, y)}-{min(x, y)})"
        else:
            s = f"El {qname(p)} terminó en tablas ({x}-{y})" if p <= 4 else f"La prórroga acabó igualada ({x}-{y})"
        run = runs_by_q.get(p)
        if run and run["pts"] >= 8:
            mentioned.add(id(run))
            if run["side"] == qw:
                s += f", con un parcial de {run['pts']}-0 a su favor"
            else:
                s += f", pese a un parcial de {run['pts']}-0 {t.de(run['side'])}"
        if p == 2:
            s += f". Al descanso, {_score_phrase(t, ca, cb)}."
        elif p == 3:
            s += f", y el marcador llegaba al último cuarto con {_score_phrase(t, ca, cb, short=True)}."
        else:
            s += "."
        return s

    first_half = " ".join(q_sentence(i) for i in range(min(2, len(qa))))
    second_half = " ".join(q_sentence(i) for i in range(2, len(qa)))

    # Momento decisivo
    decisive = ""
    stretch = g["best_stretch"].get(w)
    if stretch and stretch["net"] >= 8:
        fr, to = stretch["from"], stretch["to"]
        if fr["period"] == to["period"]:
            when = f"en el {qname(fr['period'])} (del {fr['clock']} al {to['clock']})" if fr["period"] <= 4 \
                else f"en {qname(fr['period'])} (del {fr['clock']} al {to['clock']})"
        else:
            when = f"entre el {fr['clock']} {del_q(fr['period'])} y el {to['clock']} {del_q(to['period'])}"
        decisive = rng.choice([
            f"La clave estuvo en un parcial de {stretch['for']}-{stretch['against']} {t.de(w)} {when}.",
            f"El partido se rompió con un {stretch['for']}-{stretch['against']} a favor {t.de(w)} {when}.",
        ])
    big_runs = [r for r in g["runs"] if r["pts"] >= 12 and id(r) not in mentioned]
    if big_runs:
        r = big_runs[0]
        decisive += f" El mayor parcial del partido fue un {r['pts']}-0 {t.de(r['side'])}."
    dr = g["droughts"][l]
    if dr["seconds"] >= 150:
        decisive += (f" {t.el(l, True)} estuvo {dr['seconds'] // 60}:{dr['seconds'] % 60:02d} minutos sin anotar"
                     f" ({qname(dr['from']['period'])}).")
    if "final_apretado" in tags:
        cl = [r for r in box[w] if r["clutch_pts"] > 0]
        if cl:
            c = max(cl, key=lambda r: r["clutch_pts"])
            decisive += f" En los minutos finales apareció {c['name']}, con {c['clutch_pts']} puntos en el tramo decisivo."
    if g["lead_changes"] >= 8:
        decisive += f" Fue un partido de alternativas: {g['lead_changes']} cambios de líder y {g['ties']} empates."

    # Protagonistas
    prot = []
    if w in best and best[w] is not mvp:
        prot.append(f"En {t.el(w)} también destacó {best[w]['name']} ({stat_line(best[w])}).")
    if l in best:
        bl = best[l]
        prot.append(rng.choice([
            f"En {t.el(l)}, el más destacado fue {bl['name']}, con {stat_line(bl)}.",
            f"Por parte {t.de(l)}, {bl['name']} sumó {stat_line(bl)}.",
        ]) if bl is not mvp else "")
    for s in "AB":
        for r in box[s]:
            if r is mvp:
                continue
            dd = sum(1 for k in ("PTS", "REB", "AST") if r[k] >= 10)
            if dd >= 2 and r is not best.get(s):
                prot.append(f"{r['name']} firmó un doble-doble ({r['PTS']} puntos y {r['REB']} rebotes).")
                break
    protagonists = " ".join(p for p in prot if p)

    keys = claves(g, t)
    summary = _one_liner(g, t, tags, mvp)

    return {
        "title": title,
        "summary": summary,
        "tags": tags,
        "paragraphs": [p for p in [lead, first_half, second_half + (" " + decisive if decisive else ""), protagonists] if p.strip()],
        "keys": keys,
    }


def _score_phrase(t, a, b, short=False):
    if a == b:
        return f"empate a {a}"
    s = "A" if a > b else "B"
    hi, lo = max(a, b), min(a, b)
    if short:
        return f"{t.el(s)} arriba ({hi}-{lo})"
    return f"mandaba {t.el(s)} ({hi}-{lo})"


def _one_liner(g, t, tags, mvp):
    w = g["winner"]
    l = "B" if w == "A" else "A"
    bits = []
    if "remontada" in tags:
        bits.append(f"Remontada desde -{g['biggest_lead'][l]['lead']}")
    elif "paliza" in tags:
        bits.append("Partido sin historia")
    elif "final_apretado" in tags:
        bits.append("Final apretado")
    elif "de_principio_a_fin" in tags:
        bits.append("Siempre por delante")
    if "prorroga" in tags:
        bits.append("Prórroga")
    st = g["best_stretch"].get(w)
    if st and st["net"] >= 10:
        p = st["from"]["period"]
        bits.append(f"Parcial {st['for']}-{st['against']} en el {qname(p)}" if p <= 4 else f"Parcial {st['for']}-{st['against']} en la prórroga")
    return " · ".join(bits)


def claves(g, t):
    """Detecta las 3-4 estadísticas que más explican el resultado."""
    w = g["winner"]
    l = "B" if w == "A" else "A"
    aw, al = g["adv"][w], g["adv"][l]
    bw, bl = g["team_box"][w], g["team_box"][l]
    cands = []

    def add(score, label, text):
        cands.append((score, label, text))

    d = bw["OREB"] - bl["OREB"]
    if abs(d) >= 4:
        s = w if d > 0 else l
        add(abs(d) * 1.4, "Rebote ofensivo",
            f"{t.el(s, True)} capturó {max(bw['OREB'], bl['OREB'])} rebotes ofensivos (por {min(bw['OREB'], bl['OREB'])}) "
            f"y sumó {g['adv'][s]['second_chance']} puntos de segunda oportunidad.")
    d = aw["pts_off_to"] - al["pts_off_to"]
    if abs(d) >= 5:
        s = w if d > 0 else l
        o = l if s == w else w
        add(abs(d) * 1.2, "Pérdidas",
            f"{t.el(s, True)} anotó {g['adv'][s]['pts_off_to']} puntos tras pérdida rival "
            f"({g['team_box'][o]['TOV']} pérdidas {t.de(o)}).")
    if aw["p3"] is not None and al["p3"] is not None:
        d = (aw["p3"] - al["p3"]) * 100
        if abs(d) >= 10:
            s = w if d > 0 else l
            b = g["team_box"][s]
            add(abs(d) * 0.6, "Triples",
                f"{t.el(s, True)} acertó {b['3PM']} de {b['3PA']} triples ({round(100 * b['3PM'] / b['3PA'])}%).")
    d = bw["FTA"] - bl["FTA"]
    if abs(d) >= 8:
        s = w if d > 0 else l
        add(abs(d) * 0.9, "Tiros libres",
            f"{t.el(s, True)} lanzó {max(bw['FTA'], bl['FTA'])} tiros libres por {min(bw['FTA'], bl['FTA'])} del rival.")
    d = aw["bench"] - al["bench"]
    if abs(d) >= 10:
        s = w if d > 0 else l
        add(abs(d) * 0.7, "Banquillo",
            f"El banquillo {t.de(s)} aportó {g['adv'][s]['bench']} puntos (por {min(aw['bench'], al['bench'])} del rival).")
    d = bw["AST"] - bl["AST"]
    if abs(d) >= 6:
        s = w if d > 0 else l
        add(abs(d) * 0.8, "Juego colectivo",
            f"{t.el(s, True)} repartió {max(bw['AST'], bl['AST'])} asistencias por {min(bw['AST'], bl['AST'])}.")
    d = aw["fast_break"] - al["fast_break"]
    if abs(d) >= 6:
        s = w if d > 0 else l
        add(abs(d) * 0.8, "Transición",
            f"{t.el(s, True)} hizo {g['adv'][s]['fast_break']} puntos en los primeros 8 segundos de posesión.")
    if aw["efg"] and al["efg"]:
        d = (aw["efg"] - al["efg"]) * 100
        if abs(d) >= 6:
            s = w if d > 0 else l
            add(abs(d) * 0.5, "Eficiencia",
                f"eFG% de {round(100 * g['adv'][s]['efg'])}% {t.de(s)} frente al "
                f"{round(100 * g['adv']['A' if s == 'B' else 'B']['efg'])}% del rival.")
    cands.sort(key=lambda c: -c[0])
    return [{"label": c[1], "text": c[2]} for c in cands[:4]]
