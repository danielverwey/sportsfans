#!/usr/bin/env python3
"""Bring Daniel's cricket harvests into the archive: the rebuilt player register (expanded names, aliases, the historical
players and their Wikipedia career lines), the name gap-fill, and the scorecards of the internationals that had a result
but no scorecard.

    python tools/merge_cricket_harvest.py --prototype <cricket_atlas_1877_2026_rebuilt.html>
                                          --names <cricket_names_harvest.json>
                                          --cards <cricket_harvest_progress.json>

Reads data/cricket.json + data/cricket_details/ (through prepare_cricket.unprepare), writes them back through prepare.
Nothing the archive already holds is overwritten: results, dates, grounds and Cricsheet scorecards stay as they are. A
match gets a scorecard only if it has none; the toss and the last day are filled only where the archive left them blank.
Every scorecard keeps its source (`cardSource` on the match, `cardSources` at the top of the archive).

What a historical scorecard carries is what its source carries: batting (runs, and balls, fours and sixes where they were
recorded), how each batter was out and the fielder where named, bowling figures, the extras total and the line-ups. The
bowler credited with a dismissal is usually not in the source and is left blank rather than guessed; there are no
ball-by-ball progressions, so no worm or fall of wickets.
"""
import argparse, collections, datetime, hashlib, json, pathlib, re, sys, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'sweepers'))
from archive_in import load_archive
import prepare_cricket as P
from cricket import season_rows

SOURCE_LABEL = {'test_hf': 'Test cricket dataset 1877–2014', 'odi_hf': 'ODI cricket dataset 1971–2014', 't20i_hf': 'T20I cricket dataset 2005–2014', 'cricbuzz_public_scorecards': 'Cricbuzz scorecards'}
HOW = {'caught': 'caught', 'bowled': 'bowled', 'lbw': 'lbw', 'run out': 'run out', 'stumping': 'stumped', 'stumped': 'stumped', 'hitwicket': 'hit wicket',
       'hit wicket': 'hit wicket', 'not out': 'not out', 'caught and bowled': 'caught and bowled', 'handled the ball': 'handled the ball',
       'obstructing the field': 'obstructing the field', 'retired out': 'retired out', 'retired hurt': 'retired hurt', 'retired not out': 'retired not out'}
SLACK = 2   # years a career list's span may be off by (lists round, lag, or count a season's first year)
BOWLER_KINDS = {'bowled', 'caught', 'caught and bowled', 'lbw', 'stumped', 'hit wicket'}
NOT_OUT = {'not out', 'retired hurt', 'retired not out'}
fold = lambda s: re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', re.sub(r'^(Sir|Dame)\s+', '', (s or '').replace('ı', 'i'))).encode('ascii', 'ignore').decode().lower())

def log_(msg, out): out.append(msg); print(msg)

# ---------------------------------------------------------------- the register: names and careers
def merge_register(src, proto, names, out):
    """Players, careers and the name queue from the rebuilt prototype, with the later gap-fill's names applied."""
    PL = src['players']; PP = proto['players']; R = names['player_register']
    kept = {k: v for k, v in PL.items() if k not in PP}          # anyone a sweep added after the prototype was built
    players = {}
    for k, p in PP.items():
        p = dict(p); r = R.get(k)
        if r:
            if r.get('name') and r['name'] != p.get('n'):
                p['n'] = r['name']
                res = r.get('name_resolution') or {}
                lic = res.get('licence'); url = res.get('source_url') or ''
                p['nameSource'] = res.get('source') or ('Wikidata' if 'wikidata.org' in url else 'Wikipedia contributors' if 'wikipedia.org' in url else (re.sub(r'^https?://(www\.)?', '', url).split('/')[0] if url else 'verified source'))
            if r.get('aliases') and r['aliases'] != p.get('aliases'): p['aliases'] = r['aliases']
            if r.get('full_name') and not p.get('fullName') and r['full_name'] != p['n']: p['fullName'] = r['full_name']
            if r.get('wikipedia_article') and not p.get('wiki'): p['wiki'] = r['wikipedia_article']
        players[k] = p
    for k, p in kept.items(): players[k] = p
    changed = sum(1 for k in PP if PP[k].get('n') != players[k]['n'])
    src['players'] = players
    src['careers'] = proto['careers']; src['careerSources'] = proto['careerSources']
    src['outstandingNames'] = names.get('unresolved') or []
    rb = dict(proto.get('rebuild') or {})
    rb.update(date=names.get('created') or rb.get('date'), expandedOriginalNames=(rb.get('expandedOriginalNames') or 0) + changed,
              unresolvedNames=len(src['outstandingNames']), unresolvedOriginalNames=len(src['outstandingNames']))
    src['rebuild'] = rb
    log_(f'register: {len(players):,} players ({len(players) - len(PL):,} new historical identities), {changed} names expanded by the gap-fill, {len(src["careers"]):,} career lines from {len(src["careerSources"])} Wikipedia lists, {len(src["outstandingNames"])} names still unresolved', out)

