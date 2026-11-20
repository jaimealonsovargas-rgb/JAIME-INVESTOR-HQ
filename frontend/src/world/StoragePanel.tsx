import {useQuery} from '@tanstack/react-query';
import {readStorage} from '../storageApi';

const size=(bytes:number)=>bytes>=1024**3?`${(bytes/1024**3).toLocaleString('es-ES',{maximumFractionDigits:2})} GiB`:
  `${(bytes/1024**2).toLocaleString('es-ES',{maximumFractionDigits:1})} MiB`;

export default function StoragePanel(){
  const query=useQuery({queryKey:['storage-budget'],queryFn:({signal})=>readStorage(signal),retry:false,
    refetchInterval:60000,refetchIntervalInBackground:false,staleTime:30000});
  const data=query.isError?undefined:query.data;
  return <section className="research-autonomy storage-budget" aria-label="Almacenamiento local">
    <header><div><h4>Almacenamiento local</h4><p>Datos y conservación</p></div>
      <button disabled={query.isFetching} onClick={()=>void query.refetch()}>Comprobar espacio</button></header>
    {!data?<p role="status">{query.isError?'No se puede verificar el almacenamiento. Comprueba el backend.':'Midiendo el almacenamiento…'}</p>:<>
      <p role="status"><strong>{data.state==='BLOCKED'?'Captación detenida':data.state==='WARNING'?'Presupuesto próximo al límite':'Espacio disponible'}</strong><br/>{data.message}</p>
      <div className="storage-budget-grid">
        <div><span>Datos financieros y automatización</span><strong>{size(data.data.bytes)}</strong><small>de {size(data.data.limit_bytes)}</small></div>
        <div><span>Copias, modelos locales y resultados</span><strong>{size(data.output.bytes)}</strong><small>de {size(data.output.limit_bytes)}</small></div>
        <div><span>Libre en disco</span><strong>{data.free_bytes===null?'Sin verificar':size(data.free_bytes)}</strong><small>margen mínimo {size(data.min_free_bytes)}</small></div>
      </div>
      <p>Presupuesto conjunto: {size(data.total_bytes)} de {size(data.total_limit_bytes)}.</p>
      <p className="research-note">Las nuevas consultas se detienen antes de agotar el margen. Los originales, recibos, revisiones y modelos se conservan.</p>
      <details><summary>Conservación y límites</summary>
        <p>Sin borrado automático de evidencias ni de la cartera. Una descarga idéntica reutiliza su original; una revisión nueva conserva la anterior.</p>
        <p>Reserva por unidad: {size(data.reserve_bytes)}. {data.scope}</p>
        <p>{data.recovery}</p>
        <p>n8n conserva su política de limpieza de registros de ejecución: siete días y hasta 1.000. Los recibos financieros de JAIME permanecen guardados.</p>
        <p>Comprobado: {new Date(data.measured_at).toLocaleString('es-ES',{timeZone:'Europe/Madrid'})} · Madrid.</p>
      </details>
    </>}
  </section>;
}
