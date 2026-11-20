"""Score-free projection of a verified B4 dossier for the hypothesis author."""
from app.quant_store import digest


def proposer_view(dossier):
    # Only immutable design fields cross this boundary. Free text, arbitrary IDs
    # and result-derived hashes could encode a verdict even without a numeric score.
    rules = []
    for row in dossier['hypotheses']:
        family, window = row['family'], row.get('lookback')
        if family != 'SMA_LONG_CASH' or type(window) is not int or not 2 <= window <= 252:
            raise ValueError('PROPOSER_SCHEMA_UNSUPPORTED')
        rules.append((family, window))
    structures = [dict(family=family, lookback=window) for family, window in sorted(set(rules))]
    return dict(version='jaime-proposer-context-v1', protocol=dossier['search_protocol_ref'],
                universe=dossier['source']['universe_hash'],
                observed_period=dict(first=dossier['warmup']['first'], last=dossier['evaluation']['last']),
                previously_registered=[dict(**rule, structure_id=digest(rule)) for rule in structures])
