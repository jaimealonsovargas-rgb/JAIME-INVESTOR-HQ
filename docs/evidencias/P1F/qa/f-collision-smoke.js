async(page)=>{
 const records=[];
 await page.evaluate(()=>{const colliders=window.__HQ_COLLIDERS__.filter(c=>c.center[1]+c.half[1]>.04&&c.center[1]-c.half[1]<1.78);window.__HQ_BODY_QA__={samples:0,penetrations:[]};function sample(){const p=window.__HQ_PLAYER__?.position,q=window.__HQ_BODY_QA__;if(p){q.samples++;for(const c of colliders){const dx=p[0]-c.center[0],dz=p[2]-c.center[2],co=Math.cos(c.yaw),s=Math.sin(c.yaw),lx=co*dx-s*dz,lz=s*dx+co*dz,x=lx-Math.max(-c.half[0],Math.min(c.half[0],lx)),z=lz-Math.max(-c.half[2],Math.min(c.half[2],lz));if(x*x+z*z<.348*.348&&q.penetrations.length<20)q.penetrations.push({position:p,collider:c});}}window.__HQ_BODY_QA_RAF__=requestAnimationFrame(sample);}sample();});
 async function press(key,ms){await page.locator('canvas').focus();await page.keyboard.down(key);await page.waitForTimeout(ms);await page.keyboard.up(key);await page.waitForTimeout(150);return await page.evaluate(()=>window.__HQ_PLAYER__);}
 async function teleport(label){await page.getByRole('button',{name:label}).click();await page.waitForTimeout(350);}
 await teleport(/Ir a RECEP/);
 const desk=await press('KeyW',1800),deskAgain=await press('KeyW',500);
 if(desk.position[2]<9.6||desk.position[2]>10.1||Math.abs(deskAgain.position[2]-desk.position[2])>.01)throw Error('Mostrador atravesado');
 records.push({obstacle:'mostrador',first:desk,second:deskAgain});
 await teleport(/Ir a RIESGOS/);
 let destination=[-11,-1.5];const walk=WALK;await walk(page);
 const glass=await press('KeyA',7000),glassAgain=await press('KeyA',500);
 if(glass.position[0]<-14.9||glass.position[0]>-14.7||Math.abs(glassAgain.position[0]-glass.position[0])>.01)throw Error('Cristal atravesado');
 records.push({obstacle:'mampara lateral Riesgos',first:glass,second:glassAgain});
 await teleport(/Ir a TRADING FLOOR/);
 destination=[5.5,3.35];await walk(page);
 const column=await press('KeyA',1000),columnAgain=await press('KeyA',500);
 records.push({obstacle:'columna 4.45 / 3.35, deslizamiento permitido',first:column,second:columnAgain});
 await teleport(/Ir a PERFORMANCE/);
 destination=[-5.5,12.5];await walk(page);
 const wall=await press('KeyS',3000),wallAgain=await press('KeyS',500);
 if(wall.position[2]<13.15||wall.position[2]>13.26||Math.abs(wallAgain.position[2]-wall.position[2])>.01)throw Error('Pared atravesada');
 records.push({obstacle:'pared sur Performance',first:wall,second:wallAgain});
 await teleport(/Ir a RECEP/);const body=await page.evaluate(()=>{cancelAnimationFrame(window.__HQ_BODY_QA_RAF__);return window.__HQ_BODY_QA__;});if(body.penetrations.length)throw Error('Penetraciones reales del avatar: '+JSON.stringify(body));return{input:'Teclas reales, sin escribir posiciones',records,body};
}
