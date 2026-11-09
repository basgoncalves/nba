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
shutil.copy(os.path.join(here, "sw.js"), out)   # installable app (PWA)
shutil.copytree(os.path.join(here, "app"), os.path.join(out, "app"), dirs_exist_ok=True)
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
            if v == 2 and (x * x + y * y) ** .5 >= 300:   # 30 ft+ is a three (older files)
                v = 3
            ast = row[9] if len(row) > 9 else ""
            t = side[ti]
            short, full = g["names"].get(pid, ["Unknown", "Unknown"])[:2]
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

# ---------------------------------------------------------------- landscape (box-score based)
# per game and team / player: MIN PTS FGM FGA 3PM 3PA FTM FTA OREB DREB AST STL BLK TO PF +/-
LCOLS = ["min", "pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "oreb", "dreb", "ast", "stl", "blk", "tov", "pf", "pm"]
land = os.path.join(data, "land")
os.makedirs(land, exist_ok=True)


def num(v):
    try:
        return int(str(v).replace("+", ""))
    except ValueError:
        return 0


def box_row(cols, st):
    get = lambda c: st[cols.index(c)] if c in cols and cols.index(c) < len(st) else "0"
    pair = lambda c: [num(x) for x in (str(get(c)).split("-") + ["0"])[:2]] if "-" in str(get(c)) else [0, 0]
    fg, tp, ft = pair("FG"), pair("3PT"), pair("FT")
    return [num(get("MIN")), num(get("PTS")), *fg, *tp, *ft, num(get("OREB")), num(get("DREB")), num(get("AST")),
            num(get("STL")), num(get("BLK")), num(get("TO")), num(get("PF")), num(get("+/-"))]


team_rows, pseason, career = [], {}, {}
for season in sorted(os.listdir(os.path.join(here, "raw"))):
    folder = os.path.join(here, "raw", season)
    if not os.path.isdir(folder):
        continue
    for f in os.listdir(folder):
        g = json.load(open(os.path.join(folder, f)))
        box = g.get("box") or {}
        if not box.get("rows"):
            continue
        side, tot = [g["away"], g["home"]], [[0] * len(LCOLS), [0] * len(LCOLS)]
        S = pseason.setdefault(season, {"names": {}, "rows": []})
        for pid, r in box["rows"].items():
            ti, starter, dnp, st = r[0], r[1], r[2], r[3:]
            if dnp or not st:
                continue
            row = box_row(box["cols"], st)
            tot[ti] = [a + b for a, b in zip(tot[ti], row)]
            nm = g["names"].get(pid, ["?", "?"])
            S["names"][pid] = [nm[1], side[ti]]
            S["rows"].append([g["id"], g["date"][:10], side[ti], pid, starter, *row])
            c = career.setdefault(pid, {"n": nm[1], "t": side[ti], "last": "", "g": 0, "seasons": set(), "tot": [0] * len(LCOLS)})
            c["g"] += 1; c["seasons"].add(season); c["tot"] = [a + b for a, b in zip(c["tot"], row)]
            if g["date"] > c["last"]:
                c["last"], c["t"], c["n"] = g["date"], side[ti], nm[1]
        pts = [g["as"], g["hs"]]
        for ti in (0, 1):
            tot[ti][1] = pts[ti] or tot[ti][1]   # official score
            team_rows.append([g["id"], g["date"][:10], season, side[ti], side[1 - ti], *tot[ti], *tot[1 - ti][1:14]])
team_rows.sort(key=lambda r: r[1])
json.dump({"cols": ["g", "date", "season", "team", "opp"] + LCOLS + ["o_" + c for c in LCOLS[1:14]], "rows": team_rows},
          open(os.path.join(land, "teams.json"), "w"), separators=(",", ":"))
for season, S in pseason.items():
    S["rows"].sort(key=lambda r: r[1])
    json.dump({"cols": ["g", "date", "team", "pid", "starter"] + LCOLS, **S},
              open(os.path.join(land, f"players_{season}.json"), "w"), separators=(",", ":"))
json.dump({"cols": LCOLS, "seasons": sorted(pseason),
           "players": {pid: [c["n"], c["t"], c["g"], len(c["seasons"]), *c["tot"]] for pid, c in career.items() if c["g"]}},
          open(os.path.join(land, "career.json"), "w"), separators=(",", ":"))
print(f"landscape: {len(team_rows)} team-games, {sum(len(S['rows']) for S in pseason.values())} player-games")

size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(out) for f in fs)
print(f"built {len(games)} games, {len(index)} players, {len(tindex)} team-seasons, "
      f"{size / 1e6:.0f} MB in {time.time() - T0:.0f} s")
