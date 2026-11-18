"""Genera partidos FICTICIOS en el mismo formato JSON que la API de la Euroliga.

Solo sirve para probar el diseño sin conexión. Los equipos son reales, pero los
jugadores y los resultados son inventados.
"""

import random

TEAMS = [
    ("MAD", "Real Madrid", "Movistar Arena"),
    ("BAR", "FC Barcelona", "Palau Blaugrana"),
    ("BAS", "Baskonia Vitoria-Gasteiz", "Buesa Arena"),
    ("PAM", "Valencia Basket", "Roig Arena"),
    ("OLY", "Olympiacos Piraeus", "Peace and Friendship Stadium"),
    ("PAN", "Panathinaikos Athens", "OAKA"),
    ("ULK", "Fenerbahce Beko Istanbul", "Ülker Sports Arena"),
    ("IST", "Anadolu Efes Istanbul", "Basketbol Gelişim Merkezi"),
    ("MCO", "AS Monaco", "Salle Gaston-Médecin"),
    ("PRS", "Paris Basketball", "Adidas Arena"),
    ("ASV", "LDLC ASVEL Villeurbanne", "LDLC Arena"),
    ("MUN", "FC Bayern Munich", "SAP Garden"),
    ("TEL", "Maccabi Tel Aviv", "Menora Mivtachim Arena"),
    ("HTA", "Hapoel Tel Aviv", "Menora Mivtachim Arena"),
    ("ZAL", "Zalgiris Kaunas", "Žalgirio Arena"),
    ("PAR", "Partizan Belgrade", "Belgrade Arena"),
    ("RED", "Crvena Zvezda Belgrade", "Belgrade Arena"),
    ("MIL", "EA7 Emporio Armani Milan", "Unipol Forum"),
    ("VIR", "Virtus Bologna", "Virtus Arena"),
    ("DUB", "Dubai Basketball", "Coca-Cola Arena"),
]

FIRST = ["MARCOS", "LUKA", "NIKOS", "JALEN", "MATEO", "DARIUS", "ALEX", "TOMAS", "KOSTAS", "ANDRES",
         "MILAN", "JORDAN", "PAU", "EMRE", "ISAIAH", "DEJAN", "HUGO", "VASILIS", "TYLER", "SERGI",
         "OMAR", "LORENZO", "MAODO", "NIKOLA", "JULIEN", "AARON", "PEDRO", "MARKUS", "IGNAS", "KEVIN"]
LAST = ["NAVARRO", "PETROVIC", "PAPADAKIS", "WILLIAMS", "SANTOS", "MORRIS", "RIVERA", "SABONIS", "KALAITZIS",
        "GARCIA", "JOVANOVIC", "BROWN", "MARTIN", "YILMAZ", "HAYES", "MARKOVIC", "BERTRAND", "SPANOULIS",
        "JOHNSON", "LLULL", "DIALLO", "ROSSI", "NDIAYE", "MILOSEVIC", "DUPONT", "CARTER", "ORTEGA",
        "SCHMIDT", "KAZYS", "WHITE", "OKAFOR", "BIANCHI", "LOPEZ", "IVANOV", "FOSTER", "MOREAU"]


def make_roster(rng, code):
    used = set()
    roster = []
    nums = rng.sample(range(0, 56), 12)
    for i in range(12):
        while True:
            n = f"{rng.choice(LAST)}, {rng.choice(FIRST)}"
            if n not in used:
                used.add(n)
                break
        roster.append({
            "pid": f"P9{code}{i:02d}",
            "name": n,
            "num": str(nums[i]),
            "usage": (2.2 if i < 2 else 1.6 if i < 5 else 1.0 if i < 9 else 0.5) * rng.uniform(0.7, 1.3),
            "shoot": rng.uniform(-0.05, 0.06),
            "three": rng.uniform(0.15, 0.55),
            "reb": (1.8 if i in (3, 4, 8) else 1.0) * rng.uniform(0.7, 1.3),
            "minutes": (30 if i < 5 else 18 if i < 9 else 6) * rng.uniform(0.85, 1.15),
        })
    return roster


