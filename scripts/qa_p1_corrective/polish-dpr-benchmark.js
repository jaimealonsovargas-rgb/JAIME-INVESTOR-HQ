async(page)=>{
 const results=[],warmup=[],navigations=[];page.on('framenavigated',frame=>{if(frame===page.mainFrame())navigations.push({at:new Date().toISOString(),url:frame.url()});});
 await page.reload();await page.setViewportSize({width:1920,height:1080});
 await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===17,{},{timeout:40000});
 await page.getByRole('button',{name:'Recorrer',exact:true}).click();
 const select=page.locator('.world-tools select');
 const cases=[['recepcion','RECEPCIÓN'],['trading','TRADING'],['comite','COMITÉ DE INVERSIÓN'],['sistemas','SISTEMAS']];
 async function walking(pairs){
  await page.locator('canvas').focus();
  try{for(let i=0;i<pairs;i++){
   await page.keyboard.down('ArrowLeft');await page.waitForTimeout(720);await page.keyboard.up('ArrowLeft');
   await page.keyboard.down('ArrowRight');await page.waitForTimeout(720);await page.keyboard.up('ArrowRight');
  }}finally{await page.keyboard.up('ArrowLeft');await page.keyboard.up('ArrowRight');}
 }
 async function measure(profile,id,label){
  await page.getByRole('button',{name:'Ir a '+label,exact:true}).click();await walking(2);
  await page.getByRole('button',{name:'Medir FPS',exact:true}).click();await walking(8);await page.waitForTimeout(1100);
  await page.getByRole('button',{name:'Medir FPS',exact:true}).waitFor();
  const row=await page.evaluate(()=>({at:new Date().toISOString(),metrics:window.__HQ_METRICS__,frames:window.__HQ_FRAMES__,movingFrames:window.__HQ_MOVING_FRAMES__,resolution:window.__HQ_DPR__,humans:window.__HQ_HUMANS__,player:window.__HQ_PLAYER__}));
  results.push({profile,id,...row});
  await page.evaluate(value=>{window.__HQ_BENCHMARK_PROGRESS__=value;},{results,warmup});
  if(row.metrics.hidden||row.metrics.movingSamples<100||Object.keys(row.humans).length!==17)throw Error('Muestra no válida '+JSON.stringify({profile,id,metrics:row.metrics,humans:Object.keys(row.humans).length}));
  if(profile==='adaptive')await page.screenshot({path:'docs/evidencias/P1_PULIDO_ADAPTATIVO/adaptativo-'+id+'.png'});
 }
 await select.selectOption('fixed');
 for(const [id,label] of cases)await measure('fixed-before',id,label);
 const domBefore=await page.locator('.department-label').first().evaluate(el=>({font:getComputedStyle(el).fontSize,width:el.clientWidth,height:el.clientHeight}));
 await select.selectOption('balanced');await page.getByRole('button',{name:'Ir a RECEPCIÓN',exact:true}).click();
 const start=Date.now();
 /* Permitir la recuperación lenta real: no se escribe DPR ni pose desde la prueba. */
 while(Date.now()-start<205000){
  await walking(3);
  const sample=await page.evaluate(()=>({at:new Date().toISOString(),resolution:window.__HQ_DPR__,speed:window.__HQ_PLAYER__?.speed}));warmup.push(sample);
  await page.evaluate(value=>{window.__HQ_BENCHMARK_PROGRESS__=value;},{results,warmup});
  if(!sample.resolution||sample.speed===undefined)throw Error('Recarga durante A/B '+JSON.stringify(navigations));if(sample.resolution.dpr===1&&Date.now()-start>20000)break;
 }
 for(const [id,label] of cases)await measure('adaptive',id,label);
 const domAfter=await page.locator('.department-label').first().evaluate(el=>({font:getComputedStyle(el).fontSize,width:el.clientWidth,height:el.clientHeight}));
 if(domBefore.font!==domAfter.font||Math.abs(domBefore.width-domAfter.width)>.1||Math.abs(domBefore.height-domAfter.height)>.1)throw Error('DPR altera etiquetas DOM');
 const beforePause=await page.evaluate(()=>window.__HQ_DPR__.dpr);
 await page.getByRole('button',{name:'Ver centro de control',exact:true}).click();await page.waitForTimeout(5200);
 const paused=await page.evaluate(()=>({dpr:window.__HQ_DPR__.dpr,player:window.__HQ_PLAYER__,dialog:document.querySelector('dialog[open]')?.getBoundingClientRect().toJSON()}));
 if(!paused.player.paused||paused.dpr!==beforePause)throw Error('Panel altera DPR o no pausa');
 await page.screenshot({path:'docs/evidencias/P1_PULIDO_ADAPTATIVO/panel-dom-nativo.png'});await page.keyboard.press('Escape');
 await select.selectOption('fixed');
 for(const [id,label] of cases)await measure('fixed-after',id,label);
 await select.selectOption('balanced');
 return{at:new Date().toISOString(),buildScripts:await page.evaluate(()=>performance.getEntriesByType('resource').map(r=>new URL(r.name).pathname).filter(p=>p.endsWith('.js'))),method:'Playwright Chrome con ventana / Intel D3D11; flechas nativas; fijo-adaptativo-fijo en el mismo build; sin otras cargas de QA simultáneas',results,warmup,navigations,domBefore,domAfter,paused};
}
