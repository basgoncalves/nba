"""Turn one SportVU 2015-16 tracking game into small per-quarter files plus a summary.

Usage:
  python process.py <game name>        e.g. 12.25.2015.CLE.at.GSW   (downloads it)
  python process.py --file <game.7z>   use a local file
  python process.py --list             list available games

Writes tracking/<gameId>/:
  meta.json   game, teams, players (id, name, team, jersey)
  q<N>.json   one quarter: 25 Hz frames, every player's position, speed and acceleration
  summary.json per player and quarter: distance, speeds, speed bands, accelerations/decelerations

Positions are in metres on a 28.65 x 15.24 m court (SportVU feet x 0.3048).
Players are tracked in 2D only, so jumps cannot be seen here (only the ball has height).
"""
import json, os, statistics, sys, tempfile, urllib.request

REPO = "linouk23/NBA-Player-Movements"
FOLDER = "data/2016.NBA.Raw.SportVU.Game.Logs"
FT = 0.3048
HZ = 25
SMOOTH = 7            # frames (0.28 s) moving average on positions, to remove camera jitter
BANDS = [("walk", 0, 2.0), ("jog", 2.0, 4.0), ("run", 4.0, 5.5), ("sprint", 5.5, 99)]   # m/s
ACC = 2.5             # m/s2: count accelerations / decelerations stronger than this
VJUMP = 11.0          # m/s: a frame-to-frame jump faster than this is a camera glitch, not running
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)))


def list_games():
    url = f"https://api.github.com/repos/{REPO}/contents/{FOLDER}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return [f["name"][:-3] for f in json.load(r) if f["name"].endswith(".7z")]


def download(name):
    url = f"https://raw.githubusercontent.com/{REPO}/master/{FOLDER}/{name}.7z"
    path = os.path.join(tempfile.mkdtemp(), name + ".7z")
    urllib.request.urlretrieve(url, path)
    return path


def load(path7z):
    import py7zr
    tmp = tempfile.mkdtemp()
    py7zr.SevenZipFile(path7z).extractall(tmp)
    js = [f for f in os.listdir(tmp) if f.endswith(".json")][0]
    return json.load(open(os.path.join(tmp, js)))


def smooth(v, w):
    h, out = w // 2, []
    for i in range(len(v)):
        a, b = max(0, i - h), min(len(v), i + h + 1)
        out.append(sum(v[a:b]) / (b - a))
    return out


def kinematics(frames):
    """frames: list of (index, x, y) for one player, consecutive indexes = 40 ms apart.
    Returns per-frame speed (m/s) and acceleration (m/s2), split at gaps."""
    res = {}
    seg = [frames[0]]
    segs = []
    for f in frames[1:]:
        p = seg[-1]
        dt = (f[0] - p[0]) / HZ
        jump = ((f[1] - p[1]) ** 2 + (f[2] - p[2]) ** 2) ** .5 / dt if dt else 0
        if f[0] - p[0] > 2 or jump > VJUMP:   # gap longer than 80 ms, or a tracking glitch
            segs.append(seg); seg = []
        seg.append(f)
    segs.append(seg)
    for seg in segs:
        if len(seg) < SMOOTH * 2:
            continue
        xs = smooth([f[1] for f in seg], SMOOTH); ys = smooth([f[2] for f in seg], SMOOTH)
        sp = [0.0] * len(seg)
        for i in range(1, len(seg) - 1):
            dt = (seg[i + 1][0] - seg[i - 1][0]) / HZ
            sp[i] = ((xs[i + 1] - xs[i - 1]) ** 2 + (ys[i + 1] - ys[i - 1]) ** 2) ** .5 / dt
        sp[0], sp[-1] = sp[1], sp[-2]
        sp = smooth(sp, SMOOTH)
        for i in range(len(seg)):
            j0, j1 = max(0, i - 1), min(len(seg) - 1, i + 1)
            dt = (seg[j1][0] - seg[j0][0]) / HZ or 1
            res[seg[i][0]] = (xs[i], ys[i], sp[i], (sp[j1] - sp[j0]) / dt)
    return res


