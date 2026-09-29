"""The Isle of Man TT's marque rules, shared by tools/prepare_tt.py and the TT sweeper: the marques the sources name, the
spellings the archive keeps, sidecar chassis builders, the marque a machine description names, and plausible race averages."""
import re
MARQUES = ['Honda', 'Yamaha', 'Suzuki', 'Kawasaki', 'BMW', 'Triumph', 'Norton', 'Ducati', 'MV Agusta', 'Moto Guzzi', 'BSA', 'Velocette', 'Paton', 'AJS', 'Mugen', 'Rudge', 'New Imperial', 'Excelsior', 'Sunbeam', 'Vincent', 'MotoCzysz', 'Matchless', 'Rex-Acme', 'Benelli', 'Mondial', 'Gilera', 'EMC', 'Douglas', 'Scott', 'Indian', 'Aprilia', 'LCR', 'Windle', 'Ireson', 'Baker', 'Shelbourne', 'DMR', 'Derbyshire', 'Bimota', 'Rotax', 'Konig', 'König', 'Weslake', 'Imp', 'Fath', 'URS', 'Cotton', 'Levis', 'HRD', 'Royal Enfield', 'Ariel', 'Guzzi', 'NSU', 'DKW', 'Jawa', 'CZ', 'MZ', 'Bultaco', 'Ossa', 'Montesa', 'Morini', 'Chevallier', 'Ryan', 'Harley-Davidson', 'Kreidler', 'Cagiva', 'Petronas', 'Sarolea', 'Motosacoche', 'Husqvarna', 'Puch', 'Zundapp', 'Zündapp', 'Terrot', 'Peugeot', 'Alcyon', 'Humber', 'Rover', 'Rex', 'Ivy', 'OK-Supreme', 'OK Supreme', 'Cotton', 'AJW', 'Dunelt', 'James', 'Francis-Barnett', 'Coventry-Eagle', 'Grindlay-Peerless', 'Zenith', 'Chater-Lea', 'Ner-a-Car', 'ABC', 'Sun', 'Diamond', 'Blackburne', 'Calthorpe', 'P&M', 'Panther', 'Brough Superior', 'Vincent-HRD', 'Greeves', 'Cotton', 'Villiers', 'Seeley', 'Yamsel', 'Rickman', 'Metisse', 'Padgett', 'Spondon', 'Maxton', 'Harris', 'Bakker', 'Britten', 'Buell', 'Aermacchi', 'Bianchi', 'Parilla', 'Ducson', 'Itom', 'Motobi', 'Derbi', 'Tomos', 'Garelli', 'Minarelli', 'Malanca', 'Piovaticci', 'Van Veen', 'Morbidelli', 'Sanvenero', 'Cimatti', 'Motom', 'Laverda', 'Bimota', 'Yamaha', 'Kawasaki']
# the sources spell a few marques two ways; the archive keeps one. 'Unknown' in a source is a blank, not a marque.
MARQUE_ALIAS = {'A.J.S.': 'AJS', 'M.Z.': 'MZ', 'Rex Acme': 'Rex-Acme', 'OK Supreme': 'OK-Supreme', 'B.S.A.': 'BSA', 'N.S.U.': 'NSU', 'H.R.D.': 'HRD', 'M.V. Agusta': 'MV Agusta', 'MV': 'MV Agusta', 'Unknown': '', 'unknown': '', '?': '', '—': '', '-': ''}
# sidecar chassis builders: when a machine names a chassis and an engine ('Baker Honda', 'Windle Yamaha', 'Honda LCR'),
# the marque is the engine maker, as it already is for most rows; a chassis stands alone only when no engine is named
CHASSIS = {'LCR', 'Windle', 'Ireson', 'Baker', 'Shelbourne', 'DMR', 'Derbyshire', 'Seeley', 'Rickman', 'Metisse', 'Spondon', 'Maxton', 'Harris', 'Bakker', 'Padgett'}
def derive(machine):
    """The marque named in a machine description: the engine maker if one is named, else the chassis; leftmost wins a tie.
    Deterministic — the earlier longest-name rule broke ties by set order, which Python randomises per run."""
    m = machine or ''; hits = []
    for q in dict.fromkeys(MARQUES):
        hits += [(mt.start(), mt.end(), q) for mt in re.finditer(r'(?<![A-Za-z])' + re.escape(q) + r'(?![A-Za-z])', m, flags=re.I)]
    hits = [h for h in hits if not any(o[0] <= h[0] and h[1] <= o[1] and o[1] - o[0] > h[1] - h[0] for o in hits)]   # 'Guzzi' inside 'Moto Guzzi'
    if not hits: return None
    engines = [h for h in hits if h[2] not in CHASSIS]
    return min(engines or hits, key=lambda h: (h[0], h[0] - h[1]))[2]
# plausible ceilings for a race average, by year: a table that exceeds them was transcribed in km/h (1951's Clubman's races), a value under 20 is unreadable
def ceiling(y): return 55 if y < 1914 else 72 if y < 1931 else 95 if y < 1950 else 105 if y < 1960 else 112 if y < 1976 else 122 if y < 1991 else 130 if y < 2006 else 137
