async(page)=>{
 const goal=GOAL;
 const path=await page.evaluate((goal)=>{
   const colliders=window.__HQ_COLLIDERS__.filter(c=>c.center[1]+c.half[1]>.04&&c.center[1]-c.half[1]<1.78);
   function free(x,z){if(Math.abs(x)>16.32||Math.abs(z)>13.27)return false;return !colliders.some(c=>{const dx=x-c.center[0],dz=z-c.center[2],co=Math.cos(c.yaw),s=Math.sin(c.yaw),lx=co*dx-s*dz,lz=s*dx+co*dz;const qx=lx-Math.max(-c.half[0],Math.min(c.half[0],lx)),qz=lz-Math.max(-c.half[2],Math.min(c.half[2],lz));return qx*qx+qz*qz<.38*.38-1e-6;});}
   const w=133,h=109,step=.25,at=n=>[-16.5+n%w*step,-13.5+Math.floor(n/w)*step],node=p=>Math.round((p[0]+16.5)/step)+Math.round((p[1]+13.5)/step)*w;
   const pose=window.__HQ_PLAYER__.position,from=node([pose[0],pose[2]]),to=node(goal),parents=new Int32Array(w*h).fill(-2),q=[from];parents[from]=-1;
   for(let i=0;i<q.length&&parents[to]===-2;i++){const n=q[i];for(const next of [n-w,n+w,...(n%w?[n-1]:[]),...(n%w<w-1?[n+1]:[])]){if(next<0||next>=parents.length||parents[next]!==-2)continue;const [x,z]=at(next);if(!free(x,z))continue;parents[next]=n;q.push(next);}}
   if(parents[to]===-2)throw Error('No hay camino');const route=[];for(let n=to;n>=0;n=parents[n])route.unshift(at(n));return route.filter((p,i)=>!i||i===route.length-1||(p[0]-route[i-1][0]!==route[i+1][0]-p[0])||(p[1]-route[i-1][1]!==route[i+1][1]-p[1]));
 },goal);
 await page.locator('canvas').focus();const start=await page.evaluate(()=>window.__HQ_PLAYER__);
 for(const point of path){for(let count=0;count<40;count++){
   const p=await page.evaluate(()=>window.__HQ_PLAYER__.position);const dx=point[0]-p[0],dz=point[1]-p[2];if(Math.hypot(dx,dz)<.08)break;
   const useX=Math.abs(dx)>Math.abs(dz),key=useX?(dx>0?'KeyD':'KeyA'):(dz>0?'KeyS':'KeyW');
   const distance=useX?Math.abs(dx):Math.abs(dz);await page.keyboard.down(key);await page.waitForTimeout(Math.max(25,Math.min(800,distance/1.8*1000-12)));await page.keyboard.up(key);
   if(count===39)throw Error('Recorrido bloqueado cerca de '+point+' desde '+p);
 }}
 const end=await page.evaluate(()=>window.__HQ_PLAYER__);if(Math.hypot(end.position[0]-goal[0],end.position[2]-goal[1])>.25)throw Error('Destino no alcanzado');
 return {goal,start,end,path,transport:'WASD real, sin modificar posición'};
}
