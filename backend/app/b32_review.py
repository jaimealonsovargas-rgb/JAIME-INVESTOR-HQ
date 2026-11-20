"""Code-pinned private review for one B3.2 dataset, never a caller trust switch."""
import hashlib
import json
from pathlib import Path
from app.config import ROOT
from app.admission_contracts import fingerprint, validate_candidate

PROTOCOL = 'daily-trend-retrospective-v1'
PROTOCOL_PATH = 'docs/actual/B3_2_PROTOCOLO_v1.json'
PROTOCOL_SHA256 = '49040830d387734940faab8a5d413102a98f5b1acb03bfed2fd7258b1664be1f'
REVIEW_PATH = 'output/b32-20261118/admission-review.json'
REVIEW_SHA256 = 'eb2817157b800ea0fd40f18675769ea55126c892d702b8154239c365fe3a4be2'


def checked_file(relative, expected, limit=1024*1024):
    path = ROOT / relative
    if path.resolve() != path.absolute() or not path.is_relative_to(ROOT) or path.is_symlink():
        raise ValueError('REVIEW_PATH_INVALID')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('REVIEW_FILE_INTEGRITY')
    return raw


def reviewed_bundle():
    review = json.loads(checked_file(REVIEW_PATH, REVIEW_SHA256))
    checked_file(PROTOCOL_PATH, PROTOCOL_SHA256)
    for ref in review['local_evidence']:
        checked_file(ref['path'], ref['sha256'])
    return review


def reviewed_records():
    try:
        return {r['hash']:r for r in reviewed_bundle()['evidence']['records']}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def apply_identity_review(candidate):
    """Overlay a reviewed native currency without altering the source catalogue."""
    review = reviewed_bundle()
    if fingerprint(validate_candidate(candidate)) != review['source_candidate_hash']:
        raise ValueError('REVIEW_CANDIDATE_MISMATCH')
    result = dict(candidate, currency=review['native_currency'])
    if fingerprint(validate_candidate(result)) != review['candidate_hash']:
        raise ValueError('REVIEW_CANDIDATE_MISMATCH')
    return result
