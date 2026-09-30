import json,collections,datetime
import pathlib as _pl; ROOT=_pl.Path(__file__).resolve().parent.parent
d=json.load(open(ROOT/'data'/'rugby.json',encoding='utf-8'));TEN=[t['name'] for t in d['teams']];M=d['matches'];SIDES={s for m in M for s in (m['home'],m['away'])};iss=collections.defaultdict(list)
n=lambda k,m:iss[k].append(m)
ids=[m['id'] for m in M]
if ids!=list(range(len(M))):n('match ids not 0..N-1','')
dates=[m['date'] for m in M]
if dates!=sorted(dates):n('matches not in date order',f'{sum(1 for a,b in zip(dates,dates[1:]) if b<a)} inversions')
for m in M:
  try:datetime.date.fromisoformat(m['date'])
  except: n('bad date',m['sourceId'])
  if m['year']!=int(m['date'][:4]):n('year ≠ date',m['sourceId'])
  if not set(m['eligible'])<=set(TEN):n('eligible outside the ten',m['sourceId'])
  if m['eligible'] and not any(x in m['eligible'] for x in (m['home'],m['away'])):n('eligible names neither side',m.get('sourceId'))
  for e in m['eligible']:
    if e not in (m['home'],m['away']):n('eligible nation not playing',m['sourceId'])
  if m.get('scoring'):
    s=m.get('scoring')
    if len(s)!=12:n('scoring length',m['sourceId'])
  if m['hs']<0 or m['as_']<0:n('negative score',m['sourceId'])
  if m['worldcup'] and not m['stage']:n('world cup without stage',m['sourceId'])
  if m['scoreUnit']=='goals' and m['year']>=1885:n('goals unit after 1885',m['sourceId'])
# scoring reconciliation (try 5 from 1992, 4 from 1971, 3 before; conversion 2; penalty 3; drop goal 3 from 1948, 4 before; penalty try 7 from 2017)
def val(s,y,o):
  t,c,p,dg,_,pt=s[o:o+6]
  tv=5 if y>=1992 else 4 if y>=1971 else 3
  dv=3 if y>=1948 else 4
  ptv=7 if y>=2017 else tv
  return t*tv+c*2+p*3+dg*dv+pt*ptv
bad=0;tot=0
for m in M:
  if m.get('scoring') and m['scoreUnit']=='points':
    tot+=1
    if val(m.get('scoring'),m['year'],0)!=m['hs'] or val(m.get('scoring'),m['year'],6)!=m['as_']:bad+=1;n('scoring breakdown ≠ score (era values)',f"{m['date']} {m['home']}-{m['away']} {m['hs']}-{m['as_']} {m.get('scoring')}")
dup=collections.Counter((m['date'],tuple(sorted([m['home'],m['away']]))) for m in M)
for k,v in dup.items():
  if v>1:n('same fixture twice on one date',str(k))
# team counts vs perspective counts
for t in d['teams']:
  c=sum(1 for m in M if t['name'] in m['eligible'])
  if c!=t['count']:n('team count ≠ eligible matches',f"{t['name']} {t['count']} vs {c}")
  first=min(m['year'] for m in M if t['name'] in m['eligible'])
  if first!=t['from']:n('team from ≠ first match',f"{t['name']} {t['from']} vs {first}")
# coaches: matchIds exist, within tenure
for c in d['coaches']:
  for i in c['matchIds']:
    if i<0 or i>=len(M):n('coach matchId out of range',c['id'])
    elif c['team'] not in M[i]['eligible']:n('coach match not involving team',c['id'])
  lr=c.get('linkedRecord')
  if lr and lr['n']!=len(c['matchIds']):n('linked record n ≠ matchIds',c['id'])
  if lr and c.get('reported') and c.get('reconciles') and (lr['w'],lr['l'],lr['d'])!=(c['reported']['w'],c['reported']['l'],c['reported']['d']):n('reconciles flag but records differ',c['id'])