# ---------------------------------------------------------------- identities: the scorecard sources' ids → the atlas's players
class Ids:
    def __init__(self, src, H, out):
        self.P = src['players']; self.H = H['players']; self.out = out; self.memo = {}; self.minted = {}
        self.by_espn = {str(v['espn']): k for k, v in self.P.items() if v.get('espn')}
        self.by_name = collections.defaultdict(set)
        for k, v in self.P.items():
            for n in {v.get('n'), v.get('short'), v.get('fullName'), *(v.get('aliases') or [])}:
                if n: self.by_name[fold(n)].add(k)
        self.career = collections.defaultdict(list)
        for c in src['careers']: self.career[c['p']].append(c)
        self.seen = collections.defaultdict(set)   # (player, team, gender, format) → years with a recorded scorecard
        for r in src['ps']: self.seen[(r[4], r[3], r[2], r[1])].add(r[0])
        self.ctx = collections.defaultdict(set)    # hid → {(team, gender, format, year)}
        self.joined = {}                           # register entry → the entry it was joined into
        self.subctx = collections.defaultdict(set) # hid → the sides he fielded for as a substitute
        self.stats = collections.Counter()

    def note(self, hid, team, g, f, y, sub=False):
        """An appearance; a substitute fielder's is kept apart, since a career list does not count it as a match."""
        (self.subctx if sub else self.ctx)[hid].add((team, g, f, y))

    def fits(self, pid, ctx):
        """No career line of this player's contradicts the appearances (team, format, year)."""
        cs = self.career.get(pid, [])
        for t, g, f, y in ctx:
            mine = [c for c in cs if c['t'] == t and c['f'] == f and c['g'] == g]
            if mine and not any(c['first'] - SLACK <= y <= c['last'] + SLACK for c in mine): return False
        return True

    def merge(self, ids_):
        """Join register entries that are one person: the careers move to the entry with the most games."""
        games = lambda c: sum(x.get('games') or 0 for x in self.career.get(c, []))
        keep, *rest = sorted(ids_, key=lambda c: -games(c))
        k = self.P[keep]
        for r in rest:
            o = self.P.pop(r)
            for c in self.career.pop(r, []): c['p'] = keep; self.career[keep].append(c)
            k['aliases'] = sorted(set(k.get('aliases') or []) | set(o.get('aliases') or []) | {o['n']})
            for f in ('teams', 'gender'):
                for x in o.get(f) or []:
                    if x not in k.setdefault(f, []): k[f].append(x)
            if not k.get('fullName') and o.get('fullName'): k['fullName'] = o['fullName']
            for n in {o.get('n'), o.get('fullName'), *(o.get('aliases') or [])}:
                if n: self.by_name[fold(n)].discard(r); self.by_name[fold(n)].add(keep)
            self.joined[r] = keep
        return keep

    def surname_pass(self, hids):
        """A player whose scorecard name is not the register's (Tip Foster for Reginald Foster, Charles for Charlie
        Macartney): same surname, same side and gender, and a register career in every format and year he appears in — and
        only when he is the one scorecard identity that fits that register player and that register player is the only
        one that fits him."""
        claimed = set(self.memo.values())
        per_team = collections.Counter((t, fold(v['n'].split()[-1])) for v in self.P.values() if v.get('n') and v['n'].split() for t in v.get('teams') or [])
        want = {}
        for hid in hids:
            if hid in self.memo: continue
            h = self.H.get(hid) or {}; ctx = self.ctx.get(hid, set())
            if not h.get('name') or not ctx: continue
            bare = re.sub(r'^(Sir|Dame)\s+', '', re.sub(r'[†*]', '', h['name'])).strip()
            sur = fold(bare.split()[-1]) if bare.split() else ''
            cands = []; recorded = []
            for k, v in self.P.items():
                # an entry already taken can still be this player's under a Cricbuzz id (no Cricinfo id to tell them apart)
                if (k in claimed and h.get('espn_id')) or (v.get('espn') and h.get('espn_id')): continue
                names = {v.get('n'), v.get('fullName'), *(v.get('aliases') or [])}
                if not any(n and fold(n.split()[-1]) == sur for n in names): continue
                same_team = max(per_team[(t, sur)] for t, *_ in ctx)
                init = lambda n: fold(re.sub(r'[†*\'"]', '', n))[:1]
                if same_team > 2 and not any(n and init(n) == init(h['name']) for n in names): continue   # a common surname needs the same initial too
                cs = self.career.get(k, [])
                by_list = lambda it: any(c['t'] == it[0] and c['g'] == it[1] and c['f'] == it[2] and c['first'] - 1 <= it[3] <= c['last'] + 1 for c in cs)
                by_card = lambda it: any(abs(y - it[3]) <= 1 for y in self.seen.get((k, it[0], it[1], it[2]), ()))
                if all(by_list(it) or by_card(it) for it in ctx):
                    cands.append(k)
                    if all(by_card(it) for it in ctx): recorded.append(k)
            if len(cands) > 1 and len(recorded) == 1: cands = recorded   # the one the scorecards already know
            if len(cands) == 1: want[hid] = cands[0]
        by_pid = collections.defaultdict(list)
        for hid, pid in want.items(): by_pid[pid].append(hid)
        def same_person(hs):   # the Cricbuzz and dataset ids of one player want the same entry: same name, at most one Cricinfo id
            hh = [self.H.get(x) or {} for x in hs]
            return len({fold(x.get('name')) for x in hh}) == 1 and len({x.get('espn_id') for x in hh if x.get('espn_id')}) <= 1
        for hid, pid in want.items():
            if len(by_pid[pid]) == 1 or same_person(by_pid[pid]):
                self.memo[hid] = pid; self.stats['same surname, side and career (name differs)'] += 1
                h = self.H.get(hid) or {}
                if h.get('espn_id') and not self.P[pid].get('espn'): self.P[pid]['espn'] = str(h['espn_id']); self.by_espn[str(h['espn_id'])] = pid
                al = self.P[pid].setdefault('aliases', [])
                for n in {h.get('name'), h.get('source_name')}:
                    if n and n not in al: al.append(n)
                self.P[pid]['aliases'] = sorted(al)

    def resolve_all(self, hids):
        for hid in hids: self.resolve(hid, mint=False)
        self.surname_pass(hids)
        for hid in hids: self.resolve(hid)

    def resolve(self, hid, mint=True):
        if hid in self.memo: return self.memo[hid]
        h = self.H.get(hid) or {}; ctx = self.ctx.get(hid) or self.subctx.get(hid, set()); pid = None
        teams = {t for t, *_ in ctx}; gens = {g for _, g, *_ in ctx}
        a = h.get('atlas_player_id')
        if a and a in self.P: pid = a; self.stats['given by the harvest'] += 1
        elif h.get('espn_id') and str(h['espn_id']) in self.by_espn: pid = self.by_espn[str(h['espn_id'])]; self.stats['same Cricinfo id'] += 1
        elif h.get('name'):
            cands = set()
            for n in {h.get('name'), h.get('source_name')}:
                cands |= {c for c in self.by_name.get(fold(n), ()) if set(self.P[c].get('teams') or []) & teams and set(self.P[c].get('gender') or []) & gens}
            cands = {c for c in cands if not self.P[c].get('espn') or not h.get('espn_id')}   # two different Cricinfo ids are two people
            fit = [c for c in cands if self.fits(c, ctx)]
            if len(fit) == 1: pid = fit[0]; self.stats['same name, side and career'] += 1
            elif len(fit) > 1:
                covers = lambda c, item: any(c2['t'] == item[0] and c2['g'] == item[1] and c2['f'] == item[2] and c2['first'] - SLACK <= item[3] <= c2['last'] + SLACK for c2 in self.career.get(c, []))
                whole = [c for c in fit if all(covers(c, it) for it in ctx)]
                part = [c for c in fit if any(covers(c, it) for it in ctx)]
                if len(whole) == 1: pid = whole[0]; self.stats['same name, side and career'] += 1
                elif not whole and len(part) > 1 and all(covers_any for covers_any in (any(covers(c, it) for c in part) for it in ctx)) \
                        and all(c.startswith('hist-') and not self.P[c].get('espn') and c not in set(self.memo.values()) for c in part):
                    # one Cricinfo identity whose Test career and ODI career the Wikipedia lists gave as two people
                    pid = self.merge(part); self.stats['same name, side and career (two register entries joined)'] += 1
                elif mint: self.stats['ambiguous name — new identity'] += 1
        if pid is None and not mint: return None
        if pid is None and h.get('name'):
            key = f'espn:{h["espn_id"]}' if h.get('espn_id') else hid
            pid = 'hist-' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]
            if pid not in self.P:
                self.P[pid] = {'n': h['name'], 'short': h.get('source_name') or h['name'], 'espn': str(h.get('espn_id') or ''), 'teams': sorted(teams), 'gender': sorted(gens),
                               'aliases': sorted({h['name'], h.get('source_name') or h['name']}), 'nameSource': 'scorecard source'}
                self.minted[pid] = hid; self.stats['new identity from the scorecard source'] += 1
                if h.get('espn_id'): self.by_espn[str(h['espn_id'])] = pid
                for n in {h['name'], h.get('source_name')}:   # the same player under the other source's id finds this one
                    if n: self.by_name[fold(n)].add(pid)
        if pid and h.get('espn_id') and not self.P[pid].get('espn'): self.P[pid]['espn'] = str(h['espn_id']); self.by_espn[str(h['espn_id'])] = pid
        self.memo[hid] = pid
        return pid

