async(page)=>{
 return await page.evaluate(()=>{
  window.__HQ_CAMERA_QA__={samples:0,minHeight:100,maxHeight:0,collisions:[],crossings:[]};let previous;
  const tick=()=>{const p=window.__HQ_PLAYER__,q=window.__HQ_CAMERA_QA__,cs=window.__HQ_COLLIDERS__;
   if(p&&p.mode==='play'&&!p.paused&&cs){const a=p.camera;q.samples++;q.minHeight=Math.min(q.minHeight,a[1]);q.maxHeight=Math.max(q.maxHeight,a[1]);
    const hits=cs.filter(c=>{const dx=a[0]-c.center[0],dz=a[2]-c.center[2],co=Math.cos(c.yaw),s=Math.sin(c.yaw),x=co*dx-s*dz,z=s*dx+co*dz;return Math.abs(x)<c.half[0]-.001&&Math.abs(a[1]-c.center[1])<c.half[1]-.001&&Math.abs(z)<c.half[2]-.001;});if(hits.length&&q.collisions.length<20)q.collisions.push({camera:a,player:p.position,colliders:hits});
    if(previous&&Math.hypot(a[0]-previous[0],a[2]-previous[2])<1&&Math.hypot(p.position[0]-previous[3],p.position[2]-previous[4])<.5){
     for(const c of cs){const co=Math.cos(c.yaw),s=Math.sin(c.yaw),local=b=>{const dx=b[0]-c.center[0],dz=b[2]-c.center[2];return [co*dx-s*dz,b[1]-c.center[1],s*dx+co*dz];},from=local(previous),to=local(a);let lo=0,hi=1;
      for(let ax=0;ax<3;ax++){const d=to[ax]-from[ax],h=c.half[ax]-.001;if(Math.abs(d)<1e-9){if(Math.abs(from[ax])>h){hi=-1;break;}}else{const one=(-h-from[ax])/d,two=(h-from[ax])/d;lo=Math.max(lo,Math.min(one,two));hi=Math.min(hi,Math.max(one,two));}}
      if(lo<=hi&&hi>=0&&lo<=1&&q.crossings.length<20)q.crossings.push({from:previous.slice(0,3),to:a,collider:c});
     }
    }previous=[...a,p.position[0],p.position[2]];
   }window.__HQ_CAMERA_QA_RAF__=requestAnimationFrame(tick);};tick();return 'Observador de cámara activado, sin modificar controles ni posición';
 });
}
