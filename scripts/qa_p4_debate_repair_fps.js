async(page)=>{
 if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Recorrer',exact:true}).click();
 await page.getByRole('button',{name:'Medir FPS',exact:true}).click();
 await page.locator('canvas').focus();
 const samples=[];
 for(const [key,steps] of [['ArrowLeft',12],['ArrowRight',24],['ArrowLeft',12]]){
  await page.keyboard.down(key);
  for(let i=0;i<steps;i++){
   await page.waitForTimeout(250);
   samples.push(await page.evaluate(()=>({player:window.__HQ_PLAYER__,metrics:window.__HQ_METRICS__,dpr:window.__HQ_DPR__,dialog:!!document.querySelector('[role=dialog]')})));
  }
  await page.keyboard.up(key);
 }
 await page.waitForTimeout(1100);
 const metrics=await page.evaluate(()=>window.__HQ_METRICS__);
 await page.screenshot({path:'output/p4-debate-repair/moving-no-llm.png'});
 return {method:'Native arrows, focus canvas, 12 seconds lateral corridor; local model off',viewport:page.viewportSize(),
  uninterrupted:samples.every(s=>!s.dialog&&!s.player.paused),movingSamples:samples.filter(s=>s.player.speed>.1).length,samples,metrics};
}
