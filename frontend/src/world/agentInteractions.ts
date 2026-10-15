import { Vector3 } from 'three';
import { DEPARTMENTS } from './layout';
import { PRIMARY_PERSONNEL } from './staffLayout';
import { AGENT_APPROACHES } from './workspaces';
import { firstHit } from './collisions';
import type { PlayerRuntime } from './navigation';

export const INTERACTION={enter:2,receptionEnter:2.15,rearm:2.8} as const;
export const PRIMARY_AGENT_INTERACTIONS=PRIMARY_PERSONNEL.map(p=>({id:p.department,npcId:p.id,
 anchor:new Vector3(p.position[0],1.42,p.position[2]),approach:AGENT_APPROACHES[p.department]}));
export function departmentAt(x:number,z:number){return DEPARTMENTS.find(d=>Math.abs(x-d.center[0])<=d.size[0]/2&&Math.abs(z-d.center[2])<=d.size[1]/2)?.id;}
export function canApproach(player:PlayerRuntime,agent:typeof PRIMARY_AGENT_INTERACTIONS[number]){
 if(player.mode!=='play'||player.paused||departmentAt(player.position.x,player.position.z)!==agent.id)return false;
 if(Math.hypot(player.position.x-agent.anchor.x,player.position.z-agent.anchor.z)>(agent.id==='reception'?INTERACTION.receptionEnter:INTERACTION.enter))return false;
 const eye=player.position.clone();eye.y=1.55;
 return firstHit(eye,agent.anchor,player.colliders.filter(c=>c.agentId!==agent.npcId),.01)===1;
}
export class ProximityLatch {
 private blocked=new Set<string>();
 isBlocked(id:string){return this.blocked.has(id);}
 next(player:PlayerRuntime){
  if(player.paused||player.mode!=='play')return;
  for(const agent of PRIMARY_AGENT_INTERACTIONS)if(Math.hypot(player.position.x-agent.anchor.x,player.position.z-agent.anchor.z)>INTERACTION.rearm)this.blocked.delete(agent.id);
  const agent=PRIMARY_AGENT_INTERACTIONS.find(a=>!this.blocked.has(a.id)&&canApproach(player,a));
  if(agent){this.blocked.add(agent.id);return agent.id;}
 }
}
