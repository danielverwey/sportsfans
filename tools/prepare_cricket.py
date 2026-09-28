#!/usr/bin/env python3
"""Split the cricket prototype's archive into the site's core file and per-season detail shards.

    python tools/prepare_cricket.py <extracted prototype JSON>

data/cricket.json               everything except scorecards and line-ups (results, player-season figures, registers, titles)
data/cricket_details/<year>.json  {gameId: {inn, players}} for the games with a recorded scorecard
The archive's content is not edited; it is only divided.
"""
import json, sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
src = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
core = {k: v for k, v in src.items() if k != 'games'}
core['games'] = []; details = collections.defaultdict(dict)
for g in src['games']:
    lean = {k: v for k, v in g.items() if k not in ('inn', 'players')}
    lean['sc'] = [[i[0], i[1], i[2], i[3], int(bool(i[4])), int(bool(i[5])), int(bool(i[6]))] for i in g.get('inn', [])]   # innings totals stay in the core; the scorecards go to the shards
    core['games'].append(lean)
    if g.get('inn') or g.get('players'): details[g['y']][g['id']] = {'inn': g.get('inn', []), 'players': g.get('players', [])}
for t in core['teams'].values(): t.pop('logo', None)   # flags are the flag-icons set (MIT); no other artwork is carried
core['detailYears'] = sorted(details)
(ROOT/'data'/'cricket.json').write_text(json.dumps(core, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
d = ROOT/'data'/'cricket_details'; d.mkdir(exist_ok=True)
for y, games in details.items(): (d/f'{y}.json').write_text(json.dumps(games, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'core {(ROOT/"data"/"cricket.json").stat().st_size/1e6:.1f} MB · {len(details)} detail shards · {sum(len(v) for v in details.values())} games with scorecards · {sum(p.stat().st_size for p in d.glob("*.json"))/1e6:.1f} MB')
