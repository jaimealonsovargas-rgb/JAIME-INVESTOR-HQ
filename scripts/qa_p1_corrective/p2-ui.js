async(page)=>{
 const d=page.getByRole('dialog'),q=d.locator('.data-quality'),requests=[];
 const track=r=>{if(r.url().includes('/api/data/sources/'))requests.push(r.url().split('/').at(-1));};page.on('request',track);
 await q.getByRole('heading',{name:'Fuentes y calidad de datos',exact:true}).waitFor();
 await q.locator('.data-sources-scroll tbody tr').first().waitFor();const initial=await q.locator('.data-sources-scroll tbody tr').count();if(initial!==35)throw Error('Inventario incompleto '+initial);
 const filters=[],selects=q.locator('.data-filters select');
 for(const [index,value] of [[0,'FX'],[1,'ES'],[2,'STATISTICS'],[3,'news_metadata']]){await selects.nth(index).selectOption(value);const count=await q.locator('.data-sources-scroll tbody tr').count();if(!count||count>=35)throw Error('Filtro no funciona '+value);filters.push({index,value,count});await selects.nth(index).selectOption('');}
 await q.locator('.data-sources-scroll tbody tr').filter({hasText:'B01 ·'}).getByRole('button',{name:'Ver fuente',exact:true}).click();await page.waitForTimeout(250);
 if(!await q.locator('.source-detail').getByRole('button',{name:'Consultar preset',exact:true}).isDisabled()||requests.includes('B01'))throw Error('Consulta sin credenciales');const credentials=await q.locator('.source-detail').innerText();
 await q.getByRole('button',{name:'Pausar consultas de esta vista',exact:true}).click();
 const before=requests.length;await q.locator('.data-sources-scroll tbody tr').filter({hasText:'A20 ·'}).getByRole('button',{name:'Ver fuente',exact:true}).click();await page.waitForTimeout(500);if(requests.length!==before)throw Error('Pausa permite consulta');
 await q.locator('.source-detail').getByRole('button',{name:'Consultar preset',exact:true}).click();await q.locator('.source-detail').getByText(/observaciones normalizadas/).waitFor({timeout:30000});const news=await q.locator('.source-detail').innerText();if(!news.includes('BCE')||!news.includes('5 observaciones'))throw Error('Noticias no verificadas');
 await q.locator('.source-detail').scrollIntoViewIfNeeded();await page.screenshot({path:'docs/evidencias/P2/sistemas-noticias.png'});
 await q.getByRole('button',{name:'Reanudar consultas de esta vista',exact:true}).click();await q.locator('.data-sources-scroll tbody tr').filter({hasText:'A01 ·'}).getByRole('button',{name:'Ver fuente',exact:true}).click();await q.locator('.source-detail').getByText(/observaciones normalizadas/).waitFor({timeout:30000});
 const reference=await q.locator('.source-detail').innerText();if(!reference.includes('USD/EUR'))throw Error('Divisa de referencia ambigua');
 await q.getByRole('heading',{name:'Fuentes y calidad de datos',exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:'docs/evidencias/P2/sistemas-data-quality.png'});
 const counts=await q.locator('.data-counts').innerText();page.off('request',track);return{at:new Date().toISOString(),initial,filters,credentials,news,reference,counts,requests};
}
