"""Estimate joint, ligament and muscle load per player from SportVU tracking + a task library.

Usage: python load.py <gameId> [<gameId> ...]     (after process.py has made tracking/<gameId>/)

For every player, 25 times per second:
  1. classify the movement (walk/jog/run/sprint, or accel/decel/cut events) from speed,
     acceleration and change of direction,
  2. count steps (step rate depends on speed),
  3. give each step the per-step peak loads of that movement from task_library.json.

Writes tracking/load/<gameId>.json (derived values only, no positions) and tracking/load/index.json.
The library is a placeholder until it is filled from BioScout simulations; see its "note".
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = json.load(open(os.path.join(HERE, "task_library.json")))
OUTS = list(LIB["outputs"])
BIN = 10          # seconds of game clock per timeline bin
CELL = 1.0        # m, court map cell
CW, CH = 29, 16   # cells across a 28.65 x 15.24 m court
A_CAP = 6.0       # m/s2
V_CAP = 9.0       # m/s
KIN_A_CAP = 7.0   # m/s2: larger values are tracking artefacts and are ignored
HARD = 2.5        # m/s2: an acceleration/deceleration effort starts above this
SPEED_BANDS = [("walk", 0, 2.0), ("jog", 2.0, 4.0), ("run", 4.0, 5.5), ("sprint", 5.5, 99)]
KIN_OUTPUTS = {"speed": {"label": "Running speed", "unit": "m/s", "kind": "speed"},
               "accel": {"label": "Accelerations", "unit": "m/s²", "kind": "accel"},
               "decel": {"label": "Decelerations", "unit": "m/s²", "kind": "decel"}}
PHASES = ["walk", "jog", "run", "sprint", "accel", "decel", "cut"]


def phase_of(v, a, turn):
    if v < 0.5:
        return None
    if v > 2.5 and turn > 120:
        return "cut"
    if a < -2.5:
        return "decel"
    if a > 2.5:
        return "accel"
    return "walk" if v < 2 else "jog" if v < 4 else "run" if v < 5.5 else "sprint"


def step_rate(v):
    r = LIB["step_rate"]
    return r["walk"] if v < 2 else r["run_c0"] + r["run_cv"] * v


def per_step(ph, v, a):
    c = LIB["phases"][ph]
    a = min(abs(a), A_CAP)   # tracking noise can give spikes beyond what players produce
    v = min(v, V_CAP)
    return {k: max(0.0, c[k][0] + c[k][1] * v + c[k][2] * a) for k in OUTS}


def game(gid):
    folder = os.path.join(HERE, gid)
    meta = json.load(open(os.path.join(folder, "meta.json")))
    quarters = sorted(int(f[1:-5]) for f in os.listdir(folder) if f.startswith("q") and f.endswith(".json"))
    res = {}
    for q in quarters:
        d = json.load(open(os.path.join(folder, f"q{q}.json")))
        fidx, clock = d["f"], d["clock"]
        qlen = 720 if q <= 4 else 300
        qstart = (q - 1) * 720 if q <= 4 else 2880 + (q - 5) * 300
        for pid, rows in d["players"].items():
            P = res.setdefault(pid, {
                "steps": {p: 0 for p in PHASES}, "sum": {k: 0.0 for k in OUTS}, "max": {k: 0.0 for k in OUTS},
                "q": {}, "bins": {}, "grid": {k: [0.0] * (CW * CH) for k in OUTS},
                "dir": {"knee": [0, 0, 0], "hip": [0, 0, 0]}, "top": [],
                "kin": {"dist": 0.0, "time": 0.0, "vmax": 0.0, "amax": 0.0, "dmax": 0.0, "nacc": 0, "ndec": 0,
                        "bands": {b: 0.0 for b, _, _ in SPEED_BANDS}, "q": {}, "bins": {},
                        "grid": {"t": [0.0] * (CW * CH), "vt": [0.0] * (CW * CH), "acc": [0] * (CW * CH), "dec": [0] * (CW * CH)}}})
            Q = P["q"].setdefault(str(q), {"steps": 0, "sum": {k: 0.0 for k in OUTS}, "max": {k: 0.0 for k in OUTS}})
            K = P["kin"]
            KQ = K["q"].setdefault(str(q), {"dist": 0.0, "time": 0.0, "vmax": 0.0, "amax": 0.0, "dmax": 0.0, "nacc": 0, "ndec": 0})
            effort = 0
            acc_steps, prev, hist = 0.0, None, []
            for i, r in enumerate(rows):
                if r == -1:
                    prev, hist = None, []
                    continue
                x, y, v, a = r[0] / 10, r[1] / 10, r[2] / 10, r[3] / 10
                hist.append((fidx[i], x, y)); hist = hist[-6:]
                turn = 0.0
                if len(hist) >= 6 and v > 2.5:   # heading change over ~0.2 s
                    (f0, x0, y0), (f1, x1, y1), (f2, x2, y2) = hist[0], hist[2], hist[-1]
                    h1, h2 = math.atan2(y1 - y0, x1 - x0), math.atan2(y2 - y1, x2 - x1)
                    dh = abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi)
                    turn = math.degrees(dh) / max(1e-3, (f2 - f0) / 2 / 25)
                dt = (fidx[i] - prev) / 25 if prev is not None and fidx[i] - prev <= 2 else 0.04
                prev = fidx[i]
                if 0 <= clock[i] <= 0.05:   # after the buzzer
                    continue
                # ---- running speed and accelerations, every frame ----
                # acceleration over +-0.24 s: steadier than frame-to-frame values, which carry camera noise
                ac = None   # not measurable at the edges of a tracked stretch
                if 6 <= i < len(rows) - 6 and rows[i - 6] != -1 and rows[i + 6] != -1 and fidx[i + 6] - fidx[i - 6] <= 14:
                    ac = (rows[i + 6][2] - rows[i - 6][2]) / 10 / ((fidx[i + 6] - fidx[i - 6]) / 25)
                vc = min(v, V_CAP)
                t = qstart + (qlen - clock[i]) if clock[i] >= 0 else qstart
                kb = K["bins"].setdefault(str(int(t // BIN)), {"d": 0.0, "t": 0.0, "vmax": 0.0, "amax": 0.0, "dmax": 0.0, "na": 0, "nd": 0})
                cell = min(CH - 1, max(0, int(y / CELL))) * CW + min(CW - 1, max(0, int(x / CELL)))
                for o in (K, KQ):
                    o["dist"] += vc * dt; o["time"] += dt
                    o["vmax"] = max(o["vmax"], vc)
                kb["d"] += vc * dt; kb["t"] += dt
                kb["vmax"] = max(kb["vmax"], vc)
                for b, lo, hi in SPEED_BANDS:
                    if lo <= vc < hi:
                        K["bands"][b] += vc * dt
                K["grid"]["t"][cell] += dt; K["grid"]["vt"][cell] += vc * dt
                if ac is not None and abs(ac) > KIN_A_CAP:
                    ac = None
                if ac is not None:
                    kb["amax"] = max(kb["amax"], ac); kb["dmax"] = min(kb["dmax"], ac)
                    K.setdefault("alist", []).append(ac); KQ.setdefault("alist", []).append(ac)
                if ac is None:
                    pass
                elif ac > HARD and effort != 1:
                    effort = 1; K["nacc"] += 1; KQ["nacc"] += 1; kb["na"] += 1; K["grid"]["acc"][cell] += 1
                elif ac < -HARD and effort != -1:
                    effort = -1; K["ndec"] += 1; KQ["ndec"] += 1; kb["nd"] += 1; K["grid"]["dec"][cell] += 1
                elif abs(ac) < HARD / 2:
                    effort = 0
                # ---- steps and joint/muscle loads ----
                ph = phase_of(v, a, turn)
                if not ph:
                    continue
                acc_steps += step_rate(v) * dt
                while acc_steps >= 1:
                    acc_steps -= 1
                    L = per_step(ph, v, a)
                    P["steps"][ph] += 1; Q["steps"] += 1
                    t = qstart + (qlen - clock[i]) if clock[i] >= 0 else qstart
                    b = P["bins"].setdefault(str(int(t // BIN)), {"n": 0, **{k: 0.0 for k in OUTS}, **{k + "_max": 0.0 for k in OUTS}})
                    b["n"] += 1
                    cell = min(CH - 1, max(0, int(y / CELL))) * CW + min(CW - 1, max(0, int(x / CELL)))
                    for k, val in L.items():
                        P["sum"][k] += val; Q["sum"][k] += val; b[k] += val
                        P["max"][k] = max(P["max"][k], val); Q["max"][k] = max(Q["max"][k], val)
                        b[k + "_max"] = max(b[k + "_max"], val)
                        P["grid"][k][cell] += val
                    c = LIB["phases"][ph]
                    for j in range(3):
                        P["dir"]["knee"][j] += c["knee_dir"][j] * (L["knee_med"] + L["knee_lat"])
                        P["dir"]["hip"][j] += c["hip_dir"][j] * L["hip"]
                    P["top"].append([round(L["acl"], 3), ph, q, round(clock[i], 1), round(v, 2), round(a, 2), round(x, 1), round(y, 1)])
            P["top"] = sorted(P["top"], reverse=True)[:12]

    def peaks(o):   # robust peaks: 99.5th percentile, so a single tracking glitch does not set the record
        al = sorted(o.pop("alist", []))
        if al:
            o["amax"] = al[min(len(al) - 1, int(0.995 * len(al)))]
            o["dmax"] = al[int(0.005 * len(al))]

    players = {}
    for pid, P in res.items():
        peaks(P["kin"])
        for KQ in P["kin"]["q"].values():
            peaks(KQ)
        n = sum(P["steps"].values())
        if not n:
            continue
        contrib = {}
        for ph, cnt in P["steps"].items():
            for mom, groups in LIB["moment_contributions"][ph].items():
                for g, share in groups.items():
                    contrib.setdefault(mom, {}).setdefault(g, 0.0)
                    contrib[mom][g] += share * cnt / n
        norm = lambda v: [round(c / (math.sqrt(sum(x * x for x in v)) or 1), 3) for c in v]
        info = meta["players"].get(pid, {})
        players[pid] = {
            "n": info.get("n", pid), "t": info.get("t", ""), "pos": info.get("pos", ""), "steps": n,
            "phases": P["steps"],
            "sum": {k: round(v, 1) for k, v in P["sum"].items()},
            "max": {k: round(v, 2) for k, v in P["max"].items()},
            "q": {q: {"steps": Q["steps"], "sum": {k: round(v, 1) for k, v in Q["sum"].items()},
                      "max": {k: round(v, 2) for k, v in Q["max"].items()}} for q, Q in P["q"].items()},
            "bins": {b: {k: round(v, 2) for k, v in d.items()} for b, d in sorted(P["bins"].items(), key=lambda kv: int(kv[0]))},
            "grid": {k: [round(v, 1) for v in g] for k, g in P["grid"].items()},
            "dir": {"knee": norm(P["dir"]["knee"]), "hip": norm(P["dir"]["hip"])},
            "contrib": {m: {g: round(s, 3) for g, s in gs.items()} for m, gs in contrib.items()},
            "top_acl": P["top"],
            "kin": {
                **{k: round(P["kin"][k], 2) for k in ("dist", "time", "vmax", "amax", "dmax")},
                "nacc": P["kin"]["nacc"], "ndec": P["kin"]["ndec"],
                "bands": {b: round(v) for b, v in P["kin"]["bands"].items()},
                "q": {q: {k: round(v, 2) for k, v in KQ.items()} for q, KQ in P["kin"]["q"].items()},
                "bins": {b: {k: round(v, 2) for k, v in d.items()} for b, d in sorted(P["kin"]["bins"].items(), key=lambda kv: int(kv[0]))},
                "grid": {k: [round(v, 1) for v in g] for k, g in P["kin"]["grid"].items()},
            },
        }
    out = {"id": gid, "date": meta["date"], "home": meta["home"], "away": meta["away"],
           "bin": BIN, "grid": [CW, CH, CELL], "library": {"version": LIB["version"], "status": LIB["status"], "note": LIB["note"]},
           "outputs": {**KIN_OUTPUTS, **LIB["outputs"]}, "frames": LIB["frames"], "players": players}
    os.makedirs(os.path.join(HERE, "load"), exist_ok=True)
    path = os.path.join(HERE, "load", f"{gid}.json")
    json.dump(out, open(path, "w"), separators=(",", ":"))
    return out, path


def write_index():
    folder = os.path.join(HERE, "load")
    idx = []
    for f in sorted(os.listdir(folder)):
        if f.endswith(".json") and f != "index.json":
            d = json.load(open(os.path.join(folder, f)))
            idx.append({"id": d["id"], "date": d["date"], "home": d["home"], "away": d["away"], "status": d["library"]["status"]})
    json.dump(idx, open(os.path.join(folder, "index.json"), "w"), separators=(",", ":"))


if __name__ == "__main__":
    for gid in sys.argv[1:]:
        out, path = game(gid)
        print(f"{gid}: {len(out['players'])} players, {os.path.getsize(path) / 1e3:.0f} kB")
        for p in sorted(out["players"].values(), key=lambda p: -p["sum"]["knee_med"])[:6]:
            print(f"  {p['n'][:22]:22} steps {p['steps']:5}  knee med {p['sum']['knee_med']:7.0f} BW  "
                  f"ACL max {p['max']['acl']:.2f} BW  ham strain max {p['max']['ham_strain']:.1f}%  "
                  f"phases {', '.join(f'{k}:{v}' for k, v in p['phases'].items() if v)}")
    write_index()
