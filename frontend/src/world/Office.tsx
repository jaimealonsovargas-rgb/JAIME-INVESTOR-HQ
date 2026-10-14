import { memo, useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Html, OrbitControls, useTexture } from '@react-three/drei';
import { ACESFilmicToneMapping, Color, Fog, PCFShadowMap, PMREMGenerator, Vector3 } from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { createOffice, disposeOffice } from './model';
import { makeMaterials } from './materials';
import { DEPARTMENTS, QUALITY, VIEWS, type Quality, type View } from './layout';

export interface SceneMetrics {
  ready: boolean; renderer: string; view: View; quality: Quality; fps: number;
  frameMsP95: number; calls: number; triangles: number; textures: number; geometries: number;
  loadMs: number; width: number; height: number; dpr: number; departments: string[];
  firstFrameMs: number;
  samples: number; hidden: boolean;
  camera: number[]; target: number[];
}
declare global { interface Window { __HQ_METRICS__?: SceneMetrics; __HQ_FRAMES__?: number[] } }

export default memo(function Office({ view, quality, measuring, onMetrics }: { view: View; quality: Quality; measuring: boolean; onMetrics: (m: SceneMetrics) => void }) {
  const maps = useTexture([
    '/materials/dark_wood_diffuse.jpg', '/materials/dark_wood_nor_gl.jpg', '/materials/dark_wood_rough.jpg',
    '/materials/marble_01_diffuse.jpg', '/materials/marble_01_nor_gl.jpg', '/materials/marble_01_rough.jpg',
  ]);
  const materials = useMemo(() => makeMaterials(maps), [maps[0], maps[1], maps[2], maps[3], maps[4], maps[5]]);
  const model = useMemo(() => createOffice(materials), [materials]);
  const { gl, scene, camera, invalidate, size } = useThree();
  const controls = useRef<OrbitControlsImpl>(null);
  const frames = useRef<number[]>([]);
  const last = useRef(0), report = useRef(0), loaded = useRef(0);
  const firstFrame = useRef(0);
  useEffect(() => () => disposeOffice(model), [model]);

  useEffect(() => {
    gl.toneMapping = ACESFilmicToneMapping; gl.toneMappingExposure = 1.18;
    gl.shadowMap.type = PCFShadowMap;
    const pmrem = new PMREMGenerator(gl);
    const room = new RoomEnvironment();
    const env = pmrem.fromScene(room, .04, .1, 100);
    scene.environment = env.texture; scene.environmentIntensity = .65;
    scene.background = new Color('#a5bec8'); scene.fog = new Fog('#a5bec8', 38, 155);
    room.dispose(); pmrem.dispose();
    return () => { scene.environment = null; env.dispose(); };
  }, [gl, scene]);

  useEffect(() => {
    const setting = VIEWS[view];
    camera.position.set(...setting.position);
    if ('fov' in camera) { camera.fov = setting.fov; camera.updateProjectionMatrix(); }
    camera.lookAt(new Vector3(...setting.target));
    controls.current?.target.set(...setting.target); controls.current?.update();
    const roof = model.getObjectByName('ceiling'); if (roof) roof.visible = view !== 'plan';
    gl.shadowMap.needsUpdate = true; frames.current = []; last.current = 0; invalidate();
  }, [view, camera, model, gl, invalidate]);

  useEffect(() => { gl.shadowMap.autoUpdate = true; gl.shadowMap.needsUpdate = true; frames.current = []; }, [quality, gl]);
  useEffect(() => { if (measuring) { frames.current = []; last.current = 0; report.current = 0; } }, [measuring]);

  useFrame(() => {
    const now = performance.now();
    if (!loaded.current) { loaded.current = now; invalidate(); return; }
    // Se ejecuta tras el primer render completo, una sola vez por montaje.
    if (!firstFrame.current) { gl.getContext().finish(); firstFrame.current = performance.now(); }
    if (document.hidden) { last.current = 0; return; }
    if (measuring && last.current && now - last.current < 1000) frames.current.push(now - last.current);
    last.current = now;
    if (frames.current.length > 600) frames.current.shift();
    if (report.current && (!measuring || now - report.current < 1000)) return;
    report.current = now;
    const ordered = [...frames.current].sort((a, b) => a - b);
    const context = gl.getContext(); const debug = context.getExtension('WEBGL_debug_renderer_info');
    const metrics: SceneMetrics = {
      ready: true, renderer: debug ? context.getParameter(debug.UNMASKED_RENDERER_WEBGL) : 'No expuesto por el navegador',
      view, quality, fps: frames.current.length ? 1000 * frames.current.length / frames.current.reduce((a, b) => a + b, 0) : 0,
      frameMsP95: ordered[Math.floor(ordered.length * .95)] ?? 0, samples: ordered.length,
      calls: gl.info.render.calls, triangles: gl.info.render.triangles, textures: gl.info.memory.textures,
      geometries: gl.info.memory.geometries, loadMs: loaded.current, firstFrameMs: firstFrame.current,
      width: size.width, height: size.height, dpr: gl.getPixelRatio(),
      departments: model.children.filter(c => c.name.startsWith('department:')).map(c => c.name.slice(11)), hidden: document.hidden,
      camera: camera.position.toArray(), target: controls.current?.target.toArray() ?? [],
    };
    window.__HQ_METRICS__ = metrics; window.__HQ_FRAMES__ = [...frames.current]; onMetrics(metrics);
    // La escena es estática en P1.B; una sombra ya renderizada no se recalcula cada frame.
    gl.shadowMap.autoUpdate = false;
  });

  return <>
    <hemisphereLight args={['#d7e7f2', '#75604a', 1.0]} />
    <directionalLight position={[-16, 23, -18]} color="#fff0d3" intensity={2.3} castShadow
      shadow-mapSize={[QUALITY[quality].shadows, QUALITY[quality].shadows]} shadow-camera-left={-25} shadow-camera-right={25}
      shadow-camera-top={24} shadow-camera-bottom={-24} shadow-camera-near={1} shadow-camera-far={85}
      shadow-normalBias={.035} shadow-bias={-.00015} />
    <pointLight position={[0, 3.3, 7]} color="#ffdcb1" intensity={50} distance={15} decay={2} />
    <pointLight position={[0, 3.3, -8]} color="#fff0d7" intensity={35} distance={14} decay={2} />
    <primitive object={model} />
    {view === 'plan' ? DEPARTMENTS.map(d => <Html key={d.id} position={[d.center[0], 2.2, d.center[2]]} center style={{pointerEvents: 'none'}}><div className="plan-label"><span>{d.number}</span>{d.label}</div></Html>) : null}
    <OrbitControls ref={controls} makeDefault enableDamping={false} enablePan={view === 'plan'}
      minDistance={view === 'plan' ? 26 : 2} maxDistance={view === 'plan' ? 65 : 20}
      minPolarAngle={.1} maxPolarAngle={Math.PI / 2 - .035} rotateSpeed={.5} zoomSpeed={.7} />
  </>;
});
