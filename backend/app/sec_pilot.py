"""Engineering convenience sample, NOT an index, historical universe or selection signal."""
from sqlalchemy import select
from app.universe_store import LISTINGS

PILOT_VERSION = 'sec-pilot-100-v1'
# Resolve every symbol against the observed catalogue, deduplicate issuer CIKs.
PREFERRED_SYMBOLS = '''AAPL MSFT WMT NVDA AMZN GOOGL META BRK-B JPM V MA UNH XOM JNJ PG
HD COST ABBV KO BAC MRK CVX CRM AMD PEP TMO WFC CSCO MCD ABT DIS LIN ORCL ACN
ADBE NKE DHR TXN QCOM IBM CAT GE AMGN INTU AMAT VZ NOW ISRG GS SPGI RTX LOW
PFE UNP HON BKNG COP UPS LMT SBUX DE T C BLK ADP GILD MDT TJX SCHW MMC CB
ADI PLD ELV BMY LRCX MU SYK PANW SO DUKE DUK MO EOG SLB ZTS NOC CME CL
ICE SHW WM EQIX KLAC FDX APD FCX HCA EMR MAR ROP ORLY AZO CARR AXP
TM TSM NVO ASML SAP SONY BABA UL BP SHEL RIO BHP NVS SNY SHOP SAP SE'''.split()


def select_pilot(connection, size=100):
    records = connection.execute(select(LISTINGS).where(LISTINGS.c.provider == 'SEC',
        LISTINGS.c.state == 'IDENTIFIED', LISTINGS.c.venue.in_(['NASDAQ', 'NYSE']))
        .order_by(LISTINGS.c.symbol, LISTINGS.c.cik, LISTINGS.c.id)).mappings().all()
    rank = {symbol: i for i, symbol in reversed(list(enumerate(PREFERRED_SYMBOLS)))}
    records.sort(key=lambda r: (rank.get(r['symbol'], len(rank) + len(PREFERRED_SYMBOLS)), r['symbol'], r['cik']))
    selected, seen = [], set()
    for row in records:
        if row['cik'] in seen:
            continue
        seen.add(row['cik'])
        selected.append(dict(cik=row['cik'], name=row['name'], symbol=row['symbol'], listing_id=row['id'],
                             catalogue_seen_at=row['last_seen_at']))
        if len(selected) == size:
            return selected
    raise ValueError('CATALOGUE_TOO_SMALL')
