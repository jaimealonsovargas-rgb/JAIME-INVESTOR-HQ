async(page)=>{
 const spec=SPEC;
 await page.getByRole('button',{name:'Ir a '+spec.label,exact:true}).click();await page.waitForTimeout(200);
 const walk=WALK;
 const trace=await walk(page);
 const p=await page.evaluate(()=>window.__HQ_PLAYER__.position),dx=spec.anchor[0]-p[0],dz=spec.anchor[2]-p[2];
 const keys=[];if(Math.abs(dx)>Math.abs(dz)/2.5)keys.push(dx>0?'KeyD':'KeyA');if(Math.abs(dz)>Math.abs(dx)/2.5)keys.push(dz>0?'KeyS':'KeyW');
 await page.locator('canvas').focus();for(const key of keys)await page.keyboard.down(key);await page.waitForTimeout(220);for(const key of keys)await page.keyboard.up(key);await page.waitForTimeout(600);
 await page.waitForFunction(id=>window.__HQ_TERMINALS__?.some(m=>m.id===id&&m.accessible),spec.id,{timeout:5000});
 const before=await page.evaluate(()=>window.__HQ_PLAYER__);await page.keyboard.press('KeyE');await page.getByRole('dialog').waitFor();
 await page.getByRole('heading',{name:spec.title,exact:true}).waitFor();const text=await page.getByRole('dialog').innerText();
 const focused=await page.evaluate(()=>document.activeElement.textContent);if(!focused.startsWith('Volver a la oficina'))throw Error('Foco inicial incorrecto');
 await page.keyboard.down('KeyW');await page.keyboard.down('ArrowRight');await page.waitForTimeout(250);await page.keyboard.up('KeyW');await page.keyboard.up('ArrowRight');
 const paused=await page.evaluate(()=>window.__HQ_PLAYER__);if(JSON.stringify(before.position)!==JSON.stringify(paused.position)||before.cameraYaw!==paused.cameraYaw)throw Error('Movimiento durante modal');
 await page.screenshot({path:'output/playwright/d-'+spec.id+'.png',timeout:20000});await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});await page.waitForTimeout(150);
 const after=await page.evaluate(()=>window.__HQ_PLAYER__);for(const key of ['position','yaw','cameraYaw','pitch','distance','camera'])if(JSON.stringify(before[key])!==JSON.stringify(after[key]))throw Error('Transform no restaurado: '+key);
 if(await page.evaluate(()=>document.activeElement.tagName)!=='CANVAS')throw Error('Foco no devuelto');
 const pixel=await page.evaluate(id=>window.__HQ_TERMINALS__.find(m=>m.id===id),spec.id);if(!pixel.visible||!pixel.accessible)throw Error('Monitor físico fuera de vista');
 await page.mouse.click(pixel.x,pixel.y);await page.getByRole('dialog').waitFor();await page.getByRole('heading',{name:spec.title,exact:true}).waitFor();await page.getByRole('button',{name:'Volver a la oficina Esc',exact:true}).click();
 return {id:spec.id,trace,before,paused,after,physicalClick:pixel,focused,text};
}
