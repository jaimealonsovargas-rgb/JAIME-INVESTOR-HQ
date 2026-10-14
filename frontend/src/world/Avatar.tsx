import { memo, useEffect, useMemo, useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import { useFrame,useLoader } from '@react-three/fiber';
import { AnimationMixer, FileLoader,Frustum,Group,Matrix4,Mesh,MeshStandardMaterial,SkinnedMesh,Sphere,Vector3,type AnimationAction,type Material,type Skeleton } from 'three';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import type { PlayerRuntime } from './navigation';
import {sharedHumanLods,humanLodLevel,type HumanLods} from './humanLods';
const jsonLoader=(loader:FileLoader<unknown>)=>{loader.setResponseType('json');};

export default memo(function Avatar({player,variant=0,id='avatar',npc=false,contact}:{player?:PlayerRuntime;variant?:number;id?:string;npc?:boolean;contact?:Material}) {
  const data=useGLTF('/models/professional.glb');
  const lodData=useLoader(FileLoader,'/models/professional-lods.json',jsonLoader) as unknown as HumanLods;
  const lods=useMemo(()=>sharedHumanLods(data.scene,lodData),[data.scene,lodData]);
  const model=useMemo(()=>{const scene=clone(data.scene);scene.name=id;let skeleton:Skeleton|undefined;scene.traverse(o=>{if(o instanceof Mesh){o.castShadow=false;o.receiveShadow=false;o.frustumCulled=false;if(o instanceof SkinnedMesh){if(skeleton&&skeleton.bones.length===o.skeleton.bones.length&&o.skeleton.bones.every((b,i)=>b===skeleton!.bones[i]&&o.skeleton.boneInverses[i].equals(skeleton!.boneInverses[i])))o.skeleton=skeleton;else skeleton=o.skeleton;}const name=(o.material as MeshStandardMaterial).name;if(name==='suit'||name==='shoes'){o.material=(o.material as MeshStandardMaterial).clone();(o.material as MeshStandardMaterial).color.set(name==='shoes'?'#5b5d62':['#ffffff','#b0bacb','#b1b5ad'][variant%3]);}}});return scene;},[data.scene,variant,id]);
  const wrapper=useRef<Group>(null),level=useRef(0),elapsed=useRef(0),published=useRef(0);
  const shapes=useMemo(()=>({frustum:new Frustum(),matrix:new Matrix4(),sphere:new Sphere(new Vector3(),1.2),position:new Vector3()}),[]);
  const meshes=useMemo(()=>{const list:SkinnedMesh[]=[];model.traverse(o=>{if(o instanceof SkinnedMesh)list.push(o);});return list;},[model]);
  const mixer=useMemo(()=>new AnimationMixer(model),[model]);
  const actions=useRef<{idle:AnimationAction;walk:AnimationAction}>(null);
  const walking=useRef(false);
  const ambient=npc?['idle','observe','focus'][variant%3]:'idle';
  const reduced=useRef(false);
  useEffect(()=>{const preference=window.matchMedia('(prefers-reduced-motion: reduce)');const update=()=>{reduced.current=preference.matches;};update();preference.addEventListener('change',update);return()=>preference.removeEventListener('change',update);},[]);
  useEffect(()=>{const idle=mixer.clipAction(data.animations.find(a=>a.name===ambient)!),walk=mixer.clipAction(data.animations.find(a=>a.name==='walk')!);actions.current={idle,walk};idle.play();idle.time=variant*.39;walking.current=false;mixer.update(0);return()=>{actions.current=null;mixer.stopAllAction();mixer.uncacheRoot(model);delete window.__HQ_HUMANS__?.[id];};},[mixer,model,variant,data.animations,ambient,id]);
  useFrame(({camera},delta)=>{
    const clips=actions.current;if(!clips)return;const speed=player?.speed??0;const move=speed>.1;
    let distance=0,visible=true;
    if(npc&&wrapper.current){wrapper.current.getWorldPosition(shapes.position);shapes.sphere.center.copy(shapes.position).y+=.9;distance=camera.position.distanceTo(shapes.position);shapes.matrix.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);shapes.frustum.setFromProjectionMatrix(shapes.matrix);visible=distance<26&&shapes.frustum.intersectsSphere(shapes.sphere);wrapper.current.visible=visible;
     const next=humanLodLevel(distance,level.current);if(next!==level.current){for(const mesh of meshes)mesh.geometry=lods.get((mesh.material as MeshStandardMaterial).name)![next];level.current=next;}
    }
    if(move!==walking.current){const next=move?clips.walk:clips.idle,old=move?clips.idle:clips.walk;next.reset().play();old.crossFadeTo(next,.18,false);walking.current=move;}
    elapsed.current+=Math.min(delta,.05);const cadence=npc?(distance<8?1/20:distance<16?1/10:1/5):0;
    clips.walk.setEffectiveTimeScale(Math.max(.65,speed/1.6));if(visible&&elapsed.current>=cadence){mixer.update(reduced.current&&!move?0:Math.min(elapsed.current,.2));elapsed.current=0;}
    const now=performance.now();if(now-published.current>200){published.current=now;(window.__HQ_HUMANS__??={})[id]={kind:npc?'npc':'player',rigId:meshes[0]?.skeleton.uuid??'',bones:meshes[0]?.skeleton.bones.length??0,meshes:meshes.length,triangles:meshes.reduce((n,m)=>n+(m.geometry.index?.count??0)/3,0),visible,level:level.current,animation:move?'walk':ambient,state:npc?'OFFLINE':'JUGADOR LOCAL'};}
  });
  return <group ref={wrapper}><primitive object={model}/>{contact?<mesh rotation={[-Math.PI/2,0,0]} position={[0,.029,0]} material={contact}><planeGeometry args={[.85,.7]}/></mesh>:null}</group>;
});
declare global {interface Window {__HQ_HUMANS__?:Record<string,{kind:string;rigId:string;bones:number;meshes:number;triangles:number;visible:boolean;level:number;animation:string;state:string}>}}
