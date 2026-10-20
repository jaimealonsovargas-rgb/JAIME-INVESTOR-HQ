from datetime import timedelta
from test_portfolio import quote, NOW
from app.market_history import comparable_history


def test_history_does_not_mix_venues_units_or_rights():
    base=quote()
    rows=[base.model_copy(update={'id':str(i),'observed_at':NOW-timedelta(days=i),'value':base.value+i}) for i in range(3)]
    rows += [base.model_copy(update={'venue':'OTHER','value':999}),base.model_copy(update={'unit':'OTHER','value':999})]
    rows += [base.model_copy(update={'rights':base.rights.model_copy(update={'display_allowed':False}),'value':999})]
    rows += [base.model_copy(update={'rights':base.rights.model_copy(update={'access_allowed':False}),'value':999})]
    h=comparable_history(base,rows,NOW)
    assert len(h['points'])==3 and all(p['value']!='999' for p in h['points'])
    assert h['points'][0]['observed_at']<h['points'][-1]['observed_at']
    assert comparable_history(base,rows,NOW+timedelta(days=1))['state']=='STALE'
    assert comparable_history(base,[base],NOW)['points']==[]


def test_revised_point_does_not_duplicate_time():
    base=quote()
    rows=[base.model_copy(update={'observed_at':NOW-timedelta(days=i)}) for i in range(3)]
    rows.append(base.model_copy(update={'received_at':NOW+timedelta(seconds=1),'value':base.value+1}))
    h=comparable_history(base,rows,NOW)
    assert len(h['points'])==3 and h['points'][-1]['value']=='13'
