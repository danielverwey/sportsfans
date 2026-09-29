"""UFC: every event since the archive's last one, read from its Wikipedia article (tools/harvest/wiki_ufc.py), and the last
three weeks read again so corrections land. The archive is turned back into the harvest shape (prepare_ufc.unprepare),
the new events are merged into it — existing events, fighters and ids are kept — and the whole is prepared again, so
records, venues and coverage are recomputed exactly as the first import computed them.
"""
import copy, datetime, json, pathlib, re, sys, unicodedata, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
import prepare_ufc as P

WINDOW_DAYS = 21
norm = lambda s: re.sub(r'[^a-z0-9]+', ' ', (s or '').lower().replace('’', "'")).strip()
fold = lambda s: re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower())   # 'Rafa García' = 'Rafa Garcia', 'Rong Zhu' = 'Rongzhu'
wiki_url = lambda title: 'https://en.wikipedia.org/wiki/' + title.replace(' ', '_') if title else None
def title_of_url(url):
    return urllib.parse.unquote(url.split('/wiki/')[-1]).replace('_', ' ') if url and '/wiki/' in url else None

def fetch_wikipedia(since, log):
    import wiki_ufc
    out, *_ = wiki_ufc.harvest(y0=int(since[:4]), since=since, before_today=True, log=log)
    canon = wiki_ufc.canonical_titles([f.get('title') for f in out['fighters'].values()], log)
    for f in out['fighters'].values():
        if f.get('title'): f['title'] = canon.get(f['title'], f['title']); f['url'] = wiki_url(f['title'])
    return out

def complete(ev, bouts):
    """A card counts only once its results are in: every bout has a method (a card still being fought, or not yet
    updated on Wikipedia, lists its bouts with 'vs.' and nothing after)."""
    return bool(bouts) and all((b.get('method') or '').strip() for b in bouts)

