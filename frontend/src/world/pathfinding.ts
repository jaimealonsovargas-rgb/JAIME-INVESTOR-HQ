import {isFree,type Collider} from './collisions';
/** Diagnóstico de accesibilidad: rejilla conservadora, no mueve al jugador. */
export function findWalkingPath(start:[number,number],goal:[number,number],colliders:Collider[]) {
  const step=.25,width=133,height=109,originX=-16.5,originZ=-13.5;
  const at=(index:number):[number,number]=>[originX+(index%width)*step,originZ+Math.floor(index/width)*step];
  const node=(p:[number,number])=>Math.round((p[0]-originX)/step)+Math.round((p[1]-originZ)/step)*width;
  const from=node(start),to=node(goal),parent=new Int32Array(width*height).fill(-2),queue=[from];parent[from]=-1;
  for(let i=0;i<queue.length&&parent[to]===-2;i++) {
    const n=queue[i];for(const next of [n-width,n+width,...(n%width?[n-1]:[]),...(n%width<width-1?[n+1]:[])]) {
      if(next<0||next>=parent.length||parent[next]!==-2)continue;
      const [x,z]=at(next);if(!isFree(x,z,colliders,.38))continue;parent[next]=n;queue.push(next);
    }
  }
  if(parent[to]===-2)return undefined;
  const path:[number,number][]=[];for(let n=to;n>=0;n=parent[n])path.unshift(at(n));
  const turns=path.filter((p,i)=>!i||i===path.length-1||(p[0]-path[i-1][0]!==path[i+1][0]-p[0])||(p[1]-path[i-1][1]!==path[i+1][1]-p[1]));
  return turns;
}
