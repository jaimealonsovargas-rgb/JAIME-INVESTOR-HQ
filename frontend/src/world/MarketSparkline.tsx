import type {MarketHistory} from '../portfolioApi';

/** Floating point is used only for SVG pixel coordinates, never money/returns. */
export function chartPoints(history?:MarketHistory):string|null{
 if(!history||history.state==='NO_DATA'||history.points.length<3)return null;
 const values=history.points.map(p=>Number(p.value));
 if(values.some(v=>!Number.isFinite(v)))return null;
 const min=Math.min(...values),range=Math.max(...values)-min;
 if(!Number.isFinite(range))return null;
 return values.map((v,i)=>`${(i/(values.length-1)*80).toFixed(2)},${(range?30-(v-min)/range*26:17).toFixed(2)}`).join(' ');
}
export default function MarketSparkline({history}:{history?:MarketHistory}){
 const points=chartPoints(history);
 if(!points)return <span className="market-sparkline-empty" aria-label="Sin histórico comparable">—</span>;
 return <svg className={'market-sparkline '+(history?.state==='STALE'?'is-stale':'')} viewBox="0 0 80 34" role="img" aria-label={`Histórico de ${history!.points.length} observaciones${history?.state==='STALE'?', desactualizado':''}; no representa variación diaria`}><polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.6" vectorEffect="non-scaling-stroke"/></svg>;
}
