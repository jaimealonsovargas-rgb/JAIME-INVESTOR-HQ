async(page)=>{
 if(await page.getByRole('dialog').isVisible())await page.keyboard.press('Escape');
 const rows=[],controls=[],az=0,co=Math.cos(az),si=Math.sin(az);await page.getByRole('button',{name:'Recorrer',exact:true}).click();
 await page.getByRole('button',{name:'Ir a RECEPCI\u00d3N',exact:true}).click();await page.waitForTimeout(800);
 await page.locator('canvas').focus();await page.keyboard.down('ArrowUp');await page.waitForTimeout(600);await page.keyboard.up('ArrowUp');await page.waitForTimeout(500);
 const pose=()=>page.evaluate(()=>window.__HQ_PLAYER__);
 for(const [key,opposite] of [['ArrowUp','ArrowDown'],['ArrowRight','ArrowLeft'],['ArrowDown','ArrowUp'],['ArrowLeft','ArrowRight']]){
  await page.locator('canvas').focus();const before=await pose();await page.keyboard.down(key);await page.waitForTimeout(500);await page.keyboard.up(key);await page.waitForTimeout(200);const after=await pose(),dx=after.position[0]-before.position[0],dz=after.position[2]-before.position[2],x=dx*co-dz*si,y=(dx*si+dz*co);
  if(Math.hypot(dx,dz)<.2||(key==='ArrowUp'&&y>=0)||(key==='ArrowDown'&&y<=0)||(key==='ArrowRight'&&x<=0)||(key==='ArrowLeft'&&x>=0))throw Error('Direccion de pantalla incorrecta '+key);
  controls.push({key,before,after,screenDelta:[x,y]});await page.keyboard.down(opposite);await page.waitForTimeout(500);await page.keyboard.up(opposite);await page.waitForTimeout(250);
 }
 await page.waitForTimeout(600);const before=await pose();for(const key of ['w','a','s','d']){await page.keyboard.down(key);await page.waitForTimeout(150);await page.keyboard.up(key);}await page.mouse.move(900,500);await page.mouse.down({button:'right'});await page.mouse.move(1100,650);await page.mouse.up({button:'right'});await page.mouse.wheel(0,600);await page.waitForTimeout(500);const after=await pose();if(Math.hypot(before.position[0]-after.position[0],before.position[2]-after.position[2])>.01||Math.hypot(...before.camera.map((v,i)=>v-after.camera[i]))>.03)throw Error('WASD/raton alteran juego');
 return {controls,ignoredControls:{before,after}};
}
