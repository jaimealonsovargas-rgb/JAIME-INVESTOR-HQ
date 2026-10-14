async(page)=>{
 const results=[],opened=[],az=Math.atan2(2.5,20),co=Math.cos(az),si=Math.sin(az);
 await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===17,{},{timeout:30000});
 async function panel(){const d=page.getByRole('dialog');if(!await d.isVisible())return false;for(const key of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'])await page.keyboard.up(key);opened.push(await d.getByRole('heading',{level:2}).innerText());await page.keyboard.press('Escape');await page.locator('canvas').focus();return true;}
 async function walk(goal,stop=false){
  const path=await page.evaluate(goal=>{
   const cs=window.__HQ_COLLIDERS__.filter(c=>c.center[1]+c.half[1]>.04&&c.center[1]-c.half[1]<1.78);
   function free(x,z){if(Math.abs(x)>16.32||Math.abs(z)>13.27)return false;return !cs.some(c=>{const dx=x-c.center[0],dz=z-c.center[2],co=Math.cos(c.yaw),s=Math.sin(c.yaw),lx=co*dx-s*dz,lz=s*dx+co*dz,qx=lx-Math.max(-c.half[0],Math.min(c.half[0],lx)),qz=lz-Math.max(-c.half[2],Math.min(c.half[2],lz));return qx*qx+qz*qz<.39*.39;});}
   const w=133,h=109,at=n=>[-16.5+n%w*.25,-13.5+Math.floor(n/w)*.25],node=p=>Math.round((p[0]+16.5)/.25)+Math.round((p[1]+13.5)/.25)*w,p=window.__HQ_PLAYER__.position,from=node([p[0],p[2]]),to=node(goal),parents=new Int32Array(w*h).fill(-2),q=[from];parents[from]=-1;
   for(let i=0;i<q.length&&parents[to]===-2;i++){const n=q[i];for(const next of [n-w,n+w,...(n%w?[n-1]:[]),...(n%w<w-1?[n+1]:[])]){if(next<0||next>=parents.length||parents[next]!==-2)continue;const [x,z]=at(next);if(!free(x,z))continue;parents[next]=n;q.push(next);}}
   if(parents[to]===-2)throw Error('No hay recorrido '+goal);const route=[];for(let n=to;n>=0;n=parents[n])route.unshift(at(n));return route.filter((p,i)=>!i||i===route.length-1||p[0]-route[i-1][0]!==route[i+1][0]-p[0]||p[1]-route[i-1][1]!==route[i+1][1]-p[1]);
  },goal);
  await page.locator('canvas').focus();
  for(const point of path)for(let count=0;count<55;count++){
   if(await panel()&&stop)return {goal,path,end:await page.evaluate(()=>window.__HQ_PLAYER__)};
   const p=await page.evaluate(()=>window.__HQ_PLAYER__),dx=point[0]-p.position[0],dz=point[1]-p.position[2],distance=Math.hypot(dx,dz);if(distance<.19)break;
   const right=dx*co-dz*si,up=-dx*si-dz*co,keys=[];
   if(Math.abs(right)>.30*distance)keys.push(right>0?'ArrowRight':'ArrowLeft');if(Math.abs(up)>.30*distance)keys.push(up>0?'ArrowUp':'ArrowDown');
   for(const key of keys)await page.keyboard.down(key);await page.waitForTimeout(Math.max(60,Math.min(650,(distance-.08)/1.65*1000)));for(const key of keys)await page.keyboard.up(key);await page.waitForTimeout(90);
   if(count===54)throw Error('Atasco '+point+' '+JSON.stringify(await page.evaluate(()=>window.__HQ_PLAYER__)));
  }
  await panel();return{goal,path,end:await page.evaluate(()=>window.__HQ_PLAYER__)};
 }
 if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');await page.getByRole('button',{name:'Recorrer',exact:true}).click();
 const rows=[];
 await walk([5.5,4.5]);
 async function measure(id,combined){
  await page.getByRole('button',{name:'Medir FPS',exact:true}).click();await page.locator('canvas').focus();
  for(let i=0;i<(combined?3:6);i++){for(const key of combined?['ArrowLeft','ArrowRight']:['ArrowUp','ArrowDown']){await page.keyboard.down(key);await page.waitForTimeout(750);await page.keyboard.up(key);}}
  let panelOpened=false;
  if(combined){await page.keyboard.down('ArrowUp');await page.waitForTimeout(1600);await page.keyboard.up('ArrowUp');await page.getByRole('dialog').waitFor({state:'visible',timeout:5000});panelOpened=true;await page.waitForTimeout(700);await page.keyboard.press('Escape');await page.keyboard.down('ArrowDown');await page.waitForTimeout(1600);await page.keyboard.up('ArrowDown');}
  await page.waitForTimeout(3800);
  const result=await page.evaluate(()=>({at:new Date().toISOString(),metrics:window.__HQ_METRICS__,movingFrames:window.__HQ_MOVING_FRAMES__,humans:window.__HQ_HUMANS__,player:window.__HQ_PLAYER__}));if(result.metrics.movingSamples<80)throw Error('Pocas muestras '+id);rows.push({id,panelOpened,...result});
 }
 await measure('pasillo',false);await page.getByRole('button',{name:'Ir a RECEPCI\u00d3N',exact:true}).click();await page.waitForTimeout(800);await measure('recorrido-panel',true);return {rows,minimumPassed:rows.every(r=>r.metrics.movingFps>=30)};
}
