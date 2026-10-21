# NBA Shot Maps

Interactive shot charts for every NBA game since the 2009–10 season: pick a game and scrub through it with the time slider, compare two players (per game, season or career) or two teams (untick players to see the team without them).

Live page: https://basgoncalves.github.io/nba/shotmap/

## How it works

- `fetch.py` downloads finished games from ESPN's public API into `raw/<season>/<gameId>.json` (one small file per game, written once).
- `build.py` turns those into the files the page reads (games list, player and team files) in a site folder.
- `.github/workflows/update-shotmap.yml` runs both twice a day and publishes the site with GitHub Pages (Settings → Pages → Source: **GitHub Actions**). Pushing changes to `index.html` or `build.py` republishes without downloading.

Shot locations come from ESPN play-by-play and are rounded to about a foot. Some older games have no locations.
