import type { Object3D,Skeleton } from 'three';
const poses=new WeakMap<Skeleton,()=>void>();
const worlds=new WeakMap<Object3D,(force?:boolean)=>void>();

/** NPC inmóvil: subir huesos a GPU solo cuando cambia su pose ambiental. */
export function cacheSkeletonPose(skeleton:Skeleton){
 const existing=poses.get(skeleton);if(existing)return existing;
 let dirty=true;const update=skeleton.update.bind(skeleton);
 skeleton.update=()=>{if(!dirty)return;update();dirty=false;};
 const mark=()=>{dirty=true;};poses.set(skeleton,mark);return mark;
}

export function cacheNpcWorldMatrices(model:Object3D){
 const existing=worlds.get(model);if(existing)return existing;
 const update=model.updateMatrixWorld.bind(model);model.updateMatrixWorld=()=>{};
 worlds.set(model,update);return update;
}
