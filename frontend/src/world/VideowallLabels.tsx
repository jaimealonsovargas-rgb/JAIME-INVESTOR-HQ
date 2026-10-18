import { memo } from 'react';
import { Html } from '@react-three/drei';
import { HQ_TITLES, type HQOverviewData } from './HQVideowall';
import { VIDEOWALL } from './layout';
import { eur, percent, decimalText } from '../portfolioApi';

/** Native DOM at the physical screen plane. No raster text or DPR-dependent glyphs. */
export default memo(function VideowallLabels({overview}:{overview?:HQOverviewData}){
 return <>{Object.entries(HQ_TITLES).map(([id,title],i)=>{
  const section=overview?.sections.find(s=>s.section_id===id),value=section?.value,item=section?.items[0];
  const state=!section||section.status==='NOT_IMPLEMENTED'?'NO DISPONIBLE':section.status==='STALE'?'DESACTUALIZADO':id==='agents'?'RESEARCH LOCAL':value?'CAPITAL VIRTUAL':id==='systems'?'ESTADO LOCAL':'REFERENCIA';
  return <Html key={id} transform distanceFactor={4} position={[-14.4+i*3.6,6.9,VIDEOWALL.z+.23]} zIndexRange={[6,0]} style={{pointerEvents:'none'}}><section className="wall-native-card" data-wall-section={id} aria-hidden="true"><h2>{title}</h2><span className="wall-state">{state}</span>
   {id==='portfolio'&&value?<><small>NAV MASTER</small><strong>{eur(value.nav_eur)}</strong><p>Caja<br/>{eur(value.cash_eur)}</p><p>Retorno<br/>{percent(value.cumulative_return_pct)}</p><small>{value.performance?.twr_pct==null?'Performance: historia insuficiente':'TWR '+percent(value.performance.twr_pct as string)}</small></>:
    id==='positions'&&value?<><strong>{value.positions_count}</strong><p>{value.positions_count===0?'Sin posiciones':'Posiciones en MASTER'}</p><p>Exposición<br/>{percent(value.invested_pct)}</p><p>Valor de mercado<br/>{eur(value.market_value_eur)}</p></>:
    id==='agents'&&value?<><strong>{value.active_jobs??'—'}</strong><p>Jobs activos · {value.queue??'—'} en cola</p><p>{value.runtime?.state??'NO LOCAL MODEL'}</p><small>{value.roles} roles lógicos · una inferencia</small><p>{value.failures} fallos / bloqueos</p><small>Último completado: {value.last_completed?.role_id??'Ninguno'}</small></>:
    id==='systems'&&section?<><strong>{section.quality.verified_connections??'—'}</strong><p>Conexiones verificadas</p><p>{section.quality.usable_sources??'—'} utilizables ahora</p><small>{section.quality.candidate_access_modes??'—'} modalidades auditadas</small></>:
    item?<><p className="wall-reference">{item.metadata.title??item.series_id}</p>{item.value!==null?<strong className="wall-quote">{decimalText(item.value,4)}</strong>:null}<small>{item.value!==null?item.unit:''}</small><p>{item.period}</p><small>{item.provider}</small></>:<p>{section?.phase_required?`${section.phase_required} · Sin registros autorizados`:'Servicio local sin conexión'}</p>}
   <footer>{section?.as_of_utc?new Date(section.as_of_utc).toLocaleDateString('es-ES'):section?.phase_required??'OFFLINE'}<br/>SIMULACIÓN · PAPER ONLY</footer>
  </section></Html>;
 })}</>;
});
