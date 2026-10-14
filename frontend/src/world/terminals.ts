import type { Vec3 } from './layout';
import type { PlayerRuntime } from './navigation';
import { PRIMARY_AGENT_INTERACTIONS,canApproach } from './agentInteractions';
import { WORKSPACES,AGENT_APPROACHES } from './workspaces';
import { DEPARTMENTS } from './layout';

export interface MonitorDefinition {id:string;departmentId:string;label:string;position:Vec3;rotation:Vec3;anchor:Vec3;size:[number,number];phase:string;panel:string;approach:Vec3;yaw:number}
export const MONITOR_DEFINITIONS:MonitorDefinition[]=[
 {id:'reception',departmentId:'reception',label:'Recepción',position:[-.7,1.6,8.62],rotation:[-.04,0,0],anchor:[-.7,1.6,8.68],size:[.721,.405],phase:'P1',panel:'Estado de la sede',approach:[-.7,0,9.95],yaw:0},
 {id:'trading',departmentId:'trading',label:'Trading Floor',position:[.46,1.14,-2.192],rotation:[-.04,0,0],anchor:[.46,1.14,-2.14],size:[.721,.405],phase:'P3',panel:'Posiciones',approach:[1.35,0,-.5],yaw:0},
 {id:'execution',departmentId:'execution',label:'Ejecución',position:[11,1.94,-2.916],rotation:[0,0,0],anchor:[11,1.94,-2.88],size:[2.8,1.575],phase:'P6',panel:'Órdenes y reconciliación',approach:[11,0,-1.3],yaw:0},
 {id:'performance',departmentId:'performance',label:'Performance',position:[-11,1.94,6.114],rotation:[0,0,0],anchor:[-11,1.94,6.15],size:[3.8,1.575],phase:'P3',panel:'Rentabilidad y atribución',approach:[-11,0,7.2],yaw:0},
 {id:'risk',departmentId:'risk',label:'Riesgos',position:[-11,1.94,-2.916],rotation:[0,0,0],anchor:[-11,1.94,-2.88],size:[3.5,1.575],phase:'P5',panel:'Control de riesgo',approach:[-11,0,-1.3],yaw:0},
 {id:'research',departmentId:'research',label:'Research',position:[-13,1.14,-8.612],rotation:[-.04,0,0],anchor:[-13,1.14,-8.55],size:[.721,.405],phase:'P4',panel:'Dossiers de inversión',approach:[-11.75,0,-7.1],yaw:0},
 {id:'committee',departmentId:'committee',label:'Comité de Inversión',position:[0,1.94,-11.976],rotation:[0,0,0],anchor:[1.1,1.94,-11.94],size:[2.8,1.575],phase:'P4',panel:'Decisiones y actas',approach:[2.5,0,-11.4],yaw:1.2},
 {id:'quant',departmentId:'quant',label:'Quant Lab',position:[11,1.94,-11.916],rotation:[0,0,0],anchor:[11,1.94,-11.88],size:[2.8,1.575],phase:'P5',panel:'Estrategias y backtests',approach:[11,0,-10.3],yaw:0},
 {id:'systems',departmentId:'systems',label:'Sistemas',position:[11.14,1.14,9.508],rotation:[-.04,0,0],anchor:[11.14,1.14,9.57],size:[.721,.405],phase:'P2',panel:'Sistemas y calidad de datos',approach:[10.5,0,10.85],yaw:0},
];
for(const m of MONITOR_DEFINITIONS){
 m.approach=AGENT_APPROACHES[m.id];
 const agent=PRIMARY_AGENT_INTERACTIONS.find(a=>a.id===m.id)!;
 m.yaw=Math.atan2(m.approach[0]-agent.anchor.x,m.approach[2]-agent.anchor.z);
 const w=WORKSPACES.find(w=>w.department===m.id&&w.occupant==='primary');
 if(w){const d=DEPARTMENTS.find(d=>d.id===m.id)!;m.position=[d.center[0]+w.x+(w.dual?.46:0),1.18,d.center[2]+w.z-(w.dual?.26:.23)+.018];m.anchor=[m.position[0],m.position[1],m.position[2]+.06];}
}
export function canInteract(player:PlayerRuntime,monitor:MonitorDefinition){return canApproach(player,PRIMARY_AGENT_INTERACTIONS.find(a=>a.id===monitor.id)!);}
