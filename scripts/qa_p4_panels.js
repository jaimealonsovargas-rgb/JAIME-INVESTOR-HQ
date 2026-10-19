async(page)=>{
 const context=await page.context().browser().newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1});page=await context.newPage(); await page.setViewportSize({width:1920,height:1080});await page.goto('http://127.0.0.1:5174');await page.bringToFront();const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:true});
 await page.waitForFunction(()=>window.__HQ_AGENT_INTERACTIONS__?.[0]?.screen);
 await page.locator('.financial-metrics').waitFor({timeout:15000});await page.screenshot({path:'output/playwright/p4/simple-sidebars.png'});const dimensions=await page.evaluate(()=>({width:innerWidth,height:innerHeight,pixelRatio:devicePixelRatio}));const results=[];
 for(const [id,focus] of [['research','Bull'],['quant','Quant / tendencia'],['committee','Chair'],['systems',null]]){
  if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Vista general',exact:true}).click();await page.waitForTimeout(1800);
  const anchor=await page.evaluate(id=>window.__HQ_AGENT_INTERACTIONS__.find(a=>a.id===id),id);
  await page.mouse.click(anchor.screen.x,anchor.screen.y);const dialog=page.getByRole('dialog');await dialog.waitFor();
  await dialog.getByLabel('Caso',{exact:true}).selectOption('ccadc542-5ddf-415f-8692-676415729886');await dialog.locator('.research-stats').waitFor({timeout:15000});
  await page.screenshot({path:'output/playwright/p4/final-'+id+'-header.png'});
  if(focus){const detail=dialog.locator('details.research-opinion').filter({has:page.locator('summary',{hasText:focus})});if(await detail.count()){if(await detail.getAttribute('open')===null)await detail.locator(':scope > summary').click();await detail.scrollIntoViewIfNeeded();await page.screenshot({path:'output/playwright/p4/final-'+id+'-dossier.png'});}}
  results.push({department:id,text:await dialog.innerText()});
 }
 await page.keyboard.press('Escape');await page.getByRole('button',{name:'Videowall',exact:true}).click();await page.waitForTimeout(1500);await page.screenshot({path:'output/playwright/p4/final-videowall.png'});
 return {dimensions,at:new Date().toISOString(),method:'Native NPC clicks and case selector; actual persisted dossier, including any failures or semantic limitations',results};
}
