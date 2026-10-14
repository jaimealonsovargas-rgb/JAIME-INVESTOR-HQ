import { DEPARTMENTS, type Vec3 } from './layout';

export interface Workspace {id:string;department:string;x:number;z:number;yaw:number;dual:boolean;occupant?:'primary'|'secondary'}
export const SEAT_OFFSET=.84;
// Coordenadas locales compartidas por mobiliario, asiento y operador.
export const WORKSPACES:Workspace[]=[
 {id:'recepcion',department:'reception',x:3.05,z:-.3,yaw:0,dual:false,occupant:'primary'},
 ...[-2.65,2.65].flatMap((x,column)=>[-2,0,2].map((z,row)=>({id:`trading-${column}-${row}`,department:'trading',x,z,yaw:0,dual:true,occupant:row===0?(column===0?'primary':'secondary') as 'primary'|'secondary':undefined}))),
 {id:'research-1',department:'research',x:-2,z:.6,yaw:0,dual:false,occupant:'primary'},
 {id:'research-2',department:'research',x:1.5,z:.6,yaw:0,dual:false},
 ...['quant','risk','execution'].flatMap(department=>[{id:`${department}-1`,department,x:-2,z:.15,yaw:0,dual:true,occupant:'primary' as const},{id:`${department}-2`,department,x:1.5,z:.15,yaw:0,dual:true}]),
 {id:'performance',department:'performance',x:-1.3,z:-.4,yaw:0,dual:true,occupant:'primary'},
 {id:'systems',department:'systems',x:1.55,z:-.6,yaw:0,dual:true,occupant:'primary'},
];
export const SEAT_ANCHORS=WORKSPACES.filter(w=>w.occupant).map(w=>{
 const d=DEPARTMENTS.find(d=>d.id===w.department)!;
 return {id:`personal-${w.id}`,department:w.department,primary:w.occupant==='primary',workspace:w.id,
  position:[d.center[0]+w.x+Math.sin(w.yaw)*SEAT_OFFSET,0,d.center[2]+w.z+Math.cos(w.yaw)*SEAT_OFFSET] as Vec3,yaw:w.yaw+Math.PI};
});
SEAT_ANCHORS.push({id:'personal-comite',department:'committee',primary:true,workspace:'comite-lateral',position:[-1.83,0,-9.3],yaw:Math.PI/2});

export const AGENT_APPROACHES:Record<string,Vec3>={
 reception:[1.65,0,10.3],trading:[-1,0,-1.16],research:[-11.45,0,-7.4],
 quant:[10.55,0,-7.6],risk:[-11.45,0,1.3],execution:[10.55,0,1.3],
 committee:[-3.35,0,-9.3],performance:[-10.75,0,9.5],systems:[11,0,9.3],
};
