import type {DatasetAssessment as Assessment} from '../marketApi';
import {marketTime} from '../marketApi';

export function DatasetAssessment({value,listingId,onChoose}:{value:Assessment;listingId:string;onChoose:(id:string)=>void}){
  const identity=value.identity;
  const documented=identity.state==='DOCUMENTED';
  const contract=identity.current_contract;
  const labels={PASS:'Comprobado',WARN:'Alcance limitado',BLOCKED:'Pendiente'};
  return <section className="dataset-assessment" aria-label="Calidad para investigación">
    <div className="market-heading"><h3>Calidad para investigación</h3><span className="dataset-verdict">No apto para backtest</span></div>
    <dl className="dataset-summary">
      <div><dt>Empresa y acción</dt><dd>{documented?'Vínculo documentado':'Requiere revisión'}</dd></div>
      <div><dt>Sesiones guardadas</dt><dd>{value.dataset?`${value.dataset.sessions} de ${value.dataset.expected_sessions??'—'} en el intervalo`:'Sin histórico'}</dd></div>
      <div><dt>Uso actual</dt><dd>{value.research_state==='EXPLORATORY_ONLY'?'Exploración descriptiva':'Datos insuficientes'}</dd></div>
    </dl>
    {documented?<p>{identity.security_title} · CIK {identity.cik}. Vínculo conocido desde {marketTime(identity.known_from)}.</p>:<p>{identity.reason}</p>}
    {documented&&identity.market_listing_id&&identity.market_listing_id!==listingId?<button onClick={()=>onChoose(identity.market_listing_id!)}>Abrir acción vinculada</button>:null}
    <details className="market-manifest"><summary>Ver comprobaciones y evidencia</summary>
      <p>{value.family}. La cobertura se refiere al intervalo descargado; no acredita datos actuales ni seguimiento continuo.</p>
      <ul className="dataset-checks">{value.checks.map(item=><li key={item.code}><div><strong>{item.label}</strong><span data-state={item.state}>{labels[item.state]}</span></div><p>{item.detail}</p></li>)}</ul>
      {identity.evidence.length?<><h4>Evidencia de identidad</h4><ul className="dataset-evidence">{identity.evidence.map(item=><li key={item.kind+item.id}><a href={item.url} target="_blank" rel="noreferrer">{item.kind==='SEC_COMMON_STOCK_COVER'?'Portada del informe SEC':item.kind==='CATALOGUE_SEC'?'Catálogo SEC':'Catálogo Alpaca'}</a><small>Recibido {marketTime(item.received_at)} · {item.sha256.slice(0,12)}…</small></li>)}</ul></>:null}
      {contract?<div className="dataset-contract"><h4>Contrato observado · IBKR</h4>
        <p>{contract.symbol} · {contract.currency} · {contract.primary_exchange}. Contrato {contract.con_id}; ruta {contract.routing_exchange}.</p>
        <p>Captación iniciada {marketTime(contract.observed_at)}. Vínculo revisado {marketTime(contract.known_from)}.</p>
        <p>{identity.native_currency_reason} SMART es la ruta, no la bolsa principal.</p>
        <small>Informe local verificado · {contract.report_sha256.slice(0,12)}… · <a href={contract.documentation_url} target="_blank" rel="noreferrer">Definición de los campos en IBKR</a></small>
      </div>:<p>Divisa nativa: sin verificar. {identity.native_currency_reason}</p>}
      <p>{value.dataset?`Serie solicitada en ${value.dataset.price_currency} por acción; volumen en acciones. `:''}La divisa del contrato observado no certifica la divisa ni la identidad de todo el histórico.</p>
      <small>Revisión {marketTime(value.as_of)} · {value.policy} · {value.manifest_id.slice(0,12)}…</small>
    </details>
  </section>;
}
