"""Builds site/data.json from your ballchasing.com uploads.

Runs in GitHub Actions every day. Needs the BALLCHASING_TOKEN secret.
Only the Python standard library is used.
"""
import json, os, sys, time, urllib.request, urllib.error
from pathlib import Path

API = "https://ballchasing.com/api"
TOKEN = os.environ.get("BALLCHASING_TOKEN", "").strip()
PLAYERS = [n.strip().lower() for n in os.environ.get("PLAYER_NAMES", "Display_Wave").split(",") if n.strip()]
ROOT = Path(__file__).parent
CACHE = ROOT / "data" / "games.json"
OUT = ROOT / "site" / "data.json"
MAX_GAMES = 500


def get(url, tries=6):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"Authorization": TOKEN, "User-Agent": "rl-stats-site"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(2 + i * 3)
                continue
            raise
    raise RuntimeError(f"gave up on {url}")


def n(x):
    return float(x) if isinstance(x, (int, float)) else 0.0


def pick(s):
    b, m, p, c = s.get("boost", {}), s.get("movement", {}), s.get("positioning", {}), s.get("core", {})
    d = s.get("demo", {})
    return {
        "goals": n(c.get("goals")), "assists": n(c.get("assists")), "saves": n(c.get("saves")),
        "shots": n(c.get("shots")), "score": n(c.get("score")),
        "bpm": n(b.get("bpm")), "avg_boost": n(b.get("avg_amount")),
        "zero_boost": n(b.get("percent_zero_boost")), "full_boost": n(b.get("percent_full_boost")),
        "big_pads": n(b.get("count_collected_big")), "small_pads": n(b.get("count_collected_small")),
        "stolen": n(b.get("amount_stolen")),
        "avg_speed": n(m.get("avg_speed")), "supersonic": n(m.get("percent_supersonic_speed")),
        "slow": n(m.get("percent_slow_speed")), "high_air": n(m.get("percent_high_air")),
        "ground": n(m.get("percent_ground")),
        "def_third": n(p.get("percent_defensive_third")), "off_third": n(p.get("percent_offensive_third")),
        "behind_ball": n(p.get("percent_behind_ball")), "closest": n(p.get("percent_closest_to_ball")),
        "most_back": n(p.get("percent_most_back")), "dist_ball": n(p.get("avg_distance_to_ball")),
        "demos": n(d.get("inflicted")), "demoed": n(d.get("taken")),
    }


def mean(rows):
    if not rows:
        return None
    return {k: round(sum(r[k] for r in rows) / len(rows), 2) for k in rows[0]}


def summarise(j):
    teams = {}
    for side in ("blue", "orange"):
        t = j.get(side) or {}
        for pl in t.get("players", []):
            pl["_side"] = side
        teams[side] = t
    everyone = teams["blue"].get("players", []) + teams["orange"].get("players", [])
    me = next((p for p in everyone if (p.get("name") or "").lower() in PLAYERS), None)
    if not me or "stats" not in me:
        return None
    side = me["_side"]
    other = "orange" if side == "blue" else "blue"
    gf = n(teams[side].get("stats", {}).get("core", {}).get("goals"))
    ga = n(teams[other].get("stats", {}).get("core", {}).get("goals"))
    mates = [pick(p["stats"]) for p in teams[side].get("players", []) if p is not me and "stats" in p]
    opps = [pick(p["stats"]) for p in teams[other].get("players", []) if "stats" in p]
    playlist = j.get("playlist_id") or "unknown"
    return {
        "id": j["id"], "date": j.get("date"), "playlist": playlist,
        "ranked": playlist.startswith("ranked"), "team_size": j.get("team_size") or len(teams[side].get("players", [])),
        "map": j.get("map_name") or j.get("map_code"), "duration": j.get("duration"),
        "overtime": bool(j.get("overtime")), "gf": int(gf), "ga": int(ga), "win": gf > ga,
        "me": pick(me["stats"]), "mates": mean(mates), "opps": mean(opps),
    }


def main():
    if not TOKEN:
        sys.exit("BALLCHASING_TOKEN is not set")
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    url = f"{API}/replays?uploader=me&count=200&sort-by=replay-date&sort-dir=desc"
    ids = []
    while url and len(ids) < MAX_GAMES:
        page = get(url)
        ids += [r["id"] for r in page.get("list", [])]
        url = page.get("next")
        time.sleep(0.6)
    new = 0
    for rid in ids:
        if rid in cache:
            continue
        j = get(f"{API}/replays/{rid}")
        time.sleep(0.6)
        if j.get("status") != "ok":
            continue  # still processing; picked up next run
        g = summarise(j)
        cache[rid] = g or {"id": rid, "skip": True}
        new += 1
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1))
    games = sorted((g for g in cache.values() if not g.get("skip")), key=lambda g: g["date"] or "")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "player": os.environ.get("PLAYER_NAMES", "Display_Wave").split(",")[0],
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "games": games,
    }))
    print(f"{len(games)} games ({new} new)")


if __name__ == "__main__":
    main()
