import { Vector3 } from 'three';
import type { Vec3 } from './layout';

export interface Collider { center: Vec3; half: Vec3; yaw: number; kind: 'glass' | 'solid';agentId?:string }
export const PLAYER_RADIUS=.35;
export const PLAYER_HEIGHT=1.78;
function local(x:number,z:number,c:Collider) {const dx=x-c.center[0],dz=z-c.center[2],s=Math.sin(c.yaw),co=Math.cos(c.yaw);return [co*dx-s*dz,s*dx+co*dz];}
function world(x:number,z:number,c:Collider) {const s=Math.sin(c.yaw),co=Math.cos(c.yaw);return [co*x+s*z,-s*x+co*z];}
export function isFree(x:number,z:number,colliders:Collider[],radius=PLAYER_RADIUS) {
  if(Math.abs(x)>16.7-radius||Math.abs(z)>13.65-radius)return false;
  return !colliders.some(c=>{
    if(c.center[1]+c.half[1]<=.04||c.center[1]-c.half[1]>=PLAYER_HEIGHT)return false;
    const [lx,lz]=local(x,z,c);const dx=lx-Math.max(-c.half[0],Math.min(c.half[0],lx)),dz=lz-Math.max(-c.half[2],Math.min(c.half[2],lz));
    return dx*dx+dz*dz<radius*radius-1e-6;
  });
}
export function moveCircle(position:Vector3,dx:number,dz:number,colliders:Collider[],radius=PLAYER_RADIUS,vertical:[number,number]=[.04,PLAYER_HEIGHT],bounded=true) {
  const steps=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.12));
  for(let step=0;step<steps;step++) {
    position.x+=dx/steps;position.z+=dz/steps;
    for(let pass=0;pass<3;pass++) for(const c of colliders) {
      if(c.center[1]+c.half[1]<=vertical[0]||c.center[1]-c.half[1]>=vertical[1])continue;
      const [x,z]=local(position.x,position.z,c);const hx=c.half[0],hz=c.half[2];
      const qx=Math.max(-hx,Math.min(hx,x)),qz=Math.max(-hz,Math.min(hz,z));let vx=x-qx,vz=z-qz;const distance=Math.hypot(vx,vz);
      if(distance>=radius)continue;
      if(distance>1e-7){vx*= (radius-distance)/distance;vz*= (radius-distance)/distance;}
      else {const toX=hx-Math.abs(x),toZ=hz-Math.abs(z);if(toX<toZ){vx=(x>=0?1:-1)*(toX+radius);vz=0;}else{vz=(z>=0?1:-1)*(toZ+radius);vx=0;}}
      const [wx,wz]=world(vx,vz,c);position.x+=wx;position.z+=wz;
    }
    if(bounded){position.x=Math.max(-16.7+radius,Math.min(16.7-radius,position.x));position.z=Math.max(-13.65+radius,Math.min(13.65-radius,position.z));}
  }
  if(bounded)position.y=0;
}
/** Barrido y deslizamiento de cámara después del suavizado; sin límites del jugador. */
export function moveCamera(position:Vector3,target:Vector3,colliders:Collider[]) {
  const oldY=position.y;
  moveCircle(position,target.x-position.x,target.z-position.z,colliders,.12,[Math.min(oldY,target.y)-.12,Math.max(oldY,target.y)+.12],false);
  position.y=target.y;
  if(position.distanceTo(target)<1e-7)position.copy(target);
}
/** Segmento vs OBB con altura; válido para cámara y línea de visión de terminales. */
export function firstHit(from:Vector3,to:Vector3,colliders:Collider[],margin=.08) {
  let closest=1;
  const minY=Math.min(from.y,to.y),maxY=Math.max(from.y,to.y);
  for(const c of colliders) {
    // Broadphase vertical: no cambiar el resultado del raycast, evitar mesas,
    // asientos y objetos bajos en las comprobaciones de la cámara elevada.
    if(maxY<c.center[1]-c.half[1]-margin||minY>c.center[1]+c.half[1]+margin)continue;
    const aXZ=local(from.x,from.z,c),bXZ=local(to.x,to.z,c);
    const a=[aXZ[0],from.y-c.center[1],aXZ[1]],b=[bXZ[0],to.y-c.center[1],bXZ[1]];
    let lo=0,hi=1;
    for(let axis=0;axis<3;axis++) {
      const half=c.half[axis]+margin,d=b[axis]-a[axis];
      if(Math.abs(d)<1e-8){if(Math.abs(a[axis])>half){hi=-1;break;}}
      else {const one=(-half-a[axis])/d,two=(half-a[axis])/d;lo=Math.max(lo,Math.min(one,two));hi=Math.min(hi,Math.max(one,two));}
    }
    if(lo<=hi&&hi>=0&&lo<=1)closest=Math.min(closest,Math.max(0,lo));
  }
  return closest;
}
