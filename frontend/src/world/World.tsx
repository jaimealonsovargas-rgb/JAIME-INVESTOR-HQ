import { Component, Suspense, lazy, useCallback, useEffect, useState, type ReactNode } from 'react';
import { Canvas } from '@react-three/fiber';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../api';
import { DEPARTMENTS, QUALITY, VIEWS, type Quality, type View } from './layout';
import type { SceneMetrics } from './Office';
import './world.css';

const Office = lazy(() => import('./Office'));
const INITIAL_CAMERA = { position: VIEWS.interior.position, fov: 62, near: .08, far: 220 };
const GL_SETTINGS = { antialias: true, powerPreference: 'high-performance' as const, alpha: false };
class SceneErrorBoundary extends Component<{children: ReactNode}, {failed: boolean}> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed ? <div className="world-fallback" role="alert"><h1>Escena 3D no disponible</h1><p>No se pudo iniciar WebGL o cargar los materiales locales.</p><button onClick={() => window.location.reload()}>Reintentar</button><a href="?diagnostico=1">Diagnóstico local</a></div> : this.props.children;
  }
}

export default function World() {
  const [view, setView] = useState<View>('interior');
  const [quality, setQuality] = useState<Quality>('balanced');
  const [metrics, setMetrics] = useState<SceneMetrics>();
  const [info, setInfo] = useState(false);
  const [measuring, setMeasuring] = useState(false);
  useEffect(() => { if (!measuring) return; const timer = window.setTimeout(() => setMeasuring(false), 12000); return () => clearTimeout(timer); }, [measuring]);
  const onMetrics = useCallback((m: SceneMetrics) => setMetrics(m), []);
  const health = useQuery({ queryKey: ['health'], queryFn: ({signal}) => fetchHealth(signal), retry: false, refetchInterval: 30000 });
  return <main className="world" aria-label="Oficina tridimensional JAIME INVESTOR HQ">
    <SceneErrorBoundary>
      <Canvas frameloop={measuring ? 'always' : 'demand'} shadows="percentage" dpr={QUALITY[quality].dpr} camera={INITIAL_CAMERA}
        gl={GL_SETTINGS}
        fallback={<div className="world-fallback">WebGL no disponible. <a href="?diagnostico=1">Abrir diagnóstico</a></div>}>
        <Suspense fallback={null}><Office view={view} quality={quality} measuring={measuring} onMetrics={onMetrics} /></Suspense>
      </Canvas>
    </SceneErrorBoundary>
    <header className="world-header">
      <div className="world-brand"><span>J.</span><div>JAIME INVESTOR HQ<small>INVESTIGACIÓN & CAPITAL VIRTUAL</small></div></div>
      <div className="world-badges"><span>PAPER ONLY</span><button onClick={() => setInfo(!info)} aria-expanded={info} aria-controls="architecture-info">Sobre esta entrega</button></div>
    </header>
    {!metrics ? <p className="world-loading" role="status">Preparando materiales y arquitectura…</p> : null}
    <div className="world-caption"><span>SEDE / {view === 'plan' ? 'PLANTA ÚNICA' : 'INTERIOR'}</span><h1>{VIEWS[view].label}</h1><p>{view === 'plan' ? '34 × 28 m · Nueve departamentos conectados' : 'Piedra, nogal y luz. Un lugar para pensar.'}</p></div>
    {info ? <aside className="architecture-info" id="architecture-info">
      <button className="close-info" onClick={() => setInfo(false)} aria-label="Cerrar información">×</button>
      <p className="info-kicker">REVISIÓN ARQUITECTÓNICA · P1.B</p><h2>Una planta. Nueve perspectivas.</h2>
      <p>Escena 3D real. Estas cámaras permiten revisar el diseño; el avatar y la navegación llegarán en P1.C. Los monitores todavía no abren paneles. No hay agentes activos ni datos financieros.</p>
      <ol>{DEPARTMENTS.map(d => <li key={d.id}><span>{d.number}</span>{d.label}</li>)}</ol>
      <p>Órdenes bloqueadas. Servicios locales: {health.isSuccess ? 'disponibles' : 'NO DISPONIBLE'}.</p>
      <a href="?diagnostico=1">Abrir comprobación de P0 ↗</a>
    </aside> : null}
    <footer className="world-toolbar">
      <nav aria-label="Vistas de revisión arquitectónica">{Object.entries(VIEWS).map(([key, value]) => <button key={key} aria-pressed={view === key} onClick={() => { setView(key as View); setMetrics(m => m ? {...m, samples: 0} : m); }}>{value.label}</button>)}</nav>
      <div className="world-tools"><label>Gráficos <select value={quality} onChange={e => { setQuality(e.target.value as Quality); setMetrics(m => m ? {...m, samples: 0} : m); }}><option value="balanced">Equilibrado</option><option value="detail">Detalle</option></select></label><button disabled={measuring} onClick={() => setMeasuring(true)}>{measuring ? 'Midiendo…' : 'Medir FPS'}</button><output aria-label="Fotogramas por segundo">{metrics && metrics.samples > 10 ? `${measuring ? '' : 'Última: '}${metrics.fps.toFixed(0)} FPS` : 'En reposo'}</output></div>
      <p className="world-help">Arrastrar para observar · Rueda para acercar <span>P1.B · ARQUITECTURA</span></p>
    </footer>
  </main>;
}
