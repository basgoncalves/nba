"""Download NBA shot locations from ESPN into compact per-game files.

Writes (relative to this folder), add-only so git history stays small:
  raw/<season>/<gameId>.json   one file per finished game
  raw/scanned_days.json        days already checked, so they are not re-scanned

Each game file:
  {"v": 3, "id", "date", "season", "type", "home", "away", "hs", "as",
   "names": {playerId: [short, full]},
   "types": [shot type names],
   "shots": [[playerId, team(0=away,1=home), quarter, made, value, x, y, seconds, typeIndex, assisterId or ""], ...],
   "score": [[seconds, awayScore, homeScore], ...]}
x/y: tenths of a foot from the basket. seconds: elapsed since tip-off.

build.py turns these into the files the web page reads.
"""
import json, os, statistics, time, urllib.request
from datetime import date, timedelta

FIRST_SEASON_START = date(2009, 10, 1)   # 2009-10 season onwards
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
KEEP_TYPES = {2: "Regular", 3: "Playoffs", 5: "Play-in"}
VERSION = 3
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
MAX_MINUTES = float(os.environ.get("MAX_MINUTES", "300"))  # stop early; the next run continues
T0 = time.time()
os.makedirs("raw", exist_ok=True)


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def load_json(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def season_label(year):
    return f"{year - 1}-{str(year)[2:]}"


def elapsed(q, clock):
    """Seconds since tip-off: 12-minute quarters, 5-minute overtimes."""
    try:
        if ":" in clock:
            m, sec = clock.split(":")
            left = int(m) * 60 + float(sec)
        else:
            left = float(clock or 0)
    except ValueError:
        left = 0
    start = (q - 1) * 720 if q <= 4 else 2880 + (q - 5) * 300
    return round(start + (720 if q <= 4 else 300) - left)


def out_of_time():
    return (time.time() - T0) / 60 > MAX_MINUTES


# ---------------------------------------------------------------- which games exist
have = {}
for season in os.listdir("raw"):
    d = os.path.join("raw", season)
    if os.path.isdir(d):
        for f in os.listdir(d):
            have[f[:-5]] = season

scanned = set(load_json("raw/scanned_days.json", []))
today = date.today()
todo = []
d = FIRST_SEASON_START
while d <= today and not out_of_time():
    key = d.isoformat()
    if key in scanned or d.month in (7, 8, 9):    # off-season
        d += timedelta(days=1)
        continue
    try:
        sb = get(f"{ESPN}/scoreboard?dates={d:%Y%m%d}")
    except Exception as e:
        print("scoreboard", key, e)
        d += timedelta(days=1)
        continue
    all_done = True
    for e in sb.get("events", []):
        st = e["season"].get("type")
        if not e["status"]["type"].get("completed"):
            all_done = False
            continue
        if st not in KEEP_TYPES or e["id"] in have:
            continue
        c = {t["homeAway"]: t for t in e["competitions"][0]["competitors"]}
        todo.append({"id": e["id"], "date": e["date"], "season": season_label(e["season"]["year"]),
                     "type": KEEP_TYPES[st],
                     "home": c["home"]["team"]["abbreviation"], "away": c["away"]["team"]["abbreviation"],
                     "hs": int(c["home"]["score"] or 0), "as": int(c["away"]["score"] or 0)})
    if all_done and d < today - timedelta(days=1):
        scanned.add(key)
    d += timedelta(days=1)
json.dump(sorted(scanned), open("raw/scanned_days.json", "w"), separators=(",", ":"))
print(f"{len(have)} games already saved, {len(todo)} to download")


# ---------------------------------------------------------------- one game
def download(g):
    s = get(f"{ESPN}/summary?event={g['id']}")
    side = {}
    for t in s["boxscore"]["teams"]:
        side[t["team"]["id"]] = 1 if t["team"]["abbreviation"] == g["home"] else 0
    names = {}
    for tp in s["boxscore"].get("players", []):
        for stt in tp["statistics"]:
            for a in stt["athletes"]:
                ath = a["athlete"]
                first, _, last = ath["displayName"].partition(" ")
                names[ath["id"]] = [f"{first[:1]}. {last}" if last else first, ath["displayName"]]

    plays = s.get("plays", [])
    score, last = [[0, 0, 0]], (0, 0)
    raw = []
    for p in plays:
        q = p.get("period", {}).get("number", 1)
        e = elapsed(q, p.get("clock", {}).get("displayValue", ""))
        try:
            sc = (int(p.get("awayScore", 0)), int(p.get("homeScore", 0)))
            if sc != last and sc >= last:
                score.append([e, *sc])
                last = sc
        except (TypeError, ValueError):
            pass
        txt = p.get("text", "").lower()
        if not p.get("shootingPlay") or "free throw" in txt:
            continue
        co = p.get("coordinate") or {}
        x, y = co.get("x"), co.get("y")
        if x is None or y is None or abs(x) > 200 or abs(y) > 200 or (x == 0 and y == 0):
            continue
        parts = p.get("participants") or [{}]
        pid = parts[0].get("athlete", {}).get("id")
        ast = parts[1].get("athlete", {}).get("id", "") if len(parts) > 1 and p.get("scoringPlay") else ""
        if not pid:
            continue
        raw.append({"x": x, "y": y, "txt": txt, "pid": pid, "t": side.get(p.get("team", {}).get("id"), 0),
                    "q": q, "m": 1 if p.get("scoringPlay") else 0, "v": 3 if "three point" in txt else 2,
                    "e": e, "d": p.get("type", {}).get("text", ""), "a": ast})
    shots, types = [], []
    if len(raw) >= 40:   # games without usable coordinates are kept, but with no shots
        near = [r for r in raw if any(k in r["txt"] for k in ("dunk", "layup", "tip"))] or raw
        rx = statistics.median(r["x"] for r in near)
        ry = statistics.median(r["y"] for r in near)
        sign = 1 if statistics.median(r["y"] for r in raw) >= ry else -1
        for r in raw:
            if r["d"] not in types:
                types.append(r["d"])
            shots.append([r["pid"], r["t"], r["q"], r["m"], r["v"],
                          round((r["x"] - rx) * 10), round((r["y"] - ry) * 10 * sign), r["e"], types.index(r["d"]), r["a"]])
    used = {r[0] for r in shots} | {r[9] for r in shots if r[9]}
    return {"v": VERSION, **g, "names": {k: v for k, v in names.items() if k in used},
            "types": types, "shots": shots, "score": score}


n = 0
for g in sorted(todo, key=lambda g: g["date"], reverse=True):   # newest first
    if out_of_time():
        print("time limit reached; the next run continues from here")
        break
    try:
        data = download(g)
    except Exception as e:
        print("skip", g["id"], e)
        continue
    os.makedirs(f"raw/{g['season']}", exist_ok=True)
    json.dump(data, open(f"raw/{g['season']}/{g['id']}.json", "w"), separators=(",", ":"))
    n += 1
    if n % 100 == 1:
        print(f"[{n}/{len(todo)}] {g['date'][:10]} {g['away']}@{g['home']}: {len(data['shots'])} shots")
    time.sleep(0.1)
print(f"downloaded {n} games in {(time.time() - T0) / 60:.1f} min")
