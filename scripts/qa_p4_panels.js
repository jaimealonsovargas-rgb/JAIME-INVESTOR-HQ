async(page)=>{
 await page.bringToFront();const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:true});
 const co=1,si=0;
 async function panel(){if(!await page.getByRole('dialog').isVisible())return false;for(const key of ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'])await page.keyboard.up(key);return await page.getByRole('dialog').getByRole('heading',{level:2}).innerText();}
 async function walk(goal,stop=false){
  const path=await page.evaluate(goal=>{
   const cs=window.__HQ_COLLIDERS__.filter(c=>c.center[1]+c.half[1]>.04&&c.center[1]-c.half[1]<1.78);
   function free(x,z){if(Math.abs(x)>16.32||Math.abs(z)>13.27)return false;return !cs.some(c=>{const dx=x-c.center[0],dz=z-c.center[2],co=Math.cos(c.yaw),s=Math.sin(c.yaw),lx=co*dx-s*dz,lz=s*dx+co*dz,qx=lx-Math.max(-c.half[0],Math.min(c.half[0],lx)),qz=lz-Math.max(-c.half[2],Math.min(c.half[2],lz));return qx*qx+qz*qz<.39*.39;});}
   const w=133,h=109,at=n=>[-16.5+n%w*.25,-13.5+Math.floor(n/w)*.25],node=p=>Math.round((p[0]+16.5)/.25)+Math.round((p[1]+13.5)/.25)*w,p=window.__HQ_PLAYER__.position,from=node([p[0],p[2]]),to=node(goal),parents=new Int32Array(w*h).fill(-2),q=[from];parents[from]=-1;
   for(let i=0;i<q.length&&parents[to]===-2;i++){const n=q[i];for(const next of [n-w,n+w,...(n%w?[n-1]:[]),...(n%w<w-1?[n+1]:[])]){if(next<0||next>=parents.length||parents[next]!==-2)continue;const [x,z]=at(next);if(!free(x,z))continue;parents[next]=n;q.push(next);}}
   if(parents[to]===-2)throw Error('No hay recorrido '+goal);const route=[];for(let n=to;n>=0;n=parents[n])route.unshift(at(n));return [...route.filter((p,i)=>!i||i===route.length-1||p[0]-route[i-1][0]!==route[i+1][0]-p[0]||p[1]-route[i-1][1]!==route[i+1][1]-p[1]),goal];
  },goal);
  await page.locator('canvas').focus();
  for(const point of path)for(let count=0;count<55;count++){
   const visibleTitle=await panel();if(stop&&visibleTitle===stop)return {goal,path,end:await page.evaluate(()=>window.__HQ_PLAYER__)};
   const p=await page.evaluate(()=>window.__HQ_PLAYER__),dx=point[0]-p.position[0],dz=point[1]-p.position[2],distance=Math.hypot(dx,dz);if(distance<(point===path.at(-1) ? .06 : .19))break;
   const right=dx*co-dz*si,up=-dx*si-dz*co,keys=[];
   if(Math.abs(right)>.30*distance)keys.push(right>0?'ArrowRight':'ArrowLeft');if(Math.abs(up)>.30*distance)keys.push(up>0?'ArrowUp':'ArrowDown');
   for(const key of keys)await page.keyboard.down(key);await page.waitForTimeout(Math.max(60,Math.min(650,(distance-.015)/2.05*1000)));for(const key of keys)await page.keyboard.up(key);await page.waitForTimeout(90);
   if(count===54)throw Error('Atasco '+point+' '+JSON.stringify(await page.evaluate(()=>window.__HQ_PLAYER__)));
  }
  return{goal,path,end:await page.evaluate(()=>window.__HQ_PLAYER__)};
 }

 const results=[];
 for(const [id,label,title,focus] of [['research','RESEARCH','Dossiers de inversión','Bull · argumentos a favor'],['quant','QUANT LAB','Estrategias y backtests','Quant / tendencia'],['committee','COMITÉ DE INVERSIÓN','Decisiones y actas','Chair · síntesis y desacuerdos'],['systems','SISTEMAS','Sistemas y calidad de datos',null]]){
  if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Recorrer',exact:true}).click();
  const open=page.getByRole('button',{name:'Abrir cartera',exact:true});if(await open.count())await open.click();
  await page.getByRole('tab',{name:'Mapa',exact:true}).click();await page.getByRole('button',{name:'Ir a '+label,exact:true}).click();await page.waitForTimeout(250);
  const a=await page.evaluate(id=>window.__HQ_AGENT_INTERACTIONS__.find(a=>a.id===id),id);await walk([a.approach[0],a.approach[2]],title);
  const dialog=page.getByRole('dialog');await dialog.getByLabel('Caso',{exact:true}).selectOption('7ccf5c8b-ff3f-4847-b06d-28f12eb13159');
  await dialog.getByText('COMPLETE',{exact:true}).waitFor({timeout:15000});
  await page.screenshot({path:'output/playwright/p4/final-'+id+'-header.png'});
  if(focus){const detail=dialog.locator('details.research-opinion').filter({has:page.locator('summary',{hasText:focus})});if(!await detail.getAttribute('open'))await detail.locator('summary').click();await detail.scrollIntoViewIfNeeded();await page.screenshot({path:'output/playwright/p4/final-'+id+'-dossier.png'});}
  results.push({department:id,text:await dialog.innerText(),pose:await page.evaluate(()=>window.__HQ_PLAYER__)});
 }
 await page.keyboard.press('Escape');await page.getByRole('button',{name:'Videowall',exact:true}).click();await page.waitForTimeout(1200);await page.screenshot({path:'output/playwright/p4/final-videowall.png'});
 return {at:new Date().toISOString(),method:'UI teleports followed by native arrow movement to proximity; actual persisted dossier',results};
}
