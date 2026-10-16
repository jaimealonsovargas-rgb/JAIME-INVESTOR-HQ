async(page)=>{
 const root='output/playwright/p3/';
 await page.unrouteAll();await page.bringToFront();const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:true});
 await page.setViewportSize({width:1920,height:1080});await page.reload();
 await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===17,{},{timeout:40000});
 await page.getByRole('tab',{name:'Cartera',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelector('.nav-value strong')?.textContent==='10.000,00 €');
 const results={at:new Date().toISOString(),focusEmulation:true,viewport:{width:1920,height:1080},screens:[],requests:[]};
 for(const path of ['/health','/api/portfolio/master/summary','/api/portfolio/master/positions','/api/portfolio/master/ledger','/api/portfolio/master/nav/history','/api/portfolio/master/performance','/api/markets/watchlist','/api/data/quality','/api/hq/overview']){
  const response=await page.request.get('http://127.0.0.1:8000'+path);if(!response.ok())throw Error(path+' '+response.status());
  results.requests.push({path,status:response.status(),body:await response.json()});
 }
 const summary=results.requests.find(r=>r.path.endsWith('/summary')).body;
 if(summary.nav_eur!=='10000.00'||summary.positions_count!==0||summary.events_count!==1||summary.orders_enabled)throw Error('MASTER inconsistent');
 const shot=async name=>{await page.screenshot({path:root+name+'.png'});results.screens.push(name);};
 await shot('hud-cartera');
 await page.getByRole('tab',{name:'Posiciones',exact:true}).click();if(!await page.getByRole('tabpanel').getByText('Sin posiciones',{exact:true}).isVisible())throw Error('Missing empty positions');await shot('posiciones');
 await page.getByRole('tab',{name:'Actividad',exact:true}).click();await page.getByText('Aportación virtual',{exact:true}).waitFor();await shot('actividad');
 results.activity=await page.getByRole('tabpanel').innerText();
 await page.getByRole('tab',{name:'Mapa',exact:true}).click();if(await page.getByRole('button',{name:/^Ir a /}).count()!==9)throw Error('Map must retain nine departments');await shot('mapa');
 await page.getByRole('tab',{name:'Mapa',exact:true}).focus();await page.keyboard.press('Home');if(await page.getByRole('tab',{name:'Cartera',exact:true}).getAttribute('aria-selected')!=='true')throw Error('Tab keyboard navigation');
 await page.getByRole('button',{name:'Videowall',exact:true}).click();await page.waitForTimeout(700);await shot('videowall');
 await page.getByRole('button',{name:'Ver centro de control',exact:true}).click();await page.getByRole('dialog').waitFor();await shot('centro-control');
 results.overview=await page.getByRole('dialog').innerText();await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Recorrer',exact:true}).click();await page.locator('canvas').focus();
 const before=await page.evaluate(()=>window.__HQ_PLAYER__);await page.keyboard.down('ArrowRight');await page.waitForTimeout(500);await page.keyboard.up('ArrowRight');await page.waitForTimeout(300);const after=await page.evaluate(()=>window.__HQ_PLAYER__);
 if(after.position[0]-before.position[0]<.3)throw Error('Movement broken');results.movement={before,after};
 results.dom=await page.evaluate(()=>({cards:document.querySelectorAll('.wall-native-card').length,labels:document.querySelectorAll('.department-label').length,humans:window.__HQ_HUMANS__,metrics:window.__HQ_METRICS__,overflow:document.documentElement.scrollWidth>innerWidth}));
 if(results.dom.cards!==9||results.dom.labels!==9||Object.values(results.dom.humans).filter(p=>p.kind==='npc'&&p.seated).length!==16||results.dom.overflow)throw Error('Scene regression');
 await page.route('**/api/**',route=>route.abort());await page.route('**/health',route=>route.abort());await page.reload();
 await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===17,{},{timeout:40000});
 await page.waitForFunction(()=>document.querySelector('.rail-right')?.textContent.includes('NO DISPONIBLE'));
 await shot('offline');
 if(await page.locator('.nav-value strong').count())throw Error('Offline invents cached NAV');
 const offBefore=await page.evaluate(()=>window.__HQ_PLAYER__);await page.locator('canvas').focus();await page.keyboard.down('ArrowRight');await page.waitForTimeout(500);await page.keyboard.up('ArrowRight');await page.waitForTimeout(300);const offAfter=await page.evaluate(()=>window.__HQ_PLAYER__);
 if(offAfter.position[0]-offBefore.position[0]<.3)throw Error('Offline movement broken');results.offline={before:offBefore,after:offAfter,text:await page.locator('.financial-hud').innerText()};
 await page.unrouteAll();await page.goto('http://127.0.0.1:5174/?diagnostico=1');await page.waitForTimeout(1000);await shot('diagnostico');results.diagnostic=await page.locator('body').innerText();
 await page.setViewportSize({width:390,height:844});await page.goto('http://127.0.0.1:5174/');await page.getByRole('button',{name:'Abrir cartera',exact:true}).waitFor();await page.getByRole('button',{name:'Abrir cartera',exact:true}).click();await page.waitForTimeout(800);await shot('hud-390');
 results.mobile=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,railWidth:document.querySelector('.rail-right').getBoundingClientRect().width}));if(results.mobile.overflow)throw Error('Horizontal overflow');
 await page.setViewportSize({width:1920,height:1080});await page.reload();
 return results;
}
