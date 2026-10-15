import { Suspense, useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Group, PerspectiveCamera, Vector3,type Material } from 'three';
import Avatar from './Avatar';
import { moveCircle } from './collisions';
import { ISOMETRIC, screenStep, type PlayerRuntime } from './navigation';

export default function Player({runtime,contact}:{runtime:PlayerRuntime;contact:Material}) {
  const {gl,camera,invalidate}=useThree(); const actor=useRef<Group>(null);
  const keys=useRef(new Set<string>()),snap=useRef(-1);
  const target=useRef(new Vector3()), desired=useRef(new Vector3());
  useEffect(()=>{
    runtime.invalidate=invalidate;
    const canvas=gl.domElement;canvas.tabIndex=0;canvas.setAttribute('aria-label','Oficina 3D. Flechas para desplazarse en direcciones de pantalla. Cámara isométrica automática.');
    if(document.activeElement===document.body)canvas.focus({preventScroll:true});
    const timer=setInterval(()=>{if(!document.hidden&&runtime.mode==='play'&&!runtime.paused)invalidate();},50);
    const down=(e:KeyboardEvent)=>{if(document.activeElement!==canvas||runtime.paused||runtime.mode!=='play')return;if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code)){e.preventDefault();runtime.holdCamera=false;keys.current.add(e.code);}if(e.code==='Escape'){keys.current.clear();}};
    const up=(e:KeyboardEvent)=>keys.current.delete(e.code);
    const pointer=()=>{if(runtime.mode==='play'&&!runtime.paused)canvas.focus();};
    const blur=()=>keys.current.clear();
    window.addEventListener('keydown',down);window.addEventListener('keyup',up);window.addEventListener('blur',blur);
    canvas.addEventListener('pointerdown',pointer);
    return()=>{clearInterval(timer);window.removeEventListener('keydown',down);window.removeEventListener('keyup',up);window.removeEventListener('blur',blur);canvas.removeEventListener('pointerdown',pointer);};
  },[gl,runtime,invalidate]);
  useFrame((_,delta)=>{
    // No fijar la cámara antes de montar los colliders: el primer brazo podría
    // quedar al otro lado de la fachada y el barrido impediría volver al interior.
    if(!runtime.colliders.length)return;
    if(runtime.mode!=='play'||runtime.paused||(runtime.holdCamera&&!keys.current.size)){keys.current.clear();runtime.speed=0;runtime.velocity=0;runtime.angularVelocity=0;window.__HQ_PLAYER__={position:runtime.position.toArray(),yaw:runtime.yaw,cameraYaw:runtime.cameraYaw,pitch:runtime.pitch,distance:runtime.distance,speed:0,mode:runtime.mode,paused:runtime.paused,camera:camera.position.toArray()};return;}
    const dt=Math.min(delta,.05);const k=keys.current;
    const v=screenStep(runtime,Number(k.has('ArrowUp'))-Number(k.has('ArrowDown')),Number(k.has('ArrowRight'))-Number(k.has('ArrowLeft')),dt);
    const old=runtime.position.clone();moveCircle(runtime.position,v.x,v.z,runtime.colliders);
    runtime.speed=old.distanceTo(runtime.position)/dt;
    runtime.cameraYaw=ISOMETRIC.azimuth;
    if(actor.current){actor.current.position.copy(runtime.position);actor.current.rotation.y=runtime.yaw+Math.PI;}
    target.current.copy(runtime.position).add(new Vector3(0,.7,0));
    desired.current.copy(target.current).add(new Vector3(...ISOMETRIC.offset));
    if(snap.current!==runtime.revision){camera.position.copy(desired.current);snap.current=runtime.revision;}
    else camera.position.lerp(desired.current,1-Math.exp(-dt*8));
    const perspective=camera as PerspectiveCamera;
    if(perspective.fov!==ISOMETRIC.fov){perspective.fov=ISOMETRIC.fov;perspective.updateProjectionMatrix();}
    // Objetivo derivado del mismo desplazamiento: azimut/elevación no cambian al seguir.
    camera.lookAt(camera.position.clone().sub(new Vector3(...ISOMETRIC.offset)).add(new Vector3(0,0,-ISOMETRIC.lookAhead)));
    if(k.size||runtime.velocity>.002)invalidate();
    window.__HQ_PLAYER__={position:runtime.position.toArray(),yaw:runtime.yaw,cameraYaw:runtime.cameraYaw,pitch:runtime.pitch,distance:runtime.distance,speed:runtime.speed,mode:runtime.mode,paused:runtime.paused,camera:camera.position.toArray()};
  },-1);
  return <group ref={actor} position={runtime.position} visible={runtime.mode==='play'}><Suspense fallback={null}><Avatar player={runtime}/></Suspense><mesh rotation={[-Math.PI/2,0,0]} position={[0,.027,0]} material={contact}><planeGeometry args={[.85,.7]}/></mesh></group>;
}
