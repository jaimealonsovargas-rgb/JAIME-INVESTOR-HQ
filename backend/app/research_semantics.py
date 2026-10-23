"""Narrow deterministic contradiction guards; not a general semantic verifier.

The model does not calculate or certify financial facts. These checks catch
specific falsifiable claims against typed Python evidence and reject unsupported
amounts/guarantees. Passing them still requires review of the actual argument.
"""
from decimal import Decimal, InvalidOperation
import re
import unicodedata


def normalized(text: str) -> str:
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                           if not unicodedata.combining(c)).split())


def _feature_values(pack):
    features = {}
    for row in pack.get('records', []):
        if not row.get('usable') or not (row.get('scope') == 'DERIVED_FEATURE'
                                        or row.get('data_kind') == 'derived_feature'):
            continue
        name, separator, excerpt_value = row.get('excerpt', '').partition(':')
        if separator:
            features[name.strip()] = row.get('value') if row.get('value') is not None else excerpt_value.strip()
    return features


def _scoped_gap(tail):
    """Missing forecasts/fundamentals do not deny existing historical metrics."""
    return bool(re.match(r'\s+(?:fundamentales?|futur[ao]s?|implicitas?|prospectivas?|'
                         r'fiables|suficientes|garantizad[oa]s?|de (?:valoracion|beneficios|ingresos|liquidez)|'
                         r'para\b)', tail))


def _negated_or_conditional(prefix):
    # Restrict this exemption to the current clause, not an earlier sentence.
    clause = re.split(r'[.!?;]|\b(?:pero|sin embargo)\b', prefix)[-1]
    return bool(re.search(r'\b(?:no|sin|nunca|si|podria[n]?|suponiendo|hipotesis|'
                          r'no demostrado|por comprobar)\b', clause))


def validate_financial_prose(text: str, pack: dict) -> None:
    prose = normalized(text)
    features = _feature_values(pack)
    if features:
        absence = re.compile(r'\b(?:no se (?:calculan|calcularon|han calculado)|'
                             r'no (?:hay|existen|disponemos de|contamos con)) '
                             r'(?:estadisticas|metricas|indicadores)(?: calculad[oa]s)?\b|'
                             r'\bsin (?:estadisticas|metricas|indicadores) calculad[oa]s\b')
        for match in absence.finditer(prose):
            if not _scoped_gap(prose[match.end():]):
                raise ValueError('CONTRADICTS_COMPUTED_FEATURES')
        feature_labels = {'sample_volatility': r'volatilidad(?: historica| observada| calculada)?',
                          'period_return': r'(?:retorno|rentabilidad)(?: del periodo| observad[ao]| calculad[ao])?',
                          'max_drawdown_observed': r'drawdown(?: observado| calculado)?'}
        for name, label in feature_labels.items():
            if name not in features:
                continue
            for match in re.finditer(r'\b(?:no (?:se ha calculado|se dispone de|conocemos)|falta(?: el dato de)?) (?:la |el )?'
                                     + label + r'\b', prose):
                if not _scoped_gap(prose[match.end():]):
                    raise ValueError('CONTRADICTS_COMPUTED_FEATURES')
        try:
            observed_return = Decimal(str(features['period_return']))
        except (KeyError, InvalidOperation):
            observed_return = None
        if observed_return is not None and observed_return.is_finite():
            # Only an explicit statement about this measured return. A negative
            # period return does not disprove a hypothetical future recovery.
            pattern = (r'\b(?:rentabilidad|retorno|rendimiento|variacion) '
                       r'(?:observad[ao]|calculad[ao]|del periodo|de la muestra|historica|acumulad[ao]) '
                       r'(?:es|fue|resulta|resulto|ha sido) (positiv[ao]|negativ[ao]|nul[ao])\b')
            for match in re.finditer(pattern, prose):
                if _negated_or_conditional(prose[:match.start()]):
                    continue
                claimed = 1 if match[1].startswith('positiv') else -1 if match[1].startswith('negativ') else 0
                actual = 1 if observed_return > 0 else -1 if observed_return < 0 else 0
                if claimed != actual:
                    raise ValueError('CONTRADICTS_RETURN_SIGN')

    # Typed prices cannot substantiate claimed company accounts. Conditional
    # mechanisms remain hypotheses; lack of fundamentals remains a valid gap.
    direct = [row for row in pack.get('records', []) if row.get('usable') and row.get('scope') == 'INSTRUMENT']
    market_only = bool(direct) and all(row.get('data_kind') in ('market_quote', 'ohlcv') for row in direct)
    if market_only:
        pattern = (r'\b(?:ingresos|ventas|beneficios|margenes|margen(?: operativo)?|'
                   r'flujo de caja|generacion de caja) '
                   r'(?:han (?:aumentado|mejorado|crecido)|crecen|crecieron|aumentaron|'
                   r'aumentan|mejoran|mejoraron|suben|bajan|caen|cayeron|son solidos|es solido)\b')
        for match in re.finditer(pattern, prose):
            if not _negated_or_conditional(prose[:match.start()]):
                raise ValueError('UNSUPPORTED_FINANCIAL_ASSERTION')

    guarantee = (r'\b(?:rentabilidad|beneficios|ganancias|retornos?|subida) '
                 r'(?:esta[n]? |es |son )?garantizad[oa]s?\b|'
                 r'\b(?:garantiza[n]?|asegura[n]?) (?:una? |la |los )?'
                 r'(?:beneficios|ganancias|rentabilidad|retornos?|subida)\b')
    for match in re.finditer(guarantee, prose):
        if not _negated_or_conditional(prose[:match.start()]):
            raise ValueError('UNSUPPORTED_GUARANTEE')

    # Amounts in words are still quantities; they cannot bypass a qualitative
    # contract simply because the digit guard does not recognize them.
    number = (r'(?:cero|uno|una|un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|'
              r'once|doce|trece|catorce|quince|dieciseis|diecisiete|dieciocho|diecinueve|'
              r'veinte|veinti\w+|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|'
              r'cien|ciento|doscientos|trescientos|cuatrocientos|quinientos|seiscientos|'
              r'setecientos|ochocientos|novecientos|mil|millon|millones)')
    amount = rf'\b{number}(?: y {number})? (?:de )?(?:por ciento|puntos (?:porcentuales|basicos)|euros?|dolares?|libras?)\b'
    if re.search(amount, prose):
        raise ValueError('QUALITATIVE_NUMERIC_AMOUNT')
