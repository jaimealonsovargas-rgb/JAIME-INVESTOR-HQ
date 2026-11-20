import {useEffect,useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {controlMarketJob,fetchInstrumentMarket,fetchMarketSummary,marketNumber,marketTime,startMarketJob,type Adjustment,type MarketBar,type MarketJob,type MarketRequest} from '../marketApi';
import './marketData.css';
import {DatasetAssessment} from './DatasetAssessment';

const names:Record<string,string>={READY_TO_FETCH:'Preparado para consultar',NO_CREDENTIALS:'Faltan claves locales',DISABLED:'Desactivado',NOT_VERIFIED:'Sin comprobar',AVAILABLE:'Disponible',SUCCEEDED:'Completado',PARTIAL:'Cobertura parcial',PARTIAL_COVERAGE:'Sesiones sin datos',OBSERVED_SESSIONS:'Sesiones observadas',BLOCKED:'Consulta bloqueada',QUEUED:'En cola',RUNNING:'Captando datos',PAUSED:'En pausa',CANCELLED:'Cancelado',FAILED:'No completado',NO_DATA:'Sin datos',STALE:'Dato antiguo',FRESH:'Observación reciente',AUTH_FAILED:'Acceso rechazado',RIGHTS_RESTRICTED:'Acceso restringido',WAITING:'Esperando reintento',TEST_ONLY:'Solo prueba sintética',LOCAL_STORAGE_LIMIT:'Límite local de almacenamiento',RATE_LIMITED:'Esperando cuota',OFFLINE:'Sin conexión',TIMEOUT:'Tiempo agotado',INVALID_PAYLOAD:'Respuesta rechazada',UNLINKED:'Sin vínculo confirmado',UNKNOWN:'Sin comprobar',INCOMPLETE:'Datos incompletos',CONFLICT:'Identidad en conflicto',NOT_OBSERVED:'Ausente en último catálogo',PROVIDER_IDENTIFIED:'Identificado en Alpaca',IDENTIFIED:'Identificado',UNCONFIRMED:'Sin confirmar'};
const kinds:Record<string,string>={connection:'Comprobar conexión',catalogue:'Catálogo Alpaca',snapshot:'Último precio',history:'Histórico diario'};
const adjustmentNames:Record<Adjustment,string>={raw:'Sin ajustar',split:'Ajustado por desdoblamientos',all:'Todos los ajustes del proveedor'};
const active=(job:MarketJob)=>['QUEUED','RUNNING','WAITING','PAUSED'].includes(job.state);
const label=(value:string)=>names[value]??'Estado pendiente de revisión';
const number=new Intl.NumberFormat('es-ES');

function useMarketSummary(){
  return useQuery({queryKey:['market-summary'],queryFn:({signal})=>fetchMarketSummary(signal),retry:false,refetchInterval:q=>q.state.data?.jobs.some(active)?3000:15000});
}

function useMarketActions(){
  const client=useQueryClient();
  const pending=useRef<{signature:string;key:string}|null>(null);
  const refresh=()=>{for(const key of ['market-summary','instrument-market','universe-summary','universe-listings','universe-detail'])void client.invalidateQueries({queryKey:[key]});};
  const start=useMutation({mutationFn:(body:MarketRequest)=>{
    const signature=JSON.stringify(body);
    if(pending.current?.signature!==signature)pending.current={signature,key:crypto.randomUUID()};
    return startMarketJob(pending.current.key,body);
  },onSuccess:()=>{pending.current=null;refresh();}});
  const control=useMutation({mutationFn:({id,action}:{id:string;action:'cancel'|'resume'})=>controlMarketJob(id,action),onSuccess:refresh});
  return {start,control};
}

function JobStatus({job,canResume=true}:{job:MarketJob;canResume?:boolean}){
  const {control}=useMarketActions();
  return <div className="market-job">
    <div><strong>{kinds[job.kind]??'Captación de mercado'} · {label(job.state)}</strong><p>{job.reason}</p><small>{marketTime(job.updated_at)}{job.progress.pages?` · ${number.format(job.progress.pages)} páginas`:''}{job.progress.bars?` · ${number.format(job.progress.bars)} barras recibidas`:''}</small></div>
    <div className="market-actions">{['QUEUED','RUNNING','WAITING','PAUSED'].includes(job.state)?<button disabled={control.isPending} onClick={()=>control.mutate({id:job.id,action:'cancel'})}>Cancelar captación</button>:null}
      {['PAUSED','FAILED'].includes(job.state)?<button disabled={!canResume||control.isPending} onClick={()=>control.mutate({id:job.id,action:'resume'})}>Reintentar captación</button>:null}</div>
    {control.isError?<p role="alert">{control.error.message}</p>:null}
  </div>;
}

export function MarketConnection(){
  const summary=useMarketSummary();
  const {start}=useMarketActions();
  const client=useQueryClient();
  const terminal=summary.data?.jobs.filter(j=>!active(j)).map(j=>j.id+':'+j.state+':'+j.updated_at).join('|')??'';
  useEffect(()=>{if(terminal)for(const key of ['instrument-market','universe-listings','universe-detail','universe-summary'])void client.invalidateQueries({queryKey:[key]});},[terminal,client]);
  if(summary.isPending)return <p role="status">Consultando la conexión de mercado…</p>;
  if(summary.isError)return <section className="market-connection" aria-label="Datos de mercado"><h2>Mercado y cuenta simulada</h2><p role="alert">{summary.error.message}</p><button onClick={()=>void summary.refetch()}>Reintentar mercado</button></section>;
  const value=summary.data!;
  const canFetch=value.source.state==='READY_TO_FETCH';
  const busy=value.jobs.some(active)||start.isPending;
  const job=value.jobs.find(active)??value.jobs[0];
  return <section className="market-connection" aria-label="Conexión Alpaca">
    <div className="market-heading"><div><h2>Mercado y cuenta simulada</h2><p>Alpaca · {label(value.source.state)} · IEX</p></div><div className="market-actions"><button disabled={!canFetch||busy} onClick={()=>start.mutate({kind:'connection'})}>Comprobar conexión</button><button disabled={!canFetch||busy} onClick={()=>start.mutate({kind:'catalogue'})}>Actualizar catálogo Alpaca</button></div></div>
    <p className="market-source-note">{value.source.reason}</p>
    <div className="market-register"><span>{number.format(value.counts.assets)} activos Alpaca</span><span>{number.format(value.counts.bar_sets)} captaciones históricas</span><span>{number.format(value.counts.bars)} barras guardadas</span></div>
    {job?<div role="status" aria-live="polite"><JobStatus job={job} canResume={canFetch}/></div>:null}
    {start.isError?<p role="alert">{start.error.message}</p>:null}
    <details className="market-access"><summary>Acceso a datos y cuenta PAPER</summary>
      <p>IEX refleja la actividad de ese mercado; no representa todas las operaciones de la bolsa estadounidense. La consulta de esta pantalla no genera una observación nueva en Alpaca.</p>
      {value.source.state==='NO_CREDENTIALS'?<p>Configura <code>ALPACA_API_KEY</code> y <code>ALPACA_SECRET_KEY</code> en el archivo <code>.env</code> local y reinicia el backend. Las claves no se introducen ni se muestran en esta pantalla.</p>:null}
      <dl className="market-endpoints">{value.endpoints.map(endpoint=><div key={endpoint.id}><dt>{endpoint.label}</dt><dd><strong>{label(endpoint.state)}</strong><span>{endpoint.reason}</span><small>{marketTime(endpoint.checked_at)}</small></dd></div>)}</dl>
      <section className="market-paper" aria-label="Cuenta Alpaca PAPER de solo lectura"><h3>Cuenta PAPER · solo lectura</h3><p>Cuenta simulada externa, separada de MASTER. Las órdenes continúan deshabilitadas.</p>
        <p>{label(value.paper.state)} · {marketTime(value.paper.as_of)}</p>
        {value.paper.account?<><dl className="market-account-values"><div><dt>Efectivo</dt><dd>{marketNumber(value.paper.account.cash,value.paper.account.currency)}</dd></div><div><dt>Patrimonio</dt><dd>{marketNumber(value.paper.account.equity,value.paper.account.currency)}</dd></div><div><dt>Poder de compra comunicado</dt><dd>{marketNumber(value.paper.account.buying_power,value.paper.account.currency)}</dd></div></dl>
          <p>El poder de compra comunicado por Alpaca no es un presupuesto aprobado por el motor de riesgo de JAIME.</p>
          {value.paper.positions.length?<ul className="market-positions">{value.paper.positions.map((position,index)=><li key={position.symbol+':'+index}><strong>{position.symbol}</strong><span>{marketNumber(position.qty)} unidades</span><span>{marketNumber(position.market_value,value.paper.account!.currency)}</span></li>)}</ul>:value.paper.positions_complete===true?<p>La última consulta no devolvió posiciones abiertas.</p>:<p>La lectura de posiciones aún no está confirmada.</p>}</>:<p>Aún no hay una lectura confirmada de la cuenta simulada.</p>}
      </section>
      <p>Las cuentas SEC se actualizan por solicitud. La programación automática con n8n sigue pendiente.</p>
    </details>
  </section>;
}

function DailyHistory({series,currency}:{series:MarketBar[];currency:string|null}){
  const [offset,setOffset]=useState(0);
  const closes=series.map(bar=>Number(bar.c));
  let low=Infinity,high=-Infinity;
  for(const value of closes){low=Math.min(low,value);high=Math.max(high,value);}
  const span=high-low||Math.max(Math.abs(high)*.01,1);
  const points=closes.map((value,index)=>`${50+(index/(Math.max(series.length-1,1)))*900},${180-(value-low)/span*140}`).join(' ');
  const visible=series.slice(offset,offset+25);
  return <div className="market-history-plot">
    <figure><figcaption>Cierre diario IEX{currency?' · '+currency:' · divisa sin confirmar'}</figcaption>
      <svg viewBox="0 0 1000 230" role="img" aria-label={`Cierres diarios de ${series[0].t.slice(0,10)} a ${series[series.length-1].t.slice(0,10)}. Valores exactos en la tabla desplegable.`}>
        <line x1="50" y1="180" x2="950" y2="180" className="market-chart-axis"/><line x1="50" y1="40" x2="950" y2="40" className="market-chart-axis"/>
        <text x="50" y="25">{marketNumber(String(high))}</text><text x="50" y="201">{marketNumber(String(low))}</text>
        <polyline points={points} fill="none" className="market-chart-line"/>
        {series.length===1?<circle cx="50" cy="180" r="3" className="market-chart-point"/>:null}
        <text x="50" y="224">{series[0].t.slice(0,10)}</text><text x="950" y="224" textAnchor="end">{series[series.length-1].t.slice(0,10)}</text>
      </svg>
    </figure>
    <details className="market-bars"><summary>Consultar valores de las {number.format(series.length)} barras mostradas</summary><div className="market-table-scroll"><table><caption>Fecha de sesión del proveedor · importes{currency?' en '+currency:' con divisa sin confirmar'} · volumen en acciones</caption><thead><tr><th scope="col">Sesión</th><th scope="col">Apertura</th><th scope="col">Máximo</th><th scope="col">Mínimo</th><th scope="col">Cierre</th><th scope="col">Volumen</th></tr></thead><tbody>{visible.map(bar=><tr key={bar.t}><th scope="row">{bar.t.slice(0,10)}</th><td data-label="Apertura">{marketNumber(bar.o)}</td><td data-label="Máximo">{marketNumber(bar.h)}</td><td data-label="Mínimo">{marketNumber(bar.l)}</td><td data-label="Cierre">{marketNumber(bar.c)}</td><td data-label="Volumen">{marketNumber(bar.v)}</td></tr>)}</tbody></table></div>
      <nav className="asset-pagination" aria-label="Paginación de barras"><span>{number.format(offset+1)}–{number.format(Math.min(offset+25,series.length))} de {number.format(series.length)}</span><div><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-25))}>Anteriores</button><button disabled={offset+25>=series.length} onClick={()=>setOffset(offset+25)}>Siguientes</button></div></nav>
    </details>
  </div>;
}

