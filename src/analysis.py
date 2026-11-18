"""Análisis completo de un partido a partir del play-by-play de la Euroliga.

Entrada: el JSON de https://live.euroleague.net/api/PlayByPlay (y opcionalmente
el de /api/Header). Salida: un diccionario con todo lo necesario para la web:
box score reconstruido, minutos y +/- por seguimiento de cambios, rachas,
ventajas, sequías, clutch, quintetos, red de asistencias y estadística avanzada.
"""

from collections import defaultdict

PERIOD_KEYS = [
    ("FirstQuarter", 1),
    ("SecondQuarter", 2),
    ("ThirdQuarter", 3),
    ("ForthQuarter", 4),   # así viene (con errata) en la API
    ("FourthQuarter", 4),
    ("ExtraTime", 5),
]

TYPE_ALIASES = {"2PM": "2FGM", "2PA": "2FGA", "3PM": "3FGM", "3PA": "3FGA"}
POINTS = {"2FGM": 2, "3FGM": 3, "FTM": 1}
FG_MADE = {"2FGM", "3FGM"}
PLAYER_ACTIONS = {
    "2FGM", "2FGA", "3FGM", "3FGA", "FTM", "FTA", "O", "D", "AS", "ST", "TO",
    "FV", "AG", "CM", "CMU", "CMD", "CMT", "CMTI", "OF", "RV", "OUT",
}
OWN_BALL = {"2FGM", "2FGA", "3FGM", "3FGA", "FTM", "FTA", "TO", "O", "OF"}
FOULS = {"CM", "CMU", "CMD", "CMT", "CMTI", "OF"}


def period_length(p):
    return 600 if p <= 4 else 300


def period_start(p):
    return 600 * min(p - 1, 4) + 300 * max(p - 5, 0)


def fmt_clock(rem):
    rem = max(0, int(round(rem)))
    return f"{rem // 60:02d}:{rem % 60:02d}"


def period_label(p):
    return f"{p}C" if p <= 4 else (f"PR{p - 4}" if p > 5 else "PR")


def nice_name(raw):
    if not raw:
        return ""
    raw = raw.strip()
    if "," in raw:
        last, first = [x.strip() for x in raw.split(",", 1)]
        raw = f"{first} {last}"
    return " ".join(w.capitalize() if w.isupper() or w.islower() else w for w in raw.split())


def _clock_to_rem(s):
    try:
        m, sec = s.strip().split(":")
        return int(m) * 60 + int(sec)
    except Exception:
        return None


# --------------------------------------------------------------------------
# 1. Normalización
# --------------------------------------------------------------------------

def normalize(pbp):
    code_a = (pbp.get("CodeTeamA") or "").strip()
    code_b = (pbp.get("CodeTeamB") or "").strip()
    plays = []
    for key, base_p in PERIOD_KEYS:
        rows = pbp.get(key) or []
        p = base_p
        seen_bp = False
        last_rem = None
        for r in rows:
            typ = (r.get("PLAYTYPE") or "").strip()
            typ = TYPE_ALIASES.get(typ, typ)
            if key == "ExtraTime" and typ == "BP":
                if seen_bp:
                    p += 1
                seen_bp = True
                last_rem = None
            plen = period_length(p)
            rem = _clock_to_rem(r.get("MARKERTIME") or "")
            if typ == "BP":
                rem = plen
            elif typ in ("EP", "EG"):
                rem = 0
            elif rem is None:
                rem = last_rem if last_rem is not None else plen
            rem = min(rem, plen)
            last_rem = rem
            team = (r.get("CODETEAM") or "").strip()
            side = "A" if team == code_a and team else ("B" if team == code_b and team else None)
            plays.append({
                "n": r.get("NUMBEROFPLAY"),
                "period": p,
                "rem": rem,
                "t": period_start(p) + (plen - rem),
                "team": team,
                "side": side,
                "pid": (r.get("PLAYER_ID") or "").strip(),
                "player": nice_name(r.get("PLAYER")),
                "num": (r.get("DORSAL") or "").strip(),
                "type": typ,
                "info": (r.get("PLAYINFO") or "").strip(),
            })
    return code_a, code_b, plays


