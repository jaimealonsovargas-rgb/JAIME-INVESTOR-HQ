async(page)=>{
  const result={teleports:[],input:{}};
  const labels=['RESEARCH','COMITÉ DE INVERSIÓN','QUANT LAB','RIESGOS','TRADING FLOOR','EJECUCIÓN','PERFORMANCE','RECEPCIÓN','SISTEMAS / DATA QUALITY'];
  for(const label of labels){await page.getByRole('button',{name:'Ir a '+label,exact:true}).click();await page.waitForTimeout(250);const pose=await page.evaluate(()=>({player:window.__HQ_PLAYER__,camera:window.__HQ_METRICS__?.camera}));result.teleports.push({label,...pose});}
  await page.getByRole('button',{name:'Ir a TRADING FLOOR',exact:true}).click();await page.waitForTimeout(150);
  await page.locator('canvas').focus();const before=await page.evaluate(()=>window.__HQ_PLAYER__);
  await page.keyboard.down('KeyD');await page.waitForTimeout(600);await page.keyboard.up('KeyD');await page.waitForTimeout(150);
  const after=await page.evaluate(()=>window.__HQ_PLAYER__);if(!(after.position[0]>before.position[0]+.2))throw Error('WASD sin movimiento');result.input.movement={before,after};
  await page.mouse.move(850,500);await page.mouse.down({button:'right'});await page.mouse.move(1100,540,{steps:10});await page.mouse.up({button:'right'});await page.mouse.wheel(0,2000);await page.waitForTimeout(150);result.input.mouse=await page.evaluate(()=>window.__HQ_PLAYER__);
  if(result.input.mouse.distance!==4.5||result.input.mouse.cameraYaw===0)throw Error('Ratón/zoom sin respuesta');
  const saved=await page.evaluate(()=>window.__HQ_PLAYER__);await page.getByRole('button',{name:'Planta completa',exact:true}).click();await page.getByRole('button',{name:'Recorrer',exact:true}).click();await page.waitForTimeout(150);result.input.restored=await page.evaluate(()=>window.__HQ_PLAYER__);
  if(JSON.stringify(saved.position)!==JSON.stringify(result.input.restored.position)||saved.cameraYaw!==result.input.restored.cameraYaw||saved.distance!==result.input.restored.distance)throw Error('Inspección perdió transform');
  await page.getByRole('button',{name:'Ir a RECEPCIÓN',exact:true}).click();await page.waitForTimeout(200);await page.screenshot({path:'output/playwright/c-recepcion.png',timeout:20000});
  return result;
}
