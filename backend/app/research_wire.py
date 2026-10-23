"""Lossless, bounded transport for one qualitative debate argument per call.

This changes serialization, never generates reasoning or repairs incomplete JSON.
Public contracts, evidence identities and financial validators stay authoritative.
"""
from copy import deepcopy
import json
import re

from app.research_contracts import digest


WIRE_VERSION = 'debate-wire.v2'
ROLES = {'BullResponse': 'bull_advocate', 'BearResponse': 'bear_skeptic', 'ChairResponse': 'cio_chair'}
ROW_FIELDS = {
    'bull_advocate': {'i': 'argument_id', 't': 'thesis', 'm': 'mechanism', 'e': 'supporting_evidence_ids',
                      'a': 'assumption', 'f': 'falsification'},
    'bear_skeptic': {'i': 'argument_id', 'b': 'target_bull_argument_id', 'o': 'objection', 'm': 'mechanism',
                    'e': 'counter_evidence_ids', 'g': 'evidence_gap', 'c': 'change_of_mind'},
    'cio_chair': {'b': 'bull_argument_id', 'r': 'bear_argument_id', 'd': 'disagreement',
                  'e': 'evidence_ids', 'l': 'limitation'},
}
ROW_KEYS = {'bull_advocate': 'arguments', 'bear_skeptic': 'objections', 'cio_chair': 'findings'}
CONCLUSIONS = {'A': 'ABSTAIN_INSUFFICIENT_EVIDENCE', 'C': 'CONDITIONAL_RESEARCH'}
LEGENDS = {
    'bull_advocate': 'i=argument_id; t=tesis; m=mecanismo; e=IDs de evidencia; a=supuesto; f=falsación.',
    'bear_skeptic': 'i=argument_id; b=ID Bull refutado; o=objeción; m=mecanismo; e=IDs de evidencia contraria; g=laguna; c=prueba que cambiaría el juicio.',
    'cio_chair': 'b=ID Bull; r=ID Bear; d=desacuerdo; e=IDs de evidencia; l=límite; s=síntesis; c=A abstención o C investigación condicional; u=incógnitas.',
}


def _text(minimum=12, maximum=110):
    # llama.cpp may choose the pattern branch over minLength/maxLength when
    # converting schema to grammar. Express BOTH constraints in that pattern.
    return {'type': 'string', 'minLength': minimum, 'maxLength': maximum,
            'pattern': '^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ,;:.¿?¡!()/—–-]{' + str(minimum) + ',' + str(maximum) + '}$'}


def strict_json(text):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('WIRE_DUPLICATE_FIELD')
            out[key] = value
        return out
    return json.loads(text, object_pairs_hook=unique)


def _check(value, rule, path='$'):
    """Validate the small wire schema again in Python, independently of grammar."""
    kind = rule['type']
    if kind == 'object':
        if not isinstance(value, dict) or set(value) != set(rule['required']):
            raise ValueError('WIRE_FIELDS_INVALID')
        for key, child in value.items():
            _check(child, rule['properties'][key], path + '.' + key)
    elif kind == 'array':
        if not isinstance(value, list) or not rule['minItems'] <= len(value) <= rule['maxItems']:
            raise ValueError('WIRE_ARRAY_INVALID')
        if len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            raise ValueError('WIRE_DUPLICATE_ITEM')
        for index, child in enumerate(value):
            _check(child, rule['items'], path + '[' + str(index) + ']')
    elif kind == 'string':
        if not isinstance(value, str):
            raise ValueError('WIRE_STRING_INVALID')
        if 'enum' in rule and value not in rule['enum']:
            raise ValueError('WIRE_UNKNOWN_ID_OR_ENUM')
        if not rule.get('minLength', 0) <= len(value) <= rule.get('maxLength', 1000):
            error = ValueError('WIRE_STRING_BUDGET')
            error.details = {'path':path,'chars':len(value),'min':rule.get('minLength',0),'max':rule.get('maxLength',1000)}
            raise error
        if 'pattern' in rule and re.fullmatch(rule['pattern'], value) is None:
            raise ValueError('WIRE_NUMERIC_PROSE')
    else:
        raise ValueError('WIRE_SCHEMA_INVALID')


