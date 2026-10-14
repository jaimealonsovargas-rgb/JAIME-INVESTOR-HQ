async(page)=>{
 if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');
 const rows=[],controls=[],az=Math.atan2(2.5,20),co=Math.cos(az),si=Math.sin(az);await page.getByRole('button',{name:'Recorrer',exact:true}).click();
 await page.getByRole('button',{name:'Ir a RECEPCI\u00d3N',exact:true}).click();await page.waitForTimeout(800);
 const pose=()=>page.evaluate(()=>window.__HQ_PLAYER__);
 for(const [key,opposite] of [['ArrowUp','ArrowDown'],['ArrowRight','ArrowLeft'],['ArrowDown','ArrowUp'],['ArrowLeft','ArrowRight']]){
  await page.locator('canvas').focus();const before=await pose();await page.keyboard.down(key);await page.waitForTimeout(500);await page.keyboard.up(key);await page.waitForTimeout(200);const after=await pose(),dx=after.position[0]-before.position[0],dz=after.position[2]-before.position[2],x=dx*co-dz*si,y=(dx*si+dz*co);
  if(Math.hypot(dx,dz)<.2||(key==='ArrowUp'&&y>=0)||(key==='ArrowDown'&&y<=0)||(key==='ArrowRight'&&x<=0)||(key==='ArrowLeft'&&x>=0))throw Error('Direccion de pantalla incorrecta '+key);
  controls.push({key,before,after,screenDelta:[x,y]});await page.keyboard.down(opposite);await page.waitForTimeout(500);await page.keyboard.up(opposite);await page.waitForTimeout(250);
 }
 const before=await pose();for(const key of ['w','a','s','d']){await page.keyboard.down(key);await page.waitForTimeout(150);await page.keyboard.up(key);}await page.mouse.move(900,500);await page.mouse.down({button:'right'});await page.mouse.move(1100,650);await page.mouse.up({button:'right'});await page.mouse.wheel(0,600);await page.waitForTimeout(500);const after=await pose();if(Math.hypot(before.position[0]-after.position[0],before.position[2]-after.position[2])>.01||Math.hypot(...before.camera.map((v,i)=>v-after.camera[i]))>.03)throw Error('WASD/raton alteran juego');
 for(const [id,label] of [['recepcion','RECEPCI\u00d3N'],['trading','TRADING FLOOR'],['comite','COMIT\u00c9 DE INVERSI\u00d3N'],['sistemas','SISTEMAS / DATA QUALITY']]){
  await page.getByRole('button',{name:'Ir a '+label,exact:true}).click();await page.locator('canvas').focus();
  for(let i=0;i<2;i++){await page.keyboard.down('ArrowLeft');await page.waitForTimeout(700);await page.keyboard.up('ArrowLeft');await page.keyboard.down('ArrowRight');await page.waitForTimeout(700);await page.keyboard.up('ArrowRight');}await page.waitForTimeout(400);
  await page.getByRole('button',{name:'Medir FPS',exact:true}).click();await page.locator('canvas').focus();
  for(let i=0;i<6;i++){await page.keyboard.down('ArrowLeft');await page.waitForTimeout(750);await page.keyboard.up('ArrowLeft');await page.keyboard.down('ArrowRight');await page.waitForTimeout(750);await page.keyboard.up('ArrowRight');}
  await page.waitForTimeout(3200);if(await page.getByRole('dialog').isVisible())throw Error('Panel interrumpe benchmark '+id);
  const result=await page.evaluate(()=>({at:new Date().toISOString(),metrics:window.__HQ_METRICS__,movingFrames:window.__HQ_MOVING_FRAMES__,player:window.__HQ_PLAYER__,humans:window.__HQ_HUMANS__}));if(result.metrics.hidden||result.metrics.dpr>1||result.metrics.dpr<.75||result.metrics.movingSamples<80)throw Error('Medicion invalida');rows.push({id,...result});await page.screenshot({path:'docs/evidencias/P1_SIMS/final-'+id+'.png'});
 }
 return{at:new Date().toISOString(),controls,ignoredControls:{before,after},rows,minimumPassed:rows.every(r=>r.metrics.movingFps>=30)};
}
