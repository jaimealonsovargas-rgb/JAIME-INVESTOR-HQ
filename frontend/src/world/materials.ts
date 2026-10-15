import { CanvasTexture, Color, MeshBasicMaterial, MeshPhysicalMaterial, MeshStandardMaterial, RepeatWrapping, SRGBColorSpace, Texture, Vector2 } from 'three';

export function textTexture(title: string, subtitle = '', kind: 'sign' | 'screen' | 'brand' | 'wallbrand' = 'sign') {
  const canvas = document.createElement('canvas');
  canvas.width = 1024; canvas.height = kind === 'screen' ? 576 : kind === 'sign' ? 128 : 256;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = kind === 'screen' ? '#091827' : '#171c20';
  if (kind !== 'sign'&&kind!=='wallbrand') ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ba9a6c';
  if (kind === 'screen') {
    ctx.font = '22px Arial'; ctx.fillText('JAIME INVESTOR HQ  /  PAPER ONLY', 40, 48);
    ctx.fillStyle = '#334856'; ctx.fillRect(40, 76, 944, 2);
    ctx.fillStyle = '#e5e7e5'; ctx.font = '36px Arial'; ctx.fillText(title, 40, 150);
    ctx.strokeStyle = '#335466'; ctx.lineWidth = 2; ctx.strokeRect(40, 208, 944, 250);
    ctx.fillStyle = '#90a9b6'; ctx.font = '30px Arial'; ctx.fillText('NO DISPONIBLE', 80, 302);
    ctx.fillStyle = '#7f97a6'; ctx.font = '23px Arial'; ctx.fillText(subtitle, 80, 350);
    ctx.font = '19px Arial'; ctx.fillText('Sin datos conectados · Sin órdenes', 40, 520);
  } else if (kind === 'sign') {
    ctx.textAlign = 'center'; ctx.font = '42px Arial'; ctx.fillText(title, 512, 62, 950);
    ctx.fillStyle = '#a99d89'; ctx.font = '19px Arial'; ctx.fillText(subtitle, 512, 100, 950);
  } else if(kind==='wallbrand'){
    ctx.textAlign='center';ctx.fillStyle='#172b38';ctx.font='130px Arial';ctx.fillText(title,512,150,940);
    ctx.font='30px Arial';ctx.fillText(subtitle,512,220,940);
  } else {
    ctx.textAlign = 'center'; ctx.font = kind === 'brand' ? '58px Georgia' : '44px Arial';
    ctx.fillText(title, 512, 110, 940);
    ctx.fillStyle = '#aeb8bb'; ctx.font = '21px Arial'; ctx.fillText(subtitle, 512, 169, 950);
  }
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace; texture.anisotropy = 4;
  return texture;
}

/** Videowall vivo: estados y datos locales; sin gráficas ni actividad decorativa. */
export function hqTexture(title:string,state:string,detail:string,source:string){
  const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=1536;
  const ctx=canvas.getContext('2d')!;
  const gradient=ctx.createLinearGradient(0,0,0,1536);gradient.addColorStop(0,'#102938');gradient.addColorStop(1,'#081720');
  ctx.fillStyle=gradient;ctx.fillRect(0,0,1024,1536);
  ctx.fillStyle='#bda274';ctx.fillRect(44,44,70,5);
  ctx.fillStyle='#f1eee6';ctx.font='600 80px Arial';ctx.fillText(title.toUpperCase(),44,136,936);
  ctx.fillStyle='#364b55';ctx.fillRect(44,184,936,2);
  // Un único estado real, sin curvas, indicadores de actividad ni cifras decorativas.
  ctx.fillStyle='#ddcba8';ctx.font='600 68px Arial';ctx.fillText(state,44,280,936);
  ctx.fillStyle='#cbd9df';ctx.font='64px Arial';
  const words=detail.split(/\s+/);let line='',y=430;
  for(const word of words){const next=line?line+' '+word:word;if(ctx.measureText(next).width>930&&line){ctx.fillText(line,44,y);y+=92;line=word;if(y>1194)break;}else line=next;}
  if(y<=1194)ctx.fillText(line,44,y,936);
  ctx.fillStyle='#364b55';ctx.fillRect(44,1320,936,2);
  ctx.fillStyle='#a8bdc5';ctx.font='48px Arial';ctx.fillText(source,44,1388,936);
  ctx.fillStyle='#bda274';ctx.font='40px Arial';ctx.fillText('SIMULACIÓN · PAPER ONLY',44,1484,936);
  const texture=new CanvasTexture(canvas);texture.colorSpace=SRGBColorSpace;texture.anisotropy=4;return texture;
}

