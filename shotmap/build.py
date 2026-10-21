"""Build the files the web page reads from the raw game files.

Usage: python build.py <site folder>
Creates <site>/shotmap/ with index.html, raw/ (copied) and data/:
  data/games.json            [[id, date, season, type, home, away, homeScore, awayScore, shots], ...] newest first
  data/players.json          [{id, n, t, fga, seasons}, ...]
  data/players/<id>.json     {id, n, types, shots: [[gameId, team, q, made, value, x, y, typeIndex, assisted], ...],
                                         ast: [[gameId, q, value, x, y], ...] made shots this player assisted}
  data/teams.json            [{t, s, fga, games}, ...]
  data/teams/<team>_<season>.json  {team, season, players: {id: name}, shots: [[gameId, playerId, q, made, value, x, y, assisted], ...]}
"""
import json, os, shutil, sys, time

T0 = time.time()
site = sys.argv[1] if len(sys.argv) > 1 else "_site"
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(site, "shotmap")
data = os.path.join(out, "data")
for sub in ("players", "teams"):
    os.makedirs(os.path.join(data, sub), exist_ok=True)

shutil.copy(os.path.join(here, "index.html"), out)
if os.path.isdir(os.path.join(out, "raw")):
    shutil.rmtree(os.path.join(out, "raw"))
os.makedirs(os.path.join(here, "raw"), exist_ok=True)
shutil.copytree(os.path.join(here, "raw"), os.path.join(out, "raw"))

# tracking-based player load (derived values only, never raw positions)
load_src = os.path.join(here, "tracking", "load")
if os.path.isdir(load_src):
    if os.path.isdir(os.path.join(out, "load")):
        shutil.rmtree(os.path.join(out, "load"))
    shutil.copytree(load_src, os.path.join(out, "load"))

games, players, teams = [], {}, {}
for season in sorted(os.listdir(os.path.join(here, "raw"))):
    folder = os.path.join(here, "raw", season)
    if not os.path.isdir(folder):
        continue
    for f in os.listdir(folder):
        g = json.load(open(os.path.join(folder, f)))
        side = [g["away"], g["home"]]
        games.append([g["id"], g["date"][:16], g["season"], g["type"], g["home"], g["away"], g["hs"], g["as"], len(g["shots"])])
        for row in g["shots"]:
            pid, ti, q, m, v, x, y, e, di = row[:9]
            ast = row[9] if len(row) > 9 else ""
            t = side[ti]
            short, full = g["names"].get(pid, ["Unknown", "Unknown"])
            p = players.setdefault(pid, {"id": pid, "n": full, "t": t, "last": "", "types": [], "tix": {}, "shots": [], "ast": []})
            if g["date"] > p["last"]:
                p["last"], p["t"], p["n"] = g["date"], t, full
            d = g["types"][di] if di < len(g["types"]) else ""
            if d not in p["tix"]:
                p["tix"][d] = len(p["types"]); p["types"].append(d)
            p["shots"].append([g["id"], t, q, m, v, x, y, p["tix"][d], 1 if ast else 0, g["date"]])
            if ast:   # where this player's passes led to made shots
                a = players.setdefault(ast, {"id": ast, "n": g["names"].get(ast, ["", "Unknown"])[1], "t": t, "last": "",
                                             "types": [], "tix": {}, "shots": [], "ast": []})
                a["ast"].append([g["id"], q, v, x, y, g["date"]])
            tm = teams.setdefault((t, g["season"]), {"team": t, "season": g["season"], "players": {}, "shots": []})
            tm["players"][pid] = full
            tm["shots"].append([g["id"], pid, q, m, v, x, y, 1 if ast else 0, g["date"]])

games.sort(key=lambda r: r[1], reverse=True)
json.dump(games, open(os.path.join(data, "games.json"), "w"), separators=(",", ":"))
season_of = {r[0]: r[2] for r in games}

index = []
for p in players.values():
    if not p["shots"]:
        continue   # passed but never shot: skip
    p["shots"].sort(key=lambda r: r[-1]); p["ast"].sort(key=lambda r: r[-1])
    rows = [r[:-1] for r in p["shots"]]
    json.dump({"id": p["id"], "n": p["n"], "types": p["types"], "shots": rows, "ast": [r[:-1] for r in p["ast"]]},
              open(os.path.join(data, "players", p["id"] + ".json"), "w"), separators=(",", ":"))
    index.append({"id": p["id"], "n": p["n"], "t": p["t"], "fga": len(rows),
                  "seasons": sorted({season_of[r[0]] for r in rows})})
index.sort(key=lambda r: -r["fga"])
json.dump(index, open(os.path.join(data, "players.json"), "w"), separators=(",", ":"))

tindex = []
for (t, s), tm in teams.items():
    tm["shots"].sort(key=lambda r: r[-1])
    tm["shots"] = [r[:-1] for r in tm["shots"]]
    json.dump(tm, open(os.path.join(data, "teams", f"{t}_{s}.json"), "w"), separators=(",", ":"))
    tindex.append({"t": t, "s": s, "fga": len(tm["shots"]), "games": len({r[0] for r in tm["shots"]})})
tindex.sort(key=lambda r: (r["s"], r["t"]))
json.dump(tindex, open(os.path.join(data, "teams.json"), "w"), separators=(",", ":"))

size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(out) for f in fs)
print(f"built {len(games)} games, {len(index)} players, {len(tindex)} team-seasons, "
      f"{size / 1e6:.0f} MB in {time.time() - T0:.0f} s")