function defaultDates(){const day=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());const end=new Date(day+'T00:00:00Z');end.setUTCDate(end.getUTCDate()-1);const start=new Date(end);start.setUTCFullYear(start.getUTCFullYear()-1);return {start:start.toISOString().slice(0,10),end:end.toISOString().slice(0,10)};}

export function InstrumentMarket({listingId,onChoose}:{listingId:string;onChoose:(id:string)=>void}){
  const [adjustment,setAdjustment]=useState<Adjustment>('raw');
  const [dates,setDates]=useState(defaultDates);
  const summary=useMarketSummary();
  const market=useQuery({queryKey:['instrument-market',listingId,adjustment],queryFn:({signal})=>fetchInstrumentMarket(listingId,adjustment,signal),retry:false,refetchInterval:15000});
  const {start}=useMarketActions();
  const value=market.data;
  const canFetch=summary.data?.source.state==='READY_TO_FETCH';
  const busy=!!summary.data?.jobs.some(active)||start.isPending;
  const instrument=!!value?.identity.asset_id&&!['CONFLICT','NOT_OBSERVED','INCOMPLETE','UNLINKED'].includes(value.identity.state);
  const validDates=dates.start!==''&&dates.end!==''&&dates.start>='2016-01-01'&&dates.end<new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())&&dates.start<=dates.end&&Date.parse(dates.end)-Date.parse(dates.start)<=3660*86400000;
  const latestJob=summary.data?.jobs.find(j=>j.listing_id===listingId);
  const history=value?.history;
  const manifest=history?.manifest;
  return <section id="instrument-market" className="instrument-market" aria-label="Precios e históricos del instrumento">
    <div className="market-heading"><div><h2>Precios e históricos</h2><p>Observaciones de mercado, cobertura y antigüedad.</p></div>{value&&instrument?<button disabled={!canFetch||busy} onClick={()=>start.mutate({kind:'snapshot',listing_id:listingId})}>Consultar último precio</button>:null}</div>
    {market.isPending?<p role="status">Consultando datos del instrumento…</p>:market.isError?<div role="alert"><p>{market.error.message}</p><button onClick={()=>void market.refetch()}>Reintentar datos de mercado</button></div>:value?<>
      {value.assessment?<DatasetAssessment value={value.assessment} listingId={listingId} onChoose={onChoose}/>:null}
      {!instrument&&value.assessment?.identity.state==='DOCUMENTED'?<p className="market-source-note">Los precios y las captaciones se consultan en la ficha de la acción vinculada. Esta ficha conserva las cuentas del emisor.</p>:!instrument?<div className="market-unlinked"><h3>Identidad de mercado por confirmar</h3><p>{value.identity.reason}</p><p>El símbolo SEC identifica un registro del catálogo. Para mostrar precios se necesita identificar el activo de Alpaca y su mercado.</p>
        {value.identity.candidates.length?<><p>Coincidencias para revisar. Abrir una ficha no confirma que corresponda al mismo emisor.</p><ul className="market-candidates">{value.identity.candidates.map(candidate=><li key={candidate.id}><button onClick={()=>onChoose(candidate.id)}><strong>{candidate.symbol} · {candidate.venue}</strong><span>{candidate.name}</span></button><p>{candidate.reason}</p></li>)}</ul></>:<p>No hay coincidencias verificables en el catálogo Alpaca local. {canFetch?'Actualiza el catálogo Alpaca para comprobar su disponibilidad.':'La conexión se prepara en «Mercado y cuenta simulada».'}</p>}
      </div>:<>
        <div className="market-instrument-line"><span>{value.identity.symbol} · {value.identity.venue}</span><span>{value.identity.currency?'Precios en '+value.identity.currency:'Divisa de precios sin confirmar'}</span><span>Emisor SEC: {value.identity.issuer_link==='DOCUMENTED'?'vínculo documentado':value.identity.issuer_link==='CONFIRMED'?'confirmado':'sin confirmar'}</span></div>
        <p className="market-source-note">{value.identity.reason}</p>
        <dl className="market-quote"><div><dt>Última operación IEX</dt><dd>{marketNumber(value.quote.price,value.identity.currency??'')}</dd></div><div><dt>Compra / venta cotizada</dt><dd>{marketNumber(value.quote.bid)} / {marketNumber(value.quote.ask)}</dd></div><div><dt>Estado de la observación</dt><dd>{label(value.quote.state)}</dd></div><div><dt>Sesión regular</dt><dd>{value.quote.market_state==='OPEN'?'Abierta':value.quote.market_state==='CLOSED'?'Cerrada':'Sin comprobar'}</dd></div></dl>
        <div className="market-timestamps"><span>Operación: {marketTime(value.quote.as_of)}</span><span>Cotización: {marketTime(value.quote.quote_at??null)}</span><span>Recepción local: {marketTime(value.quote.received_at)}</span><span>Reloj del mercado: {marketTime(value.quote.market_checked_at)}</span></div><p className="market-source-note">{value.quote.reason}</p>
        <p className="market-source-note">IEX es una cobertura parcial del mercado estadounidense. Mercado cerrado y dato antiguo son estados distintos; la hora de descarga no sustituye la hora de la operación.</p>
        <form className="market-history-form" onSubmit={event=>{event.preventDefault();if(canFetch&&!busy&&validDates)start.mutate({kind:'history',listing_id:listingId,...dates,adjustment});}}>
          <label>Desde<input type="date" value={dates.start} max={dates.end} onChange={event=>setDates({...dates,start:event.target.value})}/></label><label>Hasta<input type="date" value={dates.end} min={dates.start} onChange={event=>setDates({...dates,end:event.target.value})}/></label>
          <label>Serie<select aria-label="Serie histórica" value={adjustment} onChange={event=>setAdjustment(event.target.value as Adjustment)}><option value="raw">Sin ajustar</option><option value="split">Desdoblamientos</option><option value="all">Todos los ajustes del proveedor</option></select></label><button disabled={!canFetch||busy||!validDates} type="submit">Captar histórico diario</button>
        </form>
        {!validDates?<p role="alert">Elige un intervalo válido de hasta diez años.</p>:null}
        {manifest?<><div className="market-history-heading"><h3>{adjustmentNames[manifest.adjustment]}</h3><span>{number.format(manifest.bars)} barras · {label(manifest.state)}</span></div><p>{manifest.start.slice(0,10)} — {manifest.end.slice(0,10)} · recibido {marketTime(manifest.received_at)}</p>
          <p className="market-source-note">{manifest.coverage_note}{manifest.expected_sessions!==null?` Sesiones esperadas: ${number.format(manifest.expected_sessions)}.`:''}{manifest.missing_sessions!==null?` Sin barra: ${number.format(manifest.missing_sessions)}.`:''}</p>
          {history!.series.length?<DailyHistory key={manifest.id} series={history!.series} currency={value.identity.currency}/>:<p>No hay barras válidas en esta captación.</p>}
          <details className="market-manifest"><summary>Procedencia y alcance de esta serie</summary><dl><div><dt>Fuente</dt><dd>Alpaca · {manifest.feed.toUpperCase()}</dd></div><div><dt>Primera / última barra</dt><dd>{marketTime(manifest.first_at)} / {marketTime(manifest.last_at)}</dd></div><div><dt>Identificador de captación</dt><dd><code>{manifest.id}</code></dd></div></dl><p>Las series sin ajustar y ajustadas se conservan separadas. Los ajustes del proveedor no certifican por sí solos las acciones corporativas, la disponibilidad histórica de información ni la aptitud para backtests.</p></details>
        </>:<div className="market-history-empty"><h3>Sin histórico {adjustment==='raw'?'sin ajustar':'con este ajuste'}</h3><p>Selecciona el periodo y solicita la captación. Las ausencias se conservan como datos pendientes; no se completan con precios inventados.</p></div>}
      </>}
      {latestJob?<JobStatus job={latestJob} canResume={canFetch}/>:null}
      {start.isError?<p role="alert">{start.error.message}</p>:null}
    </>:null}
  </section>;
}
