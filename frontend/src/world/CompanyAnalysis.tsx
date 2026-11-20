import {useRef,useState} from 'react';
import {useQuery,useMutation,useQueryClient} from '@tanstack/react-query';
import {buildCompanyModel,fetchCompanyModel,fetchModelVersions,type CompanyModel,type ModelMetric} from '../companyModelsApi';
import {financialValue,financialDay,financialTime} from '../financialsApi';
import './companyAnalysis.css';

const states:Record<string,string>={PASS:'Comprobado',FAIL:'Discrepancia',BLOCKED:'Faltan datos',PARTIAL:'Revisión parcial',PASSED:'Revisión numérica superada',FAILED:'Revisión con discrepancias'};
const reasons:Record<string,string>={MAPPING_UPDATED:'Actualización del mapeo contable',FIRST_MODEL:'Primera versión',NEW_PERIOD:'Nuevo ejercicio',REPORTED_VALUES_CHANGED:'Cambios en cifras del mismo ejercicio',NEW_EVIDENCE:'Nueva evidencia de origen'};
export function modelValue(value:string|null,unit:string){
 if(value===null)return 'No calculable';
 if(unit==='percent'||unit==='multiple')return new Intl.NumberFormat('es-ES',{maximumFractionDigits:2}).format(Number(value))+(unit==='percent'?' %':' ×');
 return financialValue(value,unit);
}

function Evidence({model,metric}:{model:CompanyModel;metric:ModelMetric}){
 return <details className="model-evidence"><summary>Fórmula y fuentes</summary><p>{metric.formula}</p>{metric.value!==null?<p>Resultado exacto: <code>{metric.value}</code> {metric.unit==='percent'?'%':metric.unit}</p>:null}
 {metric.evidence_ids.map(id=>{const f=model.payload.evidence[id];return <dl key={id}><div><dt>Concepto</dt><dd>{f.taxonomy}:{f.concept}</dd></div><div><dt>Valor declarado</dt><dd>{f.value} {f.unit}</dd></div><div><dt>Periodo</dt><dd>{f.start?financialDay(f.start)+' — ':''}{financialDay(f.end)}</dd></div><div><dt>Documento</dt><dd><a href={f.url} target="_blank" rel="noreferrer">{f.accession}</a></dd></div><div><dt>Evidencia</dt><dd><code>{id}</code></dd></div><div><dt>Recibo local</dt><dd><code>{f.receipt_id}</code></dd></div></dl>;})}</details>;
}

export function ModelCalculations({model}:{model:CompanyModel}){
 return <><p>Ratios del ejercicio y una medida de caja. Los importes monetarios se presentan en millones; las fuentes conservan el valor exacto.</p><div className="financial-table-wrap"><table className="financial-table model-table"><thead><tr><th>Medida</th><th>Resultado</th><th>Cálculo y procedencia</th></tr></thead><tbody>{model.payload.metrics.map(m=><tr key={m.id}><th scope="row">{m.label}</th><td className="financial-numeric">{modelValue(m.value,m.unit)}{m.reason?<small>{m.reason}</small>:null}</td><td><Evidence model={model} metric={m}/></td></tr>)}</tbody></table></div></>;
}

export function EarningsChanges({model}:{model:CompanyModel}){
 const p=model.payload;
 return <><p>Comparación con las cifras del ejercicio anterior que aparecen en el mismo informe. No representa consenso de analistas ni una sorpresa de resultados.</p>
 <div className="financial-table-wrap"><table className="financial-table model-changes"><thead><tr><th>Magnitud</th><th>Actual / anterior</th><th>Variación y evidencia</th></tr></thead><tbody>{p.earnings.changes.map(m=><tr key={m.id}><th scope="row">{m.label}</th><td><span>Actual: {m.current===null?'No disponible':financialValue(m.current,m.source_unit??'')}</span><small>Anterior: {m.previous===null?'No disponible':financialValue(m.previous,m.source_unit??'')}</small></td><td><strong>{modelValue(m.value,'percent')}</strong>{m.delta!==null?<small>Diferencia: {financialValue(m.delta,m.source_unit??'')}</small>:null}{m.reason?<p>{m.reason}</p>:null}<Evidence model={model} metric={m}/></td></tr>)}</tbody></table></div>
 <p className="model-method">{p.earnings.period_note}</p><h3>Cambios frente a la versión guardada anterior</h3><p>{reasons[p.update.reason]??p.update.reason}. Una cifra modificada no explica por sí sola la causa de la revisión.</p>
 {p.update.changes.length?<ul className="model-revisions">{p.update.changes.map(c=><li key={c.metric}><strong>{c.label}</strong><span>{c.before?financialValue(c.before.value,c.before.unit):'Ausente'} → {c.after?financialValue(c.after.value,c.after.unit):'Ausente'}</span></li>)}</ul>:null}</>;
}

