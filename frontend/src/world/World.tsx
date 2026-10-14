import { Component, Suspense, lazy, useCallback, useEffect, useState, useRef, type ReactNode } from 'react';
import { Canvas } from '@react-three/fiber';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../api';
import { DEPARTMENTS, QUALITY, VIEWS, type Quality, type View } from './layout';
import type { SceneMetrics } from './Office';
import './world.css';
import { createPlayer } from './navigation';
import PlayerHud from './PlayerHud';
import MonitorOverlay from './MonitorOverlay';
import { MONITOR_DEFINITIONS,canInteract } from './terminals';

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
  const player=useRef(createPlayer()).current;
  const [mode,setMode]=useState<'play'|'inspection'>('play');
  const [panel,setPanel]=useState<string>();
  const [near,setNear]=useState<string>();
  const openPanel=useCallback((id:string)=>{const monitor=MONITOR_DEFINITIONS.find(m=>m.id===id);if(monitor&&canInteract(player,monitor)){player.paused=true;player.speed=0;player.invalidate?.();setPanel(id);}},[player]);
  const closePanel=useCallback(()=>{player.paused=false;player.invalidate?.();setPanel(undefined);document.querySelector('canvas')?.focus();},[player]);
  player.mode=mode;
  const [view, setView] = useState<View>('interior');
  const [quality, setQuality] = useState<Quality>('balanced');
  const [metrics, setMetrics] = useState<SceneMetrics>();
  const [info, setInfo] = useState(false);
  const [measuring, setMeasuring] = useState(false);
  useEffect(() => { if (!measuring) return; const timer = window.setTimeout(() => setMeasuring(false), 12000); return () => clearTimeout(timer); }, [measuring]);
  const onMetrics = useCallback((m: SceneMetrics) => setMetrics(m), []);
  const health = useQuery({ queryKey: ['health'], queryFn: ({signal}) => fetchHealth(signal), retry: false, refetchInterval: 30000 });
  const room=DEPARTMENTS.find(d=>Math.abs(player.position.x-d.center[0])<4.2&&Math.abs(player.position.z-d.center[2])<3.2);
  return <main className="world" aria-label="Oficina tridimensional JAIME INVESTOR HQ">
    <SceneErrorBoundary>
      <Canvas frameloop={measuring ? 'always' : 'demand'} shadows="percentage" dpr={QUALITY[quality].dpr} camera={INITIAL_CAMERA}
        gl={GL_SETTINGS}
        fallback={<div className="world-fallback">WebGL no disponible. <a href="?diagnostico=1">Abrir diagnóstico</a></div>}>
        <Suspense fallback={null}><Office view={view} quality={quality} measuring={measuring} onMetrics={onMetrics} player={player} mode={mode} onOpen={openPanel} onNear={setNear} /></Suspense>
      </Canvas>
    </SceneErrorBoundary>
    <header className="world-header">
      <div className="world-brand"><span>J.</span><div>JAIME INVESTOR HQ<small>INVESTIGACIÓN & CAPITAL VIRTUAL</small></div></div>
      <div className="world-badges"><span>PAPER ONLY</span><button onClick={() => setInfo(!info)} aria-expanded={info} aria-controls="architecture-info">Sobre esta entrega</button></div>
    </header>
    {!metrics ? <p className="world-loading" role="status">Preparando materiales y arquitectura…</p> : null}
    <div className="world-caption"><span>SEDE / {mode==='play'?'RECORRIDO':view === 'plan' ? 'PLANTA ÚNICA' : 'INTERIOR'}</span><h1>{mode==='play'?room?.label??'Pasillo principal':VIEWS[view].label}</h1><p>{mode==='play'?room?.use??'Nueve departamentos conectados':view === 'plan' ? '34 × 28 m · Nueve departamentos conectados' : 'Piedra, nogal y luz. Un lugar para pensar.'}</p></div>
    {info ? <aside className="architecture-info" id="architecture-info">
      <button className="close-info" onClick={() => setInfo(false)} aria-label="Cerrar información">×</button>
      <p className="info-kicker">SEDE VIRTUAL · PAPER ONLY</p><h2>Una planta. Nueve perspectivas.</h2>
      <p>Escena 3D real. Recorre la sede con tu avatar; las cámaras de inspección permiten revisar la arquitectura. Diez humanos de ambientación offline. Trabajo de agentes: NO DISPONIBLE — P4. No hay datos financieros conectados.</p>
      <ol>{DEPARTMENTS.map(d => <li key={d.id}><span>{d.number}</span>{d.label}</li>)}</ol>
      <p>Órdenes bloqueadas. Servicios locales: {health.isSuccess ? 'disponibles' : 'NO DISPONIBLE'}.</p>
      <a href="?diagnostico=1">Abrir comprobación de P0 ↗</a>
    </aside> : null}
    {mode==='play'?<PlayerHud player={player}/>:null}
    {mode==='play'&&near&&!panel?<button className="terminal-prompt" onClick={()=>openPanel(near)}>E · Abrir {MONITOR_DEFINITIONS.find(m=>m.id===near)?.label}</button>:null}
    {panel?<MonitorOverlay id={panel} onClose={closePanel}/>:null}
    <footer className="world-toolbar">
      <nav aria-label="Cámara"><button aria-pressed={mode==='play'} onClick={()=>{setMode('play');document.querySelector('canvas')?.focus();}}>Recorrer</button>{Object.entries(VIEWS).map(([key, value]) => <button key={key} aria-pressed={mode==='inspection'&&view === key} onClick={() => { setMode('inspection');setView(key as View); setMetrics(m => m ? {...m, samples: 0} : m); }}>{value.label}</button>)}</nav>
      <div className="world-tools"><label>Gráficos <select value={quality} onChange={e => { setQuality(e.target.value as Quality); setMetrics(m => m ? {...m, samples: 0} : m); }}><option value="balanced">Equilibrado</option><option value="detail">Detalle</option></select></label><button disabled={measuring} onClick={() => setMeasuring(true)}>{measuring ? 'Midiendo…' : 'Medir FPS'}</button><output aria-label="Fotogramas por segundo">{metrics && metrics.samples > 10 ? `${measuring ? '' : 'Última: '}${metrics.fps.toFixed(0)} FPS` : 'En reposo'}</output></div>
      <p className="world-help">{mode==='play'?'WASD · Mayús caminar rápido · Botón derecho + ratón mirar · Rueda zoom · E terminal':'Arrastrar para observar · Rueda para acercar'} <span>PERSONAL OFFLINE · AGENTES NO DISPONIBLES — P4</span></p>
    </footer>
  </main>;
}
