"""Matriz reproducible desde catálogo y evidencia real; no incluye valores privados."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.data_catalog import CATALOG
from app.data_service import DataService
from app.data_config import DataSettings

def main():
    file=ROOT/'docs/evidencias/P2/smoke-real.json'
    smoke=json.loads(file.read_text(encoding='utf-8')) if file.exists() else {}
    results={r['access_id']:r for r in smoke.get('results',[])}
    for extra in sorted((ROOT/'docs/evidencias/P2').glob('smoke-real-*.json')):
        data=json.loads(extra.read_text(encoding='utf-8'))
        for row in data.get('results',[]):
            old=results.get(row['access_id'],{})
            if (row.get('checked_at') or '') >= (old.get('checked_at') or ''):results[row['access_id']]=row
        if data.get('performed_at','')>smoke.get('performed_at',''):smoke['performed_at']=data['performed_at']
    lines=['# P2 · Verificación de proveedores', '', f'{len(CATALOG)} modalidades de acceso / 31 proveedores distintos (catálogo original de 34 más RSS oficial BCE). La documentación acredita un endpoint o derecho; **solo un HTTP 200 con respuesta válida acredita conexión**. Mocks, 401/403, cuerpos inválidos y existencia de documentación no cuentan. Uso exclusivo local; no redistribuir feeds personales/internos. No se han creado cuentas ni contratado planes.', '', 'Esta matriz describe un preset acotado por adaptador, no cobertura universal. Catálogo ejecutable: `backend/app/data_catalog.py`. Último smoke: '+smoke.get('performed_at','NO EJECUTADO')+'. Latencia incluye DNS/TLS/descarga real; no se inventa retraso del feed.', '', '| ID / proveedor | Endpoint de consulta | Dato / mercado | Auth / cuota | Adaptador / HTTP / usable | Última comprobación / latencia |', '|---|---|---|---|---|---|']
    for id,s in CATALOG.items():
        r=results.get(id,{});state=r.get('state',s.block or ('NO_CREDENTIALS' if s.credentials else 'NOT_VERIFIED'))
        lines.append(f"| {id} · {s.name} | {s.method} `{s.url or 'Endpoint pendiente'}` · [documentación]({s.docs}) | {s.kind} / {s.venue} / {s.country or 'global'} | {', '.join(s.credentials) or 'público'} · {s.quota_note} | {'sí' if s.implemented else 'no'} / {r.get('http_status') or '—'} / {'sí' if r.get('usable') else 'no'} · {state} | {r.get('checked_at') or 'sin petición'} / {str(r.get('latency_ms'))+' ms' if r.get('latency_ms') is not None else '—'} |")
    lines+=['', '## Derechos por modalidad', '', 'D = visualización local; C = cache local; R = redistribución. “Sí” depende del ámbito indicado y atribución; nunca licencia comercial implícita. Una clave no amplía automáticamente estos permisos.', '', '| ID | Derecho / ámbito | D / C / R | Prueba documental |','|---|---|---|---|']
    for id,s in CATALOG.items():
        r=s.rights
        lines.append(f"| {id} | {r.license} / {r.scope} | {'sí' if r.display_allowed else 'no'} / {'sí' if r.storage_allowed else 'no'} / {'sí' if r.redistribution_allowed else 'no'} | [{r.checked_at.date() if r.checked_at else 'pendiente'}]({r.source}) |")
    lines+=['', '## Límites y pendientes', '', '- SEC: necesita contacto real en `SEC_CONTACT`; no se ha inventado un email.', '- FMI: DataMapper/WEO permite una consulta selectiva; incluye estimaciones/proyecciones, explícitamente etiquetadas. SDMX beta requiere investigación separada; no se usa la antigua API como si siguiera operativa.', '- ESMA: índice machine-to-machine oficial implementado, tres enlaces; no se han descargado todos los ZIP ni se presume permiso de redistribución de referencias.', '- Finnhub / Nasdaq: candidatura gratuita condicionada; no se contabiliza adaptador sin endpoint gratuito útil confirmado.', '- Fuentes con clave: pruebas mock, estado NO_CREDENTIALS hasta configuración local; sin signup ni pago.', '- Kraken/Binance/CoinGecko/Alpaca/Twelve/Alpha/FMP/Massive: derechos de visualización pendientes; el transporte puede comprobar acceso público/documentado pero no publica valores.', '- España y UE: atribución y fidelidad obligatorias. Eurostat/OCDE/Banco Mundial pueden incluir terceros: solo el preset revisado, no permiso para todo el catálogo.', '- BLS: atribución con fecha de acceso y aviso de que BLS no avala análisis posteriores. GDELT: solo metadatos y enlaces; jamás cuerpos o imágenes de artículos.', '- Fixing BCE ≠ spot; curva Treasury ≠ bono; agregado cripto ≠ exchange; IEX ≠ SIP; EOD ≠ realtime. Todas las observaciones tienen execution_eligible=false.', '', '## Fuentes especializadas', '', 'CNMV, BoE y Fed: investigación pendiente de endpoints y permisos. FINRA/CBOE/CME y bonos corporativos: no se presume un feed gratuito. Yahoo/Google/TradingView/Investing/Stooq: sin scraping ni endpoints internos.', '']
    (ROOT/'docs/P2_PROVIDERS_VERIFICACION.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()
