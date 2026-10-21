"""Fetch finished games of the current NBA season and their shot locations.

Tries NBA.com first; if it blocks the request (it often refuses cloud servers),
falls back to ESPN's public API. Output format is the same either way:
x/y in tenths of a foot relative to the basket (NBA "legacy" coordinates).
"""
import json, os, re, statistics, urllib.request
from datetime import date, timedelta

SEASON_START = date(2026, 10, 1)          # only games from this season
os.makedirs("data/shots", exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


def get(url, nba=False):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
         "Accept-Language": "en-US,en;q=0.9"}
    if nba:
        h.update({"Origin": "https://www.nba.com", "Referer": "https://www.nba.com/"})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        return json.load(r)


def save(gid, shots):
    json.dump(shots, open(f"data/shots/{gid}.json", "w"), separators=(",", ":"))
    n3 = [s for s in shots if s["v"] == 3]
    d3 = statistics.median([(s["x"] ** 2 + s["y"] ** 2) ** .5 / 10 for s in n3]) if n3 else 0
    print(f"saved {gid}: {len(shots)} shots, median 3PT distance {d3:.1f} ft")


# ---------------------------------------------------------------- NBA.com
def from_nba():
    base = "https://cdn.nba.com/static/json"
    sched = get(f"{base}/staticData/scheduleLeagueV2.json", nba=True)
    games = []
    for day in sched["leagueSchedule"]["gameDates"]:
        for g in day["games"]:
            if g.get("gameStatus") != 3 or g["gameDateTimeUTC"][:10] < SEASON_START.isoformat():
                continue
            if not g["gameId"].startswith(("002", "004", "006")):
                continue  # skip preseason
            games.append({"id": g["gameId"], "date": g["gameDateTimeUTC"],
                          "home": g["homeTeam"]["teamTricode"], "away": g["awayTeam"]["teamTricode"],
                          "hs": g["homeTeam"]["score"], "as": g["awayTeam"]["score"]})
    for g in games:
        if os.path.exists(f"data/shots/{g['id']}.json"):
            continue
        acts = get(f"{base}/liveData/playbyplay/playbyplay_{g['id']}.json", nba=True)["game"]["actions"]
        save(g["id"], [{
            "p": a.get("playerNameI") or a.get("playerName"), "t": a["teamTricode"],
            "q": a["period"], "m": 1 if a.get("shotResult") == "Made" else 0,
            "v": 3 if a["actionType"] == "3pt" else 2,
            "x": a["xLegacy"], "y": a["yLegacy"],
            "c": a.get("clock", "")[2:7].replace("M", ":"), "d": a.get("subType", ""),
        } for a in acts if a.get("isFieldGoal") == 1 and a.get("xLegacy") is not None])
    return games


# ---------------------------------------------------------------- ESPN
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"


def from_espn():
    games, d = [], SEASON_START
    while d <= date.today():
        end = min(d + timedelta(days=13), date.today())
        sb = get(f"{ESPN}/scoreboard?dates={d:%Y%m%d}-{end:%Y%m%d}&limit=500")
        for e in sb.get("events", []):
            if e["season"].get("type") == 1 or not e["status"]["type"].get("completed"):
                continue  # skip preseason and unfinished games
            c = {t["homeAway"]: t for t in e["competitions"][0]["competitors"]}
            games.append({"id": "espn" + e["id"], "date": e["date"],
                          "home": c["home"]["team"]["abbreviation"], "away": c["away"]["team"]["abbreviation"],
                          "hs": int(c["home"]["score"]), "as": int(c["away"]["score"])})
        d = end + timedelta(days=1)
    for g in games:
        if not os.path.exists(f"data/shots/{g['id']}.json"):
            save(g["id"], espn_shots(g["id"][4:]))
    return games


def espn_shots(eid):
    s = get(f"{ESPN}/summary?event={eid}")
    team = {t["team"]["id"]: t["team"]["abbreviation"] for t in s["boxscore"]["teams"]}
    names = {}
    for tp in s["boxscore"].get("players", []):
        for st in tp["statistics"]:
            for a in st["athletes"]:
                ath = a["athlete"]
                first, _, last = ath["displayName"].partition(" ")
                names[ath["id"]] = f"{first[:1]}. {last}" if last else first
    raw = []
    for p in s.get("plays", []):
        txt = p.get("text", "").lower()
        if not p.get("shootingPlay") or "free throw" in txt:
            continue
        co = p.get("coordinate") or {}
        x, y = co.get("x"), co.get("y")
        if x is None or y is None or abs(x) > 200 or abs(y) > 200:
            continue
        ft = re.search(r"(\d+)-foot", txt)
        raw.append({"x": x, "y": y, "txt": txt, "ft": int(ft.group(1)) if ft else None,
                    "p": names.get((p.get("participants") or [{}])[0].get("athlete", {}).get("id"), "Unknown"),
                    "t": team.get(p.get("team", {}).get("id"), "?"), "q": p["period"]["number"],
                    "m": 1 if p.get("scoringPlay") else 0,
                    "v": 3 if "three point" in txt else 2,
                    "c": p.get("clock", {}).get("displayValue", ""), "d": p.get("type", {}).get("text", "")})
    if not raw:
        return []
    # Find the basket from dunks/layups, then convert feet -> tenths of a foot relative to it.
    near = [r for r in raw if any(k in r["txt"] for k in ("dunk", "layup", "tip"))] or raw
    rx = statistics.median(r["x"] for r in near)
    ry = statistics.median(r["y"] for r in near)
    sign = 1 if statistics.median(r["y"] for r in raw) >= ry else -1
    out = []
    for r in raw:
        out.append({k: r[k] for k in ("p", "t", "q", "m", "v", "c", "d")} |
                   {"x": round((r["x"] - rx) * 10), "y": round((r["y"] - ry) * 10 * sign)})
    return out


# ---------------------------------------------------------------- main
try:
    games = from_nba()
    print(f"NBA.com: {len(games)} games")
except Exception as e:
    print("NBA.com failed:", e, "-> using ESPN")
    games = from_espn()
    print(f"ESPN: {len(games)} games")

games.sort(key=lambda g: g["date"], reverse=True)
games = [g for g in games if os.path.exists(f"data/shots/{g['id']}.json")]
json.dump(games, open("data/games.json", "w"), indent=0)
