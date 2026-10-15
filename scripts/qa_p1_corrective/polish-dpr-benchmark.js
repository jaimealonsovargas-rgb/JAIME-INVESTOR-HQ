async(page)=>{
 const saved=await page.evaluate(()=>window.__HQ_BENCHMARK_PROGRESS__),prior=saved?.results?.length&&saved.results.length<12?saved:undefined,resumed=!!prior;
 const excludedSamples=[...(prior?.excludedSamples??[]),...(prior?.results??[]).filter(r=>r.player.paused||r.movingFrames.reduce((n,v)=>n+v,0)<9000)];
 const results=(prior?.results??[]).filter(r=>!excludedSamples.includes(r)),warmup=prior?.warmup??[],navigations=[];page.on('framenavigated',frame=>{if(frame===page.mainFrame())navigations.push({at:new Date().toISOString(),url:frame.url()});});
 if(!resumed)await page.reload();else{for(const key of ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'])await page.keyboard.up(key);if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');}await page.setViewportSize({width:1920,height:1080});
 await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===17,{},{timeout:40000});
 await page.getByRole('button',{name:'Recorrer',exact:true}).click();
 const select=page.locator('.world-tools select');
 const cases=[['recepcion','RECEPCIÓN'],['trading','TRADING'],['comite','COMITÉ DE INVERSIÓN'],['sistemas','SISTEMAS']];
 async function walking(pairs){
  await page.locator('canvas').focus();
  const anchor=await page.evaluate(()=>window.__HQ_PLAYER__.position[0]);
  try{for(let i=0;i<pairs;i++){
   const dx=anchor-await page.evaluate(()=>window.__HQ_PLAYER__.position[0]);
   if(Math.abs(dx)>.12){const key=dx>0?'ArrowRight':'ArrowLeft';await page.keyboard.down(key);await page.waitForTimeout(Math.abs(dx)/2.05*1000+40);await page.keyboard.up(key);await page.waitForTimeout(100);}
   await page.keyboard.down('ArrowLeft');await page.waitForTimeout(720);await page.keyboard.up('ArrowLeft');
   await page.keyboard.down('ArrowRight');await page.waitForTimeout(720);await page.keyboard.up('ArrowRight');
  }}finally{await page.keyboard.up('ArrowLeft');await page.keyboard.up('ArrowRight');}
 }
 async function measure(profile,id,label){
  if(results.some(r=>r.profile===profile&&r.id===id))return;
  await page.getByRole('button',{name:'Ir a '+label,exact:true}).click();await page.waitForTimeout(250);await walking(2);
  await page.getByRole('button',{name:'Medir FPS',exact:true}).click();await walking(8);await page.waitForTimeout(1100);
  await page.getByRole('button',{name:'Medir FPS',exact:true}).waitFor();
  const row=await page.evaluate(()=>({at:new Date().toISOString(),metrics:window.__HQ_METRICS__,frames:window.__HQ_FRAMES__,movingFrames:window.__HQ_MOVING_FRAMES__,resolution:window.__HQ_DPR__,humans:window.__HQ_HUMANS__,player:window.__HQ_PLAYER__}));
  if(row.metrics.hidden||row.player.paused||row.movingFrames.reduce((n,v)=>n+v,0)<9000||Object.keys(row.humans).length!==17)throw Error('Muestra no válida '+JSON.stringify({profile,id,metrics:row.metrics,humans:Object.keys(row.humans).length}));
  results.push({profile,id,...row});
  await page.evaluate(value=>{window.__HQ_BENCHMARK_PROGRESS__=value;},{results,warmup,excludedSamples});
  if(profile==='adaptive')await page.screenshot({path:'docs/evidencias/P1_PULIDO_ADAPTATIVO/adaptativo-'+id+'.png'});
 }
 let domBefore,domAfter,domDprBefore,domDprAfter;
 if(!resumed){
 await select.selectOption('fixed');
 for(const [id,label] of cases)await measure('fixed-before',id,label);
 domBefore=await page.locator('.department-label').first().evaluate(el=>({font:getComputedStyle(el).fontSize,width:el.clientWidth,height:el.clientHeight}));domDprBefore=await page.evaluate(()=>window.__HQ_DPR__.dpr);
 await select.selectOption('balanced');await page.getByRole('button',{name:'Ir a RECEPCIÓN',exact:true}).click();
 const start=Date.now();
 /* Permitir la recuperación lenta real: no se escribe DPR ni pose desde la prueba. */
 while(Date.now()-start<205000){
  await walking(3);
  const sample=await page.evaluate(()=>({at:new Date().toISOString(),resolution:window.__HQ_DPR__,speed:window.__HQ_PLAYER__?.speed}));warmup.push(sample);
  await page.evaluate(value=>{window.__HQ_BENCHMARK_PROGRESS__=value;},{results,warmup,excludedSamples});
  if(!sample.resolution||sample.speed===undefined)throw Error('Recarga durante A/B '+JSON.stringify(navigations));if(sample.resolution.dpr===1&&Date.now()-start>20000)break;
 }
 }else{domBefore=await page.locator('.department-label').first().evaluate(el=>({font:getComputedStyle(el).fontSize,width:el.clientWidth,height:el.clientHeight}));domDprBefore=await page.evaluate(()=>window.__HQ_DPR__.dpr);}
 for(const [id,label] of cases)await measure('adaptive',id,label);
 if(!resumed){domAfter=await page.locator('.department-label').first().evaluate(el=>({font:getComputedStyle(el).fontSize,width:el.clientWidth,height:el.clientHeight}));domDprAfter=await page.evaluate(()=>window.__HQ_DPR__.dpr);}
 const beforePause=await page.evaluate(()=>window.__HQ_DPR__.dpr);
 await page.getByRole('button',{name:'Ver centro de control',exact:true}).click();await page.waitForTimeout(5200);
 const paused=await page.evaluate(()=>({dpr:window.__HQ_DPR__.dpr,player:window.__HQ_PLAYER__,dialog:document.querySelector('dialog[open]')?.getBoundingClientRect().toJSON()}));
 if(!paused.player.paused||paused.dpr!==beforePause)throw Error('Panel altera DPR o no pausa');
 await page.screenshot({path:'docs/evidencias/P1_PULIDO_ADAPTATIVO/panel-dom-nativo.png'});await page.keyboard.press('Escape');
 await select.selectOption('fixed');
 if(resumed){await page.waitForTimeout(650);domAfter=await page.locator('.department-label').first().evaluate(el=>({font:getComputedStyle(el).fontSize,width:el.clientWidth,height:el.clientHeight}));domDprAfter=await page.evaluate(()=>window.__HQ_DPR__.dpr);}
 if(domBefore.font!==domAfter.font||Math.abs(domBefore.width-domAfter.width)>.1||Math.abs(domBefore.height-domAfter.height)>.1)throw Error('DPR altera etiquetas DOM');
 for(const [id,label] of cases)await measure('fixed-after',id,label);
 await select.selectOption('balanced');
 return{at:new Date().toISOString(),recoveredFromProximityPause:resumed,excludedSamples,domDprBefore,domDprAfter,buildScripts:await page.evaluate(()=>performance.getEntriesByType('resource').map(r=>new URL(r.name).pathname).filter(p=>p.endsWith('.js'))),method:'Playwright Chrome con ventana / Intel D3D11; flechas nativas; fijo-adaptativo-fijo en el mismo build; sin compilaciones, suites de tests, auditorías ni refrescos externos de proveedores; corrección nativa de deriva en tramos recuperados',results,warmup,navigations,domBefore,domAfter,paused};
}
