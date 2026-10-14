async(page)=>{
 await page.getByRole('button',{name:/Ir a SISTEMAS/}).click();
 const walk=WALK;
 const route=await walk(page);
 await page.locator('canvas').focus();
 await page.keyboard.down('KeyD');await page.keyboard.down('KeyW');await page.waitForTimeout(220);await page.keyboard.up('KeyD');await page.keyboard.up('KeyW');await page.waitForTimeout(600);
 await page.keyboard.press('KeyE');await page.getByRole('dialog').waitFor();
 await page.route('**/health',r=>r.abort());await page.route('**/api/providers/status',r=>r.abort());
 try{
  await page.getByRole('button',{name:/Actualizar/}).click();
  await page.getByText(/NO DISPONIBLE: no se pudo verificar el backend/).waitFor();
  await page.screenshot({path:'docs/evidencias/P1F/10-offline.png',timeout:20000});
  const content=await page.getByRole('dialog').innerText();
  await page.keyboard.press('Escape');
  const before=await page.evaluate(()=>window.__HQ_PLAYER__);
  await page.keyboard.down('KeyA');await page.waitForTimeout(450);await page.keyboard.up('KeyA');await page.waitForTimeout(150);
  const after=await page.evaluate(()=>window.__HQ_PLAYER__);
  if(Math.abs(after.position[0]-before.position[0])<.1)throw Error('Mundo inmovilizado sin backend');
  return{method:'Peticiones locales abortadas en el navegador; backend intacto',route,content,before,after};
 }finally{await page.unroute('**/health');await page.unroute('**/api/providers/status');}
}
