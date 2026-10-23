async(page)=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.setViewportSize({width:1920,height:1080});await page.bringToFront();
 const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:true});
 await page.getByRole('button',{name:'Vista general',exact:true}).click();
 await page.waitForFunction(()=>window.__HQ_AGENT_INTERACTIONS__?.length===9);
 await page.screenshot({path:'output/p4-debate-repair/office.png'});
 const cases={deep:'fcbb1bb9-1d99-4cbf-bf60-580e7e6f6be3',ordinary:'9949fc53-1ac0-4c05-83ab-d868c40c0615'};
 const results=[];
 for(const department of ['research','quant','committee','systems']){
  if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Vista general',exact:true}).click();await page.waitForTimeout(1000);
  const anchor=await page.evaluate(id=>window.__HQ_AGENT_INTERACTIONS__.find(a=>a.id===id).screen,department);
  await page.mouse.click(anchor.x,anchor.y);const dialog=page.getByRole('dialog');await dialog.waitFor();
  await dialog.getByLabel('Caso',{exact:true}).selectOption(department==='quant'?cases.ordinary:cases.deep);
  await dialog.locator('.research-stats').waitFor();await page.waitForTimeout(500);
  if(department==='research'||department==='committee'){
   const detail=dialog.locator('details.research-opinion').filter({has:page.locator('summary',{hasText:'Bull'})});
   if(await detail.count()){await detail.locator(':scope > summary').click();await detail.scrollIntoViewIfNeeded();}
  }
  await page.screenshot({path:`output/p4-debate-repair/${department}.png`});
  results.push({department,text:await dialog.innerText(),horizontalOverflow:await dialog.evaluate(e=>e.scrollWidth>e.clientWidth+1)});
 }
 await page.keyboard.press('Escape');await page.getByRole('button',{name:'Videowall',exact:true}).click();
 await page.waitForTimeout(700);await page.screenshot({path:'output/p4-debate-repair/videowall.png'});
 return {viewport:page.viewportSize(),errors,results};
}
