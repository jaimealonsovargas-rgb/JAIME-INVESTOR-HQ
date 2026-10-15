import { DEPARTMENTS, OFFICE_FORWARD, type Vec3 } from './layout';

export interface Workspace {id:string;department:string;x:number;z:number;yaw:number;dual:boolean;occupant?:'primary'|'secondary'}
export const SEAT_OFFSET=.84;
// Coordenadas locales compartidas por mobiliario, asiento y operador.
export const WORKSPACES:Workspace[]=[
 {id:'recepcion',department:'reception',x:-.6,z:-.45,yaw:Math.PI,dual:false,occupant:'primary'},
 ...[[-1.8,-.8],[1.5,-.8],[1.5,1.4]].map(([x,z],i)=>({id:`trading-${i}`,department:'trading',x,z,yaw:0,dual:true,occupant:i===0?'primary' as const:'secondary' as const})),
 {id:'research-1',department:'research',x:-1.8,z:.4,yaw:0,dual:false,occupant:'primary'},
 {id:'research-2',department:'research',x:1.6,z:.4,yaw:0,dual:false,occupant:'secondary'},
 {id:'research-3',department:'research',x:-.2,z:-1.2,yaw:0,dual:false,occupant:'secondary'},
 ...['quant','risk'].flatMap(department=>[{id:`${department}-1`,department,x:-1.7,z:.45,yaw:0,dual:true,occupant:'primary' as const},{id:`${department}-2`,department,x:1.7,z:.45,yaw:0,dual:true,occupant:'secondary' as const}]),
 {id:'execution-1',department:'execution',x:-1.2,z:.3,yaw:0,dual:true,occupant:'primary'},
 {id:'performance',department:'performance',x:-1.3,z:-.4,yaw:0,dual:true,occupant:'primary'},
 {id:'systems-2',department:'systems',x:1.2,z:1.5,yaw:0,dual:true,occupant:'secondary'},
 {id:'systems',department:'systems',x:1.2,z:-.5,yaw:0,dual:true,occupant:'primary'},
];
export const SEAT_ANCHORS=WORKSPACES.filter(w=>w.occupant).map(w=>{
 const d=DEPARTMENTS.find(d=>d.id===w.department)!;
 return {id:`personal-${w.id}`,department:w.department,primary:w.occupant==='primary',workspace:w.id,
  position:[d.center[0]+w.x+Math.sin(w.yaw)*SEAT_OFFSET,0,d.center[2]+w.z+Math.cos(w.yaw)*SEAT_OFFSET] as Vec3,yaw:w.yaw+Math.PI};
});
SEAT_ANCHORS.push({id:'personal-comite',department:'committee',primary:true,workspace:'comite-lateral',position:[-.3,0,-1.17+OFFICE_FORWARD],yaw:Math.PI});

export const AGENT_APPROACHES:Record<string,Vec3>=Object.fromEntries(Object.entries({
 reception:[-.6,0,4.6],trading:[11.5,0,-3.2],research:[-12.5,0,-8.6],
 quant:[-.35,0,-8.55],risk:[8.65,0,-8.55],execution:[-11.8,0,5.3],
 committee:[-.3,0,-.1],performance:[12.1,0,4],systems:[-9.1,0,-2.6],
}).map(([id,p])=>[id,[p[0],0,p[2]+OFFICE_FORWARD] as Vec3]));
