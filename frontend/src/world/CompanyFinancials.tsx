import {useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {fetchFinancials,fetchDocuments,fetchFactHistory,fetchFinancialSummary,startFinancialImport,financialDay,financialTime,financialValue,type AnnualAccounts,type FinancialFact} from '../financialsApi';

function Pagination({offset,total,onChange}:{offset:number;total:number;onChange:(value:number)=>void}){
  return <nav className="asset-pagination" aria-label="Paginación de evidencia"><span>{total?offset+1:0}–{Math.min(offset+25,total)} de {total.toLocaleString('es-ES')}</span><div><button disabled={offset===0} onClick={()=>onChange(Math.max(0,offset-25))}>Anterior</button><button disabled={offset+25>=total} onClick={()=>onChange(offset+25)}>Siguiente</button></div></nav>;
}

export function AnnualStatement({annual}:{annual:AnnualAccounts}){
  return <><div className="financial-period"><div><h3>Último ejercicio anual disponible</h3><p>{financialDay(annual.start)} — {financialDay(annual.end)}</p></div><div><a href={annual.url} target="_blank" rel="noreferrer">Abrir {annual.form} original</a><p>Presentado el {financialDay(annual.filed)}</p></div></div>
    {annual.stale?<p role="status">El cierre de estas cuentas tiene más de 550 días. Se conserva como histórico y requiere actualización antes de investigar la situación actual.</p>:null}
    {annual.state==='AMBIGUOUS_CURRENCY'?<p role="status">El informe contiene varias divisas de presentación. Las cifras necesitan revisión antes de formar un cuadro comparable.</p>:<>
      <p className="financial-method">Importes monetarios en millones de {annual.currency}. Beneficio por acción y acciones muestran su unidad. Todas las filas pertenecen al mismo informe y periodo.</p>
      <div className="financial-table-wrap"><table className="financial-table"><caption>{annual.core_available} de {annual.core_total} magnitudes básicas disponibles. Una ausencia no equivale a cero.</caption><thead><tr><th scope="col">Magnitud</th><th scope="col">Valor declarado</th><th scope="col">Evidencia</th></tr></thead><tbody>{annual.metrics.map(metric=><tr key={metric.metric}><th scope="row">{metric.label}</th><td className="financial-numeric">{metric.fact?financialValue(metric.fact.value,metric.fact.unit):metric.state==='CONFLICT'?'Valores contradictorios':'No disponible'}</td><td>{metric.fact?<details><summary>Ver dato original</summary><FactEvidence fact={metric.fact}/></details>:<span>Sin cifra comparable en este informe</span>}</td></tr>)}</tbody></table></div>
    </>}</>;
}

function FactEvidence({fact}:{fact:FinancialFact}){
  return <dl className="financial-evidence">{fact.quality_flags?.length?<div><dt>Control de calidad</dt><dd>Periodo incompatible con el concepto; excluido del cuadro anual.</dd></div>:null}<div><dt>Valor exacto</dt><dd>{fact.value} {fact.unit}</dd></div><div><dt>Concepto SEC</dt><dd>{fact.taxonomy}:{fact.concept}</dd></div><div><dt>Periodo</dt><dd>{fact.start?financialDay(fact.start)+' — ':''}{financialDay(fact.end)}</dd></div><div><dt>Documento</dt><dd>{fact.accession} · {fact.form}</dd></div><div><dt>Presentado</dt><dd>{financialDay(fact.filed)}</dd></div><div><dt>Evidencia local</dt><dd><code>{fact.id}</code></dd></div></dl>;
}

function Documents({cik}:{cik:string}){
  const [offset,setOffset]=useState(0);
  const docs=useQuery({queryKey:['financial-documents',cik,offset],queryFn:({signal})=>fetchDocuments(cik,offset,signal),retry:false});
  if(docs.isPending)return <p role="status">Abriendo documentos…</p>;
  if(docs.isError)return <div role="alert"><p>{docs.error.message}</p><button onClick={()=>void docs.refetch()}>Reintentar documentos</button></div>;
  const page=docs.data!;
  return <><p>Informes periódicos y comunicaciones 8-K/6-K. Los enlaces abren los originales en SEC; aquí se conserva su registro, no el texto completo.</p>{page.older_history_pending?<p>La SEC ofrece archivos anteriores adicionales. Este listado cubre la respuesta reciente descargada; el archivo histórico completo sigue pendiente.</p>:null}
    {page.total===0?<p>Sin documentos disponibles en la descarga actual.</p>:<div className="financial-table-wrap"><table className="financial-table"><thead><tr><th>Documento</th><th>Presentación</th><th>Periodo del informe</th></tr></thead><tbody>{page.items.map(d=><tr key={d.accession}><td><a href={d.url} target="_blank" rel="noreferrer">{d.form}{d.amended?' · Enmienda':''}</a><small>{d.accession}</small></td><td>{financialDay(d.filed)}{d.accepted_at?<small>Aceptado: {financialTime(d.accepted_at)}</small>:null}</td><td>{d.report_date?financialDay(d.report_date):'Sin periodo informado'}</td></tr>)}</tbody></table></div>}
    <Pagination offset={offset} total={page.total} onChange={setOffset}/></>;
}

function Revisions({cik,metrics}:{cik:string;metrics:{metric:string;label:string}[]}){
  const [metric,setMetric]=useState('revenue');const [offset,setOffset]=useState(0);
  const history=useQuery({queryKey:['financial-history',cik,metric,offset],queryFn:({signal})=>fetchFactHistory(cik,metric,offset,signal),retry:false});
  return <><p>Cifras declaradas en cada presentación, incluidos periodos comparativos. Los cambios pueden responder a revisiones, reclasificaciones o ajustes; no se interpreta su causa automáticamente.</p>
    <label className="financial-metric-picker">Magnitud a consultar<select value={metric} onChange={e=>{setMetric(e.target.value);setOffset(0);}}>{(metrics.length?metrics:[{metric:'revenue',label:'Ingresos'}]).map(m=><option key={m.metric} value={m.metric}>{m.label}</option>)}</select></label>
    {history.isPending?<p role="status">Consultando las cifras…</p>:history.isError?<div role="alert"><p>{history.error.message}</p><button onClick={()=>void history.refetch()}>Reintentar cifras</button></div>:history.data?<>
      {history.data.total===0?<p>No hay cifras registradas para esta magnitud.</p>:<div className="financial-table-wrap"><table className="financial-table"><thead><tr><th>Periodo económico</th><th>Valor declarado</th><th>Presentación y evidencia</th></tr></thead><tbody>{history.data.items.map(f=><tr key={f.id}><td>{f.start?<small>Desde {financialDay(f.start)}</small>:null}{financialDay(f.end)}<small>{f.days?`${f.days} días`:'Saldo a una fecha'}</small></td><td className="financial-numeric">{financialValue(f.value,f.unit)}</td><td>{financialDay(f.filed)} · {f.form}<details><summary>Ver procedencia</summary><FactEvidence fact={f}/></details></td></tr>)}</tbody></table></div>}
      <Pagination offset={offset} total={history.data.total} onChange={setOffset}/></>:null}</>;
}

export default function CompanyFinancials({cik,name}:{cik:string;name:string}){
  const [tab,setTab]=useState<'accounts'|'documents'|'history'>('accounts');
  const client=useQueryClient();const key=useRef<string|null>(null);
  const status=useQuery({queryKey:['financial-summary'],queryFn:({signal})=>fetchFinancialSummary(signal),retry:false});
  const active=['QUEUED','RUNNING','PAUSED'].includes(status.data?.latest_job?.state??'');
  const data=useQuery({queryKey:['financials',cik],queryFn:({signal})=>fetchFinancials(cik,signal),retry:false,refetchInterval:active?10000:false});
  const sync=useMutation({mutationFn:()=>{key.current??=crypto.randomUUID();return startFinancialImport(key.current,[cik]);},onSuccess:()=>{key.current=null;void client.invalidateQueries({queryKey:['financial-summary']});void client.invalidateQueries({queryKey:['financials',cik]});}});
  const value=data.data;
  return <section className="company-financials" id="company-financials" aria-label="Cuentas y documentos de la empresa">
    <div className="financial-company-heading"><div><h2>{name} · Información financiera</h2><p>Emisor CIK {cik} · Cuentas de la empresa, independientes de la divisa o clase del valor cotizado.</p></div><button disabled={active||sync.isPending||status.data?.access!=='READY'||!status.data?.worker_running} onClick={()=>sync.mutate()}>{sync.isPending?'Preparando…':'Actualizar esta empresa'}</button></div>
    {sync.isError?<p role="alert">{sync.error.message}</p>:null}
    {data.isPending?<p role="status">Consultando cuentas e informes…</p>:data.isError?<div role="alert"><p>{data.error.message}</p><button onClick={()=>void data.refetch()}>Reintentar cuentas</button></div>:value?<>
      <div className="financial-coverage"><span>{value.coverage.metrics} de {value.coverage.metric_denominator} magnitudes registradas</span><span>{value.coverage.facts.toLocaleString('es-ES')} cifras con procedencia</span><span>{value.documents.total} documentos recientes</span>{value.profile?.fiscal_year_end?<span>Cierre fiscal declarado: {value.profile.fiscal_year_end.slice(2)}/{value.profile.fiscal_year_end.slice(0,2)}</span>:null}</div>
      <nav className="financial-tabs" aria-label="Vistas financieras">{([['accounts','Cuentas anuales'],['documents','Documentos'],['history','Cifras y revisiones']] as const).map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</nav>
      <div className="financial-content">{tab==='accounts'?(value.annual?<AnnualStatement annual={value.annual}/>:<div className="asset-empty"><h3>Aún no hay un ejercicio anual comparable</h3><p>{active?'La captación está en curso. Las cuentas aparecerán cuando se valide la descarga de este emisor.':'Actualiza esta empresa para obtener sus cifras e informes. Si el proveedor no ofrece los conceptos necesarios, se indicarán como ausentes.'}</p></div>):tab==='documents'?<Documents cik={cik}/>:<Revisions cik={cik} metrics={value.annual?.metrics??[]}/>}</div>
      <div className="financial-footnotes"><details><summary>Cobertura, procedencia y límites</summary><p>{value.coverage.quarantined_facts} cifras aisladas por anomalías de periodo; no se utilizan en el cuadro anual.</p><p>{value.coverage.changed_value_groups} grupos de concepto, unidad y periodo presentan valores diferentes entre documentos.</p><ul>{value.limitations.map(line=><li key={line}>{line}</li>)}</ul><ul>{value.readiness.map(r=><li key={r.use}>{r.reason}</li>)}</ul>{value.sources.map(source=><div key={source.id}><a href={source.source} target="_blank" rel="noreferrer">{source.kind==='companyfacts'?'Cifras XBRL originales':'Registro de presentaciones'}</a><p>Recibido: {financialTime(source.received_at)} · {source.parser_version}</p><code>{source.payload_hash}</code></div>)}</details></div>
    </>:null}
  </section>;
}
