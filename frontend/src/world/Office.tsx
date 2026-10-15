import { memo, useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Html, useTexture } from '@react-three/drei';
import { ACESFilmicToneMapping, Color, Mesh, Object3D, PCFSoftShadowMap, PMREMGenerator, Vector3 } from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createOffice, disposeOffice } from './model';
import { makeMaterials,hqTexture } from './materials';
import {HQ_TITLES,type HQOverviewData} from './HQVideowall';
import {MeshBasicMaterial} from 'three';
import { DEPARTMENTS, OFFICE_FORWARD, QUALITY, VIEWS, type Quality, type View } from './layout';
import Player from './Player';
import { ISOMETRIC,type PlayerRuntime } from './navigation';
import type { Collider } from './collisions';
import Monitors from './Monitors';
import Personnel from './Personnel';
import {PERSONNEL_COLLIDERS} from './staffLayout';
import {frameStats} from './frameStats';
import {batchStaticOffice} from './staticBatches';
import {firstHit,type Collider as WallCollider} from './collisions';

export interface SceneMetrics {
  ready: boolean; renderer: string; view: View; quality: Quality; fps: number;
  frameMsP95: number; calls: number; triangles: number; textures: number; geometries: number;
  loadMs: number; width: number; height: number; dpr: number; departments: string[];
  firstFrameMs: number;
  samples: number; hidden: boolean;
  camera: number[]; target: number[];
  mode: string; movingSamples: number; movingFps:number; movingFrameMsP95:number;
}
declare global { interface Window { __HQ_METRICS__?: SceneMetrics; __HQ_FRAMES__?: number[];__HQ_MOVING_FRAMES__?:number[]; __HQ_COLLIDERS__?:ReadonlyArray<Collider> } }

