import {useEffect,useRef} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {fetchFinancialSummary,startFinancialImport,controlFinancialImport,financialTime} from '../financialsApi';

const jobNames:Record<string,string>={QUEUED:'En cola',RUNNING:'Captando cuentas e informes',PAUSED:'Captación en pausa',SUCCEEDED:'Captación completada',PARTIAL:'Completada con datos pendientes',CANCELLED:'Captación cancelada'};
export default function FinancialImport(){
  const client=useQueryClient();
  const key=useRef<string|null>(null);
  const summary=useQuery({queryKey:['financial-summary'],queryFn:({signal})=>fetchFinancialSummary(signal),retry:false,refetchInterval:q=>['RUNNING','QUEUED'].includes(q.state.data?.latest_job?.state??'')?3000:15000});
  const refresh=()=>{void client.invalidateQueries({queryKey:['financial-summary']});void client.invalidateQueries({queryKey:['financials']});};
  const start=useMutation({mutationFn:()=>{key.current??=crypto.randomUUID();return startFinancialImport(key.current);},onSuccess:()=>{key.current=null;refresh();}});
  const control=useMutation({mutationFn:({id,action}:{id:string;action:'pause'|'resume'|'cancel'})=>controlFinancialImport(id,action),onSuccess:refresh});
  const latest=summary.data?.latest_job;
  useEffect(()=>{if(latest&&['SUCCEEDED','PARTIAL','CANCELLED'].includes(latest.state)){
    for(const queryKey of ['financials','financial-documents','financial-history'])void client.invalidateQueries({queryKey:[queryKey]});
  }},[latest?.id,latest?.state,latest?.updated_at,client]);
  if(summary.isPending)return <p role="status">Consultando la cobertura financiera…</p>;
  if(summary.isError)return <div className="financial-import" role="alert"><p>{summary.error.message}</p><button onClick={()=>void summary.refetch()}>Reintentar cobertura</button></div>;
  const value=summary.data!;const job=value.latest_job;const active=!!job&&['QUEUED','RUNNING','PAUSED'].includes(job.state);
  return <section className="financial-import" aria-label="Captación de cuentas SEC">
    <div className="financial-import-heading"><div><h2>Cuentas e informes</h2><p>{value.counts.issuers_with_facts.toLocaleString('es-ES')} emisores con cifras · {value.counts.issuers_with_documents.toLocaleString('es-ES')} con documentos registrados</p></div>
      <button disabled={active||value.access!=='READY'||!value.worker_running||start.isPending} onClick={()=>start.mutate()}>{start.isPending?'Preparando…':job?'Actualizar piloto de 100':'Preparar piloto de 100'}</button></div>
    {job?<><div className="financial-progress-label"><strong>{jobNames[job.state]??job.state}</strong><span>{job.completed} de {job.total} descargas resueltas · {job.manifest.issuers.length} emisores</span></div><progress value={job.completed} max={job.total} aria-label="Progreso de captación financiera"/>
      <div className="financial-import-actions"><span>{financialTime(job.updated_at)}{job.counts.FAILED||job.counts.NO_DATA?` · ${job.counts.FAILED+job.counts.NO_DATA} descargas sin datos válidos`:''}</span><div>
        {['RUNNING','QUEUED'].includes(job.state)?<button disabled={control.isPending} onClick={()=>control.mutate({id:job.id,action:'pause'})}>Pausar</button>:null}
        {['PAUSED','PARTIAL'].includes(job.state)?<button disabled={control.isPending||value.access!=='READY'} onClick={()=>control.mutate({id:job.id,action:'resume'})}>{job.state==='PARTIAL'?'Reintentar pendientes':'Reanudar'}</button>:null}
        {active?<button disabled={control.isPending} onClick={()=>control.mutate({id:job.id,action:'cancel'})}>Cancelar captación</button>:null}
      </div></div>
      <details className="financial-batch-details"><summary>Empresas del lote y datos pendientes</summary><p>{job.manifest.selection}</p><p>Una descarga reúne las cifras; la otra, los documentos. Completar las descargas no certifica la calidad de una inversión.</p><ul>{job.manifest.issuers.map(issuer=><li key={issuer.cik}><a href={'?activos=1&q='+encodeURIComponent(issuer.symbol)}>{issuer.symbol}</a><span>{issuer.name}</span></li>)}</ul>
        {job.errors.length?<p>Sin completar: {job.errors.map(e=>`${e.cik} · ${e.kind==='companyfacts'?'cuentas':'documentos'} (${e.error})`).join('; ')}</p>:null}</details></>:<p>Primer piloto: 100 emisores con identidad comprobada. Se conservará el avance si el backend se reinicia.</p>}
    {!value.worker_running?<p role="status">El servicio de captación está detenido. Reinicia el backend para continuar la cola.</p>:null}
    {value.worker_error?<p role="alert">La captación ha encontrado un error local. Los datos confirmados se conservan.</p>:null}
    {value.access!=='READY'?<p>Fuente no preparada: {value.access==='CONFIG_REQUIRED'?'falta el contacto SEC local':value.access==='DISABLED'?'SEC está desactivada':'acceso restringido'}.</p>:null}
    {start.isError||control.isError?<p role="alert">{(start.error??control.error)?.message}</p>:null}
  </section>;
}