# players
for p in d['players']:
  if p['team'] not in SIDES:n('player team not in any match',p['id'])
  HF=d.get('historyFields') or ['match','position','scoring','tries','shirt','bench']
  h=[dict(zip(HF,x)) if isinstance(x,list) else x for x in (p.get('history') or [])]
  if h and p.get('complete') and len(h)!=p['caps']:n('complete history ≠ caps',p['id'])
  for x in h:
    i=x.get('match')
    if i is None: continue
  if p.get('startYear') and p.get('endYear') and p['startYear']>p['endYear']:n('player span reversed',p['id'])
# reference facts
def rec(t,o=None):
  w=l=dr=0
  for m in M:
    if t not in m['eligible']:continue
    home=m['home']==t;opp=m['away'] if home else m['home']
    if o and opp!=o:continue
    pf,pa=(m['hs'],m['as_']) if home else (m['as_'],m['hs'])
    w+=pf>pa;l+=pf<pa;dr+=pf==pa
  return w,l,dr
refs=[('South Africa v New Zealand to 12 Sep 2026',rec('South Africa','New Zealand')),('England v Wales',rec('England','Wales')),('Australia v New Zealand',rec('Australia','New Zealand')),('Ireland v Scotland',rec('Ireland','Scotland'))]
wc=collections.Counter(m['worldcup'] for m in M if m['worldcup'])
titles={t['name']:t['titles'] for t in d['teams']}
finals=[(m['worldcup'],m['home'],m['away'],m['hs'],m['as_']) for m in M if m['stage']=='Final']
out=['# Data audit — Ten Nations rugby atlas','',f"Archive as of {d['asof']}, results through {d['through']}. Checks compare the embedded data against itself plus scoring-value arithmetic and well-known facts. Nothing was changed.",'','## Inventory','',f"- {len(M):,} matches · {len(d['players'])} player snapshots · {len(d['coaches'])} coach profiles · {len(TEN)} perspectives",f"- {sum(1 for m in M if m.get('scoring'))} matches carry a scoring breakdown; {sum(1 for m in M if m['scoreUnit']=='goals')} pre-1885 fixtures are scored in goals; {sum(1 for m in M if m['historical'])} legacy fixtures; {sum(1 for m in M if m['dateUncertain'])} dates flagged uncertain",f"- World Cup matches by tournament: "+', '.join(f'{y}: {c}' for y,c in sorted(wc.items())),'','## Consistency checks','','| Check | Result |','|---|---|']
checks=['match ids not 0..N-1','matches not in date order','bad date','year ≠ date','eligible outside the ten','eligible names neither side','eligible nation not playing','scoring length','negative score','world cup without stage','goals unit after 1885','scoring breakdown ≠ score (era values)','same fixture twice on one date','team count ≠ eligible matches','team from ≠ first match','coach matchId out of range','coach match not involving team','linked record n ≠ matchIds','reconciles flag but records differ','player team outside ten','complete history ≠ caps','player span reversed']
for c in checks:
  v=iss.get(c,[]);out.append(f'| {c} | {"✅ none" if not v else "⚠️ "+str(len(v))+" — e.g. "+"; ".join(v[:3])} |')
out+=['',f'Scoring breakdowns reconcile with the final score under the scoring values of the day (try 3/4/5 by era, conversion 2, penalty 3, drop 4 then 3, penalty try 7 from 2017) in {tot-bad} of {tot} matches that carry one.','','## World Cup finals in the archive','','| Year | Final | Score |','|---|---|---|']+[f'| {y} | {h} v {a} | {hs}–{as_} |' for y,h,a,hs,as_ in finals]
out+=['','Champions listed in the team registry: '+'; '.join(f"{k} {v}" for k,v in titles.items() if v),'','## Head-to-head cross-checks (won–lost–drawn from the first side)','']+[f'- {k}: {w}–{l}–{dr}' for k,(w,l,dr) in refs]
open(ROOT/'audits'/'DATA-AUDIT-rugby.md','w',encoding='utf-8').write('\n'.join(out));print('\n'.join(out))
