import { useEffect, useRef } from 'react';
import { useFrame,useThree } from '@react-three/fiber';
import {Vector3} from 'three';
import { MONITOR_DEFINITIONS,canInteract } from './terminals';
import type {PlayerRuntime} from './navigation';

export default function Monitors({player,onOpen,onNear}:{player:PlayerRuntime;onOpen:(id:string)=>void;onNear:(id:string|undefined)=>void}) {
 const {camera,size}=useThree();
 const near=useRef<string>(undefined),last=useRef(0);
 useFrame(()=>{const now=performance.now();if(now-last.current<120)return;last.current=now;const id=MONITOR_DEFINITIONS.find(m=>canInteract(player,m))?.id;if(id!==near.current){near.current=id;onNear(id);}window.__HQ_TERMINALS__=MONITOR_DEFINITIONS.map(m=>{const p=new Vector3(...m.position).project(camera);return {id:m.id,x:(p.x+1)*size.width/2,y:(1-p.y)*size.height/2,visible:p.z<1&&p.z>-1&&Math.abs(p.x)<1&&Math.abs(p.y)<1,accessible:canInteract(player,m)};});});
 useEffect(()=>{const key=(e:KeyboardEvent)=>{if(e.code!=='KeyE'||e.repeat||document.activeElement?.tagName!=='CANVAS')return;const monitor=MONITOR_DEFINITIONS.find(m=>m.id===near.current);if(monitor&&canInteract(player,monitor)){e.preventDefault();onOpen(monitor.id);}};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);},[player,onOpen]);
 return <>{MONITOR_DEFINITIONS.map(m=><mesh key={m.id} name={`terminal:${m.id}`} position={m.position} rotation={m.rotation} onClick={e=>{e.stopPropagation();if(canInteract(player,m))onOpen(m.id);}}><planeGeometry args={m.size}/><meshBasicMaterial visible={false}/></mesh>)}</>;
}
declare global {interface Window {__HQ_TERMINALS__?:{id:string;x:number;y:number;visible:boolean;accessible:boolean}[]}}