# ---------------------------------------------------------------- one scorecard
def by_label(ids, H):
    """{folded name or surname: {hid}} for a side, to read names out of dismissal text."""
    out = collections.defaultdict(set)
    for i in ids:
        h = H.get(i) or {}
        for n in {h.get('name'), h.get('source_name')}:
            if not n: continue
            out[fold(n)].add(i); parts = re.sub(r'[†*]', '', n).split()
            if parts: out[fold(parts[-1])].add(i)
    return out

def names_in(text, labels):
    got = []
    for part in re.split(r'/', text):
        k = fold(re.sub(r'\(.*?\)|†|\*|\bsub\b', '', part))
        c = labels.get(k) or set()
        if len(c) == 1: got.append(next(iter(c)))
    return got

def parse_dismissal(text, kind, bat_labels, field_labels):
    """(bowler hid or None, [fielder hids]) from a dismissal line like 'c Tendulkar b Prabhakar' or 'run out (Kapil/More)'."""
    t = (text or '').strip()
    if not t: return None, []
    bowler = None; fielders = []
    m = re.search(r'(?:^|\s)b\s+(.+)$', t)
    if m and kind in BOWLER_KINDS:
        c = field_labels.get(fold(re.sub(r'†|\*', '', m.group(1)))) or set()
        if len(c) == 1: bowler = next(iter(c))
    if kind == 'caught':
        m = re.match(r'c\s+(.+?)\s+b\s+', t)
        if m and not re.match(r'(&|and)$', m.group(1)): fielders = names_in(m.group(1), field_labels)
    elif kind == 'stumped':
        m = re.match(r'st\s+(.+?)\s+b\s+', t)
        if m: fielders = names_in(m.group(1), field_labels)
    elif kind == 'run out':
        m = re.search(r'\((.+?)\)', t)
        if m: fielders = names_in(m.group(1), field_labels)
    return bowler, fielders

