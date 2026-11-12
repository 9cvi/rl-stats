# Rocket League Coach

A personal Rocket League stats dashboard. It's rebuilt automatically every day from the replays uploaded to ballchasing.com.

## How it works

1. **On the PC:** `pc/rl_uploader.py` runs every hour through Windows Task Scheduler (set up with `pc/setup_autoupload.bat`). It uploads new replays from `Documents\My Games\Rocket League\TAGame\DemosEpic` to ballchasing.com as private replays.
2. **On GitHub:** `.github/workflows/update.yml` runs every day at 02:17 Dubai time. `build.py` pulls the stats from the ballchasing API, and the workflow then publishes `site/` to GitHub Pages.

## Setup

- Repository secret `BALLCHASING_TOKEN`: the upload token from https://ballchasing.com/upload
- Optional repository variable `PLAYER_NAMES`: in-game names, separated by commas (default `Display_Wave`)
- Settings → Pages → Source: **GitHub Actions**

To update straight away, open Actions → *Daily stats update* → **Run workflow**.
