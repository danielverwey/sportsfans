"""Bring a fresh read of one atlas into data/, check it, and say what to commit.

    python tools/sweep.py ufc     "C:/path/to/ufc_fight_atlas_1993_2026.html"
    python tools/sweep.py motogp  "C:/path/to/motogp_race_atlas_1949_2026.html"
    python tools/sweep.py sbk     "C:/path/to/worldsbk_race_atlas_1988_2026.html"
    python tools/sweep.py cricket "C:/path/to/the cricket export (page, .json or .json.gz)"
    python tools/sweep.py tennis  "C:/path/to/tennis_data.json (or the page)"
    python tools/sweep.py tt      "C:/path/to/isle_of_man_tt_atlas_1907_2026.html"
    python tools/sweep.py dakar   "C:/path/to/paris_dakar_atlas_1979_2026.html"

Runs the atlas's prepare script (writes data/<sport>.json, and the shards for cricket and tennis), its audit (writes
audits/DATA-AUDIT-<sport>.md) and the gate against the last commit. Formula 1 is not here: it sweeps itself on GitHub
(Actions → Sweep · Formula 1). Needs Python 3.10+ and git; nothing else.
"""
import os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
STEPS = {
    'motogp': (['prepare_bikes.py', 'motogp', '{src}'], ['audit_bikes.py', 'motogp'], ['data/motogp.json', 'src/bikes/assets_motogp.json']),
    'sbk': (['prepare_bikes.py', 'sbk', '{src}'], ['audit_bikes.py', 'sbk'], ['data/sbk.json', 'src/bikes/assets_sbk.json']),
    'ufc': (['prepare_ufc.py', '{src}'], ['audit_ufc.py'], ['data/ufc.json']),
    'cricket': (['prepare_cricket.py', '{src}'], ['audit_cricket.py'], ['data/cricket.json', 'data/cricket_details']),
    'tennis': (['prepare_tennis.py', '{src}'], ['audit_tennis.py'], ['data/tennis.json', 'data/tennis_matches']),
    'tt': (['prepare_tt.py', '{src}'], None, ['data/tt.json']),
    'dakar': (['prepare_dakar.py', '{src}'], None, ['data/dakar.json']),
}
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
env = dict(os.environ, PYTHONUTF8='1')

def run(args, quiet=False):
    r = subprocess.run([PY, str(ROOT/'tools'/args[0]), *args[1:]], cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    return r.returncode, out

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in STEPS:
        sys.exit(__doc__)
    sport, src = sys.argv[1], pathlib.Path(sys.argv[2]).expanduser().resolve()
    if not src.exists(): sys.exit(f'not found: {src}')
    prep, audit, paths = STEPS[sport]
    print(f'1/3 prepare · {sport} from {src.name}')
    code, out = run([a.replace('{src}', str(src)) for a in prep])
    print('   ' + '\n   '.join(l for l in out.strip().splitlines()[-4:]))
    if code: sys.exit(f'\nprepare failed (exit {code}); data/ may be half-written — undo with:  git restore {" ".join(paths)}')
    if audit:
        code, out = run(audit)
        warns = sum(1 for l in out.splitlines() if '⚠️' in l or '❌' in l)
        print(f'2/3 audit · {"crashed — " + out.strip().splitlines()[-1] if code else f"audits/DATA-AUDIT-{sport}.md written · {warns} line(s) flagged ⚠️/❌ (read it; most are known quirks of the source)"}')
    else: print('2/3 audit · none for this atlas')
    code, out = run(['gate.py', sport])
    print('3/3 gate')
    print('   ' + '\n   '.join(out.strip().splitlines()))
    add = ' '.join(paths + (['audits'] if audit else []))
    if code:
        print(f'\nNOT READY. Nothing is committed. Either send the gate report to Claude, or undo this sweep with:\n   git restore {" ".join(paths)}\n'
              f'If you have read the report and the missing records are genuine (a duplicate removed, a renamed event), pass it by hand:\n   python tools/gate.py {sport} --accept')
        sys.exit(1)
    print(f'\nREADY. Stage it with:\n   git add {add}')
