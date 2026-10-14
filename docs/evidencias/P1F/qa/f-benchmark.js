async(page)=>{
 const spec=SPEC;await page.getByRole('button',{name:'Ir a '+spec.label,exact:true}).click();await page.waitForTimeout(500);
 if(spec.goal.length){const walk=WALK;await walk(page);}
 await page.getByRole('button',{name:'Medir FPS',exact:true}).click();await page.locator('canvas').focus();
 for(let i=0;i<4;i++){
  if(spec.turn){await page.mouse.move(850,450);await page.mouse.down({button:'right'});await page.mouse.move(925,450,{steps:6});await page.mouse.up({button:'right'});}
  await page.keyboard.down(spec.keys[0]);await page.waitForTimeout(800);await page.keyboard.up(spec.keys[0]);await page.keyboard.down(spec.keys[1]);await page.waitForTimeout(800);await page.keyboard.up(spec.keys[1]);
 }
 await page.getByRole('button',{name:'Medir FPS',exact:true}).waitFor();await page.waitForTimeout(120);
 const result=await page.evaluate(()=>({metrics:window.__HQ_METRICS__,player:window.__HQ_PLAYER__,humans:window.__HQ_HUMANS__,frames:window.__HQ_FRAMES__,movingFrames:window.__HQ_MOVING_FRAMES__}));
 if(result.metrics.movingSamples<100||result.metrics.movingFps<30||result.metrics.hidden||result.metrics.dpr!==1||result.metrics.width!==1920||result.metrics.height!==1080||!result.metrics.renderer.includes('Intel'))throw Error('Benchmark no aceptable: '+JSON.stringify(result.metrics));
 await page.keyboard.down('KeyW');await page.waitForTimeout(180);await page.screenshot({path:'docs/evidencias/P1F/'+spec.screenshot,timeout:20000});await page.keyboard.up('KeyW');
 return {scenario:spec.id,...result};
}
