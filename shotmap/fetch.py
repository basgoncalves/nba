"""Fetch NBA shot locations from ESPN for every game since the 2024-25 season.

Writes (all relative to this folder):
  data/games.json            list of games, newest first
  data/shots/<gameId>.json   every field-goal attempt of one game
  data/players.json          index of players with shot counts
  data/players/<id>.json     every shot of one player, all seasons

Coordinates: tenths of a foot relative to the basket (NBA "legacy" style).
Run again any time: games already downloaded are skipped.
"""
import json, os, re, statistics, time, urllib.request
from datetime import date, timedelta

FIRST_SEASON_START = date(2024, 10, 1)   # 2024-25 season onwards
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
KEEP_TYPES = {2, 3, 5}                    # regular season, playoffs, play-in
VERSION = 2                               # bump to force re-download of old files
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
MAX_MINUTES = float(os.environ.get("MAX_MINUTES", "300"))  # stop early, next run continues

os.makedirs("data/shots", exist_ok=True)
os.makedirs("data/players", exist_ok=True)
T0 = time.time()


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def season_label(year):
    """ESPN season year 2027 -> '2026-27'."""
    return f"{year - 1}-{str(year)[2:]}"


def load_json(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


# ---------------------------------------------------------------- game list
old = {g["id"]: g for g in load_json("data/games.json", [])}
# Days already fully scanned (all games finished) do not need re-checking.
scanned = set(load_json("data/scanned_days.json", []))
games = dict(old)
d = FIRST_SEASON_START
today = date.today()
while d <= today:
    key = d.isoformat()
    if key in scanned:
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
        if st not in KEEP_TYPES:
            continue
        comp = e["competitions"][0]
        c = {t["homeAway"]: t for t in comp["competitors"]}
        games["espn" + e["id"]] = {
            "id": "espn" + e["id"], "date": e["date"],
            "season": season_label(e["season"]["year"]),
            "type": {2: "Regular", 3: "Playoffs", 5: "Play-in"}[st],
            "home": c["home"]["team"]["abbreviation"], "away": c["away"]["team"]["abbreviation"],
            "hs": int(c["home"]["score"]), "as": int(c["away"]["score"]),
        }
    if all_done and d < today - timedelta(days=1):
        scanned.add(key)
    d += timedelta(days=1)
json.dump(sorted(scanned), open("data/scanned_days.json", "w"))
print(f"{len(games)} finished games since {FIRST_SEASON_START}")


# ---------------------------------------------------------------- shots per game
def espn_shots(eid):
    s = get(f"{ESPN}/summary?event={eid}")
    team = {t["team"]["id"]: t["team"]["abbreviation"] for t in s["boxscore"]["teams"]}
    names = {}
    for tp in s["boxscore"].get("players", []):
        for st in tp["statistics"]:
            for a in st["athletes"]:
                ath = a["athlete"]
                first, _, last = ath["displayName"].partition(" ")
                names[ath["id"]] = (f"{first[:1]}. {last}" if last else first, ath["displayName"])
    raw = []
    for p in s.get("plays", []):
        txt = p.get("text", "").lower()
        if not p.get("shootingPlay") or "free throw" in txt:
            continue
        co = p.get("coordinate") or {}
        x, y = co.get("x"), co.get("y")
        if x is None or y is None or abs(x) > 200 or abs(y) > 200:
            continue
        pid = (p.get("participants") or [{}])[0].get("athlete", {}).get("id")
        short, full = names.get(pid, ("Unknown", "Unknown"))
        raw.append({"x": x, "y": y, "txt": txt, "pid": pid or "0", "p": short, "n": full,
                    "t": team.get(p.get("team", {}).get("id"), "?"), "q": p["period"]["number"],
                    "m": 1 if p.get("scoringPlay") else 0,
                    "v": 3 if "three point" in txt else 2,
                    "c": p.get("clock", {}).get("displayValue", ""), "d": p.get("type", {}).get("text", "")})
    if not raw:
        return []
    # Locate the basket from shots at the rim, then convert feet -> tenths of a foot.
    near = [r for r in raw if any(k in r["txt"] for k in ("dunk", "layup", "tip"))] or raw
    rx = statistics.median(r["x"] for r in near)
    ry = statistics.median(r["y"] for r in near)
    sign = 1 if statistics.median(r["y"] for r in raw) >= ry else -1
    return [{k: r[k] for k in ("pid", "p", "n", "t", "q", "m", "v", "c", "d")} |
            {"x": round((r["x"] - rx) * 10), "y": round((r["y"] - ry) * 10 * sign)} for r in raw]


def done(g):
    f = load_json(f"data/shots/{g['id']}.json", None)
    return isinstance(f, dict) and f.get("v") == VERSION


todo = [g for g in sorted(games.values(), key=lambda g: g["date"], reverse=True) if not done(g)]
print(f"{len(todo)} games to download")
for i, g in enumerate(todo):
    if (time.time() - T0) / 60 > MAX_MINUTES:
        print("time limit reached; the next run continues from here")
        break
    try:
        shots = espn_shots(g["id"][4:])
    except Exception as e:
        print("skip", g["id"], e)
        continue
    json.dump({"v": VERSION, "shots": shots}, open(f"data/shots/{g['id']}.json", "w"), separators=(",", ":"))
    if i % 50 == 0:
        print(f"[{i + 1}/{len(todo)}] {g['date'][:10]} {g['away']}@{g['home']}: {len(shots)} shots")
    time.sleep(0.15)


# ---------------------------------------------------------------- write indexes
have = []
players = {}
for g in games.values():
    f = load_json(f"data/shots/{g['id']}.json", None)
    if not isinstance(f, dict) or f.get("v") != VERSION:
        continue
    have.append(g)
    for s in f["shots"]:
        if s["pid"] == "0":
            continue
        p = players.setdefault(s["pid"], {"id": s["pid"], "n": s["n"], "p": s["p"], "t": s["t"], "last": "", "shots": []})
        if g["date"] > p["last"]:
            p["last"], p["t"] = g["date"], s["t"]
        p["shots"].append([g["id"], g["season"], s["t"], s["q"], s["m"], s["v"], s["x"], s["y"], s["d"]])

have.sort(key=lambda g: g["date"], reverse=True)
json.dump(have, open("data/games.json", "w"), separators=(",", ":"))

index = []
for p in players.values():
    p["shots"].sort(key=lambda r: games[r[0]]["date"])
    json.dump({"id": p["id"], "n": p["n"], "cols": ["g", "s", "t", "q", "m", "v", "x", "y", "d"],
               "shots": p["shots"]}, open(f"data/players/{p['id']}.json", "w"), separators=(",", ":"))
    seasons = sorted({r[1] for r in p["shots"]})
    index.append({"id": p["id"], "n": p["n"], "t": p["t"], "fga": len(p["shots"]), "seasons": seasons})
index.sort(key=lambda p: -p["fga"])
json.dump(index, open("data/players.json", "w"), separators=(",", ":"))
print(f"wrote {len(have)} games, {len(index)} players in {(time.time() - T0) / 60:.1f} min")
