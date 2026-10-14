import { Vector3 } from 'three';
import type { Collider } from './collisions';
import { isFree } from './collisions';
import type { Vec3 } from './layout';

export const CAMERA={height:3.2,minHeight:2.8,maxHeight:3.8,distance:3.8,minDistance:3,maxDistance:4.5,fov:65,minFov:60,maxFov:75} as const;
export const SAFE_SPAWNS:Record<string,Vec3>={reception:[0,0,11],trading:[0,0,3.05],committee:[.85,0,-6.15],research:[-11,0,-6.65],quant:[11,0,-6.65],risk:[-11,0,2.35],execution:[11,0,2.35],performance:[-11,0,11.7],systems:[11,0,11.5]};
export function movementVector(forward:number,strafe:number,yaw:number) {
  const vector=new Vector3(strafe,0,-forward);if(vector.lengthSq()>1)vector.normalize();return vector.applyAxisAngle(new Vector3(0,1,0),yaw);
}
export function validTeleport(id:string,colliders:Collider[]) {const p=SAFE_SPAWNS[id];return p&&isFree(p[0],p[2],colliders)?new Vector3(...p):undefined;}
export interface PlayerRuntime { position:Vector3; yaw:number; cameraYaw:number; pitch:number; distance:number; speed:number; velocity:number;angularVelocity:number;direction:number;holdCamera:boolean;paused:boolean; revision:number; mode:'play'|'inspection'; colliders:Collider[];invalidate?:()=>void }
export function createPlayer():PlayerRuntime {return {position:new Vector3(...SAFE_SPAWNS.reception),yaw:0,cameraYaw:0,pitch:0,distance:CAMERA.distance,speed:0,velocity:0,angularVelocity:0,direction:1,holdCamera:false,paused:false,revision:0,mode:'play',colliders:[]};}
export function tankStep(player:PlayerRuntime,forward:number,turn:number,dt:number) {
 const blend=1-Math.exp(-dt*10);
 player.velocity+=(forward*(forward<0?.95:1.45)-player.velocity)*blend;
 player.angularVelocity+=(turn*1.25-player.angularVelocity)*blend;
 if(Math.abs(player.velocity)<.002)player.velocity=0;
 if(Math.abs(player.angularVelocity)<.002)player.angularVelocity=0;
 player.yaw+=player.angularVelocity*dt;player.direction=player.velocity<0?-1:1;
 return movementVector(1,0,player.yaw).multiplyScalar(player.velocity*dt);
}
declare global { interface Window { __HQ_PLAYER__?:{position:number[];yaw:number;cameraYaw:number;pitch:number;distance:number;speed:number;mode:string;paused:boolean;camera:number[]}; } }
