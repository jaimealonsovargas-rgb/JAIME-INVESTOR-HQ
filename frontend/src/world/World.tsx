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
import HQVideowall,{type HQOverviewData} from './HQVideowall';
import { MONITOR_DEFINITIONS,canInteract } from './terminals';
import AdaptiveResolution from './AdaptiveResolution';

const Office = lazy(() => import('./Office'));
const INITIAL_CAMERA = { position: VIEWS.interior.position, fov: VIEWS.interior.fov, near: .08, far: 400 };
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
  const [overview,setOverview]=useState<HQOverviewData>();
  const [near,setNear]=useState<string>();
  const openPanel=useCallback((id:string)=>{const monitor=MONITOR_DEFINITIONS.find(m=>m.id===id);if(monitor&&canInteract(player,monitor)){player.paused=true;player.speed=0;player.invalidate?.();setPanel(id);}},[player]);
  const closePanel=useCallback(()=>{player.paused=false;player.holdCamera=true;player.invalidate?.();setPanel(undefined);document.querySelector('canvas')?.focus();},[player]);
  player.mode=mode;
  useEffect(()=>{const back=(e:KeyboardEvent)=>{if(e.key==='Escape'&&player.mode==='inspection'){setMode('play');document.querySelector('canvas')?.focus();}};window.addEventListener('keydown',back);return()=>window.removeEventListener('keydown',back);},[player]);
  const [view, setView] = useState<View>('interior');
  const [quality, setQuality] = useState<Quality>('balanced');
  const [renderDpr,setRenderDpr]=useState<number>(QUALITY.balanced.dpr);
  const [metrics, setMetrics] = useState<SceneMetrics>();
  const [info, setInfo] = useState(false);
  const [measuring, setMeasuring] = useState(false);
  useEffect(() => { if (!measuring) return; const timer = window.setTimeout(() => setMeasuring(false), 12000); return () => clearTimeout(timer); }, [measuring]);
  const onMetrics = useCallback((m: SceneMetrics) => setMetrics(m), []);
  const health = useQuery({ queryKey: ['health'], queryFn: ({signal}) => fetchHealth(signal), retry: false, refetchInterval: 30000 });
  const room=DEPARTMENTS.find(d=>Math.abs(player.position.x-d.center[0])<d.size[0]/2&&Math.abs(player.position.z-d.center[2])<d.size[1]/2);
  return <main className="world" aria-label="Oficina tridimensional JAIME INVESTOR HQ">
    <SceneErrorBoundary>
      <Canvas frameloop={measuring ? 'always' : 'demand'} shadows="percentage" dpr={renderDpr} camera={INITIAL_CAMERA}
        gl={GL_SETTINGS}
        fallback={<div className="world-fallback">WebGL no disponible. <a href="?diagnostico=1">Abrir diagnóstico</a></div>}>
        <AdaptiveResolution quality={quality} player={player} onDprChange={setRenderDpr}/>
        <Suspense fallback={null}><Office view={view} quality={quality} measuring={measuring} onMetrics={onMetrics} player={player} mode={mode} onOpen={openPanel} onNear={setNear} overview={overview} /></Suspense>
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
      <p>Oficina Sims 3D real con dieciséis profesionales sentados. Usa las flechas en direcciones de pantalla. Los NPC son ambientación; agentes IA NO DISPONIBLES — P4. Las funciones de inversión permanecen deshabilitadas.</p>
      <ol>{DEPARTMENTS.map(d => <li key={d.id}><span>{d.number}</span>{d.label}</li>)}</ol>
      <p>Órdenes bloqueadas. Servicios locales: {health.isSuccess ? 'disponibles' : 'NO DISPONIBLE'}.</p>
      <a href="?diagnostico=1">Abrir comprobación de P0 ↗</a>
    </aside> : null}
    {mode==='play'?<PlayerHud player={player}/>:null}
    <HQVideowall onOverview={setOverview} onPause={paused=>{player.paused=paused;player.speed=0;player.invalidate?.();if(!paused)document.querySelector('canvas')?.focus();}}/>
    {mode==='play'&&near&&!panel?<p className="terminal-prompt">Acércate al agente principal para abrir su panel</p>:null}
    {panel?<MonitorOverlay id={panel} onClose={closePanel}/>:null}
    <footer className="world-toolbar">
      <nav aria-label="Cámara"><button aria-pressed={mode==='play'} onClick={()=>{setMode('play');document.querySelector('canvas')?.focus();}}>Recorrer</button>{Object.entries(VIEWS).map(([key, value]) => <button key={key} aria-pressed={mode==='inspection'&&view === key} onClick={() => { setMode('inspection');setView(key as View); setMetrics(m => m ? {...m, samples: 0} : m); }}>{value.label}</button>)}</nav>
      <div className="world-tools"><label>Gráficos <select value={quality} onChange={e => { const next=e.target.value as Quality;setQuality(next);setRenderDpr(QUALITY[next].dpr);setMetrics(m => m ? {...m, samples: 0} : m); }}><option value="balanced">Equilibrado automático</option><option value="fixed">Equilibrado fijo (80 %)</option><option value="detail">Detalle</option></select></label><span className="resolution-status" aria-label="Resolución de la escena 3D">{Math.round(renderDpr*100)} % 3D</span><button disabled={measuring} onClick={() => setMeasuring(true)}>{measuring ? 'Midiendo…' : 'Medir FPS'}</button><output aria-label="Fotogramas por segundo">{metrics && metrics.samples > 10 ? `${measuring ? '' : 'Última: '}${metrics.fps.toFixed(0)} FPS` : 'En reposo'}</output></div>
      <p className="world-help">{mode==='play'?'↑↓←→ desplazarse en pantalla · Cámara isométrica · Acércate al agente':'Vista general · Esc para volver'} <span>PERSONAL OFFLINE · AGENTES NO DISPONIBLES — P4</span></p>
    </footer>
  </main>;
}
