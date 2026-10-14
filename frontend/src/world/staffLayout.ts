import type {Vec3} from './layout';
import type {Collider} from './collisions';
import {SEAT_ANCHORS} from './workspaces';
export interface Person {id:string;department:string;position:Vec3;yaw:number;variant:number;primary:boolean;workspace:string;seated:true;state:'OFFLINE';work:'NO DISPONIBLE \u2014 P4'}
export const PERSONNEL:Person[]=SEAT_ANCHORS.map((s,variant)=>({...s,variant,seated:true,state:'OFFLINE',work:'NO DISPONIBLE \u2014 P4'}));
export const PRIMARY_PERSONNEL=PERSONNEL.filter(p=>p.primary);
export const PERSONNEL_COLLIDERS:Collider[]=PERSONNEL.map(p=>({center:[p.position[0],.72,p.position[2]],half:[.30,.72,.32],yaw:p.yaw,kind:'solid',agentId:p.id}));
