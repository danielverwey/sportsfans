# Publishing the APEX atlases

The site is static: GitHub Pages serves `docs/` on `main`. Nothing runs server-side.

## First release (from `C:\Users\Daniel\Sportsfans`)

```powershell
cd C:\Users\Daniel\Sportsfans
git init -b main
git add .
git commit -m "APEX sports atlases: F1, rugby, cricket, tennis"
```

Create an empty repository on GitHub (no README, no .gitignore), then:

```powershell
git remote add origin https://github.com/<you>/Sportsfans.git
git push -u origin main
```

Turn on Pages: **Settings → Pages → Build and deployment → Source: GitHub Actions.** The `Build and deploy` workflow runs on every push to `main`: it rebuilds `docs/` (including the data files and offline editions, which are not committed), refuses if the committed pages drifted, checks every internal link and publishes. The site appears within a couple of minutes. (Deploy-from-branch with `/docs` also works, but the sweepers rely on the Actions route.)

## The domain: sportsfans.co.za

The build already targets the domain: `python build.py` writes `docs/CNAME` containing `sportsfans.co.za` and uses `https://sportsfans.co.za` for canonical links and the sitemap. Once the repository is pushed:

1. At the registrar for sportsfans.co.za, create these DNS records (GitHub's published addresses):

   | Type | Host | Value |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153` (optional, IPv6) |
   | CNAME | `www` | `<you>.github.io` |

2. On GitHub: **Settings → Pages → Custom domain → `sportsfans.co.za` → Save.** GitHub checks the DNS; when it passes, tick **Enforce HTTPS** (the option can take up to 24 hours to appear while the certificate issues).

3. `www.sportsfans.co.za` then redirects to the apex domain automatically.

To preview on GitHub's own address before the DNS is live, build without the CNAME file and with that URL:

```powershell
python build.py --site https://<you>.github.io/Sportsfans --no-cname
```

and rebuild with plain `python build.py` before the real release, so the CNAME and canonical links go back to the domain.

## What runs on its own

| Workflow | When | What it does |
|---|---|---|
| `Build and deploy` | every push to `main`, on demand | rebuild, drift check, link check, publish |
| `Sweep · Formula 1` | Mondays 06:00 UTC, on demand | harvests the current season from Jolpica, runs the gate (history immutable, current season only grows, reference facts hold), rebuilds, commits `data: f1 sweep <date>` and deploys; an idle week commits nothing; a gate failure leaves the site untouched and the run red |
| `Verify in a browser` | Mondays 07:30 UTC, on demand | Playwright over every atlas: seasons × tabs × eras, phone width, deep links, offline editions |
| `Harvest · MotoGP and WorldSBK from Wikipedia` | on demand | the clean-room rebuild: writes the archive and a coverage report as artifacts for review; commits nothing |
| `Circuit outlines from OpenStreetMap` | on demand | fetches raceway geometry for every circuit of a bikes archive that still lacks one into `src/bikes/assets_<sport>.json` and commits it — run it for `motogp` and for `sbk` after a data update; the outlines it adds go live on the next deploy |

Sweepers for the other sports are switched on as each one's rights position and source cadence settle (see ACTION-PLAN.md): rugby waits on the permission emails; cricket (Cricsheet publishes new scorecards daily) and tennis (Sackmann's repositories update irregularly) get theirs in the next phase — until then, re-run the prepare script on a fresh export and push. Failed runs email the repository owner.

## Held sports

`build.py` publishes the sports in its `PUBLISH` list — all seven today. A sport taken out of the list is built into `build/held/` as an offline edition and stays off the site and out of the sitemap; the hub shows it as held. `python build.py --publish f1,rugby,motogp,sbk` overrides the list.

## Updating an atlas

1. Replace `data/<sport>.json` with the newer export. For cricket and tennis, run `python tools/prepare_cricket.py <export>` or `python tools/prepare_tennis.py <export>` instead: they write the core file and the yearly shards.
2. `python build.py`
3. `node tools/check_site.js <sport>` and `python tools/check_links.py` — both must end clean.
4. Commit `data/` and `docs/` together and push. The deploy workflow rebuilds, checks and publishes; the static pages, sitemap, reading edition and offline edition all come from the same build.

## What is in the repository

About 420 MB: the archives and their shards (130 MB in `data/`), the reading editions and ~22,000 static pages (290 MB in `docs/`). `docs/data/`, `docs/downloads/` and `HTML FILEs/` are not committed — the build regenerates them from `data/` and `src/`, and the deploy workflow does the same before publishing. The published site is about 400 MB, within GitHub Pages’ 1 GB limit, served gzip-compressed.

## Sharing a single atlas without the site

Each file in `docs/downloads/` (and its local copy in `HTML FILEs/`) is complete on its own: attach it, drop it on any web host, or open it from disk. The lights-out opening plays once per browser session; everything else is inside the file.

## Size notes

The live atlas pages are small shells; the archive each fetches is 2.5–10.5 MB of JSON (roughly 3–4× smaller gzip-compressed on the wire) and is cached by the browser between visits. Cricket fetches a 0.5–2 MB scorecard shard the first time a season’s match is opened; tennis fetches a 0.7–1.1 MB shard the first time a season’s draw is opened, and a head-to-head loads the seasons the two players shared. The offline editions are 3.4–17 MB each; the two large ones embed their archive gzipped.
