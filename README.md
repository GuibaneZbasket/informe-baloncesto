# Informe de baloncesto (Euroliga → después ACB)

Web que se actualiza sola cada mañana con los resultados de la Euroliga:

- **Portada de jornada**: tarjeta por partido (marcador, parciales, gráfico de la evolución, titular, resumen y MVP), récords de la jornada, mejores valoraciones y ranking de equipos (ORtg, DRtg, Net, ritmo, eFG%…).
- **Página de cada partido**: crónica, claves del partido, gráfico interactivo del marcador, rachas, tiempo por delante, sequías, comparativa de equipos, estadística avanzada (cuatro factores, ratings, posesiones), box score con TS% y Uso%, +/- en pista y en el banquillo, puntos por cuarto, quintetos, conexiones de asistencia y jugada a jugada con filtros.

Todo se calcula a partir del **play-by-play oficial** (`live.euroleague.net/api/PlayByPlay`), sin coste y sin dependencias: solo Python.

---

## Puesta en marcha (una sola vez, ~10 minutos)

### 1. Crea el repositorio
En GitHub: **New repository** → nombre `informe-baloncesto` → **Public** (GitHub Pages es gratis en repos públicos) → *Create repository*.

### 2. Sube los archivos
En el repositorio vacío: **Add file → Upload files** y arrastra **todo el contenido** de la carpeta descomprimida (`build.py`, `src/`, `demo/`, `README.md`). Pulsa *Commit changes*.

> ⚠️ La carpeta `.github` está oculta en Mac/Windows y no suele subirse arrastrando. Créala a mano:
> **Add file → Create new file**, escribe como nombre `.github/workflows/informe.yml` y pega el contenido del archivo `informe.yml` que te he pasado. *Commit changes*.

### 3. Dale permiso para guardar
**Settings → Actions → General → Workflow permissions** → marca **Read and write permissions** → *Save*.

### 4. Lánzalo por primera vez
Pestaña **Actions** → *Informe diario* → **Run workflow**. La primera vez descarga todos los partidos de la temporada (tarda unos minutos). Si sale en verde, ya hay carpeta `docs/` con la web.

### 5. Publica la web
**Settings → Pages** → *Source: Deploy from a branch* → rama **main**, carpeta **/docs** → *Save*.
En un par de minutos tendrás la web en:
`https://TU-USUARIO.github.io/informe-baloncesto/`

Guárdala en la pantalla de inicio del móvil y listo: cada madrugada (hacia las 6, hora de Madrid) se actualiza sola.

---

## Uso en local (opcional)

```bash
python build.py            # descarga lo nuevo y genera docs/
python build.py --demo     # demo con datos ficticios en demo/web/ (no necesita internet)
python build.py --no-fetch # regenera la web sin descargar
```

## Estructura

| Archivo | Qué hace |
|---|---|
| `src/euroleague.py` | Descarga cabecera y play-by-play de los partidos terminados |
| `src/analysis.py` | Motor de análisis: box score, minutos, +/-, posesiones, rachas, clutch, quintetos… |
| `src/cronica.py` | Crónicas y claves del partido con plantillas |
| `src/render.py` | Genera la web (portada, jornadas y partidos) |
| `data/euroleague/E2026/` | Datos en bruto guardados (histórico para análisis futuros) |
| `docs/` | La web publicada |

## Próximos pasos previstos
- ACB los fines de semana (scraping de acb.com).
- Mapas de tiro (la API de la Euroliga tiene coordenadas de cada lanzamiento).
- Acumulados de temporada: rankings, tendencias, ratings por equipo y jugador.
