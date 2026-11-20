"""Selected standard concepts, without silently equating different accounting scopes.

Raw companyfacts is retained privately for reproducibility / future mappings.
An annual view is one filing, one period, one unit. No forecasts or FX conversion.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import re
from app.data_identity import fingerprint

PARSER_VERSION = 'sec-financials-v2'
# Priority applies only within a filing and period; never sum alternatives.
METRICS = {
    'revenue': ('Ingresos', 'duration', ['us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax', 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax', 'us-gaap:Revenues', 'us-gaap:SalesRevenueNet', 'ifrs-full:Revenue']),
    'net_income': ('Resultado atribuible a la matriz', 'duration', ['us-gaap:NetIncomeLoss', 'ifrs-full:ProfitLossAttributableToOwnersOfParent']),
    'income_total': ('Resultado neto con minoritarios', 'duration', ['us-gaap:ProfitLoss', 'ifrs-full:ProfitLoss']),
    'income_common': ('Resultado disponible para acciones ordinarias', 'duration', ['us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic']),
    'operating_income': ('Resultado operativo', 'duration', ['us-gaap:OperatingIncomeLoss', 'ifrs-full:ProfitLossFromOperatingActivities']),
    'assets': ('Activos', 'instant', ['us-gaap:Assets', 'ifrs-full:Assets']),
    'liabilities': ('Pasivos', 'instant', ['us-gaap:Liabilities', 'ifrs-full:Liabilities']),
    'equity': ('Patrimonio atribuible a la matriz', 'instant', ['us-gaap:StockholdersEquity', 'ifrs-full:EquityAttributableToOwnersOfParent']),
    'equity_total': ('Patrimonio con minoritarios', 'instant', ['us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', 'ifrs-full:Equity']),
    'current_assets': ('Activo corriente', 'instant', ['us-gaap:AssetsCurrent', 'ifrs-full:CurrentAssets']),
    'current_liabilities': ('Pasivo corriente', 'instant', ['us-gaap:LiabilitiesCurrent', 'ifrs-full:CurrentLiabilities']),
    'cash': ('Efectivo y equivalentes', 'instant', ['us-gaap:CashAndCashEquivalentsAtCarryingValue', 'ifrs-full:CashAndCashEquivalents']),
    'cash_restricted': ('Efectivo, equivalentes y efectivo restringido', 'instant', ['us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']),
    'debt_current': ('Deuda corriente declarada', 'instant', ['us-gaap:DebtCurrent']),
    'long_debt_current': ('Vencimientos corrientes de deuda a largo plazo', 'instant', ['us-gaap:LongTermDebtCurrent']),
    'long_debt_noncurrent': ('Deuda a largo plazo no corriente', 'instant', ['us-gaap:LongTermDebtNoncurrent']),
    'long_debt_total': ('Deuda a largo plazo total declarada', 'instant', ['us-gaap:LongTermDebt']),
    'operating_cash_flow': ('Flujo de caja operativo', 'duration', ['us-gaap:NetCashProvidedByUsedInOperatingActivities', 'ifrs-full:CashFlowsFromUsedInOperatingActivities']),
    'capex': ('Pagos por inmovilizado material', 'duration', ['us-gaap:PaymentsToAcquirePropertyPlantAndEquipment', 'ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities']),
    'basic_eps': ('Beneficio por acción básico', 'duration', ['us-gaap:EarningsPerShareBasic', 'ifrs-full:BasicEarningsLossPerShare']),
    'diluted_eps': ('Beneficio por acción diluido', 'duration', ['us-gaap:EarningsPerShareDiluted', 'ifrs-full:DilutedEarningsLossPerShare']),
    'shares_basic': ('Acciones medias básicas', 'duration', ['us-gaap:WeightedAverageNumberOfSharesOutstandingBasic', 'ifrs-full:WeightedAverageNumberOfOrdinarySharesOutstanding']),
    'shares_diluted': ('Acciones medias diluidas', 'duration', ['us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding']),
    'shares_outstanding': ('Acciones en circulación declaradas', 'instant', ['dei:EntityCommonStockSharesOutstanding', 'us-gaap:CommonStockSharesOutstanding']),
    'investing_cash_flow': ('Flujo de inversión', 'duration', ['us-gaap:NetCashProvidedByUsedInInvestingActivities']),
    'financing_cash_flow': ('Flujo de financiación', 'duration', ['us-gaap:NetCashProvidedByUsedInFinancingActivities']),
    'restricted_cash_fx': ('Efecto de divisas sobre efectivo incluido restringido', 'duration', ['us-gaap:EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']),
    'restricted_cash_change': ('Variación de efectivo incluido restringido y divisas', 'duration', ['us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect']),
    'balance_total': ('Pasivos y patrimonio total declarados', 'instant', ['us-gaap:LiabilitiesAndStockholdersEquity']),
}
CORE_METRICS = ('revenue', 'net_income', 'assets', 'equity', 'cash', 'operating_cash_flow')
PERIODIC_FORMS = {'10-K', '10-K/A', '10-Q', '10-Q/A', '20-F', '20-F/A', '40-F', '40-F/A'}
ANNUAL_FORMS = {'10-K', '10-K/A', '20-F', '20-F/A', '40-F', '40-F/A'}
DOCUMENT_FORMS = PERIODIC_FORMS | {'8-K', '8-K/A', '6-K', '6-K/A'}


def cik_text(value):
    value = str(value)
    if not re.fullmatch(r'\d{1,10}', value) or int(value) <= 0:
        raise ValueError('INVALID_CIK')
    return value.zfill(10)


def text(value, limit=500):
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError('INVALID_TEXT')
    return value


def day(value):
    return date.fromisoformat(value).isoformat()


def accession(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}', value):
        raise ValueError('INVALID_ACCESSION')
    return value


def filed_bound(value):
    return (datetime.fromisoformat(value).replace(tzinfo=timezone.utc) + timedelta(days=1, hours=5)).isoformat()


def document_url(cik, accn, primary=None):
    base = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn.replace("-", "")}/'
    if primary and re.fullmatch(r'[A-Za-z0-9_.-]{1,240}', primary) and '..' not in primary:
        return base + primary
    return base + accn + '-index.html'


def parse_submissions(body, cik):
    if cik_text(body['cik']) != cik:
        raise ValueError('ISSUER_MISMATCH')
    recent = body['filings']['recent']
    keys = ('accessionNumber', 'filingDate', 'reportDate', 'form', 'primaryDocument')
    if not all(isinstance(recent.get(k), list) for k in keys):
        raise ValueError('INVALID_FILINGS')
    count = len(recent['accessionNumber'])
    if count > 100000 or any(len(recent[k]) != count for k in keys):
        raise ValueError('INVALID_FILINGS')
    accept = recent.get('acceptanceDateTime', [''] * count)
    if not isinstance(accept, list) or len(accept) != count:
        raise ValueError('INVALID_FILINGS')
    documents = {}
    for i in range(count):
        form = text(recent['form'][i], 30)
        if form not in DOCUMENT_FORMS:
            continue
        accn = accession(recent['accessionNumber'][i])
        filed = day(recent['filingDate'][i])
        primary = text(recent['primaryDocument'][i], 500)
        accepted = text(accept[i], 50) or None
        if accepted:
            parsed = datetime.fromisoformat(accepted.replace('Z', '+00:00'))
            accepted = parsed.astimezone(timezone.utc).isoformat() if parsed.utcoffset() is not None else None
        doc = dict(accession=accn, form=form, filed=filed,
                   report_date=day(recent['reportDate'][i]) if recent['reportDate'][i] else None,
                   accepted_at=accepted, published_bound=filed_bound(filed),
                   url=document_url(cik, accn, primary), primary_document=primary,
                   amended=form.endswith('/A'))
        if accn in documents and documents[accn] != doc:
            raise ValueError('CONFLICTING_FILING')
        documents[accn] = doc
    old = body['filings'].get('files', [])
    if not isinstance(old, list) or len(old) > 1000:
        raise ValueError('INVALID_HISTORY_MANIFEST')
    # Record coverage gaps; do not fetch caller-supplied historic file paths.
    older = [dict(name=text(f['name'], 120), filing_from=day(f['filingFrom']),
                  filing_to=day(f['filingTo'])) for f in old]
    fy_end = text(body.get('fiscalYearEnd', ''), 4)
    return list(documents.values()), dict(name=text(body['name']), fiscal_year_end=fy_end or None,
        sic=text(str(body.get('sic', '')), 10), sic_description=text(body.get('sicDescription', '')),
        entity_type=text(body.get('entityType', ''), 50), document_count=len(documents),
        recent_filing_count=count, older_files=older, complete_history=not bool(older),
        scope='Recent periodic reports and 8-K/6-K metadata; linked originals, not downloaded HTML.')


def parse_companyfacts(body, cik):
    if cik_text(body['cik']) != cik or not isinstance(body['facts'], dict):
        raise ValueError('ISSUER_MISMATCH')
    result = {}
    for metric, (_, kind, tags) in METRICS.items():
        for priority, full_tag in enumerate(tags):
            taxonomy, concept = full_tag.split(':')
            field = body['facts'].get(taxonomy, {}).get(concept)
            if field is None:
                continue
            units = field['units']
            if not isinstance(units, dict):
                raise ValueError('INVALID_UNITS')
            for unit, values in units.items():
                text(unit, 40)
                if not isinstance(values, list):
                    raise ValueError('INVALID_FACTS')
                for row in values:
                    if row.get('form') not in PERIODIC_FORMS:
                        continue
                    end = day(row['end'])
                    start = day(row['start']) if row.get('start') else None
                    if start and start > end:
                        raise ValueError('INVALID_PERIOD')
                    unresolved = (kind == 'duration') != bool(start)
                    value = Decimal(str(row['val']))
                    if not value.is_finite() or len(str(value)) > 80:
                        raise ValueError('INVALID_NUMBER')
                    filed = day(row['filed'])
                    fy = row.get('fy')
                    if fy is not None and (not isinstance(fy, int) or not 1900 <= fy <= 2200):
                        raise ValueError('INVALID_FISCAL_YEAR')
                    duration = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1 if start else None
                    fact = dict(cik=cik, metric=metric, taxonomy=taxonomy, concept=concept, priority=priority,
                        unit=unit, value=format(value, 'f'), start=start, end=end, days=duration,
                        period_type='INSTANT' if start is None else 'ANNUAL' if 300 <= duration <= 400 else 'QUARTER' if 60 <= duration <= 120 else 'DURATION',
                        accession=accession(row['accn']), filed=filed, form=row['form'],
                        filing_fiscal_year=fy, filing_fiscal_period=text(row.get('fp') or '', 10),
                        frame=text(row.get('frame') or '', 40) or None, published_bound=filed_bound(filed))
                    if unresolved:
                        fact['period_type'] = 'UNRESOLVED'
                        fact['quality_flags'] = ['PERIOD_TYPE_MISMATCH']
                    # Fiscal labels/frame describe filing context, not the period's year.
                    fact['id'] = fingerprint([PARSER_VERSION, fact])
                    result[fact['id']] = fact
                    if len(result) > 150000:
                        raise ValueError('TOO_MANY_FACTS')
    facts = list(result.values())
    return facts, dict(name=text(body['entityName']), fact_count=len(facts), mapped_metrics=len({f['metric'] for f in facts}),
        metric_denominator=len(METRICS), window_start=min((f['end'] for f in facts), default=None),
        window_end=max((f['end'] for f in facts), default=None),
        scope='Selected standard entity-wide concepts; custom/segment facts not covered.')


def annual_view(facts):
    """Latest annual period; exact accession/end/start, explicit conflicts and gaps."""
    durations = [f for f in facts if not f.get('quality_flags') and f['period_type'] == 'ANNUAL' and f['form'] in ANNUAL_FORMS and re.fullmatch('[A-Z]{3}', f['unit'])]
    if not durations:
        return None
    keys = {(f['end'], f['filed'], f['accession'], f['start'], f['unit']) for f in durations}
    end, filed, accn, start = max(k[:4] for k in keys)
    units = {k[4] for k in keys if k[:4] == (end, filed, accn, start)}
    if len(units) != 1:
        return dict(start=start, end=end, accession=accn, filed=filed, currency=None,
                    form=next(f['form'] for f in durations if f['accession'] == accn),
                    metrics=[], core_available=0, core_total=len(CORE_METRICS),
                    state='AMBIGUOUS_CURRENCY', currencies=sorted(units), url=document_url(facts[0]['cik'], accn))
    unit = next(iter(units))
    pool = defaultdict(list)
    for fact in facts:
        if fact.get('quality_flags'):
            continue
        if (fact['end'], fact['filed'], fact['accession']) != (end, filed, accn):
            continue
        if fact['start'] not in (None, start):
            continue
        expected_unit = 'shares' if fact['metric'].startswith('shares_') else unit + '/shares' if fact['metric'].endswith('_eps') else unit
        if fact['unit'] == expected_unit:
            pool[fact['metric']].append(fact)
    metrics = []
    for key, (label, _, _) in METRICS.items():
        options = pool[key]
        preferred = [f for f in options if f['priority'] == min(x['priority'] for x in options)] if options else []
        values = {Decimal(f['value']) for f in preferred}
        status = 'AVAILABLE' if len(values) == 1 else 'CONFLICT' if values else 'MISSING'
        chosen = sorted(preferred, key=lambda f: f['id'])[0] if status == 'AVAILABLE' else None
        metrics.append(dict(metric=key, label=label, state=status, fact=chosen,
                            candidate_ids=sorted({f['id'] for f in options})))
    available = sum(m['state'] == 'AVAILABLE' for m in metrics if m['metric'] in CORE_METRICS)
    return dict(start=start, end=end, accession=accn, filed=filed, currency=unit,
                form=durations[next(i for i, f in enumerate(durations) if f['accession'] == accn)]['form'],
                metrics=metrics, core_available=available, core_total=len(CORE_METRICS),
                state='DESCRIPTIVE_COMPLETE' if available == len(CORE_METRICS) else 'PARTIAL',
                url=document_url(facts[0]['cik'], accn))
