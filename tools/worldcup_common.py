"""What the World Cup tools share — tools/prepare_worldcup.py, tools/sweepers/worldcup.py and tools/audit_worldcup.py:
the stage codes, the team-name aliases between the sources, the readers for the Fjelstul CSV tables and the OpenFootball
JSON files, and the small gazetteer that places each final on the map."""
import csv, io, json, re, unicodedata

STAGES = {'group stage': 'group', 'matchday': 'group', 'first group stage': 'group', 'second group stage': 'group2', 'final round': 'final-round',
          'first round': 'r16', 'round of 32': 'r32', 'round of 16': 'r16', 'quarter-finals': 'qf', 'quarter-final': 'qf', 'quarterfinal': 'qf', 'quarterfinals': 'qf',
          'semi-finals': 'sf', 'semi-final': 'sf', 'semifinal': 'sf', 'semifinals': 'sf', 'third-place match': '3rd', 'third-place play-off': '3rd', 'third place play-off': '3rd',
          'match for third place': '3rd', 'third place': '3rd', 'play-off for third place': '3rd', 'final': 'final'}
STAGE_ORDER = ['group', 'group2', 'final-round', 'r32', 'r16', 'qf', 'sf', '3rd', 'final']
STAGE_LABEL = {'group': 'Group stage', 'group2': 'Second group stage', 'final-round': 'Final round', 'r32': 'Round of 32', 'r16': 'Round of 16', 'qf': 'Quarter-final', 'sf': 'Semi-final', '3rd': 'Third place', 'final': 'Final'}

def stage_code(label):
    t = (label or '').strip().lower()
    if t.startswith('matchday'): return 'group'
    return STAGES.get(t) or STAGES.get(t.rstrip('s')) or ('final' if t == 'final' else None)

# the names the sources use for one team; the archive keeps the Fjelstul spelling (historical teams stay historical)
ALIASES = {'USA': 'United States', 'U.S.A.': 'United States', 'Korea Republic': 'South Korea', 'Korea DPR': 'North Korea', 'Côte d’Ivoire': 'Ivory Coast', "Côte d'Ivoire": 'Ivory Coast',
           'Bosnia & Herzegovina': 'Bosnia and Herzegovina', 'Bosnia-Herzegovina': 'Bosnia and Herzegovina', 'DR Congo': 'DR Congo', 'Congo DR': 'DR Congo', 'Czechia': 'Czech Republic',
           'Ireland': 'Republic of Ireland', 'IR Iran': 'Iran', 'Türkiye': 'Turkey', 'Cabo Verde': 'Cape Verde', 'Cape Verde Islands': 'Cape Verde', 'Curacao': 'Curaçao', 'Trinidad & Tobago': 'Trinidad and Tobago',
           'UAE': 'United Arab Emirates', 'China PR': 'China', 'Chinese Taipei': 'Chinese Taipei', 'Holland': 'Netherlands', 'FR Yugoslavia': 'Yugoslavia', 'Germany FR': 'West Germany', 'FRG': 'West Germany', 'GDR': 'East Germany', 'USSR': 'Soviet Union'}
def team_name(n):
    n = (n or '').strip()
    return ALIASES.get(n, n)

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii').lower()).strip('-')

def person_name(given, family):
    parts = [p for p in (given, family) if p and p != 'not applicable']
    return ' '.join(parts).strip()

def read_csv(text):
    return list(csv.DictReader(io.StringIO(text)))

# the final's city, as approximate coordinates on the Natural Earth silhouette (lon, lat)
FINALS = {'M1930': ['Montevideo', -56.19, -34.9], 'M1934': ['Rome', 12.5, 41.9], 'M1938': ['Paris', 2.35, 48.86], 'M1950': ['Rio de Janeiro', -43.17, -22.91], 'M1954': ['Bern', 7.45, 46.95],
          'M1958': ['Solna', 18.0, 59.37], 'M1962': ['Santiago', -70.65, -33.45], 'M1966': ['London', -0.13, 51.51], 'M1970': ['Mexico City', -99.13, 19.43], 'M1974': ['Munich', 11.58, 48.14],
          'M1978': ['Buenos Aires', -58.38, -34.6], 'M1982': ['Madrid', -3.7, 40.42], 'M1986': ['Mexico City', -99.13, 19.43], 'M1990': ['Rome', 12.5, 41.9], 'M1994': ['Pasadena', -118.14, 34.15],
          'M1998': ['Saint-Denis', 2.36, 48.92], 'M2002': ['Yokohama', 139.64, 35.44], 'M2006': ['Berlin', 13.4, 52.52], 'M2010': ['Johannesburg', 28.05, -26.2], 'M2014': ['Rio de Janeiro', -43.17, -22.91],
          'M2018': ['Moscow', 37.62, 55.75], 'M2022': ['Lusail', 51.49, 25.42], 'M2026': ['East Rutherford', -74.07, 40.81],
          'W1991': ['Guangzhou', 113.26, 23.13], 'W1995': ['Solna', 18.0, 59.37], 'W1999': ['Pasadena', -118.14, 34.15], 'W2003': ['Carson', -118.28, 33.83], 'W2007': ['Shanghai', 121.47, 31.23],
          'W2011': ['Frankfurt', 8.68, 50.11], 'W2015': ['Vancouver', -123.12, 49.28], 'W2019': ['Lyon', 4.83, 45.76], 'W2023': ['Sydney', 151.21, -33.87]}
