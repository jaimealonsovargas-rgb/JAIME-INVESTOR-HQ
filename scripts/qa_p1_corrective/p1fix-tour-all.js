async(page)=>{const walk=async(page,goal,stopOnPanel=false)=>{
 const path=await page.evaluate(goal=>{
  const colliders=window.__HQ_COLLIDERS__.filter(c=>c.center[1]+c.half[1]>.04&&c.center[1]-c.half[1]<1.78);
  function free(x,z){if(Math.abs(x)>16.32||Math.abs(z)>13.27)return false;return !colliders.some(c=>{const dx=x-c.center[0],dz=z-c.center[2],co=Math.cos(c.yaw),s=Math.sin(c.yaw),lx=co*dx-s*dz,lz=s*dx+co*dz,qx=lx-Math.max(-c.half[0],Math.min(c.half[0],lx)),qz=lz-Math.max(-c.half[2],Math.min(c.half[2],lz));return qx*qx+qz*qz<.38*.38-1e-6;});}
  const w=133,h=109,at=n=>[-16.5+n%w*.25,-13.5+Math.floor(n/w)*.25],node=p=>Math.round((p[0]+16.5)/.25)+Math.round((p[1]+13.5)/.25)*w,p=window.__HQ_PLAYER__.position,from=node([p[0],p[2]]),to=node(goal),parents=new Int32Array(w*h).fill(-2),q=[from];parents[from]=-1;
  for(let i=0;i<q.length&&parents[to]===-2;i++){const n=q[i];for(const next of [n-w,n+w,...(n%w?[n-1]:[]),...(n%w<w-1?[n+1]:[])]){if(next<0||next>=parents.length||parents[next]!==-2)continue;const [x,z]=at(next);if(!free(x,z))continue;parents[next]=n;q.push(next);}}
  if(parents[to]===-2)throw Error('No hay recorrido');const route=[];for(let n=to;n>=0;n=parents[n])route.unshift(at(n));return route.filter((p,i)=>!i||i===route.length-1||p[0]-route[i-1][0]!==route[i+1][0]-p[0]||p[1]-route[i-1][1]!==route[i+1][1]-p[1]);
 },goal);
 const start=await page.evaluate(()=>window.__HQ_PLAYER__),opened=[];
 async function modal(){if(!(await page.getByRole('dialog').isVisible()))return false;await page.keyboard.up('ArrowUp');await page.keyboard.up('ArrowLeft');await page.keyboard.up('ArrowRight');const title=await page.getByRole('dialog').getByRole('heading',{level:2}).innerText();opened.push(title);if(!stopOnPanel){await page.keyboard.press('Escape');await page.waitForTimeout(100);}return true;}
 await page.locator('canvas').focus();
 for(const point of path)for(let count=0;count<60;count++){
  if(await modal()){if(stopOnPanel)return{goal,start,end:await page.evaluate(()=>window.__HQ_PLAYER__),path,opened,input:'Flechas reales'};}
  let pose=await page.evaluate(()=>window.__HQ_PLAYER__);let dx=point[0]-pose.position[0],dz=point[1]-pose.position[2];if(Math.hypot(dx,dz)<.12)break;
  const heading=Math.atan2(-dx,-dz);
  for(let turn=0;turn<30;turn++){
   pose=await page.evaluate(()=>window.__HQ_PLAYER__);const error=Math.atan2(Math.sin(heading-pose.yaw),Math.cos(heading-pose.yaw));if(Math.abs(error)<.04)break;
   const key=error>0?'ArrowLeft':'ArrowRight';await page.keyboard.down(key);await page.waitForTimeout(Math.max(25,Math.min(500,Math.abs(error)/1.25*1000-90)));await page.keyboard.up(key);await page.waitForTimeout(180);
  }
  pose=await page.evaluate(()=>window.__HQ_PLAYER__);const distance=Math.hypot(point[0]-pose.position[0],point[1]-pose.position[2]);
  await page.keyboard.down('ArrowUp');await page.waitForTimeout(Math.max(30,Math.min(700,distance/1.45*1000-50)));await page.keyboard.up('ArrowUp');await page.waitForTimeout(160);
  if(count===59)throw Error('Recorrido bloqueado: '+point+' / '+JSON.stringify(await page.evaluate(()=>window.__HQ_PLAYER__)));
 }
 if(await modal()){if(stopOnPanel)return{goal,start,end:await page.evaluate(()=>window.__HQ_PLAYER__),path,opened,input:'Flechas reales'};}
 const end=await page.evaluate(()=>window.__HQ_PLAYER__);if(Math.hypot(end.position[0]-goal[0],end.position[2]-goal[1])>.3)throw Error('Destino no alcanzado');return{goal,start,end,path,opened,input:'Flechas reales'};
},cases=[['reception', [1.65, 10.3]], ['systems', [11, 9.3]], ['execution', [10.55, 1.3]], ['quant', [10.55, -7.6]], ['committee', [-3.35, -9.3]], ['research', [-11.45, -7.4]], ['risk', [-11.45, 1.3]], ['performance', [-10.75, 9.5]], ['trading', [-1, -1.16]]];await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===11);await page.evaluate(()=>{window.__HQ_QA_TOUR__=[];});const start=await page.evaluate(()=>window.__HQ_PLAYER__);for(const [id,goal] of cases){const trace=await walk(page,goal,false);await page.screenshot({path:'docs/evidencias/P1_CORRECTIVO/final-'+id+'.png'});await page.evaluate(row=>window.__HQ_QA_TOUR__.push(row),{id,...trace});}return {start,steps:await page.evaluate(()=>window.__HQ_QA_TOUR__),humans:await page.evaluate(()=>window.__HQ_HUMANS__),recorded_at:new Date().toISOString()};}