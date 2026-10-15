async(page)=>{
 await page.reload();await page.setViewportSize({width:1920,height:1080});
 await page.waitForFunction(()=>Object.keys(window.__HQ_HUMANS__||{}).length===17,{},{timeout:40000});
 const captures=[];
 for(const [name,file] of [['Recepción','recepcion-final'],['Vista general','planta-final'],['Trading Floor','trading-final'],['Comité','comite-final'],['Videowall','videowall-final']]){
  await page.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(1000);
  await page.screenshot({path:'docs/evidencias/P1_PULIDO_ADAPTATIVO/'+file+'.png'});
  captures.push({name,metrics:await page.evaluate(()=>window.__HQ_METRICS__)});
 }
 await page.getByRole('button',{name:'Recorrer',exact:true}).click();await page.waitForTimeout(1000);
 await page.screenshot({path:'docs/evidencias/P1_PULIDO_ADAPTATIVO/recepcion-jugador-final.png'});
 return {at:new Date().toISOString(),captures,labels:await page.locator('.department-label').allTextContents(),humans:await page.evaluate(()=>window.__HQ_HUMANS__)};
}