# --------------------------------------------------------------------------
# 2. Análisis
# --------------------------------------------------------------------------

def _empty_player():
    return defaultdict(float)


def analyze(pbp, header=None, game_code=None, season=None):
    header = header or {}
    code_a, code_b, plays = normalize(pbp)
    if not plays:
        raise ValueError("Play-by-play vacío")
    names = {"A": (pbp.get("TeamA") or code_a).strip(), "B": (pbp.get("TeamB") or code_b).strip()}
    codes = {"A": code_a, "B": code_b}
    other = {"A": "B", "B": "A"}
    n_periods = max(p["period"] for p in plays)
    game_seconds = period_start(n_periods) + period_length(n_periods)

    # ---- Marcador acumulado en cada jugada
    sc = {"A": 0, "B": 0}
    for p in plays:
        pts = POINTS.get(p["type"], 0)
        if pts and p["side"]:
            sc[p["side"]] += pts
        p["pts"] = pts if p["side"] else 0
        p["sA"], p["sB"] = sc["A"], sc["B"]
    final = dict(sc)

    # ---- Jugadores (box score reconstruido)
    players = {}          # pid -> info
    stats = defaultdict(_empty_player)
    team_extra = {"A": defaultdict(float), "B": defaultdict(float)}
    q_points = defaultdict(lambda: defaultdict(int))  # pid -> period -> pts
    for s, lst in (pbp.get("Rosters") or {}).items():
        for r in lst:
            players.setdefault(r["pid"], {"pid": r["pid"], "name": nice_name(r.get("name")), "num": str(r.get("num", "")), "side": s})
    for p in plays:
        s, pid, t = p["side"], p["pid"], p["type"]
        if not s:
            continue
        if pid:
            if pid not in players:
                players[pid] = {"pid": pid, "name": p["player"], "num": p["num"], "side": s}
            st = stats[pid]
        else:
            st = team_extra[s]
        if t == "2FGM": st["2PM"] += 1; st["2PA"] += 1
        elif t == "2FGA": st["2PA"] += 1
        elif t == "3FGM": st["3PM"] += 1; st["3PA"] += 1
        elif t == "3FGA": st["3PA"] += 1
        elif t == "FTM": st["FTM"] += 1; st["FTA"] += 1
        elif t == "FTA": st["FTA"] += 1
        elif t == "O": st["OREB"] += 1
        elif t == "D": st["DREB"] += 1
        elif t == "AS": st["AST"] += 1
        elif t == "ST": st["STL"] += 1
        elif t == "TO": st["TOV"] += 1
        elif t == "FV": st["BLK"] += 1
        elif t == "AG": st["BLKA"] += 1
        elif t in FOULS: st["PF"] += 1
        elif t == "RV": st["FD"] += 1
        if p["pts"]:
            st["PTS"] += p["pts"]
            if pid:
                q_points[pid][p["period"]] += p["pts"]

    # ---- Quintetos en pista, minutos y +/-
    by_period = defaultdict(list)
    for p in plays:
        by_period[p["period"]].append(p)

    def infer_starters(pp, side, carried):
        first = {}
        for p in pp:
            if p["side"] != side or not p["pid"] or p["pid"] not in players:
                continue
            if p["type"] not in PLAYER_ACTIONS and p["type"] != "IN":
                continue
            if p["pid"] not in first:
                first[p["pid"]] = "in" if p["type"] == "IN" else "other"
        starters = [pid for pid, k in first.items() if k == "other"][:5]
        for pid in carried:
            if len(starters) >= 5:
                break
            if pid not in starters and first.get(pid) != "in":
                starters.append(pid)
        return starters

    seconds = defaultdict(float)
    plus_minus = defaultdict(int)
    starters_g = {"A": [], "B": []}
    lineups = {"A": defaultdict(lambda: {"sec": 0.0, "pf": 0, "pa": 0}),
               "B": defaultdict(lambda: {"sec": 0.0, "pf": 0, "pa": 0})}
    on = {"A": [], "B": []}
    for per in sorted(by_period):
        pp = by_period[per]
        given = (pbp.get("Lineups") or {}).get(str(per)) or (pbp.get("Lineups") or {}).get(per)
        for s in "AB":
            on[s] = list(given[s]) if given else infer_starters(pp, s, on[s])
            if per == 1:
                starters_g[s] = list(on[s])
        last_t = period_start(per)
        for p in pp:
            dt = p["t"] - last_t
            if dt > 0:
                for s in "AB":
                    for pid in on[s]:
                        seconds[pid] += dt
                    if len(on[s]) == 5:
                        lineups[s][tuple(sorted(on[s]))]["sec"] += dt
                last_t = p["t"]
            s = p["side"]
            if p["type"] == "IN" and s and p["pid"] in players and p["pid"] not in on[s]:
                on[s].append(p["pid"])
            elif p["type"] == "OUT" and s and p["pid"] in on[s]:
                on[s].remove(p["pid"])
            if p["pts"] and s:
                o = other[s]
                for pid in on[s]:
                    plus_minus[pid] += p["pts"]
                for pid in on[o]:
                    plus_minus[pid] -= p["pts"]
                if len(on[s]) == 5:
                    lineups[s][tuple(sorted(on[s]))]["pf"] += p["pts"]
                if len(on[o]) == 5:
                    lineups[o][tuple(sorted(on[o]))]["pa"] += p["pts"]
        end_t = period_start(per) + period_length(per)
        if end_t > last_t:
            for s in "AB":
                for pid in on[s]:
                    seconds[pid] += end_t - last_t
                if len(on[s]) == 5:
                    lineups[s][tuple(sorted(on[s]))]["sec"] += end_t - last_t

    # ---- Posesiones por jugada: origen, segundas opciones, contraataque
    poss = {"A": 0, "B": 0}
    pts_off_to = {"A": 0, "B": 0}
    second_ch = {"A": 0, "B": 0}
    fast = {"A": 0, "B": 0}
    owner, origin, start_t, oreb, ended = None, None, 0, False, False
    pending = ("START", 0)
    last_scoring_side = None
    for p in plays:
        s, t = p["side"], p["type"]
        if t == "BP":
            owner, pending, ended = None, ("START", p["t"]), False
            continue
        if not s:
            continue
        if t == "D":
            owner, origin, start_t, oreb, ended = s, "REB", p["t"], False, False
            poss[s] += 1
            pending = None
            continue
        if t not in OWN_BALL:
            continue
        new = owner != s or (ended and t not in ("FTM", "FTA"))
        if new:
            if pending:
                origin, start_t = pending
            else:
                origin, start_t = ("MADE" if last_scoring_side == other[s] else "OTHER"), p["t"]
            owner, oreb, ended, pending = s, False, False, None
            poss[s] += 1
        if t == "O":
            oreb = True
        if p["pts"]:
            last_scoring_side = s
            if origin == "TO":
                pts_off_to[s] += p["pts"]
            if oreb:
                second_ch[s] += p["pts"]
            if origin in ("TO", "REB") and p["t"] - start_t <= 8:
                fast[s] += p["pts"]
        if t == "TO" or t == "OF":
            ended, pending = True, ("TO", p["t"])
        elif t in FG_MADE:
            ended, pending = True, ("MADE", p["t"])

    # ---- Eventos de anotación, ventajas, rachas
    scoring = [p for p in plays if p["pts"] and p["side"]]
    timeline = [{"t": 0, "d": 0, "a": 0, "b": 0}]
    for p in scoring:
        timeline.append({"t": p["t"], "d": p["sA"] - p["sB"], "a": p["sA"], "b": p["sB"]})
    timeline.append({"t": game_seconds, "d": final["A"] - final["B"], "a": final["A"], "b": final["B"]})

    lead_changes, ties = 0, 0
    last_leader = None
    biggest = {"A": {"lead": 0}, "B": {"lead": 0}}
    time_leading = {"A": 0.0, "B": 0.0, "tie": 0.0}
    prev_t, prev_d = 0, 0
    lead_change_events = []
    for p in scoring:
        d = p["sA"] - p["sB"]
        span = p["t"] - prev_t
        time_leading["A" if prev_d > 0 else "B" if prev_d < 0 else "tie"] += span
        prev_t = p["t"]
        leader = "A" if d > 0 else "B" if d < 0 else None
        if leader and last_leader and leader != last_leader:
            lead_changes += 1
            lead_change_events.append(_moment(p))
        if d == 0 and prev_d != 0:
            ties += 1
        if leader:
            last_leader = leader
            if abs(d) > biggest[leader]["lead"]:
                biggest[leader] = {"lead": abs(d), **_moment(p)}
        prev_d = d
    time_leading["A" if prev_d > 0 else "B" if prev_d < 0 else "tie"] += game_seconds - prev_t

    # Rachas X-0
    runs = []
    cur = None
    for i, p in enumerate(scoring):
        if cur and cur["side"] == p["side"]:
            cur["pts"] += p["pts"]
            cur["end"] = _moment(p)
        else:
            if cur and cur["pts"] >= 7:
                runs.append(cur)
            prev = scoring[i - 1] if i else None
            cur = {"side": p["side"], "pts": p["pts"],
                   "start": _moment(prev) if prev else {"t": 0, "period": 1, "clock": "10:00", "a": 0, "b": 0},
                   "end": _moment(p)}
    if cur and cur["pts"] >= 7:
        runs.append(cur)
    runs.sort(key=lambda r: -r["pts"])

    # Mejor tramo de 5 minutos (parcial tipo 15-2)
    best_stretch = {}
    for s in "AB":
        best = None
        for i in range(len(timeline)):
            for j in range(i + 1, len(timeline)):
                if timeline[j]["t"] - timeline[i]["t"] > 300:
                    break
                fa = timeline[j]["a"] - timeline[i]["a"]
                fb = timeline[j]["b"] - timeline[i]["b"]
                net = (fa - fb) if s == "A" else (fb - fa)
                if best is None or net > best["net"]:
                    best = {"net": net, "for": fa if s == "A" else fb, "against": fb if s == "A" else fa,
                            "t0": timeline[i]["t"], "t1": timeline[j]["t"],
                            "score0": [timeline[i]["a"], timeline[i]["b"]],
                            "score1": [timeline[j]["a"], timeline[j]["b"]]}
        if best:
            best["from"] = _t_label(best["t0"])
            best["to"] = _t_label(best["t1"])
        best_stretch[s] = best

    # Sequías
    droughts = {}
    for s in "AB":
        ts = [0] + [p["t"] for p in scoring if p["side"] == s] + [game_seconds]
        best = (0, 0, 0)
        for x, y in zip(ts, ts[1:]):
            if y - x > best[0]:
                best = (y - x, x, y)
        droughts[s] = {"seconds": best[0], "from": _t_label(best[1]), "to": _t_label(best[2]),
                       "t0": best[1], "t1": best[2]}

    # Clutch: últimos 5' del 4C y prórrogas con diferencia <= 5
    clutch_pts = defaultdict(int)
    clutch_team = {"A": 0, "B": 0}
    clutch = False
    for p in plays:
        in_window = (p["period"] == 4 and p["rem"] <= 300) or p["period"] > 4
        if not in_window:
            continue
        margin_before = abs((p["sA"] - p["sB"]) - ((p["pts"] if p["side"] == "A" else -p["pts"]) if p["pts"] else 0))
        if margin_before <= 5:
            clutch = True
            if p["pts"] and p["side"]:
                clutch_team[p["side"]] += p["pts"]
                if p["pid"]:
                    clutch_pts[p["pid"]] += p["pts"]

    # Red de asistencias
    assist_pairs = defaultdict(int)
    for i, p in enumerate(plays):
        if p["type"] != "AS" or not p["pid"]:
            continue
        for q in reversed(plays[max(0, i - 4):i]):
            if q["side"] == p["side"] and q["type"] in FG_MADE and q["pid"]:
                assist_pairs[(p["pid"], q["pid"])] += 1
                break

    # Puntos por cuarto
    q_team = {s: [0] * n_periods for s in "AB"}
    for p in scoring:
        q_team[p["side"]][p["period"] - 1] += p["pts"]

    # ---- Construcción de tablas
    def finish(st):
        st = dict(st)
        for k in ("2PM", "2PA", "3PM", "3PA", "FTM", "FTA", "OREB", "DREB", "AST", "STL", "TOV",
                  "BLK", "BLKA", "PF", "FD", "PTS"):
            st[k] = int(st.get(k, 0))
        st["FGM"] = st["2PM"] + st["3PM"]
        st["FGA"] = st["2PA"] + st["3PA"]
        st["REB"] = st["OREB"] + st["DREB"]
        st["PIR"] = (st["PTS"] + st["REB"] + st["AST"] + st["STL"] + st["BLK"] + st["FD"]
                     - (st["FGA"] - st["FGM"]) - (st["FTA"] - st["FTM"]) - st["TOV"] - st["BLKA"] - st["PF"])
        tsa = st["FGA"] + 0.44 * st["FTA"]
        st["TS"] = round(st["PTS"] / (2 * tsa), 3) if tsa else None
        st["EFG"] = round((st["FGM"] + 0.5 * st["3PM"]) / st["FGA"], 3) if st["FGA"] else None
        return st

    team_box = {}
    for s in "AB":
        tot = defaultdict(float)
        for pid, info in players.items():
            if info["side"] == s:
                for k, v in stats[pid].items():
                    tot[k] += v
        for k, v in team_extra[s].items():
            tot[k] += v
        team_box[s] = finish(tot)

    game_min = game_seconds / 60
    box = {"A": [], "B": []}
    for pid, info in players.items():
        st = finish(stats[pid])
        s = info["side"]
        mp = seconds[pid] / 60
        tb = team_box[s]
        team_use = tb["FGA"] + 0.44 * tb["FTA"] + tb["TOV"]
        use = st["FGA"] + 0.44 * st["FTA"] + st["TOV"]
        st["USG"] = round(100 * use * (game_min) / (mp * team_use), 1) if mp > 0 and team_use else None
        team_diff = (final[s] - final[other[s]])
        on_pm = plus_minus[pid]
        row = {**info, **st, "SEC": round(seconds[pid]), "MIN": _mmss(seconds[pid]),
               "PM": on_pm, "OFF_PM": team_diff - on_pm,
               "starter": pid in starters_g[s],
               "q_pts": [q_points[pid].get(k, 0) for k in range(1, n_periods + 1)],
               "clutch_pts": clutch_pts.get(pid, 0)}
        if row["SEC"] == 0 and not any(st[k] for k in ("PTS", "REB", "AST", "PF", "TOV", "FGA", "FTA")):
            continue
        box[s].append(row)
    for s in "AB":
        box[s].sort(key=lambda r: (not r["starter"], -r["SEC"]))

    # Avanzada de equipo
    adv = {}
    est = {}
    for s in "AB":
        tb = team_box[s]
        est[s] = tb["FGA"] - tb["OREB"] + tb["TOV"] + 0.44 * tb["FTA"]
    avg_poss = (est["A"] + est["B"]) / 2
    for s in "AB":
        tb, ob = team_box[s], team_box[other[s]]
        bench = sum(r["PTS"] for r in box[s] if not r["starter"])
        adv[s] = {
            "poss": round(est[s], 1),
            "poss_pbp": poss[s],
            "pace": round(avg_poss * 40 / game_min, 1),
            "ortg": round(100 * final[s] / avg_poss, 1) if avg_poss else None,
            "drtg": round(100 * final[other[s]] / avg_poss, 1) if avg_poss else None,
            "efg": tb["EFG"], "ts": tb["TS"],
            "tov_pct": _r(tb["TOV"] / (tb["FGA"] + 0.44 * tb["FTA"] + tb["TOV"])) if tb["FGA"] else None,
            "orb_pct": _r(tb["OREB"] / (tb["OREB"] + ob["DREB"])) if (tb["OREB"] + ob["DREB"]) else None,
            "drb_pct": _r(tb["DREB"] / (tb["DREB"] + ob["OREB"])) if (tb["DREB"] + ob["OREB"]) else None,
            "ftr": _r(tb["FTA"] / tb["FGA"]) if tb["FGA"] else None,
            "ast_pct": _r(tb["AST"] / tb["FGM"]) if tb["FGM"] else None,
            "three_rate": _r(tb["3PA"] / tb["FGA"]) if tb["FGA"] else None,
            "p2": _r(tb["2PM"] / tb["2PA"]) if tb["2PA"] else None,
            "p3": _r(tb["3PM"] / tb["3PA"]) if tb["3PA"] else None,
            "pft": _r(tb["FTM"] / tb["FTA"]) if tb["FTA"] else None,
            "pts_off_to": pts_off_to[s],
            "second_chance": second_ch[s],
            "fast_break": fast[s],
            "bench": bench,
            "paint_proxy": tb["2PM"] * 2,
            "clutch": clutch_team[s],
            "biggest_lead": biggest[s].get("lead", 0),
            "time_leading": round(time_leading[s]),
        }
        adv[s]["net"] = round(adv[s]["ortg"] - adv[s]["drtg"], 1) if adv[s]["ortg"] is not None else None

    # Quintetos
    pname = {pid: info["name"] for pid, info in players.items()}
    lineup_out = {}
    for s in "AB":
        rows = []
        for key, v in lineups[s].items():
            if v["sec"] < 60:
                continue
            rows.append({"players": [pname.get(x, x) for x in key], "sec": round(v["sec"]),
                         "min": _mmss(v["sec"]), "pf": v["pf"], "pa": v["pa"], "pm": v["pf"] - v["pa"]})
        rows.sort(key=lambda r: -r["sec"])
        lineup_out[s] = rows[:6]

    assists = sorted(
        [{"from": pname.get(a, a), "to": pname.get(b, b), "n": n, "side": players[a]["side"]}
         for (a, b), n in assist_pairs.items() if a in players],
        key=lambda r: -r["n"])[:8]

    all_rows = box["A"] + box["B"]
    winner = "A" if final["A"] > final["B"] else "B"
    mvp = max(all_rows, key=lambda r: (r["PIR"], r["side"] == winner, r["PTS"])) if all_rows else None

    pbp_out = [{"period": p["period"], "clock": fmt_clock(p["rem"]), "side": p["side"],
                "player": p["player"], "type": p["type"], "info": p["info"],
                "a": p["sA"], "b": p["sB"], "pts": p["pts"]}
               for p in plays]

    return {
        "season": season,
        "game_code": game_code,
        "round": header.get("Round") or header.get("round"),
        "date": header.get("Date") or header.get("date"),
        "hour": header.get("Hour") or header.get("hour"),
        "venue": header.get("Stadium") or header.get("stadium"),
        "teams": {s: {"code": codes[s], "name": names[s], "short": pbp.get(f"ShortTeam{s}")} for s in "AB"},
        "us": header.get("Us"),
        "score": final,
        "winner": winner,
        "periods": n_periods,
        "game_seconds": game_seconds,
        "quarters": q_team,
        "box": box,
        "team_box": team_box,
        "adv": adv,
        "timeline": timeline,
        "lead_changes": lead_changes,
        "ties": ties,
        "lead_change_events": lead_change_events,
        "biggest_lead": biggest,
        "runs": runs[:8],
        "best_stretch": best_stretch,
        "droughts": droughts,
        "clutch": clutch,
        "lineups": lineup_out,
        "assists": assists,
        "mvp": mvp,
        "pbp": pbp_out,
    }


def _r(x):
    return round(x, 3)


def _mmss(sec):
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def _t_label(t):
    """Segundo absoluto -> 'min. 23' estilo crónica y etiqueta de cuarto."""
    p = 1
    while p < 20 and t > period_start(p) + period_length(p):
        p += 1
    rem = period_start(p) + period_length(p) - t
    return {"period": p, "clock": fmt_clock(rem), "minute": int(t // 60) + (1 if t % 60 else 0) or 1}


def _moment(p):
    return {"t": p["t"], "period": p["period"], "clock": fmt_clock(p["rem"]), "a": p["sA"], "b": p["sB"],
            "player": p["player"], "minute": int(p["t"] // 60) + (1 if p["t"] % 60 else 0) or 1}