def lineup_of(m):
    """{team: [source ids]}: the listed eleven, plus a replacement who batted or bowled without being listed."""
    xi = m.get('participants_from_batting_scorecard') or m.get('playing_xi') or {}
    teams = list(xi) or list(m['teams'])
    lineup = {t: list(xi.get(t, [])) for t in teams}
    for inn in m['innings']:
        bt = inn['team']; ft = next((t for t in teams if t != bt), None)
        for b in inn['batting']:
            if b['player'] not in lineup.get(bt, []): lineup.setdefault(bt, []).append(b['player'])
        for b in inn['bowling']:
            if ft and b['player'] not in lineup.get(ft, []): lineup.setdefault(ft, []).append(b['player'])
    return teams, lineup

def note_all(m, ids):
    """Pass one: every appearance (and every substitute fielder's side) is known before any identity is decided."""
    teams, lineup = lineup_of(m); y = int(m['date'][:4]); g = m['gender']; f = m['format']
    for t, hs in lineup.items():
        for h in hs: ids.note(h, t, g, f, y)
    for inn in m['innings']:
        ft = next((t for t in teams if t != inn['team']), None)
        for b in inn['batting']:
            for x in b.get('fielders') or []:
                if x and ft and x not in lineup.get(ft, []): ids.note(x, ft, g, f, y, sub=True)

