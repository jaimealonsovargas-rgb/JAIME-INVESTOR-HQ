import { BatchedMesh, Group, Material, Mesh } from 'three';

/** Misma geometría/materiales y culling por pieza; menos cambios de estado WebGL. */
export function batchStaticOffice(office:Group){
 const groups=new Map<string,Mesh[]>();
 office.updateMatrixWorld(true);
 office.traverse(object=>{if(!(object instanceof Mesh)||Array.isArray(object.material))return;
  const key=[object.material.uuid,object.castShadow,object.receiveShadow,object.renderOrder,Object.keys(object.geometry.attributes).sort().join(',')].join(':');
  const meshes=groups.get(key)??[];meshes.push(object);groups.set(key,meshes);
 });
 const batches:BatchedMesh[]=[];
 for(const meshes of groups.values()){
  if(meshes.length<2)continue;
  const vertices=meshes.reduce((n,m)=>n+m.geometry.attributes.position.count,0),indices=meshes.reduce((n,m)=>n+(m.geometry.index?.count??m.geometry.attributes.position.count),0);
  const first=meshes[0],batch=new BatchedMesh(meshes.length,vertices,indices,first.material as Material);
  batch.name='static-batch:'+(first.material as Material).name;batch.castShadow=first.castShadow;batch.receiveShadow=first.receiveShadow;batch.renderOrder=first.renderOrder;
  batch.perObjectFrustumCulled=true;batch.sortObjects=true;
  for(const mesh of meshes){const geometry=batch.addGeometry(mesh.geometry),instance=batch.addInstance(geometry);batch.setMatrixAt(instance,mesh.matrixWorld);}
  batch.computeBoundingBox();batch.computeBoundingSphere();
  for(const mesh of meshes){mesh.removeFromParent();mesh.geometry.dispose();}
  office.add(batch);batches.push(batch);
 }
 return batches;
}
