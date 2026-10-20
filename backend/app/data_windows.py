"""Date-only rolling windows for existing audited presets. No caller URL/params."""
from datetime import timedelta


def request_window(source, now):
    params = dict(source.params)
    payload = source.payload
    if source.id in ('A05', 'A07'):
        params.update(startPeriod=(now - timedelta(days=183)).strftime('%Y-%m'),
                      endPeriod=now.strftime('%Y-%m'))
    elif source.id == 'A08':
        params['field_tdr_date_value_month'] = now.strftime('%Y%m')
    elif source.id == 'A11':
        params['periods'] = ','.join(str(y) for y in range(now.year - 2, now.year + 1))
    elif source.id == 'A12':
        start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        params['fq'] = f'publication_date:[{start}T00:00:00Z TO {now:%Y-%m-%d}T23:59:59Z]'
    elif source.id == 'B02':
        params['Year'] = str(now.year - 1)
    elif source.id == 'B03':
        payload = {**source.payload, 'startyear': str(now.year - 1), 'endyear': str(now.year)}
    return params, payload
