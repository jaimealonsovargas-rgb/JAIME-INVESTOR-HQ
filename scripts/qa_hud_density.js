async(page)=>{
 const report={at:new Date().toISOString(),method:'Real local API and headed browser; no fixture prices or LLM requests',screens:[]};
 const context=await page.context().browser().newContext({deviceScaleFactor:1});
 const app=await context.newPage();const errors=[];app.on('pageerror',e=>errors.push(e.message));
 try{
  for(const [width,height] of [[1920,1080],[1366,768]]){
   await app.setViewportSize({width,height});await app.goto('http://127.0.0.1:5174');
   await app.bringToFront();await app.locator('.market-row').first().waitFor({timeout:45000});await app.evaluate(()=>document.fonts.ready);
   await app.waitForFunction(()=>window.__HQ_METRICS__?.ready);await app.waitForTimeout(1000);
   const phase=await app.locator('.financial-hud').getAttribute('data-density')||'before';
   const row=await app.evaluate(()=>{
    const body=document.querySelector('#market-body'),clip=body.getBoundingClientRect();
    const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
    const css=(selector,keys)=>{const s=getComputedStyle(document.querySelector(selector));return Object.fromEntries(keys.map(k=>[k,s[k]]))};
    const rows=[...body.querySelectorAll('.market-row')].map(e=>({symbol:e.querySelector('.market-symbol').textContent,height:e.getBoundingClientRect().height,fullyVisible:e.getBoundingClientRect().top>=clip.top&&e.getBoundingClientRect().bottom<=clip.bottom}));
    return {width:innerWidth,height:innerHeight,rows,visibleRows:rows.filter(r=>r.fullyVisible).length,totalRows:rows.length,left:rect(document.querySelector('.rail-left')),right:rect(document.querySelector('.rail-right')),scrollWidth:body.scrollWidth,clientWidth:body.clientWidth,overflow:document.documentElement.scrollWidth>innerWidth,styles:{body:css('.rail-body',['fontSize','padding']),symbol:css('.market-symbol',['fontSize']),price:css('.market-price',['fontSize']),heading:css('.financial-rail h2',['fontSize']),nav:css('.nav-value strong',['fontSize']),row:css('.market-row',['paddingTop','paddingBottom'])},sparklines:document.querySelectorAll('.market-sparkline').length};
   });
   const base=`output/playwright/hud-density/${phase}-${width}`;
   await app.screenshot({path:base+'-office.png'});
   await app.locator('.rail-left').screenshot({path:base+'-left.png'});
   await app.locator('.rail-right').screenshot({path:base+'-right.png'});
   const details=app.locator('.market-row').first();await details.locator('summary').click();
   row.details={open:await details.evaluate(e=>e.open),source:await details.getByRole('link',{name:'Fuente original'}).getAttribute('href'),observed:await details.locator('.market-detail').innerText().then(t=>t.includes('Observado:')&&t.includes('Recibido:'))};
   await details.locator('summary').click();
   row.tabs=[];
   for(const name of ['Posiciones','Actividad','Mapa','Cartera']){
    const tab=app.getByRole('tab',{name,exact:true});await tab.click();
    row.tabs.push({name,selected:await tab.getAttribute('aria-selected')==='true',panel:await app.getByRole('tabpanel').isVisible()});
   }
   await app.getByRole('tab',{name:'Cartera',exact:true}).focus();await app.keyboard.press('ArrowRight');
   row.keyboardTab=await app.getByRole('tab',{name:'Posiciones',exact:true}).getAttribute('aria-selected')==='true';
   await app.getByRole('tab',{name:'Cartera',exact:true}).click();
   row.controls=await app.evaluate(()=>[...document.querySelectorAll('.world-toolbar button')].filter(e=>e.offsetWidth).map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent,uncovered:e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}}));
   if(phase!=='before'){
    const response=await app.request.get('http://127.0.0.1:8000/api/markets/watchlist').then(r=>r.json());
    const expected=[...response.items,...response.pulse];row.allDetails=[];
    for(let i=0;i<await app.locator('.market-row').count();i++){
     const item=app.locator('.market-row').nth(i);await item.locator('summary').click();
     const text=await item.locator('.market-detail').innerText();
     const href=await item.getByRole('link',{name:'Fuente original'}).getAttribute('href');
     const sourceMatches=href===expected[i]?.observation.source_ref;
     const unitVisible=await item.locator('.market-price small').innerText()===expected[i]?.observation.unit;
     if(!sourceMatches||!unitVisible||!text.includes('Observado:')||!text.includes('Recibido:'))throw Error('Provenance mismatch in row '+i);
     row.allDetails.push({index:i,sourceMatches,unitVisible,dates:true,statusVisible:await item.locator('.financial-state').isVisible()});
     await item.locator('summary').click();
    }
    const density=app.getByLabel('Densidad de los paneles');await density.selectOption('normal');
    row.normal=await app.evaluate(()=>({body:getComputedStyle(document.querySelector('.rail-body')).fontSize,width:document.querySelector('.rail-left').getBoundingClientRect().width}));
    await density.selectOption('compact');await app.reload();await app.locator('.market-row').first().waitFor();
    row.densityPersists=await app.locator('.financial-hud').getAttribute('data-density')==='compact';
   }
   row.phase=phase;report.screens.push(row);
   if(row.overflow||row.scrollWidth>row.clientWidth||!row.keyboardTab||row.tabs.some(t=>!t.selected||!t.panel)||row.controls.some(c=>!c.uncovered))throw Error('HUD regression at '+width);
  }
  if(report.screens[0].phase!=='before'){
   await app.setViewportSize({width:390,height:844});await app.evaluate(()=>localStorage.removeItem('hq.financial-density.v1'));await app.reload();
   await app.getByRole('button',{name:'Abrir mercados',exact:true}).click();await app.locator('.market-row').first().waitFor();
   report.mobile={defaultDensity:await app.locator('.financial-hud').getAttribute('data-density')};
   await app.getByLabel('Densidad de los paneles').selectOption('compact');
   await app.screenshot({path:'output/playwright/hud-density/compact-390-markets.png'});
   report.mobile.overflow=await app.evaluate(()=>document.documentElement.scrollWidth>innerWidth||document.querySelector('#market-body').scrollWidth>document.querySelector('#market-body').clientWidth);
   await app.getByRole('button',{name:'Plegar mercados',exact:true}).click();await app.getByRole('button',{name:'Abrir cartera',exact:true}).click();
   await app.getByRole('tab',{name:'Posiciones',exact:true}).click();report.mobile.positions=await app.getByRole('tabpanel').getByText('Sin posiciones',{exact:true}).isVisible();
   if(report.mobile.overflow||!report.mobile.positions)throw Error('Mobile HUD regression');
  }
  report.errors=errors;
  const status=await app.request.get('http://127.0.0.1:8000/api/agents/status').then(r=>r.json());
  const master=await app.request.get('http://127.0.0.1:8000/api/portfolio/master/summary').then(r=>r.json());
  report.safety={roles:status.roles,activeJobs:status.active_jobs,queue:status.queue,model:status.runtime.state,masterHash:master.ledger_hash,cash:master.cash_eur,ordersEnabled:master.orders_enabled,ordersHttp:(await app.request.post('http://127.0.0.1:8000/api/orders',{data:{}})).status()};
  return report;
 }finally{await context.close();}
}