def card_of(m, ids, H, out):
    """A harvested match → (inn rows, line-ups, balls per over)."""
    teams, lineup = lineup_of(m)
    f = m['format']
    bpos = {inn.get('balls_per_over') for inn in m['innings'] if inn.get('balls_per_over')}
    bpo = bpos.pop() if len(bpos) == 1 else 6
    rows = []; n_inn = len(m['innings'])
    for k, inn in enumerate(m['innings']):
        bt = inn['team']; ft = next((t for t in teams if t != bt), None)
        bat_l = by_label(lineup.get(bt, []), H); fld_l = by_label(lineup.get(ft, []) if ft else [], H)
        bat = []; notouts = 0
        for b in sorted(inn['batting'], key=lambda b: (b.get('position') is None, b.get('position') or 0)):
            if not b.get('did_bat'): continue
            text = b.get('dismissal') or ''
            kind = HOW.get(b.get('dismissal_type') or '', b.get('dismissal_type') or '')
            if kind == 'retired not out' and re.match(r'retire?d?\s+(hurt|ill)', text, re.I): kind = 'retired hurt'
            if kind == 'caught' and re.match(r'c\s*(&|and)\s*b\b', text): kind = 'caught and bowled'
            bw, fl = parse_dismissal(text, kind, bat_l, fld_l)
            if b.get('dismissal_bowler_name') and not bw:
                c = fld_l.get(fold(b['dismissal_bowler_name'])) or set()
                if len(c) == 1: bw = next(iter(c))
            if b.get('fielders'): fl = [x for x in b['fielders'] if x]
            if kind in NOT_OUT: notouts += kind == 'not out'
            bat.append([ids.resolve(b['player']), b['runs'], b.get('balls'), b.get('fours'), b.get('sixes'), kind,
                        (ids.resolve(bw) or '') if bw and kind in BOWLER_KINDS else '', [p for p in (ids.resolve(x) for x in fl) if p] if kind in ('caught', 'stumped', 'run out') else []])
        bowl = [[ids.resolve(b['player']), b['balls'], b['runs'], b['wickets'], b['maidens'], b.get('wides'), b.get('no_balls'), None] for b in inn['bowling']]
        balls = sum(b[1] for b in bowl) if bowl and all(isinstance(b[1], int) for b in bowl) else None
        xb = inn.get('extras_breakdown')
        X = [xb.get('wides'), xb.get('noBalls'), xb.get('byes'), xb.get('legByes'), xb.get('penalty')] if xb else [None] * 5
        if 'declared' in inn: dec = bool(inn['declared'])
        else:   # a Test innings closed with two batters still in, and more cricket to come, was declared
            dec = f == 'Test' and inn['wickets'] < 10 and notouts >= 2 and k < n_inn - 1
        rows.append([bt, inn['runs'], inn['wickets'], balls, dec, False, bool(inn.get('super_over')), X, bat, bowl, [], [], None, None])
    players = [[t, [p for p in dict.fromkeys(ids.resolve(h) for h in hs) if p]] for t, hs in lineup.items()]
    return rows, players, bpo

