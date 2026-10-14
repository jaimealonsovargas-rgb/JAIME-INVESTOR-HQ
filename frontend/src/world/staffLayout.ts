import type {Vec3} from './layout';
import type {Collider} from './collisions';
export interface Person {id:string;department:string;position:Vec3;yaw:number;variant:number;state:'OFFLINE';work:'NO DISPONIBLE — P4'}
export const PERSONNEL:Person[]=[
 {id:'personal-recepcion',department:'reception',position:[-.7,0,7.4],yaw:0,variant:0,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-trading-1',department:'trading',position:[-1.325,0,.58],yaw:Math.PI,variant:1,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-trading-2',department:'trading',position:[1.325,0,.58],yaw:Math.PI,variant:2,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-trading-3',department:'trading',position:[3.7,0,.1],yaw:-Math.PI/2,variant:3,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-research',department:'research',position:[-10.2,0,-10.1],yaw:Math.PI,variant:4,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-quant',department:'quant',position:[13.4,0,-10.4],yaw:Math.PI,variant:5,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-riesgos',department:'risk',position:[-8.4,0,-1.65],yaw:Math.PI,variant:6,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-ejecucion',department:'execution',position:[13.4,0,-1.65],yaw:Math.PI,variant:7,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-comite',department:'committee',position:[-2.7,0,-8.8],yaw:Math.PI/2,variant:8,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
 {id:'personal-sistemas',department:'systems',position:[13.8,0,7.75],yaw:0,variant:9,state:'OFFLINE',work:'NO DISPONIBLE — P4'},
];
export const PERSONNEL_COLLIDERS:Collider[]=PERSONNEL.map(p=>({center:[p.position[0],.91,p.position[2]],half:[.3,.91,.28],yaw:0,kind:'solid'}));
