import { Vector3 } from 'three';
import type { Collider } from './collisions';
import { isFree } from './collisions';
import { DEPARTMENTS,OFFICE_FORWARD,type Vec3 } from './layout';

export const ISOMETRIC={offset:[0,21.5,18] as const, lookAhead:9.5, azimuth:0, fov:50};
export const WALK_SPEED=2.05;
export const CAMERA={height:3.2,minHeight:2.8,maxHeight:3.8,distance:3.8,minDistance:3,maxDistance:4.5,fov:65,minFov:60,maxFov:75} as const;
export const SAFE_SPAWNS:Record<string,Vec3>=Object.fromEntries(DEPARTMENTS.map(d=>[d.id,[d.center[0],0,d.center[2]+d.size[1]/2+.55] as Vec3]));
SAFE_SPAWNS.reception=[0,0,13.1];
SAFE_SPAWNS.committee=[-4,0,-2.2+OFFICE_FORWARD];
SAFE_SPAWNS.trading=[7,0,-3.2+OFFICE_FORWARD];
SAFE_SPAWNS.performance=[7,0,4+OFFICE_FORWARD];
SAFE_SPAWNS.systems=[-7,0,-2.6+OFFICE_FORWARD];
SAFE_SPAWNS.execution=[-7,0,4.4+OFFICE_FORWARD];
export function movementVector(forward:number,strafe:number,yaw:number) {
  const vector=new Vector3(strafe,0,-forward);if(vector.lengthSq()>1)vector.normalize();return vector.applyAxisAngle(new Vector3(0,1,0),yaw);
}
export function validTeleport(id:string,colliders:Collider[]) {const p=SAFE_SPAWNS[id];return p&&isFree(p[0],p[2],colliders)?new Vector3(...p):undefined;}
export interface PlayerRuntime { position:Vector3; yaw:number; cameraYaw:number; pitch:number; distance:number; speed:number; velocity:number;angularVelocity:number;direction:number;holdCamera:boolean;paused:boolean; revision:number; mode:'play'|'inspection'; colliders:Collider[];invalidate?:()=>void }
export function createPlayer():PlayerRuntime {return {position:new Vector3(...SAFE_SPAWNS.reception),yaw:0,cameraYaw:0,pitch:0,distance:CAMERA.distance,speed:0,velocity:0,angularVelocity:0,direction:1,holdCamera:false,paused:false,revision:0,mode:'play',colliders:[]};}
/** Las flechas usan la base fija proyectada de la cámara; nunca giran en vacío. */
export function screenStep(player:PlayerRuntime,forward:number,right:number,dt:number) {
 const axis=movementVector(forward,right,ISOMETRIC.azimuth);
 const active=axis.lengthSq()>0,blend=1-Math.exp(-dt*12);
 player.velocity+=((active?WALK_SPEED:0)-player.velocity)*blend;
 if(player.velocity<.002)player.velocity=0;
 player.direction=1;player.angularVelocity=0;
 if(active){const desired=Math.atan2(-axis.x,-axis.z);const error=Math.atan2(Math.sin(desired-player.yaw),Math.cos(desired-player.yaw));player.angularVelocity=error*10;player.yaw+=error*(1-Math.exp(-dt*10));}
 return active?axis.multiplyScalar(player.velocity*dt):new Vector3();
}
declare global { interface Window { __HQ_PLAYER__?:{position:number[];yaw:number;cameraYaw:number;pitch:number;distance:number;speed:number;mode:string;paused:boolean;camera:number[]}; } }