def move_careers(src):
    """A career line attached to a player with no scorecard inside its span belongs to the one other player of that side
    whose scorecards fall inside it and who goes by that name — or, failing that, by the same surname and initial (the
    register had tied Imran Khan's 1971–92 career to a later namesake, and kept Deandra Dottin's published career on a
    second entry beside the one her scorecards use). When every line moves, the article link and the name go with them."""
    seen = collections.defaultdict(set); PL = src['players']
    for r in src['ps']: seen[(r[4], r[3], r[2], r[1])].add(r[0])
    variants = lambda v: {n for n in {v.get('n'), v.get('fullName'), *(v.get('aliases') or [])} if n}
    names = collections.defaultdict(set); surs = collections.defaultdict(set)
    for k, v in PL.items():
        for n in variants(v):
            names[fold(n)].add(k)
            w = re.sub(r'\(.*?\)', '', n).split()
            if w: surs[fold(w[-1])].add(k)
    def initials(v): return {fold(re.sub(r'^(Sir|Dame)\s+', '', n))[:1] for n in variants(v)}
    def given(v, all_=False):
        """The first given name (or, for the other side, every given name): Dwayne Leverock is Russell Dwayne Mark Leverock."""
        out = set()
        for n in variants(v):
            w = [fold(x) for x in re.sub(r'\(.*?\)|^(Sir|Dame)\s+', '', n).split()[:-1] if len(fold(x)) > 1]
            out |= set(w if all_ else w[:1])
        return out
    moved = []; lines = collections.Counter(c['p'] for c in src['careers']); gone = collections.defaultdict(collections.Counter)
    for c in src['careers']:
        ys = seen.get((c['p'], c['t'], c['g'], c['f'])) or ()
        if any(c['first'] - SLACK <= y <= c['last'] + SLACK for y in ys): continue
        inspan = lambda k: any(c['first'] - 1 <= y <= c['last'] + 1 for y in seen.get((k, c['t'], c['g'], c['f']), ()))
        me = PL[c['p']]
        other = [k for k in set().union(*(names[fold(n)] for n in variants(me))) - {c['p']} if inspan(k)]
        if not other:
            sur = {fold(re.sub(r'\(.*?\)', '', n).split()[-1]) for n in variants(me) if re.sub(r'\(.*?\)', '', n).split()}
            other = [k for k in set().union(*(surs[x] for x in sur)) - {c['p']} if inspan(k) and (initials(PL[k]) & initials(me) or given(me) & given(PL[k], all_=True))]
        if len(other) == 1:
            moved.append(f'{me["n"]} → {PL[other[0]]["n"]} ({c["t"]} {c["f"]} {c["first"]}–{c["last"]})')
            gone[c['p']][other[0]] += 1; c['p'] = other[0]
    for p, to in gone.items():
        if sum(to.values()) == lines[p] and len(to) == 1:
            q = next(iter(to)); o = PL[p]; k = PL[q]
            w = o.pop('wiki', None)
            if w and not k.get('wiki'): k['wiki'] = w
            if o.get('n') and o['n'] not in variants(k): k['aliases'] = sorted(set(k.get('aliases') or []) | {o['n']})
            if not k.get('fullName') and o.get('fullName') and o['fullName'] != k.get('n'): k['fullName'] = o['fullName']
    return moved

