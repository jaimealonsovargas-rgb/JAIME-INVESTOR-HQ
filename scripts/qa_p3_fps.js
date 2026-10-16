async(page)=>{
 await page.unrouteAll();await page.bringToFront();const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:true});
 await page.setViewportSize({width:1920,height:1080});await page.reload();await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===17,{},{timeout:40000});
 await page.getByRole('tab',{name:'Mapa',exact:true}).click();
 const results=[];
 async function walk(pairs){await page.locator('canvas').focus();const anchor=await page.evaluate(()=>window.__HQ_PLAYER__.position[0]);try{for(let i=0;i<pairs;i++){
  const dx=anchor-await page.evaluate(()=>window.__HQ_PLAYER__.position[0]);if(Math.abs(dx)>.12){const key=dx>0?'ArrowRight':'ArrowLeft';await page.keyboard.down(key);await page.waitForTimeout(Math.abs(dx)/2.05*1000+40);await page.keyboard.up(key);await page.waitForTimeout(100);}
  await page.keyboard.down('ArrowLeft');await page.waitForTimeout(720);await page.keyboard.up('ArrowLeft');await page.keyboard.down('ArrowRight');await page.waitForTimeout(720);await page.keyboard.up('ArrowRight');
 }}finally{await page.keyboard.up('ArrowLeft');await page.keyboard.up('ArrowRight');}}
 for(const label of ['RECEPCIÓN','TRADING','COMITÉ DE INVERSIÓN','SISTEMAS']){
  await page.getByRole('button',{name:'Ir a '+label,exact:true}).click();await page.waitForTimeout(300);await walk(2);
  await page.getByRole('button',{name:'Medir FPS',exact:true}).click();await walk(8);await page.waitForTimeout(1100);
  const row=await page.evaluate(()=>({at:new Date().toISOString(),metrics:window.__HQ_METRICS__,movingFrames:window.__HQ_MOVING_FRAMES__,frames:window.__HQ_FRAMES__,resolution:window.__HQ_DPR__,humans:window.__HQ_HUMANS__,player:window.__HQ_PLAYER__}));
  if(row.player.paused||row.metrics.hidden||row.movingFrames.reduce((s,n)=>s+n,0)<9000)throw Error('Invalid moving sample '+label);
  results.push({label,...row});
 }
 await page.getByRole('tab',{name:'Cartera',exact:true}).click();
 return {at:new Date().toISOString(),focusEmulation:true,method:'Real Windows Intel / headed Chrome / 1920x1080 / balanced adaptive / native arrows / 16 seated NPC / no builds, audits or tests during frame samples; not a controlled before-after comparison',results};
}
