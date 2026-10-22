async(page)=>{
 const context=await page.context().browser().newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 const results={at:new Date().toISOString(),viewports:[],departments:[],errors:[]};
 page=await context.newPage();page.on('pageerror',e=>results.errors.push(e.message));
 try{
  for(const width of [1920,1280,390]){
   await page.setViewportSize({width,height:1080});await page.goto('http://127.0.0.1:5174');await page.bringToFront();
   await page.waitForFunction(()=>window.__HQ_AGENT_INTERACTIONS__?.[0]?.screen);
   const left=page.getByRole('button',{name:'Abrir mercados',exact:true});if(await left.isVisible())await left.click();
   await page.locator('.market-row').first().waitFor({timeout:15000});
   await page.waitForFunction(()=>document.querySelector('[data-wall-section=agents]')?.textContent.includes('RESEARCH LOCAL'),{timeout:25000});
   await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(2000);
   await page.screenshot({path:'output/playwright/p4/advanced-rails-'+width+'.png'});
   results.viewports.push(await page.evaluate(()=>({width:innerWidth,dpr:devicePixelRatio,overflow:document.documentElement.scrollWidth>innerWidth,rail:document.querySelector('.rail-left').getBoundingClientRect().toJSON(),sparklines:document.querySelectorAll('svg.market-sparkline').length,font:getComputedStyle(document.querySelector('.market-symbol')).fontSize})));
   await page.getByRole('button',{name:'Plegar mercados',exact:true}).focus();await page.keyboard.press('Enter');
   if(await page.locator('#market-body').count())throw Error('Collapse failed');
  }
  await page.setViewportSize({width:1920,height:1080});await page.goto('http://127.0.0.1:5174');await page.waitForFunction(()=>window.__HQ_AGENT_INTERACTIONS__?.[0]?.screen);
  await page.getByRole('tab',{name:'Cartera',exact:true}).focus();await page.keyboard.press('ArrowRight');
  if(await page.getByRole('tab',{name:'Posiciones',exact:true}).getAttribute('aria-selected')!=='true')throw Error('Tab keyboard failed');
  await page.getByRole('tab',{name:'Mapa',exact:true}).click();await page.screenshot({path:'output/playwright/p4/advanced-map.png'});
  for(const id of ['research','quant','risk','systems','committee','trading','execution','reception','performance']){
   await page.getByRole('button',{name:'Vista general',exact:true}).click();await page.waitForTimeout(1400);
   const anchor=await page.evaluate(id=>window.__HQ_AGENT_INTERACTIONS__.find(a=>a.id===id),id);
   if(!anchor?.screen)throw Error('Missing NPC '+id);
   await page.mouse.click(anchor.screen.x,anchor.screen.y);const dialog=page.getByRole('dialog');await dialog.waitFor();
   await dialog.getByLabel('Caso',{exact:true}).selectOption('66dc5f17-849a-4e32-a90a-76e45a7ba447');
   await dialog.getByText('Informe de referencia · debate no aplicable',{exact:false}).first().waitFor();
   if(['research','quant','committee','systems'].includes(id))await page.screenshot({path:'output/playwright/p4/advanced-'+id+'.png'});
   results.departments.push({id,opened:true,text:(await dialog.innerText()).slice(0,650)});await page.keyboard.press('Escape');
  }
  await page.getByRole('button',{name:'Videowall',exact:true}).click();await page.waitForTimeout(1200);await page.screenshot({path:'output/playwright/p4/advanced-videowall.png'});
  return results;
 }finally{await context.close();}
}
