"""Nombres cortos de los equipos de Euroliga (por código de la API).
Si un código no está aquí se usa el nombre que venga en los datos."""

EUROLEAGUE_TEAMS = {
    "MAD": "Real Madrid",
    "BAR": "Barça",
    "BAS": "Baskonia",
    "PAM": "Valencia Basket",
    "OLY": "Olympiacos",
    "PAN": "Panathinaikos",
    "ULK": "Fenerbahçe",
    "IST": "Anadolu Efes",
    "MCO": "Mónaco",
    "PRS": "Paris Basketball",
    "ASV": "ASVEL",
    "MUN": "Bayern Múnich",
    "TEL": "Maccabi Tel Aviv",
    "HTA": "Hapoel Tel Aviv",
    "ZAL": "Žalgiris",
    "PAR": "Partizan",
    "RED": "Estrella Roja",
    "MIL": "Olimpia Milano",
    "VIR": "Virtus Bolonia",
    "DUB": "Dubai Basketball",
    "BES": "Beşiktaş",
}


def short_name(code, fallback=None):
    name = EUROLEAGUE_TEAMS.get((code or "").strip())
    if name:
        return name
    fallback = fallback or code
    return fallback.title() if fallback and fallback.isupper() else fallback