def merge(H, new, log, today):
    """Merge a harvest window into the archive's harvest shape. Returns the number of events added or refreshed."""
    F = H['fighters']; by_title = {title_of_url(f['url']): fid for fid, f in F.items() if f.get('url')}
    by_name = {}
    for fid, f in F.items(): by_name.setdefault(fold(f['name']), []).append(fid)
    idmap = {}
    for nid, nf in new['fighters'].items():
        url = nf.get('url') or wiki_url(nf.get('title'))
        fid = by_title.get(title_of_url(url)) if url else None
        if not fid and len(by_name.get(fold(nf['name']), [])) == 1: fid = by_name[fold(nf['name'])][0]
        if fid:
            old = F[fid]
            for k in ('nat', 'dob', 'height_cm'):
                if not old.get(k) and nf.get(k): old[k] = nf[k]
            if not old.get('url') and url: old['url'] = url
        else:
            fid = nid; k = 2
            while fid in F: fid = f'{nid}-{k}'; k += 1
            F[fid] = {'id': fid, 'name': nf['name'], 'url': url, 'title': nf.get('title'), 'nat': nf.get('nat') or [], 'dob': nf.get('dob'), 'height_cm': nf.get('height_cm')}
            by_name.setdefault(fold(nf['name']), []).append(fid)
            if url: by_title[title_of_url(url)] = fid
            log.append(f'  - new fighter: {nf["name"]}')
        idmap[nid] = fid
    evs = {e['id']: e for e in H['events']}
    on_date = {}
    for e in H['events']: on_date.setdefault(e['date'], []).append(e)
    nb = {}
    for b in new['bouts']: nb.setdefault(b['e'], []).append(b)
    pages = {p.get('title'): p for p in H.get('pages') or []}
    next_n = max((e.get('n') or 0) for e in H['events']) + 1
    touched = 0
    for ev in sorted(new['events'], key=lambda e: e['date']):
        bouts = sorted(nb.get(ev['id'], []), key=lambda b: b['n'])
        if not complete(ev, bouts):
            log.append(f'- {ev["name"]} ({ev["date"]}): results not in yet — left for the next sweep'); continue
        same = [e for e in on_date.get(ev['date'], []) if e['id'] == ev['id'] or norm(e['name']) == norm(ev['name']) or norm(e['name']).split(' ')[:3] == norm(ev['name']).split(' ')[:3]]
        if not same and len(on_date.get(ev['date'], [])) == 1: same = on_date[ev['date']]
        old = same[0] if same else None
        if old:
            old_bouts = [b for b in H['bouts'] if b['e'] == old['id']]
            if len(bouts) < len(old_bouts):
                log.append(f'- {ev["name"]}: Wikipedia now lists {len(bouts)} bouts, the archive {len(old_bouts)} — the archive is kept'); continue
            eid = old['id']; n = old.get('n')
        else:
            eid = ev['id']; k = 2
            while eid in evs: eid = f'{ev["id"]}-{k}'; k += 1
            n = next_n; next_n += 1
        rec = {'id': eid, 'n': n, 'name': ev['name'], 'title': ev.get('title') or ev['name'], 'date': ev['date'], 'y': ev['y'], 'venue': ev.get('venue') or (old or {}).get('venue') or '',
               'city': ev.get('city') or (old or {}).get('city') or '', 'attendance': ev.get('attendance') or (old or {}).get('attendance'), 'gate': ev.get('gate'), 'buyrate': ev.get('buyrate'),
               'url': ev.get('url') or wiki_url(ev.get('title')) or (old or {}).get('url'), 'bouts': [], 'bonuses': ev.get('bonuses') or (old or {}).get('bonuses') or []}
        new_bouts = [{'id': f'{eid}#{k + 1}', 'e': eid, 'date': ev['date'], 'y': ev['y'], 'n': k + 1, 'card': b['card'], 'wc': b['wc'], 'a': idmap.get(b['a'], b['a']), 'b': idmap.get(b['b'], b['b']),
                      'champ': b.get('champ') or [], 'sep': b['sep'], 'method': b['method'], 'round': b['round'], 'time': b['time'], 'notes': b['notes']} for k, b in enumerate(bouts)]
        rec['bouts'] = [b['id'] for b in new_bouts]
        if old:
            before = json.dumps([{k: v for k, v in b.items() if k not in ('title', 'tour')} for b in old_bouts], sort_keys=True)
            if before == json.dumps(new_bouts, sort_keys=True) and old.get('venue') == rec['venue'] and old.get('attendance') == rec['attendance']: continue
            H['events'] = [rec if e['id'] == eid else e for e in H['events']]
            H['bouts'] = [b for b in H['bouts'] if b['e'] != eid]
            log.append(f'- {ev["name"]} ({ev["date"]}): re-read, {len(new_bouts)} bouts')
        else:
            H['events'].append(rec); evs[eid] = rec; on_date.setdefault(ev['date'], []).append(rec)
            log.append(f'- **{ev["name"]}** ({ev["date"]}): {len(new_bouts)} bouts added')
        H['bouts'] += new_bouts; touched += 1
        t = ev.get('title') or ev['name']
        if ev.get('revid'):
            pages[t] = {'requested': t.replace(' ', '_'), 'title': t, 'revision': ev['revid'], 'retrieved': today, 'sha256': ev.get('sha256')}
    H['pages'] = list(pages.values())
    for i in new.get('issues') or []:
        if i not in H['issues'] and i.get('date', '') > max((e['date'] for e in H['events']), default=''): H['issues'].append(i)
    return touched

def sweep(log, fetch=None, today=None):
    today = today or datetime.date.today()
    path = ROOT/'data'/'ufc.json'; core = json.loads(path.read_text(encoding='utf-8'))
    H = P.unprepare(core)
    # the archive must come back through the converter byte for byte, or a merge could not be trusted
    if json.dumps(P.prepare(copy.deepcopy(H)), ensure_ascii=False, sort_keys=True) != json.dumps(core, ensure_ascii=False, sort_keys=True):
        raise SystemExit('data/ufc.json does not come back unchanged through tools/prepare_ufc.py — the converter and the archive disagree; nothing written')
    log.append('Round trip: the archive comes back unchanged through prepare_ufc.py.')
    after_last = (datetime.date.fromisoformat(core['lastDate']) + datetime.timedelta(days=1)).isoformat()
    since = min((today - datetime.timedelta(days=WINDOW_DAYS)).isoformat(), after_last)
    log.append(f'Archive through {core["lastDate"]}; reading every event from {since} to yesterday.'); log.append('')
    new = (fetch or fetch_wikipedia)(since, log)
    touched = merge(H, new, log, today.isoformat())
    if not touched: log.append('- nothing new'); return
    H['snapshot'] = today.isoformat()
    out = P.prepare(H)
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    c = out['coverage']; log += ['', f'Archive now {c["events"]} events · {c["bouts"]:,} bouts · {c["fighters"]:,} fighters, through {out["lastDate"]}.']