# capitals of host countries the gazetteer may need for a future tournament it does not know the final of
CAPITALS = {'Brazil': ['Brasília', -47.88, -15.79], 'Spain': ['Madrid', -3.7, 40.42], 'Portugal': ['Lisbon', -9.14, 38.72], 'Morocco': ['Rabat', -6.85, 34.02], 'Saudi Arabia': ['Riyadh', 46.68, 24.69],
            'United States': ['Washington', -77.04, 38.9], 'Mexico': ['Mexico City', -99.13, 19.43], 'Canada': ['Ottawa', -75.7, 45.42], 'Australia': ['Canberra', 149.13, -35.28], 'New Zealand': ['Wellington', 174.78, -41.29]}

# hosts of tournaments the database does not hold yet (the editor's knowledge; the database's host table replaces it when published)
HOSTS_KNOWN = {'M2026': ['United States', 'Canada', 'Mexico'], 'W2023': ['Australia', 'New Zealand'], 'W2027': ['Brazil'], 'M2030': ['Spain', 'Portugal', 'Morocco'], 'W2031': ['United States'], 'M2034': ['Saudi Arabia']}

# 2026: the sources give the host city; the stadium names are the editor's, as commonly known
GROUNDS_2026 = {'Atlanta': ('Mercedes-Benz Stadium', 'Atlanta', 'United States'), 'Boston (Foxborough)': ('Gillette Stadium', 'Foxborough', 'United States'), 'Dallas (Arlington)': ('AT&T Stadium', 'Arlington', 'United States'),
                'Guadalajara (Zapopan)': ('Estadio Akron', 'Zapopan', 'Mexico'), 'Houston': ('NRG Stadium', 'Houston', 'United States'), 'Kansas City': ('Arrowhead Stadium', 'Kansas City', 'United States'),
                'Los Angeles (Inglewood)': ('SoFi Stadium', 'Inglewood', 'United States'), 'Mexico City': ('Estadio Azteca', 'Mexico City', 'Mexico'), 'Miami (Miami Gardens)': ('Hard Rock Stadium', 'Miami Gardens', 'United States'),
                'Monterrey (Guadalupe)': ('Estadio BBVA', 'Guadalupe', 'Mexico'), 'New York/New Jersey (East Rutherford)': ('MetLife Stadium', 'East Rutherford', 'United States'), 'Philadelphia': ('Lincoln Financial Field', 'Philadelphia', 'United States'),
                'San Francisco Bay Area (Santa Clara)': ("Levi's Stadium", 'Santa Clara', 'United States'), 'Seattle': ('Lumen Field', 'Seattle', 'United States'), 'Toronto': ('BMO Field', 'Toronto', 'United States'), 'Vancouver': ('BC Place', 'Vancouver', 'Canada')}
GROUNDS_2026['Toronto'] = ('BMO Field', 'Toronto', 'Canada')
CITY_COUNTRY_2023 = {'Auckland': 'New Zealand', 'Dunedin': 'New Zealand', 'Hamilton': 'New Zealand', 'Wellington': 'New Zealand', 'Adelaide': 'Australia', 'Brisbane': 'Australia', 'Melbourne': 'Australia', 'Perth': 'Australia', 'Sydney': 'Australia'}

def points_rule(sex, y):
    """Three points for a win from 1994 (men) and 1995 (women); two before."""
    return 3 if (sex == 'M' and y >= 1994) or (sex == 'W' and y >= 1995) else 2

def minute_of(label, regulation=None, stoppage=None, period=None):
    """A goal's minute as the archive keys it: 'regulation' and 'stoppage' from the source, else parsed from "90'+3'"."""
    if regulation not in (None, '', 'not applicable'):
        return int(regulation), int(stoppage or 0)
    m = re.match(r"(\d+)'?(?:\s*\+\s*(\d+))?", str(label or ''))
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)

def openfootball_matches(doc, y, sex='M'):
    """OpenFootball's worldcup.json → the archive's match shape (scores after extra time, penalties, goals by name)."""
    out = []
    for i, m in enumerate(doc.get('matches', [])):
        sc = m.get('score') or {}
        ft = sc.get('ft'); et = sc.get('et'); p = sc.get('p')
        if not ft or ft[0] is None: continue
        final = et if et else ft
        out.append({'num': m.get('num') or i + 1, 'round': m.get('round') or '', 'group': m.get('group') or None, 'date': m.get('date'), 'time': (m.get('time') or '').split(' ')[0] or None,
                    'home': team_name(m.get('team1')), 'away': team_name(m.get('team2')), 'hs': int(final[0]), 'as': int(final[1]), 'et': bool(et), 'pens': [int(p[0]), int(p[1])] if p else None,
                    'ground': m.get('ground') or m.get('city') or None, 'goals': [(1, g) for g in (m.get('goals1') or [])] + [(0, g) for g in (m.get('goals2') or [])]})
    return out
