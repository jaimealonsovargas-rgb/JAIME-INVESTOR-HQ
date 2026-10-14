import { useRef } from 'react';
import { useFrame,useThree } from '@react-three/fiber';
import {Vector3} from 'three';
import { MONITOR_DEFINITIONS,canInteract } from './terminals';
import type {PlayerRuntime} from './navigation';
import { PRIMARY_AGENT_INTERACTIONS,ProximityLatch } from './agentInteractions';

export default function Monitors({player,onOpen,onNear}:{player:PlayerRuntime;onOpen:(id:string)=>void;onNear:(id:string|undefined)=>void}) {
 const {camera,size}=useThree();
 const near=useRef<string>(undefined),last=useRef(0),latch=useRef(new ProximityLatch());
 useFrame(()=>{const now=performance.now();if(now-last.current<120)return;last.current=now;const id=MONITOR_DEFINITIONS.find(m=>!latch.current.isBlocked(m.id)&&canInteract(player,m))?.id;if(id!==near.current){near.current=id;onNear(id);}window.__HQ_TERMINALS__=MONITOR_DEFINITIONS.map(m=>{const p=new Vector3(...m.position).project(camera);return {id:m.id,x:(p.x+1)*size.width/2,y:(1-p.y)*size.height/2,visible:p.z<1&&p.z>-1&&Math.abs(p.x)<1&&Math.abs(p.y)<1,accessible:canInteract(player,m)};});});
 useFrame(()=>{const id=latch.current.next(player);if(id)onOpen(id);window.__HQ_AGENT_INTERACTIONS__=PRIMARY_AGENT_INTERACTIONS.map(a=>({id:a.id,npcId:a.npcId,anchor:a.anchor.toArray(),approach:a.approach,blocked:latch.current.isBlocked(a.id)}));});
 return <>{MONITOR_DEFINITIONS.map(m=><mesh key={m.id} name={`terminal:${m.id}`} position={m.position} rotation={m.rotation}><planeGeometry args={m.size}/><meshBasicMaterial visible={false}/></mesh>)}</>;
}
declare global {interface Window {__HQ_TERMINALS__?:{id:string;x:number;y:number;visible:boolean;accessible:boolean}[]}}
declare global {interface Window {__HQ_AGENT_INTERACTIONS__?:{id:string;npcId:string;anchor:number[];approach:number[];blocked:boolean}[]}}
