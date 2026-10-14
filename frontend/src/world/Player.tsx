import { Suspense, useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Group, PerspectiveCamera, Vector3,type Material } from 'three';
import Avatar from './Avatar';
import { firstHit, moveCircle,moveCamera } from './collisions';
import { CAMERA, tankStep, type PlayerRuntime } from './navigation';

export default function Player({runtime,contact}:{runtime:PlayerRuntime;contact:Material}) {
  const {gl,camera,invalidate}=useThree(); const actor=useRef<Group>(null);
  const keys=useRef(new Set<string>()),snap=useRef(-1);
  const target=useRef(new Vector3()), desired=useRef(new Vector3());
  useEffect(()=>{
    runtime.invalidate=invalidate;
    const canvas=gl.domElement;canvas.tabIndex=0;canvas.setAttribute('aria-label','Oficina 3D. Flechas arriba y abajo para caminar; izquierda y derecha para girar. Cámara automática.');
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
    const v=tankStep(runtime,Number(k.has('ArrowUp'))-Number(k.has('ArrowDown')),Number(k.has('ArrowLeft'))-Number(k.has('ArrowRight')),dt);
    const old=runtime.position.clone();moveCircle(runtime.position,v.x,v.z,runtime.colliders);
    runtime.speed=old.distanceTo(runtime.position)/dt;
    runtime.cameraYaw+=Math.atan2(Math.sin(runtime.yaw-runtime.cameraYaw),Math.cos(runtime.yaw-runtime.cameraYaw))*(1-Math.exp(-dt*7));
    if(actor.current){actor.current.position.copy(runtime.position);actor.current.rotation.y=runtime.yaw+Math.PI;}
    target.current.copy(runtime.position).add(new Vector3(0,1.18,0));
    const height=Math.max(CAMERA.minHeight,Math.min(CAMERA.maxHeight,CAMERA.height+runtime.pitch));
    desired.current.set(Math.sin(runtime.cameraYaw)*runtime.distance,height,Math.cos(runtime.cameraYaw)*runtime.distance).add(runtime.position);
    // El brazo nace a la altura de la cabeza: una silla baja no debe convertir
    // una cámara elevada en cenital. La mirada permanece sobre el torso.
    const head=runtime.position.clone().add(new Vector3(0,1.78,0));
    const cameraObstacles=runtime.colliders.filter(c=>c.kind!=='glass'||c.center[1]+c.half[1]>=CAMERA.minHeight-.15);
    let t=firstHit(head,desired.current,cameraObstacles,.12);
    // Si el respaldo deseado queda ocluido, buscar un ángulo posterior libre.
    if(t<.72){for(const offset of [.45,-.45,.9,-.9]){const candidate=new Vector3(Math.sin(runtime.cameraYaw+offset)*runtime.distance,height,Math.cos(runtime.cameraYaw+offset)*runtime.distance).add(runtime.position);const hit=firstHit(head,candidate,cameraObstacles,.12);if(hit>t+.1){desired.current.copy(candidate);t=hit;}if(t>.9)break;}}
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
    if(k.size||Math.abs(runtime.velocity)>.002||Math.abs(runtime.angularVelocity)>.002)invalidate();
    window.__HQ_PLAYER__={position:runtime.position.toArray(),yaw:runtime.yaw,cameraYaw:runtime.cameraYaw,pitch:runtime.pitch,distance:runtime.distance,speed:runtime.speed,mode:runtime.mode,paused:runtime.paused,camera:camera.position.toArray()};
  },-1);
  return <group ref={actor} position={runtime.position} visible={runtime.mode==='play'}><Suspense fallback={null}><Avatar player={runtime}/></Suspense><mesh rotation={[-Math.PI/2,0,0]} position={[0,.027,0]} material={contact}><planeGeometry args={[.85,.7]}/></mesh></group>;
}
