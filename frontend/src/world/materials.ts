import { CanvasTexture, Color, MeshBasicMaterial, MeshPhysicalMaterial, MeshStandardMaterial, RepeatWrapping, SRGBColorSpace, Texture, Vector2 } from 'three';

export function textTexture(title: string, subtitle = '', kind: 'sign' | 'screen' | 'brand' = 'sign') {
  const canvas = document.createElement('canvas');
  canvas.width = 1024; canvas.height = kind === 'screen' ? 576 : 256;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = kind === 'screen' ? '#091827' : '#171c20';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ba9a6c';
  if (kind === 'screen') {
    ctx.font = '22px Arial'; ctx.fillText('JAIME INVESTOR HQ  /  PAPER ONLY', 40, 48);
    ctx.fillStyle = '#334856'; ctx.fillRect(40, 76, 944, 2);
    ctx.fillStyle = '#e5e7e5'; ctx.font = '36px Arial'; ctx.fillText(title, 40, 150);
    ctx.strokeStyle = '#335466'; ctx.lineWidth = 2; ctx.strokeRect(40, 208, 944, 250);
    ctx.fillStyle = '#90a9b6'; ctx.font = '30px Arial'; ctx.fillText('NO DISPONIBLE', 80, 302);
    ctx.fillStyle = '#7f97a6'; ctx.font = '23px Arial'; ctx.fillText(subtitle, 80, 350);
    ctx.font = '19px Arial'; ctx.fillText('Sin datos conectados · Sin órdenes', 40, 520);
  } else {
    ctx.textAlign = 'center'; ctx.font = kind === 'brand' ? '58px Georgia' : '44px Arial';
    ctx.fillText(title, 512, 110, 940);
    ctx.fillStyle = '#aeb8bb'; ctx.font = '21px Arial'; ctx.fillText(subtitle, 512, 169, 950);
  }
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace; texture.anisotropy = 4;
  return texture;
}

export function makeMaterials(maps: Texture[]) {
  maps.forEach((map, index) => { map.wrapS = map.wrapT = RepeatWrapping; map.anisotropy = 4; if (index % 3 === 0) map.colorSpace = SRGBColorSpace; });
  const [woodMap, woodNormal, woodRough, stoneMap, stoneNormal, stoneRough] = maps;
  const floorMap = stoneMap.clone(); floorMap.repeat.set(11, 9); floorMap.needsUpdate = true;
  const floorNormal = stoneNormal.clone(); floorNormal.repeat.set(11, 9); floorNormal.needsUpdate = true;
  const wood = new MeshStandardMaterial({ map: woodMap, normalMap: woodNormal, roughnessMap: woodRough, color: '#8d7964', roughness: .86, normalScale: new Vector2(.14, .14) });
  // Acabado de nogal: desaturación del albedo CC0, sin modificar el fichero fuente.
  wood.onBeforeCompile = shader => { shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n diffuseColor.rgb = mix(diffuseColor.rgb, vec3(dot(diffuseColor.rgb, vec3(0.299, 0.587, 0.114))), 0.65);'); };
  wood.customProgramCacheKey = () => 'walnut-stain-v1';
  const shadowCanvas = document.createElement('canvas'); shadowCanvas.width = shadowCanvas.height = 128;
  const ctx = shadowCanvas.getContext('2d')!;
  const gradient = ctx.createRadialGradient(64, 64, 8, 64, 64, 62);
  gradient.addColorStop(0, '#0009'); gradient.addColorStop(.5, '#0005'); gradient.addColorStop(1, '#0000');
  ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
  return {
    wood,
    contact: new MeshBasicMaterial({ map: new CanvasTexture(shadowCanvas), transparent: true, depthWrite: false, opacity: .7, polygonOffset: true, polygonOffsetFactor: -1 }),
    stone: new MeshStandardMaterial({ map: stoneMap, normalMap: stoneNormal, color: '#454b50', roughnessMap: stoneRough, roughness: .36, metalness: .15, normalScale: new Vector2(.12, .12) }),
    floor: new MeshStandardMaterial({ map: floorMap, normalMap: floorNormal, color: '#2f363d', roughness: .35, metalness: .15, normalScale: new Vector2(.1, .1) }),
    bronze: new MeshStandardMaterial({ color: '#b9915e', metalness: .78, roughness: .28 }),
    dark: new MeshStandardMaterial({ color: '#151d22', roughness: .43, metalness: .35 }),
    leather: new MeshStandardMaterial({ color: '#30383c', roughness: .78 }),
    cognac: new MeshStandardMaterial({ color: '#604938', roughness: .85 }),
    carpet: new MeshStandardMaterial({ color: '#202d35', roughness: 1 }),
    cream: new MeshStandardMaterial({ color: '#d0c5ac', roughness: .78 }),
    ceiling: new MeshStandardMaterial({ color: '#66676a', roughness: .92 }),
    soffit: new MeshStandardMaterial({ color: '#20282d', roughness: 1, metalness: 0 }),
    glass: new MeshPhysicalMaterial({ color: '#a6c7cf', transparent: true, opacity: .13, roughness: .12, metalness: .3, depthWrite: false, side: 2 }),
    light: new MeshBasicMaterial({ color: new Color('#ffdfad').multiplyScalar(1.65), toneMapped: false }),
    green: new MeshStandardMaterial({ color: '#425846', roughness: .75, side: 2 }),
    greenLight: new MeshStandardMaterial({ color: '#6b7851', roughness: .7, side: 2 }),
    paper: new MeshStandardMaterial({ color: '#d6d2be', roughness: .95 }),
    book: new MeshStandardMaterial({ color: '#3b4e54', roughness: .9 }),
    city: new MeshStandardMaterial({ color: '#617d87', roughness: .62, metalness: .22 }),
    cityDark: new MeshStandardMaterial({ color: '#415e6e', roughness: .5, metalness: .32 }),
    window: new MeshBasicMaterial({ color: '#a9c0c4', transparent: true, opacity: .32 }),
  };
}
export type Materials = ReturnType<typeof makeMaterials>;
