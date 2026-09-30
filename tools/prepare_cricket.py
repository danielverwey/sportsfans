#!/usr/bin/env python3
"""Split the cricket prototype's archive into the site's core file and per-season detail shards.

    python tools/prepare_cricket.py <the reader's export: the prototype page, or its archive as .json / .json.gz>

data/cricket.json               everything except scorecards and line-ups (results, player-season figures, registers, titles,
                                the career register as rows under careerFields)
data/cricket_details/<year>.json  {gameId: {inn, players}} for the games with a recorded scorecard
The archive's content is not edited; it is only divided. unprepare() puts it back together (the sweeper uses it).
"""
import json, sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools')); from archive_in import load_archive

def prepare(src):
    """The whole archive → (core, {year: {gameId: {inn, players}}}). Pure."""
    core = {k: v for k, v in src.items() if k != 'games'}
    core['games'] = []; details = collections.defaultdict(dict)
    for g in src['games']:
        lean = {k: v for k, v in g.items() if k not in ('inn', 'players')}
        lean['sc'] = [[i[0], i[1], i[2], i[3], int(bool(i[4])), int(bool(i[5])), int(bool(i[6]))] for i in g.get('inn', [])]   # innings totals stay in the core; the scorecards go to the shards
        core['games'].append(lean)
        if g.get('inn') or g.get('players'): details[g['y']][g['id']] = {'inn': g.get('inn', []), 'players': g.get('players', [])}
    for t in core['teams'].values(): t.pop('logo', None)   # flags are the flag-icons set (MIT); no other artwork is carried
    cs = src.get('careers')
    if cs and isinstance(cs[0], dict) and all(tuple(c) == tuple(cs[0]) for c in cs):   # the career register as rows under one field list
        core['careerFields'] = list(cs[0]); core['careers'] = [list(c.values()) for c in cs]
    core['detailYears'] = sorted(details)
    return core, details

def read_details():
    return {int(f.stem): json.loads(f.read_text(encoding='utf-8')) for f in sorted((ROOT/'data'/'cricket_details').glob('*.json'))}

def unprepare(core, details):
    """The site's files back into the whole archive, so prepare(unprepare(core, details)) gives them again."""
    src = {k: v for k, v in core.items() if k not in ('games', 'detailYears', 'careerFields')}
    if 'careerFields' in core: src['careers'] = [dict(zip(core['careerFields'], r)) for r in core['careers']]
    games = []
    for g in core['games']:
        x = {k: v for k, v in g.items() if k != 'sc'}
        d = details.get(g['y'], {}).get(g['id'])
        if d is not None: x['inn'] = d['inn']; x['players'] = d['players']
        games.append(x)
    src['games'] = games
    return src

def write(core, details):
    (ROOT/'data'/'cricket.json').write_text(json.dumps(core, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    d = ROOT/'data'/'cricket_details'; d.mkdir(exist_ok=True)
    for y, games in details.items(): (d/f'{y}.json').write_text(json.dumps(games, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return d

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit('usage: python tools/prepare_cricket.py <prototype page or archive .json>')
    src = load_archive(sys.argv[1], need=('games', 'teams', 'players'))
    core, details = prepare(src)
    d = write(core, details)
    print(f'core {(ROOT/"data"/"cricket.json").stat().st_size/1e6:.1f} MB · {len(details)} detail shards · {sum(len(v) for v in details.values())} games with scorecards · {sum(p.stat().st_size for p in d.glob("*.json"))/1e6:.1f} MB')
