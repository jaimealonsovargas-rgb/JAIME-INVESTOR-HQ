import {Suspense,memo} from 'react';
import type {Material} from 'three';
import Avatar from './Avatar';
import {PERSONNEL} from './staffLayout';
import {Html} from '@react-three/drei';
const TEAM:Record<string,string>={research:'research',quant:'quant',trading:'trading_execution',execution:'trading_execution',risk:'risk',performance:'performance',systems:'systems_data',committee:'committee'};
export default memo(function Personnel({contact,states,onOpen}:{contact:Material;states?:Record<string,string>;onOpen:(id:string)=>void}) {
 return <group name="personal-offline"><Suspense fallback={null}>{PERSONNEL.map(p=><group key={p.id} name={p.id} position={p.position} rotation={[0,p.yaw,0]} onClick={event=>{if(event.button!==0)return;event.stopPropagation();document.body.style.cursor='';onOpen(p.department);}} onPointerOver={event=>{event.stopPropagation();document.body.style.cursor='pointer';}} onPointerOut={()=>{document.body.style.cursor='';}}><mesh name={`npc-hit:${p.id}`} position={[0,1.05,0]}><capsuleGeometry args={[.3,.8,2,6]}/><meshBasicMaterial visible={false}/></mesh><group scale={1+(p.variant%3-1)*.015}><Avatar id={p.id} variant={p.variant} npc contact={contact}/></group>{p.primary&&states?.[TEAM[p.department]]?<Html position={[0,1.85,0]} center zIndexRange={[4,0]} style={{pointerEvents:'none'}}><span style={{fontSize:12,color:'#e0cca4',background:'#101e26ee',padding:'3px 7px',whiteSpace:'nowrap'}}>{states[TEAM[p.department]]}</span></Html>:null}</group>)}</Suspense></group>;
});
