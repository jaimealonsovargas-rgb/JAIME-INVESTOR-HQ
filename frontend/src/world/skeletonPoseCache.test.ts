import {it,expect} from 'vitest';
import {Bone,Matrix4,Skeleton} from 'three';
import {cacheSkeletonPose} from './skeletonPoseCache';

it('mantiene la pose GPU entre ticks y actualiza solo el rig marcado',()=>{
 const bone=new Bone(),skeleton=new Skeleton([bone],[new Matrix4()]);
 const otherBone=new Bone(),other=new Skeleton([otherBone],[new Matrix4()]);
 const mark=cacheSkeletonPose(skeleton);cacheSkeletonPose(other);
 expect(cacheSkeletonPose(skeleton)).toBe(mark);
 skeleton.update();other.update();
 bone.position.x=2;bone.updateMatrixWorld(true);skeleton.update();
 expect(skeleton.boneMatrices![12]).toBe(0);
 mark();skeleton.update();expect(skeleton.boneMatrices![12]).toBe(2);
 expect(other.boneMatrices![12]).toBe(0);
 skeleton.dispose();other.dispose();
});
