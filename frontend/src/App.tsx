import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from './api';
import { lazy, Suspense } from 'react';

const World = lazy(() => import('./world/World'));

export function App() {
  return new URLSearchParams(window.location.search).has('diagnostico')
    ? <Diagnostics />
    : <Suspense fallback={<div role="status">Preparando oficina 3D…</div>}><World /></Suspense>;
}

function Diagnostics() {
  const health = useQuery({
    queryKey: ['health'], queryFn: ({ signal }) => fetchHealth(signal),
    retry: false, refetchOnWindowFocus: true, staleTime: 0,
  });
  const available = health.isSuccess && !health.isFetching;

  return (
    <main>
      <header><span className="monogram" aria-hidden="true">J.</span><span>JAIME INVESTOR HQ</span><span className="phase">P0 / BASE LOCAL</span></header>
      <section aria-labelledby="title">
        <p className="eyebrow">ENTORNO DE COMPROBACIÓN</p>
        <h1 id="title">La base, antes<br />del mundo.</h1>
        <p className="intro">Comprobación técnica local conservada desde P0. <a href="/">Volver a la oficina 3D</a></p>
        <div className="status" role="status" aria-live="polite">
          <span className={available ? 'dot ready' : 'dot'} aria-hidden="true" />
          <div><strong>{health.isFetching ? 'COMPROBANDO…' : available ? 'BASE LOCAL DISPONIBLE' : 'NO DISPONIBLE'}</strong>
            <p>{available ? `Backend y SQLite responden. Migración ${health.data.schema_version}.` : health.isFetching ? 'Consultando el backend local.' : 'Arranca el backend y aplica las migraciones para comprobar la conexión.'}</p>
            {available ? <small>Comprobado: {new Date(health.data.checked_at).toLocaleString('es-ES')}</small> : null}
          </div>
        </div>
        <button type="button" disabled={health.isFetching} onClick={() => void health.refetch()}>Comprobar conexión <span aria-hidden="true">↗</span></button>
        <a href="http://127.0.0.1:8000/openapi.json" target="_blank" rel="noreferrer">Consultar contrato API</a>
      </section>
      <aside aria-label="Límites de P0">
        <p><strong>PAPER ONLY</strong><span>Todas las órdenes bloqueadas por código.</span></p>
        <p><strong>DATOS EXTERNOS</strong><span>NO DISPONIBLE · proveedores sin conectar.</span></p>
        <p><strong>0 € EN SERVICIOS</strong><span>Ejecución en este ordenador, sin nube.</span></p>
      </aside>
      <footer>Fase P0 · Sin cotizaciones, actividad de agentes ni saldos simulados. Ledger maestro previsto para P3.</footer>
    </main>
  );
}