def process(d):
    gid = d["gameid"]
    e0 = d["events"][0]
    home, away = e0["home"], e0["visitor"]
    players = {}
    for side in (home, away):
        for p in side["players"]:
            players[str(p["playerid"])] = {"n": f'{p["firstname"]} {p["lastname"]}', "t": side["abbreviation"],
                                           "j": p["jersey"], "pos": p["position"]}
    tid = {home["teamid"]: home["abbreviation"], away["teamid"]: away["abbreviation"]}

    moments = {}
    for e in d["events"]:
        for m in e["moments"]:
            moments.setdefault(m[1], m)
    times = sorted(moments)

    out_dir = os.path.join(OUT, gid)
    os.makedirs(out_dir, exist_ok=True)
    json.dump({"id": gid, "date": d["gamedate"], "home": home["abbreviation"], "away": away["abbreviation"],
               "hz": HZ, "units": "m, m/s, m/s2", "players": players},
              open(os.path.join(out_dir, "meta.json"), "w"), separators=(",", ":"))

    summary = {"id": gid, "players": {}}
    for q in sorted({moments[t][0] for t in times}):
        qt = [t for t in times if moments[t][0] == q]
        t0 = qt[0]
        idx = [round((t - t0) / (1000 / HZ)) for t in qt]
        clock = {}
        ball = {}
        track = {}
        for i, t in zip(idx, qt):
            m = moments[t]
            clock[i] = round(m[2], 2)
            for row in m[5]:
                if row[0] == -1:
                    ball[i] = (row[2] * FT, row[3] * FT, row[4] * FT)
                else:
                    track.setdefault(str(row[1]), []).append((i, row[2] * FT, row[3] * FT))
        fidx = sorted(set(idx))
        # game-clock running = clock went down since the previous frame
        running = {}
        prev = None
        for i in fidx:
            running[i] = prev is not None and clock[i] < clock[prev]
            prev = i
        qfile = {"q": q, "hz": HZ, "frames": len(fidx),
                 "f": fidx,                                   # frame number (x 40 ms since quarter start)
                 "clock": [clock[i] for i in fidx],
                 "ball": [[round(c * 10) for c in ball[i]] if i in ball else -1 for i in fidx],   # dm
                 "players": {},
                 "units": "x, y in dm; speed in dm/s; accel in dm/s2; -1 = not on court"}
        for pid, fr in track.items():
            fr.sort()
            kin = kinematics(fr)
            rows = [[round(k[0] * 10), round(k[1] * 10), round(k[2] * 10), round(k[3] * 10)] if (k := kin.get(i)) else -1
                    for i in fidx]
            qfile["players"][pid] = rows
            sp = [k[2] for k in kin.values()]; ac = [k[3] for k in kin.values()]
            if not sp:
                continue
            s = summary["players"].setdefault(pid, {"n": players.get(pid, {}).get("n", pid), "t": players.get(pid, {}).get("t", ""), "q": {}})
            dist = sum(sp) / HZ
            bands = {b: round(sum(v for v in sp if lo <= v < hi) / HZ) for b, lo, hi in BANDS}
            # count separate acceleration / deceleration efforts (threshold crossings)
            efforts = {"acc": 0, "dec": 0}
            state = 0
            for a in ac:
                if a > ACC and state != 1: efforts["acc"] += 1; state = 1
                elif a < -ACC and state != -1: efforts["dec"] += 1; state = -1
                elif abs(a) < ACC / 2: state = 0
            game_sec = sum(1 for i in kin if running.get(i)) / HZ
            s["q"][str(q)] = {"sec": round(game_sec), "real_sec": round(len(sp) / HZ), "dist": round(dist), "vmax": round(max(sp), 2),
                              "vmean": round(statistics.mean(sp), 2), "bands": bands, **efforts,
                              "amax": round(max(ac), 2), "dmax": round(min(ac), 2)}
        json.dump(qfile, open(os.path.join(out_dir, f"q{q}.json"), "w"), separators=(",", ":"))
        print(f"quarter {q}: {len(fidx)} frames, {len(track)} players, "
              f"{os.path.getsize(os.path.join(out_dir, f'q{q}.json')) / 1e6:.1f} MB")
    for s in summary["players"].values():
        qs = s["q"].values()
        s["game"] = {"sec": sum(x["sec"] for x in qs), "dist": sum(x["dist"] for x in qs),
                     "vmax": max(x["vmax"] for x in qs), "acc": sum(x["acc"] for x in qs), "dec": sum(x["dec"] for x in qs),
                     "bands": {b: sum(x["bands"][b] for x in qs) for b, _, _ in BANDS}}
    json.dump(summary, open(os.path.join(out_dir, "summary.json"), "w"), separators=(",", ":"))
    return out_dir, summary


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print("\n".join(list_games())); sys.exit()
    path = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--file" else download(sys.argv[1])
    out_dir, summary = process(load(path))
    rows = sorted(summary["players"].values(), key=lambda s: -s["game"]["dist"])
    print(f"\n{'player':24} {'team':4} {'min':>5} {'km':>5} {'vmax':>5} {'sprint m':>8} {'acc':>4} {'dec':>4}")
    for s in rows:
        g = s["game"]
        print(f"{s['n'][:24]:24} {s['t']:4} {g['sec'] / 60:5.1f} {g['dist'] / 1000:5.2f} {g['vmax']:5.2f} {g['bands']['sprint']:8} {g['acc']:4} {g['dec']:4}")
