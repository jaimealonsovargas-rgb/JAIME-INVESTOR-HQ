import {useEffect,useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {fetchUniverse,fetchListings,fetchListing,syncCatalogue,refreshEuropeanClose,type ListingDetail} from '../universeApi';
import './assetCenter.css';
import FinancialImport from './FinancialImport';
import CompanyFinancials from './CompanyFinancials';
import CompanyAnalysis from './CompanyAnalysis';
import {MarketConnection,InstrumentMarket} from './MarketData';

const states:Record<string,string>={IDENTIFIED:'Identificado',CONFLICT:'Revisar identidad',INCOMPLETE:'Mercado sin confirmar',NOT_OBSERVED:'Ausente en último catálogo',READY_TO_FETCH:'Configurado',CONFIG_REQUIRED:'Falta contacto',NO_CREDENTIALS:'Faltan claves',NOT_IMPLEMENTED:'Integración pendiente',DISABLED:'Desactivado',SUCCEEDED:'Actualización completada',RUNNING:'Actualizando catálogo',RATE_LIMITED:'Esperando cuota',RIGHTS_RESTRICTED:'Acceso restringido',INVALID_PAYLOAD:'Respuesta rechazada',OFFLINE:'Sin conexión',TIMEOUT:'Tiempo agotado',INTERRUPTED:'Actualización interrumpida',ERROR:'No se pudo actualizar',AUTH_FAILED:'Acceso rechazado'};
export const universeState=(state:string)=>states[state]??'Estado sin confirmar';
const number=new Intl.NumberFormat('es-ES',{useGrouping:true});
const time=(stamp:string)=>new Intl.DateTimeFormat('es-ES',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Madrid'}).format(new Date(stamp))+' · Madrid';

export function EuropeanClose({close}:{close:ListingDetail['historical_close']}){
  if(!close)return <p role="status">Cierre histórico no disponible para esta consulta.</p>;
  const [whole,fraction='']=close.price.split('.');
  return <section aria-label="Cierre histórico de Zagreb"><h3>Cierre de sesión</h3>
    <p><strong>{whole},{fraction.padEnd(2,'0')} EUR</strong> por acción · <time dateTime={close.session}>{close.session}</time></p>
    <p>{close.stale?'Último dato guardado · actualización pendiente':'Histórico diario · sesión terminada'} · ISIN {close.isin}</p>
    <p><a href={close.source} target="_blank" rel="noreferrer">Bolsa de Zagreb</a> · Recibido {time(close.received_at)}</p>
  </section>;
}

function AssetDetail({item}:{item:ListingDetail}){
  const heading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{heading.current?.focus({preventScroll:true});if(window.matchMedia('(max-width: 850px)').matches)heading.current?.scrollIntoView({block:'start',behavior:'instant'});},[item.id]);
  return <article className="asset-detail" aria-label="Ficha del activo">
    <div className="asset-symbol">{item.symbol}<span>{item.venue==='UNKNOWN'?'Mercado sin confirmar':item.venue}</span></div>
    <h2 ref={heading} tabIndex={-1}>{item.name}</h2>
    <p className="asset-detail-status">{universeState(item.state)}</p>
    {item.provider==='ZSE'?<EuropeanClose close={item.historical_close}/>:null}
    <dl className="asset-facts">
      <div><dt>Identificador de emisor</dt><dd>{item.cik?'CIK '+item.cik:'Sin vincular'}</dd></div>
      <div><dt>Divisa</dt><dd>{item.currency??'No confirmada por esta fuente'}</dd></div>
      <div><dt>Primera observación local</dt><dd>{time(item.first_seen_at)}</dd></div>
      <div><dt>Última presencia observada</dt><dd>{time(item.last_seen_at)}</dd></div>
    </dl>
    <h3>Investigar este emisor</h3>
    {item.cik?<p><a href="#company-financials">Abrir cuentas, documentos y revisiones</a></p>:<p>El emisor todavía no está vinculado.</p>}
    {item.cik?<p><a href="#company-analysis">Abrir modelo, resultados y valoración</a></p>:null}
    {item.provider!=='ZSE'?<p><a href="#instrument-market">Abrir precios, históricos y cobertura</a></p>:null}
    <p>La divisa de las cuentas no confirma la divisa del valor cotizado. La identidad y los permisos de datos de mercado se comprueban por separado.</p>
    <details className="asset-history"><summary>Procedencia e historial ({item.versions.length}{item.versions.length===100?'+':''})</summary>
      <p>Fechas de conocimiento local. No reconstruyen el universo disponible en una fecha pasada del mercado.</p>
      <ol>{item.versions.map(v=><li key={v.id}><strong>{v.payload.symbol} · {universeState(v.payload.state)}</strong><span>{time(v.known_from)}</span><a href={v.source} target="_blank" rel="noreferrer">Fuente oficial</a><details><summary>Huella del documento</summary><code>{v.payload_hash}</code></details></li>)}</ol>
    </details>
  </article>;
}

export default function AssetCenter(){
  const initial=new URLSearchParams(window.location.search);
  const [input,setInput]=useState(initial.get('q')??'');
  const [query,setQuery]=useState(initial.get('q')??'');
  const [state,setState]=useState('');
  const [offset,setOffset]=useState(0);
  const [selected,setSelected]=useState(initial.get('valor')??'');
  const key=useRef<string|null>(null);
  const client=useQueryClient();
  const summary=useQuery({queryKey:['universe-summary'],queryFn:({signal})=>fetchUniverse(signal),retry:false,refetchInterval:q=>q.state.data?.imports.some(j=>j.state==='RUNNING')?3000:30000});
  const page=useQuery({queryKey:['universe-listings',query,state,offset],queryFn:({signal})=>fetchListings(query,state,offset,signal),retry:false});
  const detail=useQuery({queryKey:['universe-detail',selected],queryFn:({signal})=>fetchListing(selected,signal),enabled:!!selected,retry:false,
    refetchInterval:q=>q.state.data?.provider==='ZSE'?60000:false});
  const sync=useMutation({mutationFn:()=>{key.current??=crypto.randomUUID();return syncCatalogue(key.current);},onSuccess:result=>{key.current=result.state==='RUNNING'?result.id:null;void client.invalidateQueries({queryKey:['universe-summary']});void client.invalidateQueries({queryKey:['universe-listings']});void client.invalidateQueries({queryKey:['universe-detail']});}});
  const last=summary.data?.imports[0];
  useEffect(()=>{if(last&&last.id===key.current&&last.state!=='RUNNING'){key.current=null;void client.invalidateQueries({queryKey:['universe-listings']});void client.invalidateQueries({queryKey:['universe-detail']});}},[last?.id,last?.state,client]);
  const running=sync.isPending||last?.state==='RUNNING';
  const europe=useMutation({mutationFn:async()=>{
    const result=await refreshEuropeanClose();
    if(!result.normalized_count)return {reason:result.reason,listing:null};
    const page=await fetchListings('HRHT00RA0005','',0);
    const listing=page.items.find(row=>row.provider==='ZSE'&&row.symbol==='HT'&&row.venue==='XZAG');
    if(!listing)throw new Error('No se pudo verificar la identidad de HT.');
    return {reason:result.reason,listing};
  },onSuccess:({listing})=>{
    if(!listing)return;
    const isin='HRHT00RA0005';
    setInput(isin);setQuery(isin);setOffset(0);setState('');choose(listing.id,isin);
    void client.invalidateQueries({queryKey:['universe-listings']});
    void client.invalidateQueries({queryKey:['universe-detail',listing.id]});
  }});
  const ready=summary.data?.sources.find(s=>s.provider==='SEC')?.state==='READY_TO_FETCH';
  function choose(id:string,term=query){setSelected(id);const params=new URLSearchParams({activos:'1'});if(term)params.set('q',term);params.set('valor',id);window.history.replaceState(null,'','?'+params);}
  function search(){setQuery(input.trim());setOffset(0);}
  return <main className="asset-center">
    <header className="asset-header"><a href="/" className="asset-brand">JAIME INVESTOR HQ</a><nav aria-label="Navegación"><a href="/">Volver a la oficina</a><a href="?especialista=personal-research-1">Equipo de análisis</a></nav></header>
    <div className="asset-title"><div><h1>Centro de activos</h1><p>Empresas, identidad y cobertura. La base de cada investigación.</p></div><button disabled={!ready||running} onClick={()=>sync.mutate()}>{running?'Actualizando…':'Actualizar catálogo SEC'}</button></div>
    {summary.isError?<div role="alert" className="asset-notice"><p>{summary.error.message}</p><button onClick={()=>void summary.refetch()}>Reintentar conexión</button></div>:null}
    {summary.isPending?<p role="status">Consultando el registro local…</p>:summary.data?<>
      <div className="asset-register-line"><span><strong>{number.format(summary.data.counts.entities)}</strong> emisores identificados</span><span><strong>{number.format(summary.data.counts.current_listings)}</strong> símbolos en el último catálogo</span><span><strong>{number.format(summary.data.counts.conflicts)}</strong> registros con conflicto</span></div>
      <details className="asset-sources"><summary>Fuentes y configuración <span>SEC · Alpaca</span></summary><div>{summary.data.sources.map(s=><section key={s.provider}><h2>{s.provider}<span>{universeState(s.state)}</span></h2><p>{s.purpose}</p><p>{s.reason}</p><a href={s.docs} target="_blank" rel="noreferrer">Documentación oficial</a></section>)}</div></details>
    </>:null}
    <div className="asset-import-status" role="status" aria-live="polite">{sync.isError?<span>La actualización no pudo confirmarse. Reintentar conserva el mismo identificador para evitar duplicados.</span>:last?<span>{universeState(last.state)} · {time(last.finished_at??last.started_at)}{last.reason?' · '+last.reason:''}</span>:<span>El catálogo identifica empresas; las cotizaciones y los históricos se incorporan por separado.</span>}</div>
    <FinancialImport/>
    <MarketConnection/>
    <details className="asset-sources"><summary>Cierres europeos <span>Bolsa de Zagreb</span></summary>
      <p>Hrvatski Telekom · HT · XZAG · EUR por acción</p>
      <button disabled={europe.isPending} onClick={()=>europe.mutate()}>{europe.isPending?'Consultando…':'Consultar cierre de HT'}</button>
      {europe.isError?<p role="alert">No se pudo consultar el cierre. Reintenta la conexión.</p>:europe.data?<p role="status">{europe.data.listing?'Ficha de HT actualizada.':europe.data.reason}</p>:null}
    </details>
    <div className="asset-workspace"><section className="asset-catalogue" aria-label="Catálogo de activos">
<form className="asset-search" onSubmit={e=>{e.preventDefault();search();}}><label>Buscar empresa, símbolo, CIK o ISIN<input value={input} onChange={e=>setInput(e.target.value)} maxLength={120} placeholder="Nombre o identificador" type="search"/></label><button type="submit">Buscar</button><label>Identidad<select aria-label="Filtrar por estado de identidad" value={state} onChange={e=>{setState(e.target.value);setOffset(0);}}><option value="">Todos los estados</option><option value="IDENTIFIED">Identificados</option><option value="CONFLICT">Con conflicto</option><option value="INCOMPLETE">Mercado sin confirmar</option><option value="NOT_OBSERVED">Ausentes en último catálogo</option></select></label></form>
      {page.isPending?<p className="asset-empty" role="status">Buscando en el catálogo…</p>:page.isError?<div className="asset-empty" role="alert"><p>{page.error.message}</p><button onClick={()=>void page.refetch()}>Reintentar búsqueda</button></div>:page.data?.total===0?<div className="asset-empty"><h2>{query||state?'No hay coincidencias':'El registro empresarial está vacío'}</h2><p>{query||state?'Prueba otro nombre o elimina el filtro.':'Configura el contacto SEC y actualiza el catálogo para incorporar empresas con procedencia verificable.'}</p></div>:page.data?<>
        <div className="asset-table-wrap"><table><caption>{number.format(page.data.total)} {page.data.total===1?'resultado':'resultados'} · la identidad no acredita disponibilidad de datos</caption><thead><tr><th scope="col">Empresa y símbolo</th><th scope="col">Mercado</th><th scope="col">Identidad</th></tr></thead><tbody>{page.data.items.map(row=><tr key={row.id} className={selected===row.id?'selected':''}><td><button aria-pressed={selected===row.id} aria-label={'Ver '+row.symbol+': '+row.name} onClick={()=>choose(row.id)}><strong>{row.symbol}</strong><span>{row.name}</span><small>{row.provider}{row.cik?' · CIK '+row.cik:''}</small></button></td><td data-label="Mercado">{row.venue==='UNKNOWN'?'Sin confirmar':row.venue}</td><td data-label="Identidad"><span className={'asset-state state-'+row.state.toLowerCase()}>{universeState(row.state)}</span></td></tr>)}</tbody></table></div>
        <nav className="asset-pagination" aria-label="Paginación del catálogo"><span>{number.format(offset+1)}–{number.format(Math.min(offset+50,page.data.total))} de {number.format(page.data.total)}</span><div><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-50))}>Anterior</button><button disabled={offset+50>=page.data.total} onClick={()=>setOffset(offset+50)}>Siguiente</button></div></nav>
      </>:null}
    </section><aside className="asset-inspection" aria-label="Detalle seleccionado">{!selected?<div className="asset-empty"><h2>Abre una empresa</h2><p>Selecciona un símbolo para consultar su identidad, procedencia y datos pendientes.</p><p>Un emisor puede tener varias clases de acciones o símbolos. El catálogo conserva esas diferencias.</p></div>:detail.isPending?<p role="status">Abriendo ficha…</p>:detail.isError?<div role="alert"><p>{detail.error.message}</p><button onClick={()=>void detail.refetch()}>Reintentar ficha</button></div>:detail.data?<AssetDetail item={detail.data}/>:null}</aside></div>
    {detail.data&&detail.data.provider!=='ZSE'?<InstrumentMarket key={detail.data.id} listingId={detail.data.id} onChoose={choose}/>:null}
    {detail.data?.cik?<CompanyFinancials key={detail.data.cik} cik={detail.data.cik} name={detail.data.name}/>:null}
    {detail.data?.cik?<CompanyAnalysis key={'model-'+detail.data.cik} cik={detail.data.cik}/>:null}
    <footer>Registro local de investigación · Datos IEX con cobertura y antigüedad explícitas · Órdenes deshabilitadas</footer>
  </main>;
}