class DebateWire:
    def __init__(self, contract, data):
        self.contract = contract
        self.role = ROLES[contract.__name__]
        rows = data.get('evidence_pack', {}).get('records', [])
        ids = [row['id'] for row in rows]
        if any(not isinstance(item, str) for item in ids) or len(ids) != len(set(ids)):
            raise ValueError('WIRE_EVIDENCE_IDS_INVALID')
        self.to_wire = {item: f'E{index + 1}' for index, item in enumerate(ids)}
        self.from_wire = {alias: item for item, alias in self.to_wire.items()}
        self.usable = [self.to_wire[row['id']] for row in rows if row.get('usable')]
        self.prior = data.get('prior_arguments', {})
        self.data = deepcopy(data)
        for row in self.data.get('evidence_pack', {}).get('records', []):
            row['id'] = self.to_wire[row['id']]
        # Explicit typed location only: never replace IDs embedded in prose or
        # the immutable source evidence_id, which model_view deliberately omits.
        for finding in self.data.get('computed_context', {}).get('findings', []):
            if 'evidence_id' in finding or 'id' in finding:
                try:
                    key = 'evidence_id' if 'evidence_id' in finding else 'id'
                    finding['id'] = self.to_wire[finding.pop(key)]
                except KeyError:
                    raise ValueError('WIRE_COMPUTED_EVIDENCE_MISSING') from None
        self.data['prior_arguments'] = {
            role: self._encode_prior(role, result) if role in ROW_FIELDS else deepcopy(result)
            for role, result in self.prior.items()
        }
        self.schema = self._schema()

    @property
    def metadata(self):
        return {'wire_version': WIRE_VERSION, 'wire_map_hash': digest(self.to_wire)}

    @property
    def instructions(self):
        # Trusted serialization contract; input evidence remains untrusted data.
        previous = ''
        if self.role != 'bull_advocate':
            previous = ' Previos Bull: ' + LEGENDS['bull_advocate']
        if self.role == 'cio_chair':
            previous += ' Previos Bear: ' + LEGENDS['bear_skeptic']
        return (' Transporte ' + WIRE_VERSION + ': devuelve exactamente UN objeto JSON compacto, sin envoltorio. '
                + LEGENDS[self.role] + ' Una oración breve por campo; no repitas etiquetas. '
                'e contiene solo aliases E de las fuentes. Los argumentos previos usan estas mismas claves. '
                'Máximo ciento diez caracteres por campo, síntesis ciento ochenta.' + previous)

    def _encode_prior(self, role, result):
        encoded = []
        for row in result.get(ROW_KEYS[role], []):
            out = {short: deepcopy(row[long]) for short, long in ROW_FIELDS[role].items()}
            try:
                out['e'] = [self.to_wire[item] for item in out['e']]
            except KeyError:
                raise ValueError('WIRE_PRIOR_EVIDENCE_MISSING') from None
            encoded.append(out)
        # Prior evidence/argument structure remains visible, including multiple legacy arguments.
        return encoded

    def _schema(self):
        cite = {'type': 'array', 'minItems': 0 if self.role == 'bear_skeptic' else 1, 'maxItems': 2,
                'items': {'type': 'string', 'enum': self.usable}}
        bull_ids = [row['argument_id'] for row in self.prior.get('bull_advocate', {}).get('arguments', [])]
        bear_ids = [row['argument_id'] for row in self.prior.get('bear_skeptic', {}).get('objections', [])]
        ident = lambda items: {'type': 'string', 'enum': items}
        if self.role == 'bull_advocate':
            fields = {'i': ident(['B1']), 't': _text(), 'm': _text(), 'e': cite, 'a': _text(8), 'f': _text(8)}
        elif self.role == 'bear_skeptic':
            fields = {'i': ident(['R1']), 'b': ident(bull_ids), 'o': _text(), 'm': _text(), 'e': cite,
                      'g': _text(0), 'c': _text(8)}
        else:
            fields = {'b': ident(bull_ids), 'r': ident(bear_ids), 'd': _text(), 'e': cite, 'l': _text(8),
                      's': _text(12, 180), 'c': ident(list(CONCLUSIONS)),
                      'u': {'type': 'array', 'minItems': 1, 'maxItems': 1, 'items': _text(1)}}
        return {'type': 'object', 'properties': fields, 'required': list(fields), 'additionalProperties': False}

    def decode(self, value):
        _check(value, self.schema)
        row = {long: deepcopy(value[short]) for short, long in ROW_FIELDS[self.role].items()}
        citations = ROW_FIELDS[self.role]['e']
        row[citations] = [self.from_wire[item] for item in value['e']]
        decoded = {ROW_KEYS[self.role]: [row]}
        if self.role == 'cio_chair':
            decoded.update(synthesis=value['s'], conclusion=CONCLUSIONS[value['c']], unknowns=value['u'])
        return self.contract.model_validate(decoded)
