"""Evidence-bound adaptations of three pinned research skills; no tools or inference."""
from datetime import datetime, timedelta
from app.research_contracts import digest, sanitize

SKILL_PIN = '41ccf4e41bb0927f4d718e78e1fc01d639b6f53e'


def research_workflows(dossier, now):
    valid = {e['id']: e for e in dossier['evidence']
             if e['available'] and e['rights_ok'] and e['freshness'] == 'FRESH'}
    complete = bool(dossier['jobs']) and all(j['state'] == 'SUCCEEDED' for j in dossier['jobs'])
    usable = complete and dossier['quality']['state'] == 'VERIFIED_DATA'
    claims = []
    if usable:
        for result in dossier['results']:
            if result.get('quality', {}).get('state') == 'REJECTED':
                continue
            for c in result['claims']:
                if c['verified'] and c['evidence_ids'] and all(i in valid for i in c['evidence_ids']):
                    claims.append(dict(kind=c['claim_type'], text=sanitize(c['text']), evidence_ids=c['evidence_ids']))
    # No news coverage is NOT evidence that nothing material happened overnight.
    morning = dict(skill='morning-note', state='AVAILABLE' if claims else 'ABSTAINED',
        headline='Resumen descriptivo del ciclo' if claims else 'Sin evidencia suficiente para una nota',
        observations=claims[:8], coverage='Solo evidencia del ciclo seleccionado; no cobertura completa de noticias nocturnas.',
        trade_ideas=[], target_price=None)
    hypotheses = [c for c in claims if c['kind'] == 'HYPOTHESIS']
    thesis = dict(skill='thesis-tracker', state='PROVISIONAL' if hypotheses else 'NO_THESIS',
        hypotheses=hypotheses, pillars=[], risks=[], conviction=None, action=None,
        version=dossier['thesis_version'], run_key=dossier['active_run_key'],
        update_log=[dict(run_key=r) for r in reversed(dossier['runs'])],
        reason='Hipótesis vinculadas; revisión de pilares e invalidación pendiente.' if hypotheses else
               'El ciclo descriptivo no ha formulado una tesis; no se deduce de métricas de precio.')
    events = []
    if usable:
        for ident, e in valid.items():
            content=e.get('content', {}); meta=content.get('metadata', {})
            if content.get('data_kind') != 'news_metadata' or meta.get('event_confirmed') != 'true':
                continue
            try:
                date=datetime.fromisoformat(meta['event_at'])
                if date.utcoffset() is None or not now <= date <= now + timedelta(days=30):
                    continue
            except (KeyError, TypeError, ValueError):
                continue
            events.append(dict(at=date.isoformat(), title=sanitize(meta.get('title','Evento')),
                evidence_ids=[ident], source=e['url']))
    calendar = dict(skill='catalyst-calendar', state='AVAILABLE' if events else 'NO_CONFIRMED_EVENTS',
        events=sorted(events, key=lambda e:e['at'])[:30], horizon_days=30,
        reason='Solo eventos con fecha y zona confirmadas por P2; no se estima la próxima fecha de resultados.')
    payload=dict(version='p4-research-workflows-v1', skill_pin=SKILL_PIN, evaluated_at=now.isoformat(),
        case_id=dossier['id'], run_key=dossier['active_run_key'], advisory_only=True,
        morning_note=morning, thesis_tracker=thesis, catalyst_calendar=calendar)
    return {**payload, 'content_hash':digest(payload)}
