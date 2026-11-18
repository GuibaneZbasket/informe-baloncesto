#!/usr/bin/env python3
"""Genera el informe.

Uso:
  python build.py                 # descarga lo nuevo de la Euroliga y regenera la web
  python build.py --demo          # web de demostración con datos ficticios (sin internet)
  python build.py --season E2026  # otra temporada (E2026 = 2026-27)
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src.analysis import analyze  # noqa: E402
from src.render import build_site  # noqa: E402


def load_raw(raw_dir, season):
    games = []
    for f in sorted(os.listdir(raw_dir)):
        if not f.endswith("_pbp.json"):
            continue
        code = int(f.split("_")[0])
        with open(os.path.join(raw_dir, f), encoding="utf-8") as fh:
            pbp = json.load(fh)
        hp = os.path.join(raw_dir, f"{code}_header.json")
        header = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else {}
        try:
            g = analyze(pbp, header, code, season)
            if not g.get("round"):
                # Liga regular con 20 equipos: 10 partidos por jornada
                g["round"] = str((code - 1) // 10 + 1)
            games.append(g)
        except Exception as e:  # un partido raro no debe tumbar el informe
            print(f"  ! partido {code}: {e}")
    return games


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="E2026")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default=None, help="carpeta de salida (por defecto docs/, o demo/web con --demo)")
    ap.add_argument("--no-fetch", action="store_true", help="no descargar, solo regenerar")
    args = ap.parse_args()

    if args.demo:
        args.out = args.out or os.path.join(ROOT, "demo", "web")
        from demo.simulate import simulate_round
        games = []
        for rnd, seed, dates in ((10, 7, ("10/11/2026", "11/11/2026")), (11, 11, ("17/11/2026", "18/11/2026"))):
            for code, pbp, header in simulate_round(seed, rnd, dates):
                games.append(analyze(pbp, header, code, args.season))
        rounds = build_site(games, args.out, demo=True)
        print(f"Demo generada en {args.out} (jornadas {', '.join(rounds)})")
        return

    args.out = args.out or os.path.join(ROOT, "docs")
    raw_dir = os.path.join(ROOT, "data", "euroleague", args.season)
    if not args.no_fetch:
        from src.euroleague import sync
        print(f"Buscando partidos nuevos de {args.season}…")
        new = sync(args.season, raw_dir)
        print(f"{len(new)} partidos nuevos")
    if not os.path.isdir(raw_dir):
        print("No hay datos todavía.")
        return
    games = load_raw(raw_dir, args.season)
    rounds = build_site(games, args.out)
    print(f"Web generada en {args.out}: {len(games)} partidos, jornadas {', '.join(rounds)}")
    build_own(args.out)
    copy_app(args.out)


def build_own(out):
    """Partidos de nuestro equipo anotados con la app (data/equipo/*.json)."""
    d = os.path.join(ROOT, "data", "equipo")
    games = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                data = json.load(fh)
            code = os.path.splitext(f)[0]
            games.append(analyze(data["pbp"], data.get("header") or {}, code, "EQ"))
        except Exception as e:
            print(f"  ! {f}: {e}")
    if not games:
        from src.render import page
        os.makedirs(os.path.join(out, "equipo"), exist_ok=True)
        with open(os.path.join(out, "equipo", "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page("Nuestro equipo", '<header class="top"><div class="kicker">Informe de nuestro equipo</div>'
                          '<h1>Aún no hay partidos</h1><p class="sub">Anota un partido con la '
                          '<a href="../app/"><b>App Banquillo</b></a>, expórtalo y súbelo a la carpeta '
                          '<b>data/equipo</b> del repositorio.</p></header>'))
        return

    def dkey(g):
        try:
            dd, mm, yy = (g.get("date") or "").split("/")
            return (int(yy), int(mm), int(dd))
        except ValueError:
            return (0, 0, 0)
    for i, g in enumerate(sorted(games, key=dkey), 1):
        if not g.get("round"):
            g["round"] = str(i)
    build_site(games, os.path.join(out, "equipo"), competition="de nuestro equipo",
               footer="Generado a partir del play-by-play anotado con la app Banquillo.")
    print(f"Informes del equipo: {len(games)} partidos")


def copy_app(out):
    """Publica la app de anotación en docs/app."""
    import shutil
    src = os.path.join(ROOT, "app")
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(out, "app"), dirs_exist_ok=True)


if __name__ == "__main__":
    main()
