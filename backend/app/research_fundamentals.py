"""A small descriptive statement contract. It is not a DCF/valuation model."""
from datetime import date
from decimal import Decimal, InvalidOperation


def coherent_annual_facts(evidence):
    groups = {}
    for e in evidence:
        if e['scope']!='INSTRUMENT' or not e['rights_ok'] or not e.get('available',True) or e['freshness']!='FRESH':
            continue
        c=e['content']; m=c.get('metadata',{})
        if c.get('data_kind')!='fundamental_fact' or m.get('taxonomy')!='us-gaap':
            continue
        if not all(m.get(k) for k in ('cik','concept','accn','filed')) or m.get('form') not in ('10-K','10-K/A','20-F','20-F/A'):
            continue
        if c.get('currency')!=c.get('unit') or not c.get('currency') or not c.get('published_at'):
            continue
        try:
            value=Decimal(str(c['value']))
            end=date.fromisoformat(c['period'])
            if not value.is_finite():continue
            concept=m['concept']
            if concept in ('Revenues','NetIncomeLoss'):
                if not 300 <= (end-date.fromisoformat(m['start'])).days <= 400:continue
            elif concept not in ('Assets','StockholdersEquity') or m.get('start'):
                continue
        except (KeyError,ValueError,InvalidOperation):
            continue
        key=(m['cik'],m['accn'],c['period'],c['currency'])
        group=groups.setdefault(key,{})
        # Contradictory values within one filing do not form an accepted bundle.
        group.setdefault(concept,set()).add((str(value.normalize()),m.get('start')))
    for group in groups.values():
        if set(group)=={'Assets','StockholdersEquity','Revenues','NetIncomeLoss'} and all(len(v)==1 for v in group.values()):
            if next(iter(group['Revenues']))[1]==next(iter(group['NetIncomeLoss']))[1]:
                return True
    return False
