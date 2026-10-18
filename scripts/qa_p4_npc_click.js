async(page)=>{
 await page.setViewportSize({width:1920,height:1080});await page.goto('http://127.0.0.1:5174');await page.bringToFront();const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:true});
 await page.waitForFunction(()=>window.__HQ_AGENT_INTERACTIONS__?.[0]?.screen);
 await page.screenshot({path:'output/playwright/p4/simple-sidebars.png'});
 const layout=await page.evaluate(()=>{const left=document.querySelector('.rail-left'),brand=document.querySelector('.world-brand');return{railTop:left.getBoundingClientRect().top,brandBottom:brand.getBoundingClientRect().bottom,font:getComputedStyle(document.querySelector('.financial-rail h2')).fontFamily,railWidth:left.getBoundingClientRect().width};});
 const results=[];
 for(const id of ['reception','research','quant','risk','trading','performance','execution','systems','committee']){
  if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Vista general',exact:true}).click();await page.waitForTimeout(1800);
  const anchor=await page.evaluate(id=>window.__HQ_AGENT_INTERACTIONS__.find(a=>a.id===id),id);
  await page.mouse.click(anchor.screen.x,anchor.screen.y);await page.getByRole('dialog').waitFor({timeout:4000});
  const title=await page.getByRole('dialog').getByRole('heading',{level:2}).innerText();
  const paused=await page.evaluate(()=>window.__HQ_PLAYER__.paused);if(!paused)throw Error('Not paused '+id);
  await page.screenshot({path:'output/playwright/p4/click-'+id+'.png'});
  await page.keyboard.press('Escape');await page.waitForTimeout(250);if(await page.getByRole('dialog').isVisible())throw Error('Reopened '+id);
  results.push({id,title,clicked:anchor.screen,paused,released:await page.evaluate(()=>!window.__HQ_PLAYER__.paused)});
 }
 await page.getByRole('button',{name:'Recorrer',exact:true}).click();await page.locator('canvas').focus();const before=await page.evaluate(()=>window.__HQ_PLAYER__.position);await page.keyboard.down('ArrowLeft');await page.waitForTimeout(400);await page.keyboard.up('ArrowLeft');const after=await page.evaluate(()=>window.__HQ_PLAYER__.position);
 if(Math.abs(before[0]-after[0])<.2)throw Error('Control not restored');
 return {at:new Date().toISOString(),method:'Native mouse clicks on projected visible NPC anchors, no direct state mutation; keyboard movement after closing',layout,results,before,after};
}