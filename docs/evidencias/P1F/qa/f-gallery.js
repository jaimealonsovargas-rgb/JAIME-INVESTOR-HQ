async(page)=>{
 await page.getByRole('button',{name:/Ir a EJECUCI/}).click();
 await page.waitForTimeout(350);
 const walk=WALK;const route=await walk(page);
 await page.locator('canvas').focus();
 const box=await page.locator('canvas').boundingBox();const x=box.x+box.width/2,y=box.y+box.height/2;
 await page.mouse.move(x,y);await page.mouse.down({button:'right'});await page.mouse.move(x+524,y,{steps:30});await page.mouse.up({button:'right'});
 await page.keyboard.down('KeyW');await page.waitForTimeout(180);await page.keyboard.up('KeyW');await page.waitForTimeout(1000);
 await page.screenshot({path:'docs/evidencias/P1F/08-skyline.png',timeout:20000});
 const skyline=await page.evaluate(()=>window.__HQ_PLAYER__);
 await page.getByRole('button',{name:/Ir a COMIT/}).click();await page.waitForTimeout(1200);
 await page.screenshot({path:'docs/evidencias/P1F/12-comite-entrada.png',timeout:20000});
 await page.getByRole('button',{name:/Ir a TRADING FLOOR/}).click();await page.waitForTimeout(1200);
 await page.screenshot({path:'docs/evidencias/P1F/09-escena-npc-minimapa.png',timeout:20000});
 const humans=await page.evaluate(()=>Object.values(window.__HQ_HUMANS__));
 if(humans.length!==11||new Set(humans.map(h=>h.rigId)).size!==11)throw Error('Rigs compartidos o personal ausente');
 await page.getByRole('button',{name:/Ir a RECEP/}).click();
 return{route,skyline,humans};
}
