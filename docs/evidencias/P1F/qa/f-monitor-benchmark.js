async(page)=>{
 await page.getByRole('button',{name:'Ir a TRADING FLOOR',exact:true}).click();await page.waitForTimeout(300);
 await page.getByRole('button',{name:'Medir FPS',exact:true}).click();await page.locator('canvas').focus();
 for(let i=0;i<2;i++){await page.keyboard.down('KeyA');await page.waitForTimeout(700);await page.keyboard.up('KeyA');await page.keyboard.down('KeyD');await page.waitForTimeout(700);await page.keyboard.up('KeyD');}
 const spec={goal:[1.35,-.5]};const walk=WALK;const trace=await walk(page);
 await page.keyboard.down('KeyW');await page.keyboard.down('KeyA');await page.waitForTimeout(180);await page.keyboard.up('KeyW');await page.keyboard.up('KeyA');await page.waitForTimeout(500);
 await page.keyboard.press('KeyE');await page.getByRole('dialog').waitFor();await page.screenshot({path:'docs/evidencias/P1F/06-trading-overlay.png',timeout:20000});await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});
 await page.keyboard.press('KeyE');await page.getByRole('dialog').waitFor();await page.getByRole('button',{name:'Volver a la oficina Esc',exact:true}).click();
 await page.getByRole('button',{name:'Medir FPS',exact:true}).waitFor();await page.waitForTimeout(100);
 const result=await page.evaluate(()=>({metrics:window.__HQ_METRICS__,player:window.__HQ_PLAYER__,frames:window.__HQ_FRAMES__,movingFrames:window.__HQ_MOVING_FRAMES__}));
 if(result.metrics.movingSamples<100||result.metrics.movingFps<30)throw Error('Monitor benchmark insuficiente');return {scenario:'monitor',trace,...result};
}
