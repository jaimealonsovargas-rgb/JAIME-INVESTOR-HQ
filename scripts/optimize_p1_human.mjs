// Optimización offline. Conserva posiciones, UV, normales, rig, pesos y animaciones.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {MeshoptSimplifier} from '../frontend/node_modules/meshoptimizer/meshopt_simplifier.js';
await MeshoptSimplifier.ready;
const source=await readFile(new URL('../frontend/public/models/professional.glb',import.meta.url));
const jsonLength=source.readUInt32LE(12),gltf=JSON.parse(source.subarray(20,20+jsonLength).toString()),binStart=28+jsonLength;
function accessor(index){const a=gltf.accessors[index],view=gltf.bufferViews[a.bufferView];if(view.byteStride)throw Error('Se requiere buffer contiguo');const components={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type],length=a.count*components;const bytes={5123:2,5125:4,5126:4}[a.componentType];const start=binStart+(view.byteOffset??0)+(a.byteOffset??0);const data=source.subarray(start,start+length*bytes);return a.componentType===5126?Float32Array.from({length},(_,i)=>data.readFloatLE(i*4)):Uint32Array.from({length},(_,i)=>bytes===2?data.readUInt16LE(i*2):data.readUInt32LE(i*4));}
const output={version:1,sourceSha256:createHash('sha256').update(source).digest('hex'),parts:{}};
let near=0,medium=0,far=0;
for(const mesh of gltf.meshes){const primitive=mesh.primitives[0],positions=accessor(primitive.attributes.POSITION),indices=accessor(primitive.indices),name=gltf.materials[primitive.material].name;const levels=[];
 for(const [fraction,error] of [[.32,.009],[.085,.035]]){const [simplified]=MeshoptSimplifier.simplify(indices,positions,3,Math.floor(indices.length*fraction/3)*3,error,['LockBorder']);levels.push(Array.from(simplified));}
 output.parts[name]=levels;near+=indices.length/3;medium+=levels[0].length/3;far+=levels[1].length/3;
}
const data=Buffer.from(JSON.stringify(output));await writeFile(new URL('../frontend/public/models/professional-lods.json',import.meta.url),data);
const manifestUrl=new URL('../assets/P1_HUMAN_MANIFEST.json',import.meta.url),manifest=JSON.parse(await readFile(manifestUrl,'utf8'));
manifest.lods={file:'professional-lods.json',bytes:data.length,sha256:createHash('sha256').update(data).digest('hex'),nearTriangles:near,mediumTriangles:medium,farTriangles:far,license:'CC0-1.0',tool:'meshoptimizer 1.1.1 · MIT · offline'};
await writeFile(manifestUrl,JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify(manifest.lods));
