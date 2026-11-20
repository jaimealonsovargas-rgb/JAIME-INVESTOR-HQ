"""Read two direct statement equations published by the filer. Never resolve XML links."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from io import BytesIO
import re
import xml.etree.ElementTree as ET

from app.company_reconciliation import decimal_text

LINK = '{http://www.xbrl.org/2003/linkbase}'
XL = '{http://www.w3.org/1999/xlink}'
XBRLI = '{http://www.xbrl.org/2003/instance}'
NIL = '{http://www.w3.org/2001/XMLSchema-instance}nil'
SUM = {'http://www.xbrl.org/2003/arcrole/summation-item','https://xbrl.org/2023/arcrole/summation-item'}
CASH = 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect'
BALANCE = 'LiabilitiesAndStockholdersEquity'


def xml_document(raw):
    if b'\x00' in raw or re.search(br'<!\s*(DOCTYPE|ENTITY)',raw,re.I):
        raise ValueError('UNSAFE_FILING_XML')
    namespaces = defaultdict(set)
    try:
        parser = ET.iterparse(BytesIO(raw),events=('start-ns','end'))
        for event, entry in parser:
            if event == 'start-ns':
                namespaces[entry[0]].add(entry[1])
    except ET.ParseError:
        raise ValueError('INVALID_FILING_XML') from None
    return parser.root, namespaces


def formula(root, parent, role_hint):
    candidates = []
    for link in root.iter(LINK+'calculationLink'):
        role = link.get(XL+'role','')
        if role_hint not in role.rsplit('/',1)[-1].lower():
            continue
        locs = {}
        for loc in link.findall(LINK+'loc'):
            label = loc.get(XL+'label')
            if label in locs:
                raise ValueError('Localizadores duplicados en la relación.')
            href = loc.get(XL+'href','')
            tag = re.fullmatch(r'https?://(?:xbrl|fasb)\.fasb\.org/us-gaap/(\d{4})/elts/us-gaap-\1\.xsd#us-gaap_([A-Za-z0-9]+)',href)
            locs[label] = (tag[1],tag[2]) if tag else None
        terms = {}
        year = None
        for arc in link.findall(LINK+'calculationArc'):
            origin = locs.get(arc.get(XL+'from'))
            if not origin or origin[1] != parent:
                continue
            child = locs.get(arc.get(XL+'to'))
            if (not child or child[0]!=origin[0] or child[1] in terms or arc.get(XL+'arcrole') not in SUM
                    or arc.get('use','optional')!='optional' or arc.get('priority','0')!='0'
                    or not re.fullmatch(r'-?1(?:\.0+)?',arc.get('weight',''))):
                raise ValueError('La relación contiene una partida o un peso sin soporte.')
            year = origin[0]
            terms[child[1]] = int(Decimal(arc.get('weight')))
        if terms:
            candidates.append((role,year,terms))
    if len(candidates)!=1:
        raise ValueError('Falta una relación de cálculo única para el estado principal.')
    return candidates[0]


def contexts(instance,cik,start,end):
    result = set()
    for context in instance.findall(XBRLI+'context'):
        entity = context.find(XBRLI+'entity')
        period = context.find(XBRLI+'period')
        if entity is None or period is None or len(entity)!=1 or len(context)!=2:
            continue
        identifier = entity.find(XBRLI+'identifier')
        if (identifier is None or identifier.get('scheme') not in ('http://www.sec.gov/CIK','https://www.sec.gov/CIK')
                or (identifier.text or '').strip().zfill(10)!=cik):
            continue
        if start:
            matches = (period.findtext(XBRLI+'startDate'),period.findtext(XBRLI+'endDate'))==(start,end)
        else:
            matches = period.findtext(XBRLI+'instant')==end
        if matches:
            result.add(context.get('id'))
    return result


def amount(instance,year,concept,period,units):
    observations = {}
    for elem in instance.findall('{http://fasb.org/us-gaap/'+year+'}'+concept):
        context = elem.get('contextRef')
        if context not in period or elem.get('unitRef') not in units:
            continue
        if elem.get(NIL) in ('true','1'):
            value = None
        else:
            text = (elem.text or '').strip()
            if not re.fullmatch(r'-?[0-9]{1,40}(?:\.[0-9]{1,30})?',text):
                raise ValueError('Importe inválido en '+concept+'.')
            value = Fraction(text)
        observations.setdefault(value,[]).append(context)
    if len(observations)!=1:
        raise ValueError('Falta un importe inequívoco para '+concept+'.')
    value, refs = next(iter(observations.items()))
    return dict(concept=concept,context=min(refs),value=None if value is None else decimal_text(value))


def extract_equations(calc, raw, model):
    rules,_ = xml_document(calc)
    instance,ns = xml_document(raw)
    if rules.tag not in (LINK+'linkbase','{http://www.w3.org/2001/XMLSchema}schema') or instance.tag!=XBRLI+'xbrl':
        raise ValueError('INVALID_FILING_XML')
    annual = model['annual']
    units = set()
    for unit in instance.findall(XBRLI+'unit'):
        measure = unit.findtext(XBRLI+'measure','')
        prefix,_,currency = measure.rpartition(':')
        if len(unit)==1 and ns.get(prefix)=={'http://www.xbrl.org/2003/iso4217'} and currency==annual['currency']:
            units.add(unit.get('id'))
    result = {}
    for ident,parent,hint in [('balance',BALANCE,'balancesheet'),('cash_roll_forward',CASH,'cashflow')]:
        try:
            role,year,terms = formula(rules,parent,hint)
            start = annual['start'] if parent==CASH else None
            period = contexts(instance,model['entity_id'],start,annual['end'])
            total = amount(instance,year,parent,period,units)
            children = [dict(**amount(instance,year,tag,period,units),weight=w) for tag,w in sorted(terms.items())]
            if total['value'] is None or any(t['value'] is None and t['concept']!='CommitmentsAndContingencies' for t in children):
                raise ValueError('El informe presenta una partida monetaria sin cuantificar.')
            result[ident] = dict(role=role,total=total,terms=children)
        except ValueError as error:
            result[ident] = dict(blocked=str(error))
    return result


def review_equation(model, ident, equation):
    annual = model['annual']
    metrics = {r['metric']:r['fact'] for r in annual['metrics']}
    evidence = []
    def blocked(reason):
        return dict(id=ident,state='BLOCKED',reason=reason,evidence_ids=evidence)
    if 'blocked' in equation:
        return blocked(equation['blocked'])
    total = Fraction(equation['total']['value'])
    terms = equation['terms']
    total_parts = sum(t['weight']*Fraction(t['value']) for t in terms if t['value'] is not None)
    subtotal_residual = total-total_parts
    if ident=='balance':
        required = [metrics.get('balance_total'),metrics.get('assets')]
    else:
        required = [metrics.get('restricted_cash_change'),model['evidence'].get(model['opening_cash_id']),metrics.get('cash_restricted')]
    if not all(required):
        return blocked('Faltan comparadores independientes de Companyfacts para esta ecuación.')
    for index,fact in enumerate(required):
        expected_start = annual['start'] if ident=='cash_roll_forward' and index==0 else None
        expected_end = annual['end']
        if ident=='cash_roll_forward' and index==1:
            expected_end = (date.fromisoformat(annual['start'])-timedelta(days=1)).isoformat()
        if (fact['cik'],fact['accession'],fact['filed'],fact['unit'],fact['start'],fact['end'],fact['taxonomy']) != (
            model['entity_id'],annual['accession'],annual['filed'],annual['currency'],expected_start,expected_end,'us-gaap'):
            return blocked('El comparador tiene otra identidad, divisa, fecha o alcance.')
        evidence.append(fact['id'])
    if ident=='cash_roll_forward' and required[1]['concept']!=required[2]['concept']:
        return blocked('Los saldos de apertura y cierre usan conceptos distintos.')
    source_residual = total-Fraction(required[0]['value'])
    independent = Fraction(required[-1]['value'])
    if ident=='cash_roll_forward':
        independent -= Fraction(required[1]['value'])
    cross_residual = independent-total
    passed = subtotal_residual==source_residual==cross_residual==0
    reason = ('Activos contrastados con el total y las partidas del balance publicado.' if ident=='balance' else
              'Apertura y cierre contrastados con la variación y los flujos que incluye el emisor en este informe.')
    if any(t['value'] is None for t in terms):
        reason += ' El emisor presenta compromisos y contingencias sin importe en esa línea.'
    if not passed:
        reason += ' Hay una diferencia entre partidas, total o comparadores.'
    return dict(id=ident,state='PASS' if passed else 'FAIL',reason=reason,evidence_ids=evidence,
                residual=decimal_text(subtotal_residual),cross_residual=decimal_text(cross_residual),
                source_residual=decimal_text(source_residual),unit=annual['currency'],method='FILED_XBRL')
