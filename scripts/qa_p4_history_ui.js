async(page)=>{
 const context=await page.context().browser().newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const report={at:new Date().toISOString(),classification:'PERSONAL_LOCAL_DO_NOT_PUBLISH_VALUES',departments:[],errors};
 try{
  await page.goto('http://127.0.0.1:5174');await page.bringToFront();
  await page.waitForFunction(()=>window.__HQ_AGENT_INTERACTIONS__?.[0]?.screen);
  await page.locator('svg.market-sparkline').first().waitFor({timeout:20000});
  await page.evaluate(()=>document.fonts.ready);
  report.watchlist=await page.evaluate(()=>({sparklines:document.querySelectorAll('svg.market-sparkline').length,font:getComputedStyle(document.querySelector('.market-symbol')).fontFamily,fontSize:getComputedStyle(document.querySelector('.market-symbol')).fontSize,overflow:document.documentElement.scrollWidth>innerWidth}));
  await page.screenshot({path:'output/playwright/p4/history-watchlist.png'});
  for(const id of ['research','quant','committee','systems']){
   await page.getByRole('button',{name:'Vista general',exact:true}).click();await page.waitForTimeout(1400);
   const anchor=await page.evaluate(id=>window.__HQ_AGENT_INTERACTIONS__.find(a=>a.id===id)?.screen,id);
   if(!anchor)throw Error('Missing visible NPC '+id);
   await page.mouse.click(anchor.x,anchor.y);const dialog=page.getByRole('dialog');await dialog.waitFor();
   const cases=dialog.getByLabel('Caso',{exact:true});await cases.selectOption('de7188a7-de42-4318-b5ae-e77b5c86dc76');
   await dialog.locator('.research-case-heading').waitFor({timeout:20000});
   await dialog.locator('.research-case-heading').scrollIntoViewIfNeeded();
   await page.screenshot({path:'output/playwright/p4/history-'+id+'.png'});
   report.departments.push({id,opened:true,caseVisible:(await dialog.locator('.research-case-heading').innerText()).includes('btc-bitcoin'),paused:await page.evaluate(()=>window.__HQ_PLAYER__.paused)});
   await page.keyboard.press('Escape');
  }
  await page.getByRole('button',{name:'Videowall',exact:true}).click();await page.waitForTimeout(1400);
  await page.screenshot({path:'output/playwright/p4/history-videowall.png'});
  report.wallAgents=await page.locator('[data-wall-section=agents]').innerText();
  report.master=(await page.request.get('http://127.0.0.1:8000/api/portfolio/master/summary').then(r=>r.json())).ledger_hash;
  report.ordersStatus=(await page.request.post('http://127.0.0.1:8000/api/orders',{data:{}})).status();
  return report;
 }finally{await context.close();}
}