function FilingEvidence({model}:{model:CompanyModel}){
 const filing=model.payload.filing_statement;
 if(!filing)return null;
 const labels:Record<string,string>={
   Liabilities:'Pasivos',StockholdersEquity:'Patrimonio de los accionistas',LiabilitiesCurrent:'Pasivos corrientes',
   StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest:'Patrimonio con minoritarios',
   RedeemableNoncontrollingInterestEquityCarryingAmount:'Participación minoritaria reembolsable',
   LongTermDebtNoncurrent:'Deuda a largo plazo',OperatingLeaseLiabilityNoncurrent:'Arrendamientos operativos a largo plazo',
   FinanceLeaseLiabilityNoncurrent:'Arrendamientos financieros a largo plazo',DeferredIncomeTaxesAndOtherLiabilitiesNoncurrent:'Impuestos diferidos y otros pasivos',
   CommitmentsAndContingencies:'Compromisos y contingencias',NetCashProvidedByUsedInOperatingActivities:'Flujo operativo',
   NetCashProvidedByUsedInInvestingActivities:'Flujo de inversión',NetCashProvidedByUsedInFinancingActivities:'Flujo de financiación',
   EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents:'Efecto de divisas',
   EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations:'Efecto de divisas con el alcance declarado por el emisor'
 };
 return <details className="asset-history"><summary>Partidas y documentos del informe anual</summary>
   {Object.entries(filing.equations).map(([id,equation])=><section key={id}><h4>{id==='balance'?'Balance':'Variación de caja'}</h4>
     {'blocked' in equation?<p>{equation.blocked}</p>:<ul>{equation.terms.map(t=><li key={t.concept}>
       <span>{t.weight<0?'Restar · ':''}{labels[t.concept]??t.concept}</span>
       <strong>{t.value===null?'Sin importe declarado':t.value.replace('.',',')+' '+model.payload.annual.currency}</strong>
     </li>)}</ul>}</section>)}
   <p><a href={filing.receipt.calculation.url} target="_blank" rel="noreferrer">Relaciones de cálculo SEC</a> · <a href={filing.receipt.instance.url} target="_blank" rel="noreferrer">Cifras originales SEC</a></p>
 </details>;
}

export function ValuationReview({model}:{model:CompanyModel}){
 const p=model.payload;
 const checkLabel=(id:string)=>p.metrics.find(m=>m.id===id)?.label??(id.startsWith('change_')?'Variación: '+(p.earnings.changes.find(m=>m.id===id.slice(7))?.label??id):({annual_filing_coverage:'Cobertura del último informe anual local',filed_balance:'Cotejo del balance publicado',filed_cash_roll_forward:'Cotejo de flujos publicados',balance_reported_total:'Total declarado del balance',balance:'Conciliación del balance',cash_roll_forward:'Conciliación de caja',provenance:'Trazabilidad de los inputs'}[id]??id));
 return <div className="model-review-layout"><div><h3>Valoración pendiente de inputs</h3><p>No se calcula un precio objetivo ni se emite una recomendación. Para construir una valoración hacen falta:</p><ul>{p.valuation.missing.map(x=><li key={x}>{x}</li>)}</ul><p>{p.narrative.reason}</p></div><div><h3>Revisión independiente del cálculo</h3><p>{p.review.scope}</p><FilingEvidence model={model}/><ul className="model-checks">{p.review.checks.map(c=><li key={c.id}><strong data-state={c.state}>{states[c.state]??c.state}</strong><div><b>{checkLabel(c.id)}</b><span>{c.reason}</span>{c.residual!==undefined?<span>Diferencia pendiente: {c.residual.replace('.',',')+' '+(c.unit??p.annual.currency??'')}</span>:null}{c.cross_residual!==undefined&&c.cross_residual!=='0'?<span>Diferencia con el saldo independiente: {c.cross_residual} {c.unit}</span>:null}{c.source_residual!==undefined&&c.source_residual!=='0'?<span>Diferencia con Companyfacts: {c.source_residual} {c.unit}</span>:null}{c.reported_residual!==undefined?<span>Diferencia con la variación declarada: {c.reported_residual.replace('.',',')+' '+(c.unit??p.annual.currency??'')}</span>:null}</div></li>)}</ul></div></div>;
}