# ---------------------------------------------------------------- the merge
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--prototype', required=True); ap.add_argument('--names', required=True); ap.add_argument('--cards', required=True)
    a = ap.parse_args(); out = []
    core = json.loads((ROOT/'data'/'cricket.json').read_text(encoding='utf-8')); det = P.read_details()
    src = P.unprepare(core, det)
    proto = load_archive(a.prototype, need=('games', 'teams', 'players'))
    names = json.loads(pathlib.Path(a.names).read_text(encoding='utf-8'))
    H = json.loads(pathlib.Path(a.cards).read_text(encoding='utf-8'))
    # the prototype must be this archive (same matches), or its register cannot be trusted to fit
    pg = {g['id'] for g in proto['games']}; sg = {g['id'] for g in src['games']}
    if not pg <= sg: raise SystemExit(f'the prototype holds {len(pg - sg)} matches the archive does not — not the same archive; nothing written')
    merge_register(src, proto, names, out)
    PSF = src['psFields']
    if 'sruns' not in PSF:   # runs scored in innings whose balls faced are known: the strike rate's numerator
        src['psFields'] = PSF = PSF + ['sruns']; ri = PSF.index('runs')
        src['ps'] = [r + [r[ri]] for r in src['ps']]   # every scorecard so far is Cricsheet's, where every ball is known
    ids = Ids(src, H, out)
    G = {g['id']: g for g in src['games']}
    cards = {}; skipped = collections.Counter(); filled = collections.Counter(); take = []
    for m in H['matches']:
        g = G.get(m['atlas_match_id'])
        if not g: skipped['match not in the archive'] += 1; continue
        if g.get('inn') or g.get('detail'): skipped['archive already has a scorecard'] += 1; continue
        if (g['date'], sorted(g['teams']), g['f'], g['g']) != (m['date'], sorted(m['teams']), m['format'], m['gender']): skipped['date, sides or format differ'] += 1; continue
        take.append(m); note_all(m, ids)
    ids.resolve_all(list(dict.fromkeys([*ids.ctx, *ids.subctx])))
    for m in take: cards[m['atlas_match_id']] = card_of(m, ids, H['players'], out)
    hm = {m['atlas_match_id']: m for m in H['matches']}
    for gid, (inn, players, bpo) in cards.items():
        g = G[gid]; m = hm[gid]
        g['inn'] = inn; g['players'] = players; g['detail'] = True; g['cardSource'] = m['source']
        if bpo != 6: g['bpo'] = bpo
        tz = m.get('toss') or {}
        dec = {'bat': 'bat', 'field': 'field', 'bowl': 'field'}.get(tz.get('decision'))   # the archive writes Cricsheet's word, 'field'
        if (not g.get('toss') or not g['toss'][0]) and tz.get('winner') in g['teams'] and dec:
            g['toss'] = [tz['winner'], dec]; filled['toss'] += 1
        e = m.get('end_date')
        if e and g.get('end') == g['date'] and e > g['date'] and (datetime.date.fromisoformat(e) - datetime.date.fromisoformat(g['date'])).days <= 10:
            g['end'] = e; filled['last day'] += 1
    # the players' teams and genders from the line-ups
    for gid, (inn, players, bpo) in cards.items():
        for t, ps in players:
            for p in ps:
                pl = src['players'][p]
                if t not in pl.setdefault('teams', []): pl['teams'].append(t)
                if G[gid]['g'] not in pl.setdefault('gender', []): pl['gender'].append(G[gid]['g'])
    log_(f'scorecards: {len(cards):,} added ({", ".join(f"{n} {k}" for k, n in skipped.items()) or "none skipped"}); filled where blank: {", ".join(f"{n} {k}" for k, n in filled.items())}', out)
    log_('identities: ' + ', '.join(f'{n:,} {k}' for k, n in ids.stats.most_common()), out)
    # the provenance of every historical scorecard
    srcs = {s['id']: s for s in H['sources']}
    src['cardSources'] = {k: {'name': SOURCE_LABEL.get(k, k), 'url': s['url'], 'revision': s.get('revision'), 'licence': s.get('licence'), 'terms': 'no licence stated',
                              'matches': sum(1 for v in cards if G[v]['cardSource'] == k),
                              **({'pages': {gid: hm[gid]['source_url'] for gid in cards if G[gid]['cardSource'] == k and hm[gid].get('source_url')}} if k.startswith('cricbuzz') else {})}
                          for k, s in srcs.items()}
    src['cardSources']['_crosscheck'] = {'name': 'CricketWeb scorecards', 'url': 'https://www.cricketweb.net/statsspider/', 'matches': sum(1 for gid in cards if hm[gid].get('independent_scorecard_crosscheck')),
                                         'note': 'independent cross-check of the first Tests; nothing is taken from it'}
    # player-season figures for every season a new scorecard touches, recomputed from all of that season's scorecards
    affected = {(G[gid]['y'], G[gid]['f'], G[gid]['g']) for gid in cards}
    rows = season_rows([g for g in src['games'] if (g['y'], g['f'], g['g']) in affected], PSF)
    kept, seen, changed_rows = [], set(), 0
    for r in src['ps']:
        k = tuple(r[:5])
        if (k[0], k[1], k[2]) in affected:
            if k in rows:
                if rows[k] != r: changed_rows += 1
                kept.append(rows[k]); seen.add(k)
        else: kept.append(r)
    new_rows = [r for k, r in rows.items() if k not in seen]
    src['ps'] = kept + new_rows
    moved = move_careers(src)
    if moved: log_(f'career lines moved to the player the scorecards record in that span ({len(moved)}): {"; ".join(moved)}', out)
    # a historical identity left with no career line, no scorecard and no mention anywhere was a duplicate: it goes
    used = {c['p'] for c in src['careers']} | {r[4] for r in src['ps']} | {p for g in src['games'] for _, ps in (g.get('players') or []) for p in ps} | {p for g in src['games'] for p in g.get('pom') or []}
    orphans = [k for k in src['players'] if k.startswith('hist-') and k not in used]
    for k in orphans: del src['players'][k]
    if orphans: log_(f'register: {len(orphans)} historical duplicates left empty by the joins and moves removed', out)
    src['rebuild']['newHistoricalPlayers'] = sum(1 for k in src['players'] if k.startswith('hist-'))
    log_(f'player seasons: {len(new_rows):,} new, {changed_rows:,} existing rows recomputed with the added scorecards (seasons {min(y for y, *_ in affected)}–{max(y for y, *_ in affected)})', out)
    # coverage
    G2 = src['games']; cov = src['coverage']
    cov.update(detailed=sum(1 for g in G2 if g.get('detail')), historicOnly=sum(1 for g in G2 if not g.get('detail')), players=len(src['players']),
               historicCards=len(cards), withDeliveries=sum(1 for g in G2 if g.get('detail') and g.get('source') == 'cricsheet'))
    kinds = lambda gs: collections.Counter(b[5] for g in gs for i in g.get('inn') or [] for b in i[8] if b[5] != 'not out')
    if isinstance(cov.get('dismissals'), dict):
        before = kinds(g for g in G2 if g.get('detail') and not g.get('cardSource'))
        if dict(before) != cov['dismissals']: log_('note: the recorded dismissal counts did not match the Cricsheet scorecards before the merge; recounted', out)
        allk = kinds(G2); cov['dismissals'] = {**{k: allk[k] for k in cov['dismissals']}, **{k: v for k, v in allk.items() if k not in cov['dismissals']}}
    for sc in cov.get('scope', []):
        mine = [g for g in G2 if g['g'] == sc['g'] and g['f'] == sc['f']]
        det_ = [g for g in mine if g.get('detail')]
        if mine: sc.update(detail=len(det_), detailStart=min(g['date'] for g in det_) if det_ else sc.get('detailStart'))
    core2, det2 = P.prepare(src)
    P.write(core2, det2)
    log_(f'written: data/cricket.json {(ROOT/"data"/"cricket.json").stat().st_size / 1e6:.1f} MB, {len(det2)} scorecard shards', out)

if __name__ == '__main__':
    main()
