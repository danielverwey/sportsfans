"""Formula 1: the season from the Jolpica F1 API (tools/harvest/f1.py). From March the current season; in January and
February the one just finished, so a late reclassification still lands and no empty season is opened."""
import datetime, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

def sweep(log):
    import f1 as h   # tools/harvest/f1.py
    today = datetime.date.today(); year = today.year if today.month >= 3 else today.year - 1
    h.harvest(year)
    rep = ROOT/'build'/'harvest'/'f1.md'
    if rep.exists(): log += rep.read_text(encoding='utf-8').splitlines()