function surfaceTexture(kind: 'fabric' | 'facade' | 'keys') {
  const c = document.createElement('canvas'); c.width = kind === 'fabric' ? 128 : 512; c.height = kind === 'facade' ? 1024 : 128;
  const ctx = c.getContext('2d')!;
  ctx.fillStyle = kind === 'facade' ? '#727b7e' : '#292d2d'; ctx.fillRect(0,0,c.width,c.height);
  if (kind === 'fabric') {
    for (let y = 0; y < 128; y += 2) for (let x = 0; x < 128; x += 2) { const n = 70 + ((x * 17 + y * 31) % 70); ctx.fillStyle = `rgb(${n},${n},${n})`; ctx.fillRect(x,y,1,1); }
  } else if (kind === 'facade') {
    for (let y = 0; y < 16; y++) for (let x = 0; x < 6; x++) {
      const n = (x * 19 + y * 13) % 11;
      ctx.fillStyle = n === 0 ? '#a59c8b' : n < 4 ? '#415766' : '#718691'; ctx.fillRect(x * 85 + 3, y * 64 + 3, 80, 56);
      ctx.fillStyle = '#899a9d'; ctx.fillRect(x * 85 + 4, y * 64 + 3, 1, 56);
      ctx.fillStyle = '#414b50'; ctx.fillRect(x * 85 + 3, y * 64 + 60, 81, 2);
    }
  } else {
    for (let y = 0; y < 5; y++) for (let x = 0; x < 15; x++) {
      ctx.fillStyle = '#5d6263'; ctx.fillRect(8 + x * 33, 7 + y * 23, 29, 18);
      ctx.fillStyle = '#383e40'; ctx.fillRect(9 + x * 33, 8 + y * 23, 27, 15);
      ctx.fillStyle = '#b6b8b4'; ctx.font = '7px Arial'; ctx.fillText(y ? 'QWERTYUIOPASDFG'[x] : '·', 13 + x * 33, 16 + y * 23);
    }
    ctx.fillStyle = '#5b6263'; ctx.fillRect(145,101,200,18);
  }
  const t = new CanvasTexture(c); t.wrapS = t.wrapT = RepeatWrapping; t.anisotropy = 4;
  if (kind !== 'fabric') t.colorSpace = SRGBColorSpace;
  return t;
}

export function makeMaterials(maps: Texture[]) {
  maps.forEach((map, index) => { map.wrapS = map.wrapT = RepeatWrapping; map.anisotropy = 4; if (index % 3 === 0) map.colorSpace = SRGBColorSpace; });
  const [woodMap, woodNormal, woodRough, stoneMap, stoneNormal, stoneRough] = maps;
  const floorMap = stoneMap.clone(); floorMap.repeat.set(8, 7); floorMap.needsUpdate = true;
  const floorNormal = stoneNormal.clone(); floorNormal.repeat.set(8, 7); floorNormal.needsUpdate = true;
  const wood = new MeshStandardMaterial({ map: woodMap, normalMap: woodNormal, roughnessMap: woodRough, color: '#b28f69', roughness: .58, normalScale: new Vector2(.08, .08) });
  // Acabado de nogal: desaturación del albedo CC0, sin modificar el fichero fuente.
  wood.onBeforeCompile = shader => { shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.075, 0.042, 0.021), 0.72);'); };
  wood.customProgramCacheKey = () => 'sims-walnut-v3';
  const floor=new MeshStandardMaterial({map:floorMap,normalMap:floorNormal,color:'#152638',roughness:.34,metalness:.16,normalScale:new Vector2(.09,.09)});
  floor.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\n diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.009,0.017,0.029),0.72);');};
  floor.customProgramCacheKey=()=> 'sims-blue-black-stone-v3';
  const shadowCanvas = document.createElement('canvas'); shadowCanvas.width = shadowCanvas.height = 128;
  const ctx = shadowCanvas.getContext('2d')!;
  const gradient = ctx.createRadialGradient(64, 64, 8, 64, 64, 62);
  gradient.addColorStop(0, '#0009'); gradient.addColorStop(.5, '#0005'); gradient.addColorStop(1, '#0000');
  ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
  const fabric = surfaceTexture('fabric');
  return {
    wood,
    contact: new MeshBasicMaterial({ map: new CanvasTexture(shadowCanvas), transparent: true, depthWrite: false, opacity: .7, polygonOffset: true, polygonOffsetFactor: -1 }),
    stone: new MeshStandardMaterial({ map: stoneMap, normalMap: stoneNormal, color: '#e1dccb', roughnessMap: stoneRough, roughness: .3, metalness: .08, normalScale: new Vector2(.07, .07) }),
    floor,
    bronze: new MeshStandardMaterial({ color: '#b9915e', metalness: .78, roughness: .28 }),
    dark: new MeshStandardMaterial({ color: '#151d22', roughness: .43, metalness: .35 }),
    steel: new MeshStandardMaterial({ color: '#a4a9a7', metalness: .88, roughness: .26 }),
    keys: new MeshStandardMaterial({ map: surfaceTexture('keys'), roughness: .72 }),
    leather: new MeshStandardMaterial({ color: '#252b2d', roughness: .58, bumpMap: fabric, bumpScale: .003 }),
    cognac: new MeshStandardMaterial({ color: '#76513c', roughness: .64, bumpMap: fabric, bumpScale: .003 }),
    carpet: new MeshStandardMaterial({ color: '#263b4b', roughness: 1, bumpMap: fabric, bumpScale: .006 }),
    cream: new MeshStandardMaterial({ color: '#a7987e', roughness: .82 }),
    ceiling: new MeshStandardMaterial({ color: '#50504c', roughness: .92 }),
    soffit: new MeshStandardMaterial({ color: '#20282d', roughness: 1, metalness: 0 }),
    glass: new MeshPhysicalMaterial({ color: '#e1e8e3', transparent: true, opacity: .085, roughness: .07, metalness: .15, depthWrite: false, side: 2,forceSinglePass:true }),
    light: new MeshBasicMaterial({ color: new Color('#ffe2b5').multiplyScalar(1.1), toneMapped: false }),
    green: new MeshStandardMaterial({ color: '#233d2c', roughness: .48, side: 2 }),
    greenLight: new MeshStandardMaterial({ color: '#496342', roughness: .57, side: 2 }),
    paper: new MeshStandardMaterial({ color: '#d6d2be', roughness: .95 }),
    book: new MeshStandardMaterial({ color: '#3b4e54', roughness: .9 }),
  };
}
export type Materials = ReturnType<typeof makeMaterials>;
