import { Suspense, useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Group, PerspectiveCamera, Vector3,type Material } from 'three';
import Avatar from './Avatar';
import { firstHit, moveCircle,moveCamera } from './collisions';
import { CAMERA, movementVector, type PlayerRuntime } from './navigation';

export default function Player({runtime,contact}:{runtime:PlayerRuntime;contact:Material}) {
  const {gl,camera,invalidate}=useThree(); const actor=useRef<Group>(null);
  const keys=useRef(new Set<string>()),snap=useRef(-1),drag=useRef(false);
  const target=useRef(new Vector3()), desired=useRef(new Vector3());
  useEffect(()=>{
    runtime.invalidate=invalidate;
    const canvas=gl.domElement;canvas.tabIndex=0;canvas.setAttribute('aria-label','Oficina 3D. WASD para caminar, botón derecho y ratón para mirar, rueda para zoom.');
    if(document.activeElement===document.body)canvas.focus({preventScroll:true});
    const timer=setInterval(()=>{if(!document.hidden&&runtime.mode==='play'&&!runtime.paused)invalidate();},50);
    const down=(e:KeyboardEvent)=>{if(document.activeElement!==canvas||runtime.paused||runtime.mode!=='play')return;if(['KeyW','KeyA','KeyS','KeyD','ArrowLeft','ArrowRight','ShiftLeft'].includes(e.code)){e.preventDefault();keys.current.add(e.code);}if(e.code==='Escape'){keys.current.clear();drag.current=false;}};
    const up=(e:KeyboardEvent)=>keys.current.delete(e.code);
    const pointer=(e:PointerEvent)=>{if(runtime.mode!=='play'||runtime.paused)return;canvas.focus();if(e.button===2){drag.current=true;canvas.setPointerCapture(e.pointerId);}};
    const move=(e:PointerEvent)=>{if(drag.current&&!runtime.paused&&runtime.mode==='play'){runtime.cameraYaw-=e.movementX*.003;runtime.pitch=Math.max(-.4,Math.min(.6,runtime.pitch+e.movementY*.004));}};
    const release=()=>{drag.current=false;};const blur=()=>{keys.current.clear();drag.current=false;};
    const wheel=(e:WheelEvent)=>{if(runtime.mode==='play'&&!runtime.paused){e.preventDefault();runtime.distance=Math.max(CAMERA.minDistance,Math.min(CAMERA.maxDistance,runtime.distance+e.deltaY*.002));}};
    const context=(e:Event)=>{if(runtime.mode==='play')e.preventDefault();};
    window.addEventListener('keydown',down);window.addEventListener('keyup',up);window.addEventListener('blur',blur);
    canvas.addEventListener('pointerdown',pointer);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',release);canvas.addEventListener('lostpointercapture',release);canvas.addEventListener('wheel',wheel,{passive:false});canvas.addEventListener('contextmenu',context);
    return()=>{clearInterval(timer);window.removeEventListener('keydown',down);window.removeEventListener('keyup',up);window.removeEventListener('blur',blur);canvas.removeEventListener('pointerdown',pointer);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',release);canvas.removeEventListener('lostpointercapture',release);canvas.removeEventListener('wheel',wheel);canvas.removeEventListener('contextmenu',context);};
  },[gl,runtime,invalidate]);
  useFrame((_,delta)=>{
    if(runtime.mode!=='play'||runtime.paused){keys.current.clear();drag.current=false;runtime.speed=0;window.__HQ_PLAYER__={position:runtime.position.toArray(),yaw:runtime.yaw,cameraYaw:runtime.cameraYaw,pitch:runtime.pitch,distance:runtime.distance,speed:0,mode:runtime.mode,paused:runtime.paused,camera:camera.position.toArray()};return;}
    const dt=Math.min(delta,.05);const k=keys.current;
    runtime.cameraYaw+=(Number(k.has('ArrowLeft'))-Number(k.has('ArrowRight')))*dt*1.4;
    const v=movementVector(Number(k.has('KeyW'))-Number(k.has('KeyS')),Number(k.has('KeyD'))-Number(k.has('KeyA')),runtime.cameraYaw);
    const old=runtime.position.clone();moveCircle(runtime.position,v.x*dt*(k.has('ShiftLeft')?2.8:1.8),v.z*dt*(k.has('ShiftLeft')?2.8:1.8),runtime.colliders);
    runtime.speed=old.distanceTo(runtime.position)/dt;
    if(v.lengthSq()>.01){const heading=Math.atan2(-v.x,-v.z);const angle=Math.atan2(Math.sin(heading-runtime.yaw),Math.cos(heading-runtime.yaw));runtime.yaw+=angle*(1-Math.exp(-dt*14));}
    if(actor.current){actor.current.position.copy(runtime.position);actor.current.rotation.y=runtime.yaw+Math.PI;}
    target.current.copy(runtime.position).add(new Vector3(0,1.18,0));
    const height=Math.max(CAMERA.minHeight,Math.min(CAMERA.maxHeight,CAMERA.height+runtime.pitch));
    desired.current.set(Math.sin(runtime.cameraYaw)*runtime.distance,height,Math.cos(runtime.cameraYaw)*runtime.distance).add(runtime.position);
    // El brazo nace a la altura de la cabeza: una silla baja no debe convertir
    // una cámara elevada en cenital. La mirada permanece sobre el torso.
    const head=runtime.position.clone().add(new Vector3(0,1.78,0));
    const t=firstHit(head,desired.current,runtime.colliders,.12);
    if(t<1){desired.current.lerpVectors(head,desired.current,Math.max(.08,t-.04));desired.current.y=height;}
    if(snap.current!==runtime.revision){camera.position.copy(desired.current);snap.current=runtime.revision;}
    else {const next=camera.position.distanceTo(desired.current)<.002?desired.current.clone():camera.position.clone().lerp(desired.current,1-Math.exp(-dt*14));
      // Cerca de obstáculos, pasos menores que el diámetro de la cámara evitan
      // cortar una esquina entre dos fotogramas. El giro libre conserva respuesta.
      if(firstHit(camera.position,next,runtime.colliders,.12)<1){const step=next.clone().sub(camera.position);if(step.length()>.1)next.copy(camera.position).add(step.setLength(.1));}
      moveCamera(camera.position,next,runtime.colliders);
    }
    // La expansión de FOV conserva el cuerpo al acortar el brazo junto a una pared.
    const perspective=camera as PerspectiveCamera;const fov=t<.7?CAMERA.maxFov:CAMERA.fov;
    if(perspective.fov!==fov){perspective.fov=fov;perspective.updateProjectionMatrix();}
    camera.lookAt(target.current);
    if(k.size||drag.current)invalidate();
    window.__HQ_PLAYER__={position:runtime.position.toArray(),yaw:runtime.yaw,cameraYaw:runtime.cameraYaw,pitch:runtime.pitch,distance:runtime.distance,speed:runtime.speed,mode:runtime.mode,paused:runtime.paused,camera:camera.position.toArray()};
  },-1);
  return <group ref={actor} position={runtime.position} visible={runtime.mode==='play'}><Suspense fallback={null}><Avatar player={runtime}/></Suspense><mesh rotation={[-Math.PI/2,0,0]} position={[0,.027,0]} material={contact}><planeGeometry args={[.85,.7]}/></mesh></group>;
}
