import {describe,it,expect} from 'vitest';
import {Mesh,Matrix4,BoxGeometry,MeshStandardMaterial,Group,BatchedMesh} from 'three';
import {batchStaticOffice} from './staticBatches';

describe('batching estático conserva geometría y transform',()=>{
 it('conserva piezas, índices, transformaciones, transparencia y sombras distintas',()=>{
  const root=new Group(),stone=new MeshStandardMaterial(),glass=new MeshStandardMaterial({transparent:true,opacity:.1});
  for(let i=0;i<6;i++){const parent=new Group();parent.position.set(i*2,1,-i);const mesh=new Mesh(new BoxGeometry(1,2,3),i<4?stone:glass);mesh.position.set(.3,0,.7);mesh.castShadow=i!==0;parent.add(mesh);root.add(parent);}
  root.updateMatrixWorld(true);const originals:Mesh[]=[];root.traverse(o=>{if(o instanceof Mesh)originals.push(o);});
  const expected=originals.map(m=>({matrix:m.matrixWorld.clone(),material:m.material,shadow:m.castShadow}));
  const triangles=originals.reduce((n,m)=>n+m.geometry.index!.count/3,0);
  const batches=batchStaticOffice(root);expect(batches.length).toBe(2);
  let actual=0;const pieces:{matrix:Matrix4;material:unknown;shadow:boolean}[]=[];
  root.traverse(o=>{if(o instanceof Mesh){actual+=o.geometry.index!.count/3;if(o instanceof BatchedMesh){for(let i=0;i<o.instanceCount;i++){const matrix=new Matrix4();o.getMatrixAt(i,matrix);pieces.push({matrix,material:o.material,shadow:o.castShadow});}}else pieces.push({matrix:o.matrixWorld.clone(),material:o.material,shadow:o.castShadow});}});
  expect(actual).toBe(triangles);expect(pieces).toHaveLength(6);
  for(const piece of expected)expect(pieces.some(p=>p.matrix.elements.every((value,i)=>Math.abs(value-piece.matrix.elements[i])<1e-6)&&p.material===piece.material&&p.shadow===piece.shadow)).toBe(true);
 });
});
