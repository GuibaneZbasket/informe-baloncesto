"""Descarga de partidos de la Euroliga desde su API pública (la que usa su web).

Endpoints:
  https://live.euroleague.net/api/Header?gamecode=N&seasoncode=E2026
  https://live.euroleague.net/api/PlayByPlay?gamecode=N&seasoncode=E2026

Los códigos de partido son correlativos. Recorremos desde el 1 saltando los que
ya tenemos guardados y paramos tras varios partidos seguidos sin jugar.
"""

import json
import os
import time
import urllib.error
import urllib.request

BASE = "https://live.euroleague.net/api"
UA = {"User-Agent": "Mozilla/5.0 (informe-baloncesto; uso personal)", "Accept": "application/json"}


def get_json(endpoint, game_code, season, retries=3):
    url = f"{BASE}/{endpoint}?gamecode={game_code}&seasoncode={season}"
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8")
                return json.loads(body) if body.strip() else None
        except urllib.error.HTTPError as e:
            if e.code in (404, 500):
                return None
            time.sleep(2 * (i + 1))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(2 * (i + 1))
    return None


def is_finished(header, pbp):
    if not header or not pbp:
        return False
    if header.get("Live") in (True, "true", "True") or pbp.get("Live") in (True, "true"):
        return False
    for key in ("ExtraTime", "ForthQuarter", "FourthQuarter"):
        for row in pbp.get(key) or []:
            if (row.get("PLAYTYPE") or "").strip() == "EG":
                return True
    # algunos partidos antiguos no traen EG: aceptamos si hay 4 cuartos con jugadas
    return bool(pbp.get("ForthQuarter")) and not pbp.get("Live")


def sync(season, raw_dir, max_gap=12, max_code=400, log=print):
    """Descarga los partidos terminados que aún no tengamos. Devuelve los nuevos."""
    os.makedirs(raw_dir, exist_ok=True)
    have = {int(f.split("_")[0]) for f in os.listdir(raw_dir) if f.endswith("_pbp.json")}
    new = []
    gap = 0
    for code in range(1, max_code + 1):
        if code in have:
            gap = 0
            continue
        header = get_json("Header", code, season)
        if not header or not str(header.get("ScoreA") or "").strip():
            gap += 1
            if gap >= max_gap and code > max(have or {0}):
                break
            continue
        pbp = get_json("PlayByPlay", code, season)
        if not is_finished(header, pbp):
            gap += 1
            if gap >= max_gap and code > max(have or {0}):
                break
            continue
        gap = 0
        for name, data in (("header", header), ("pbp", pbp)):
            with open(os.path.join(raw_dir, f"{code}_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        log(f"  + partido {code}: {header.get('TeamA')} {header.get('ScoreA')}-{header.get('ScoreB')} {header.get('TeamB')}")
        new.append(code)
        time.sleep(0.3)
    return new