export default memo(function Office({ view, quality, measuring, onMetrics, player, mode,onOpen,onNear,overview }: { view: View; quality: Quality; measuring: boolean; onMetrics: (m: SceneMetrics) => void; player:PlayerRuntime; mode:'play'|'inspection';onOpen:(id:string)=>void;onNear:(id:string|undefined)=>void;overview?:HQOverviewData }) {
  const maps = useTexture([
    '/materials/dark_wood_diffuse.jpg', '/materials/dark_wood_nor_gl.jpg', '/materials/dark_wood_rough.jpg',
    '/materials/marble_01_diffuse.jpg', '/materials/marble_01_nor_gl.jpg', '/materials/marble_01_rough.jpg',
  ]);
  const materials = useMemo(() => makeMaterials(maps), [maps[0], maps[1], maps[2], maps[3], maps[4], maps[5]]);
  const lightTargets=useMemo(()=>[4,-3].map(z=>{const target=new Object3D();target.position.set(0,0,z+OFFICE_FORWARD);return target;}),[]);
  const { gl, scene, camera, invalidate, size } = useThree();
  const model = useMemo(() => {const office=createOffice(materials);office.getObjectByName('ceiling')?.traverse(o=>{if(o instanceof Mesh)o.castShadow=false;});
    const batches=gl.extensions.has('WEBGL_multi_draw')?batchStaticOffice(office):[];
    office.userData.batches=batches;office.updateMatrixWorld(true);office.traverse(object=>{object.matrixAutoUpdate=false;});return office;}, [materials,gl]);
  const cutaways=useMemo(()=>{const walls:{object:Object3D;wall:WallCollider}[]=[];model.traverse(object=>{if(object.userData.cutaway)walls.push({object,wall:object.userData.wall});});return walls;},[model]);
  const frames = useRef<number[]>([]);
  const last = useRef(0), report = useRef(0), loaded = useRef(0);
  const firstFrame = useRef(0);
  const moving=useRef<number[]>([]);
  useEffect(()=>{player.colliders=[...model.userData.colliders,...PERSONNEL_COLLIDERS];window.__HQ_COLLIDERS__=player.colliders;model.getObjectByName('ceiling')?.traverse(o=>{if(o instanceof Mesh)o.castShadow=false;});return()=>{delete window.__HQ_COLLIDERS__;};},[model,player]);
  useEffect(() => () => {for(const batch of model.userData.batches)batch.dispose();disposeOffice(model, new Set(maps));}, [model]);

  useEffect(() => {
    const roof = model.getObjectByName('ceiling'); if (roof) roof.visible = false;
        gl.toneMapping = ACESFilmicToneMapping; gl.toneMappingExposure = 1.06;
    gl.shadowMap.type = PCFSoftShadowMap;
    const pmrem = new PMREMGenerator(gl);
    const room = new RoomEnvironment();
    const env = pmrem.fromScene(room, .04, .1, 100);
    scene.environment = env.texture; scene.environmentIntensity = .7;
    scene.background=new Color('#000000');scene.fog=null;
    room.dispose(); pmrem.dispose();
    return () => { scene.environment = null; scene.background=null; env.dispose(); };
  }, [gl, scene]);

  useEffect(() => {
    if(mode==='play'){player.holdCamera=false;player.revision+=1;invalidate();return;}
    const setting = VIEWS[view];
    camera.position.set(...setting.position);
    if ('fov' in camera) { camera.fov = setting.fov; camera.updateProjectionMatrix(); }
    camera.lookAt(new Vector3(...setting.target));
    gl.shadowMap.needsUpdate = true; frames.current = []; last.current = 0; invalidate();
  }, [view, mode, camera, model, gl, invalidate,player]);

  useEffect(()=>{
    model.traverse(object=>{if(!(object instanceof Mesh)||!(object.material instanceof MeshBasicMaterial)||!object.material.name.startsWith('hq:'))return;
      const id=object.material.name.slice(3),section=overview?.sections.find(s=>s.section_id===id),item=section?.items[0];
      let detail=section?.reason??'NO DISPONIBLE / servicio local sin verificar';
      if(id==='systems'&&section)detail=`${section.quality.candidate_access_modes} modalidades / ${section.quality.verified_connections} conexiones verificadas`;
      if(item)detail=(section?.status==='STALE'?'DESACTUALIZADO / ':'REFERENCIA / ')+(item.metadata.title?.slice(0,52)??`${item.series_id}: ${item.value} ${item.unit}`)+' / '+item.period;
      const state=section?.status==='AVAILABLE'?(id==='systems'?'ESTADO LOCAL':'REFERENCIA'):section?.status==='STALE'?'DESACTUALIZADO':'NO DISPONIBLE';
      const old=object.material.map;object.material.map=hqTexture(HQ_TITLES[id]??id,state,detail,item?item.provider+' / '+item.period:section?.phase_required??'Sin conexión');old?.dispose();
    });invalidate();
  },[overview,model,invalidate]);

  useEffect(() => { gl.shadowMap.autoUpdate = true; gl.shadowMap.needsUpdate = true; frames.current = []; }, [quality, gl]);
  useEffect(() => { if (measuring) { frames.current = [];moving.current=[]; last.current = 0; }report.current=0; }, [measuring]);

  useFrame(() => {
    for(const wall of cutaways){
      const head=player.position.clone();head.y=1.25;
      wall.object.visible=mode!=='play'||firstHit(camera.position,head,[wall.wall],.08)===1;
    }
    const now = performance.now();
    if (!loaded.current) { loaded.current = now; invalidate(); return; }
    // Se ejecuta tras el primer render completo, una sola vez por montaje.
    if (!firstFrame.current) { gl.getContext().finish(); firstFrame.current = performance.now(); }
    if (document.hidden) { last.current = 0; return; }
    if (measuring && last.current) {frames.current.push(now - last.current);if(player.speed>.1)moving.current.push(now-last.current);}
    last.current = now;
    if (frames.current.length > 1200) frames.current.shift();if(moving.current.length>1200)moving.current.shift();
    if (report.current && now - report.current < 1000) return;
    report.current = now;
    const stats=frameStats(frames.current),motion=frameStats(moving.current);
    const context = gl.getContext(); const debug = context.getExtension('WEBGL_debug_renderer_info');
    const metrics: SceneMetrics = {
      ready: true, renderer: debug ? context.getParameter(debug.UNMASKED_RENDERER_WEBGL) : 'No expuesto por el navegador',
      view, quality, fps:stats.fps,
      frameMsP95:stats.p95,samples:stats.samples,
      calls: gl.info.render.calls, triangles: gl.info.render.triangles, textures: gl.info.memory.textures,
      geometries: gl.info.memory.geometries, loadMs: loaded.current, firstFrameMs: firstFrame.current,
      width: size.width, height: size.height, dpr: gl.getPixelRatio(),
      departments: model.children.filter(c => c.name.startsWith('department:')).map(c => c.name.slice(11)), hidden: document.hidden,
      camera: camera.position.toArray(), target: mode==='play'?[player.position.x,.7,player.position.z-ISOMETRIC.lookAhead]:[...VIEWS[view].target],
      mode,movingSamples:motion.samples,movingFps:motion.fps,movingFrameMsP95:motion.p95,
    };
    window.__HQ_METRICS__ = metrics; window.__HQ_FRAMES__ = [...frames.current];window.__HQ_MOVING_FRAMES__=[...moving.current]; onMetrics(metrics);
    // La escena es estática en P1.B; una sombra ya renderizada no se recalcula cada frame.
    gl.shadowMap.autoUpdate = false;
  });

  return <>
    <hemisphereLight args={['#e6e8e3', '#676a70', .95]} />
    <directionalLight position={[-20, 25, 16]} color="#ffe9c9" intensity={1.9} castShadow
      shadow-mapSize={[QUALITY[quality].shadows, QUALITY[quality].shadows]} shadow-camera-left={-25} shadow-camera-right={25}
      shadow-camera-top={24} shadow-camera-bottom={-24} shadow-camera-near={1} shadow-camera-far={85}
      shadow-normalBias={.035} shadow-bias={-.00015} />
    {lightTargets.map((target,i)=><primitive key={i} object={target} />)}
    <spotLight position={[0, 4.08, 4+OFFICE_FORWARD]} target={lightTargets[0]} color="#ffe0b1" intensity={70} distance={18} decay={2} angle={1.1} penumbra={1} />
    <spotLight position={[0, 4.08, -3+OFFICE_FORWARD]} target={lightTargets[1]} color="#ffe7c6" intensity={70} distance={17} decay={2} angle={1.1} penumbra={1} />
    <primitive object={model} />
    <Player runtime={player} contact={materials.contact}/>
    <Personnel contact={materials.contact}/>
    <Monitors player={player} onOpen={onOpen} onNear={onNear}/>
    {DEPARTMENTS.map(d => <Html key={d.id} position={[d.center[0],2.76,d.center[2]-d.size[1]/2+.15]} transform distanceFactor={4} zIndexRange={[5,0]} style={{pointerEvents: 'none'}}><div className="department-label" data-department={d.id} style={{width:d.id==='committee'?480:320}}>{d.label}</div></Html>)}

  </>;
});
