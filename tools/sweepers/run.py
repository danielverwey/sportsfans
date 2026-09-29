"""Run one atlas's sweeper.

    python tools/sweepers/run.py <f1|motogp|sbk|ufc|cricket|tennis|rugby|tt|dakar>

Reads the source, merges what is new into data/ (and src/bikes/ for the circuit outlines), and writes the report to
build/harvest/<sport>.md. It never commits: the workflow runs tools/gate.py, rebuilds, checks links and commits only if
all of that passes. Exits 1 if the source could not be read, so a broken sweep shows red in Actions.
"""
import datetime, importlib, pathlib, sys, traceback
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0, str(ROOT/'tools'/'harvest'))
SPORTS = ['f1', 'motogp', 'sbk', 'ufc', 'cricket', 'tennis', 'rugby', 'tt', 'dakar']
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in SPORTS: sys.exit(__doc__)
    sport = sys.argv[1]; log = [f'# {sport} sweep · {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC', '']
    code = 0
    try:
        mod = importlib.import_module(f'sweepers.{"bikes" if sport in ("motogp", "sbk") else sport}')
        mod.sweep(log, sport) if sport in ('motogp', 'sbk') else mod.sweep(log)
    except SystemExit as e:
        if e.code not in (None, 0): log.append(f'\n**Stopped:** {e.code}'); code = 1
    except Exception:
        log += ['', '**The sweeper failed:**', '', '```', traceback.format_exc()[-3000:], '```']; code = 1
    out = ROOT/'build'/'harvest'/f'{sport}.md'; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(log) + '\n', encoding='utf-8'); print('\n'.join(log))
    sys.exit(code)