export default function CompanyAnalysis({cik}:{cik:string}){
 const [selected,setSelected]=useState('');const [offset,setOffset]=useState(0);const [tab,setTab]=useState<'model'|'earnings'|'valuation'>('model');
 const client=useQueryClient();const key=useRef<string|null>(null);
 const versions=useQuery({queryKey:['company-versions',cik,offset],queryFn:({signal})=>fetchModelVersions(cik,offset,signal),retry:false});
 const ident=selected||versions.data?.items[0]?.id||'';
 const detail=useQuery({queryKey:['company-model',cik,ident],queryFn:({signal})=>fetchCompanyModel(cik,ident,signal),enabled:!!ident,retry:false});
 const build=useMutation({mutationFn:()=>{key.current??=crypto.randomUUID();return buildCompanyModel(cik,key.current);},onSuccess:m=>{key.current=null;setOffset(0);setSelected(m.id);client.setQueryData(['company-model',cik,m.id],m);void client.invalidateQueries({queryKey:['company-versions',cik]});void client.invalidateQueries({queryKey:['company-model-recent']});}});
 const model=detail.data;
 return <section id="company-analysis" className="company-analysis" aria-label="Análisis de empresa">
 <header className="model-heading"><div><h2>Análisis de empresa</h2><p>Construcción contable, revisión de resultados y controles de valoración.</p></div><button disabled={build.isPending||versions.isError} onClick={()=>build.mutate()}>{build.isPending?'Construyendo y revisando…':'Construir con cuentas guardadas'}</button></header>
 {build.isError?<p role="alert">{build.error.message}</p>:null}{build.isSuccess?<p role="status">Versión {build.data.version} disponible. Si la evidencia no cambia, se conserva la misma versión.</p>:null}
 {versions.isPending?<p role="status">Consultando modelos guardados…</p>:versions.isError?<div role="alert"><p>{versions.error.message}</p><button onClick={()=>void versions.refetch()}>Reintentar modelos</button></div>:!versions.data?.total?<div className="model-empty"><h3>Las cuentas están listas para su revisión</h3><p>Construye un modelo con la evidencia local. Las ausencias quedarán señaladas y cada cálculo conservará sus fuentes. Si aún no hay cuentas, actualiza primero esta empresa.</p></div>:<>
 <div className="model-version"><label>Versión guardada<select value={ident} onChange={e=>setSelected(e.target.value)}>{versions.data.items.map(v=><option key={v.id} value={v.id}>Versión {v.version} · Cierre {financialDay(v.period_end)}</option>)}</select></label><span>{versions.data.total} {versions.data.total===1?'versión conservada':'versiones conservadas'}</span>{versions.data.total>20?<><button disabled={offset===0} onClick={()=>{setOffset(Math.max(0,offset-20));setSelected('');}}>Más recientes</button><button disabled={offset+20>=versions.data.total} onClick={()=>{setOffset(offset+20);setSelected('');}}>Anteriores</button></>:null}</div>
 {detail.isPending?<p role="status">Abriendo modelo y evidencia…</p>:detail.isError?<div role="alert"><p>{detail.error.message}</p><button onClick={()=>void detail.refetch()}>Reintentar versión</button></div>:model?<>
 <div className="model-context"><div><strong>{financialDay(model.payload.annual.start)} — {financialDay(model.payload.annual.end)}</strong><span>Informe {model.payload.annual.form} · {model.payload.annual.currency}</span></div><div><strong>{states[model.payload.review.state]??model.payload.review.state}</strong><span>Construido: {financialTime(model.created_at)}</span><span>Conocimiento local hasta: {financialTime(model.as_of)}</span></div></div>
 <nav className="financial-tabs" aria-label="Análisis empresarial">{([['model','Modelo'],['earnings','Resultados'],['valuation','Valoración y controles']] as const).map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</nav>
 {tab==='model'?<ModelCalculations model={model}/>:tab==='earnings'?<EarningsChanges model={model}/>:<ValuationReview model={model}/>}
 <details className="model-audit"><summary>Alcance y trazabilidad de la versión</summary><ul>{model.payload.limitations.map(x=><li key={x}>{x}</li>)}</ul><p>Recepción de la evidencia: {financialTime(model.payload.source.received_at)}</p><p>Modelo: <code>{model.id}</code></p><p>Huella de contenido: <code>{model.payload_hash}</code></p><p>Plantilla: {model.payload.template_version}</p></details>
 </>:null}</>}
 </section>;
}