class Game:
    def __init__(self, rng, home, away):
        self.rng = rng
        self.t = {"A": home, "B": away}
        self.rosters = {"A": make_roster(rng, home[0]), "B": make_roster(rng, away[0])}
        self.strength = {"A": rng.uniform(-0.03, 0.035) + 0.01, "B": rng.uniform(-0.03, 0.035)}
        self.momentum = {"A": 0.0, "B": 0.0}
        self.score = {"A": 0, "B": 0}
        self.n = 1
        self.rows = []
        self.on = {}
        self.stint = {}
        self.played = {}

    # ---- emisión de jugadas en formato API
    def emit(self, typ, side=None, pl=None, rem=None, info="", pts=False):
        code, name, _ = self.t[side] if side else ("", None, "")
        self.n += 1
        row = {
            "TYPE": 0, "NUMBEROFPLAY": self.n,
            "CODETEAM": (code or "").ljust(10), "PLAYER_ID": (pl["pid"] if pl else "").ljust(10),
            "PLAYTYPE": typ, "PLAYER": pl["name"] if pl else None, "TEAM": name,
            "DORSAL": pl["num"] if pl else None, "MINUTE": self.minute,
            "MARKERTIME": "" if typ == "BP" else f"{int(rem) // 60:02d}:{int(rem) % 60:02d}",
            "POINTS_A": self.score["A"] if pts else None, "POINTS_B": self.score["B"] if pts else None,
            "COMMENT": "", "PLAYINFO": info,
        }
        self.cur.append(row)

    def pick(self, side, weight="usage", exclude=None):
        cands = [p for p in self.on[side] if p is not exclude]
        return self.rng.choices(cands, [p[weight] for p in cands])[0]

    def subs(self, rem, force=False):
        for s in "AB":
            for p in list(self.on[s]):
                limit = 60 * self.rng.uniform(4, 8) * (p["minutes"] / 30)
                if force or self.stint[p["pid"]] > limit:
                    bench = [b for b in self.rosters[s] if b not in self.on[s]]
                    bench.sort(key=lambda b: self.played.get(b["pid"], 0) / b["minutes"])
                    if not bench or self.rng.random() < 0.4:
                        continue
                    new = bench[0]
                    self.emit("OUT", s, p, rem, "Out")
                    self.emit("IN", s, new, rem, "In")
                    self.on[s].remove(p)
                    self.on[s].append(new)
                    self.stint[new["pid"]] = 0

    def tick(self, dt):
        for s in "AB":
            for p in self.on[s]:
                self.stint[p["pid"]] = self.stint.get(p["pid"], 0) + dt
                self.played[p["pid"]] = self.played.get(p["pid"], 0) + dt

    def score_pts(self, side, pts):
        self.score[side] += pts
        o = "B" if side == "A" else "A"
        self.momentum[side] = min(0.06, self.momentum[side] + 0.008 * pts)
        self.momentum[o] = max(-0.04, self.momentum[o] - 0.004 * pts)

    def free_throws(self, side, shooter, k, rem):
        for i in range(k):
            if self.rng.random() < 0.78 + shooter["shoot"]:
                self.score_pts(side, 1)
                self.emit("FTM", side, shooter, rem, "Free Throw In", pts=True)
            else:
                self.emit("FTA", side, shooter, rem, "Free Throw Missed")
                if i == k - 1:
                    return "miss"
        return "made"

    def possession(self, off, rem):
        rng = self.rng
        de = "B" if off == "A" else "A"
        adj = self.strength[off] - self.strength[de] * 0.5 + self.momentum[off]
        adj += 0.0025 * max(0, self.score[de] - self.score[off])
        for s in "AB":
            self.momentum[s] *= 0.88
        dur = rng.uniform(10, 24)
        rem2 = max(0, rem - dur)
        self.tick(rem - rem2)
        rem = rem2
        # pérdida
        if rng.random() < 0.13 - adj * 0.3:
            pl = self.pick(off)
            if rng.random() < 0.55:
                self.emit("TO", off, pl, rem, "Turnover")
                self.emit("ST", de, self.pick(de), rem, "Steal")
            elif rng.random() < 0.3:
                self.emit("OF", off, pl, rem, "Offensive Foul")
                self.emit("TO", off, pl, rem, "Turnover")
            else:
                self.emit("TO", off, pl, rem, "Turnover")
            return rem, "dead"
        if rng.random() < 0.09:
            f = self.pick(de, "reb")
            v = self.pick(off)
            self.emit("CM", de, f, rem, "Foul")
            self.emit("RV", off, v, rem, "Foul Drawn")
            if rng.random() < 0.35:
                self.free_throws(off, v, 2, rem)
                return rem, "dead"
        for attempt in range(4):
            shooter = self.pick(off)
            three = rng.random() < shooter["three"] * 0.85
            pct = (0.345 if three else 0.52) + shooter["shoot"] + adj
            fouled = rng.random() < (0.03 if three else 0.12)
            made = rng.random() < (pct - (0.15 if fouled else 0))
            if made:
                pts = 3 if three else 2
                self.score_pts(off, pts)
                self.emit("3FGM" if three else "2FGM", off, shooter, rem,
                          "Three Pointer" if three else "Two Pointer", pts=True)
                if rng.random() < 0.62:
                    self.emit("AS", off, self.pick(off, exclude=shooter), rem, "Assist")
                if fouled:
                    f = self.pick(de, "reb")
                    self.emit("CM", de, f, rem, "Foul")
                    self.emit("RV", off, shooter, rem, "Foul Drawn")
                    self.free_throws(off, shooter, 1, rem)
                return rem, "made"
            if fouled:
                f = self.pick(de, "reb")
                self.emit("CM", de, f, rem, "Foul")
                self.emit("RV", off, shooter, rem, "Foul Drawn")
                if self.free_throws(off, shooter, 3 if three else 2, rem) == "made":
                    return rem, "made"
            else:
                self.emit("3FGA" if three else "2FGA", off, shooter, rem,
                          "Missed Three Pointer" if three else "Missed Two Pointer")
                if not three and rng.random() < 0.09:
                    self.emit("FV", de, self.pick(de, "reb"), rem, "Block")
                    self.emit("AG", off, shooter, rem, "Shot Rejected")
            if rng.random() < 0.27 + adj:
                self.emit("O", off, self.pick(off, "reb"), rem, "Offensive Rebound")
                d2 = rng.uniform(2, 9)
                rem2 = max(0, rem - d2)
                self.tick(rem - rem2)
                rem = rem2
                continue
            if rng.random() < 0.05:
                self.emit("D", de, None, rem, "Defensive Rebound")
            else:
                self.emit("D", de, self.pick(de, "reb"), rem, "Defensive Rebound")
            return rem, "dreb"
        return rem, "dead"

    def play_period(self, per):
        length = 600 if per <= 4 else 300
        self.minute = 1 + 10 * min(per - 1, 4) + 5 * max(per - 5, 0)
        self.emit("BP", rem=length, info="Begin Period")
        rem = length
        if per == 1:
            for s in "AB":
                self.on[s] = self.rosters[s][:5]
                for p in self.on[s]:
                    self.stint[p["pid"]] = 0
            self.emit("JB", "A", None, length - 1, "Jump Ball")
            off = "A" if self.rng.random() < 0.5 else "B"
            self.first_off = off
        else:
            if per == 3:
                for s in "AB":
                    for p in list(self.on[s]):
                        if p not in self.rosters[s][:5]:
                            new = [x for x in self.rosters[s][:5] if x not in self.on[s]][0]
                            self.emit("OUT", s, p, rem, "Out")
                            self.emit("IN", s, new, rem, "In")
                            self.on[s].remove(p)
                            self.on[s].append(new)
                            self.stint[new["pid"]] = 0
            off = self.first_off if per in (4,) else ("B" if self.first_off == "A" else "A")
        while rem > 0:
            elapsed = length - rem
            self.minute = 1 + 10 * min(per - 1, 4) + 5 * max(per - 5, 0) + int(elapsed // 60)
            rem, how = self.possession(off, rem)
            if rem <= 0:
                break
            if how == "dead" and self.rng.random() < 0.5:
                self.subs(rem)
            if self.rng.random() < 0.02:
                self.emit("TOUT", off, None, rem, "Time Out")
                self.subs(rem)
            off = "B" if off == "A" else "A"
        self.emit("EP", rem=0, info="End Period")

    def run(self):
        out = {"Live": False, "TeamA": self.t["A"][1], "TeamB": self.t["B"][1],
               "CodeTeamA": self.t["A"][0], "CodeTeamB": self.t["B"][0], "ActualQuarter": 4}
        keys = ["FirstQuarter", "SecondQuarter", "ThirdQuarter", "ForthQuarter"]
        for i, k in enumerate(keys, 1):
            self.cur = []
            self.play_period(i)
            out[k] = self.cur
        ot = []
        per = 5
        while self.score["A"] == self.score["B"]:
            self.cur = []
            self.play_period(per)
            ot.extend(self.cur)
            per += 1
        if ot:
            out["ExtraTime"] = ot
        last = out["ExtraTime"] if ot else out["ForthQuarter"]
        self.cur = last
        self.emit("EG", rem=0, info="End Game")
        return out


def simulate_round(seed=11, round_number=11, dates=("17/11/2026", "18/11/2026")):
    rng = random.Random(seed)
    teams = TEAMS[:]
    rng.shuffle(teams)
    games = []
    for i in range(10):
        home, away = teams[2 * i], teams[2 * i + 1]
        g = Game(random.Random(seed * 100 + i), home, away)
        pbp = g.run()
        header = {"Round": str(round_number), "Date": dates[0] if i < 5 else dates[1],
                  "Hour": ["18:30", "19:00", "20:00", "20:30", "20:45"][i % 5], "Stadium": home[2],
                  "TeamA": home[1], "TeamB": away[1], "CodeTeamA": home[0], "CodeTeamB": away[0],
                  "ScoreA": str(g.score["A"]), "ScoreB": str(g.score["B"]), "Live": False}
        games.append((100 + i + 10 * round_number, pbp, header))
    return games
