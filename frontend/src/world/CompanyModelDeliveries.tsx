import {useQuery} from '@tanstack/react-query';
import {fetchRecentModels} from '../companyModelsApi';
import {financialTime} from '../financialsApi';

export default function CompanyModelDeliveries(){
 const recent=useQuery({queryKey:['company-model-recent'],queryFn:({signal})=>fetchRecentModels(signal),retry:false,staleTime:30000});
 return <section className="person-model-deliveries"><h4>Modelos empresariales compartidos</h4><p>Python construye las cifras y revisa los cálculos. Estas entregas del flujo empresarial se registran por separado de los debates con IA local.</p>
 {recent.isPending?<p role="status">Consultando modelos…</p>:recent.isError?<div role="alert"><p>{recent.error.message}</p><button onClick={()=>void recent.refetch()}>Reintentar modelos</button></div>:recent.data?.length?<ul>{recent.data.map(m=><li key={m.id}><a href={'?activos=1&q='+encodeURIComponent(m.cik)}>{m.name} · versión {m.version}</a><p>{financialTime(m.created_at)} · {m.evidence_count} cifras citadas · {m.state==='FAILED'?'Revisión con discrepancias':m.state==='PARTIAL'?'Revisión parcial':'Revisión numérica superada'}</p></li>)}</ul>:<p>Aún no se han construido modelos. Abre una empresa con cuentas SEC en el Centro de activos.</p>}
 </section>;
}
