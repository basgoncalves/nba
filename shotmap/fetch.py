"""Fetch finished games of the current NBA season and their shot locations from cdn.nba.com."""
import json, os, urllib.request

BASE = "https://cdn.nba.com/static/json"
SEASON_START = "2026-10-01"  # only games from this season
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nba.com/"}
os.makedirs("data/shots", exist_ok=True)

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=30) as r:
        return json.load(r)

sched = get(f"{BASE}/staticData/scheduleLeagueV2.json")
games = []
for day in sched["leagueSchedule"]["gameDates"]:
    for g in day["games"]:
        if g.get("gameStatus") != 3 or g["gameDateTimeUTC"][:10] < SEASON_START:
            continue
        if g["homeTeam"]["teamTricode"] is None or not g["gameId"].startswith(("002", "004", "006")):
            continue  # regular season, playoffs, NBA Cup; skip preseason
        games.append({
            "id": g["gameId"], "date": g["gameDateTimeUTC"],
            "home": g["homeTeam"]["teamTricode"], "away": g["awayTeam"]["teamTricode"],
            "hs": g["homeTeam"]["score"], "as": g["awayTeam"]["score"],
        })

for g in games:
    path = f"data/shots/{g['id']}.json"
    if os.path.exists(path):
        continue
    try:
        acts = get(f"{BASE}/liveData/playbyplay/playbyplay_{g['id']}.json")["game"]["actions"]
    except Exception as e:
        print("skip", g["id"], e); continue
    shots = [{
        "p": a.get("playerNameI") or a.get("playerName"), "t": a["teamTricode"],
        "q": a["period"], "m": 1 if a.get("shotResult") == "Made" else 0,
        "v": 3 if a["actionType"] == "3pt" else 2,
        "x": a.get("xLegacy"), "y": a.get("yLegacy"),
        "c": a.get("clock", "")[2:7].replace("M", ":"), "d": a.get("subType", ""),
    } for a in acts if a.get("isFieldGoal") == 1 and a.get("xLegacy") is not None]
    json.dump(shots, open(path, "w"), separators=(",", ":"))
    print("saved", g["id"], len(shots), "shots")

games.sort(key=lambda g: g["date"], reverse=True)
games = [g for g in games if os.path.exists(f"data/shots/{g['id']}.json")]
json.dump(games, open("data/games.json", "w"), indent=0)
