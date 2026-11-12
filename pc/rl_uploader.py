"""Uploads new Rocket League replays to ballchasing.com.

Runs on your PC every day (set up by setup_autoupload.bat).
Reads the token from rl_uploader_token.txt next to this file.
Remembers what it already uploaded in rl_uploader_done.json.
"""
import json, time, uuid, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMOS = [HERE / "TAGame" / "DemosEpic", HERE / "TAGame" / "Demos"]
TOKEN = (HERE / "rl_uploader_token.txt").read_text().strip()
DONE = HERE / "rl_uploader_done.json"
LOG = HERE / "rl_uploader.log"


def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def upload(path):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://ballchasing.com/api/v2/upload?visibility=private", data=body, method="POST",
                                 headers={"Authorization": TOKEN, "Content-Type": f"multipart/form-data; boundary={boundary}",
                                          "User-Agent": "rl-stats-uploader"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def main():
    done = set(json.loads(DONE.read_text())) if DONE.exists() else set()
    files = sorted((f for d in DEMOS if d.exists() for f in d.glob("*.replay")), key=lambda f: f.stat().st_mtime)
    new = [f for f in files if f.name not in done]
    log(f"{len(new)} new replay(s)")
    for f in new:
        status, body = upload(f)
        if status in (200, 201, 409):  # 409 = already on ballchasing
            done.add(f.name)
            log(f"ok {status} {f.name}")
        elif status == 429:
            log("daily upload limit reached, the rest will go tomorrow")
            break
        else:
            log(f"failed {status} {f.name}: {body[:200]}")
        DONE.write_text(json.dumps(sorted(done)))
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"error: {e!r}")
