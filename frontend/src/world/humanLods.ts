import {BufferAttribute,BufferGeometry,Mesh,type Object3D} from 'three';
export interface HumanLods {version:1;parts:Record<string,[number[],number[]]>}
const cache=new WeakMap<Object3D,Map<string,BufferGeometry[]>>();
export function sharedHumanLods(source:Object3D,data:HumanLods) {
 const existing=cache.get(source);if(existing)return existing;
 if(data.version!==1||!data.parts)throw Error('LOD humano no válido');
 const geometries=new Map<string,BufferGeometry[]>();
 source.traverse(o=>{if(!(o instanceof Mesh))return;const name=Array.isArray(o.material)?'':o.material.name;const parts=data.parts[name];if(!parts||parts.length!==2)throw Error('LOD humano incompleto');
  const levels=[o.geometry];for(const indices of parts){if(!indices.length||indices.length%3||indices.some(i=>!Number.isInteger(i)||i<0||i>=o.geometry.getAttribute('position').count))throw Error('Índices LOD no válidos');
   const geometry=new BufferGeometry();for(const key in o.geometry.attributes)geometry.setAttribute(key,o.geometry.getAttribute(key));geometry.setIndex(new BufferAttribute(Uint32Array.from(indices),1));geometry.boundingBox=o.geometry.boundingBox;geometry.boundingSphere=o.geometry.boundingSphere;levels.push(geometry);
  }geometries.set(name,levels);
 });cache.set(source,geometries);return geometries;
}
export function humanLodLevel(distance:number,previous:number) {if(distance>16.7)return 2;if(distance<7.3)return 0;if(previous===2&&distance>=15.3)return 2;if(previous===0&&distance<=8.7)return 0;return 1;}
