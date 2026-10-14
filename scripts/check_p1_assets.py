"""Comprueba integridad, procedencia y skinning de los assets P1, sin red."""
from pathlib import Path
import hashlib
import json
import math
import struct

ROOT=Path(__file__).resolve().parents[1]

def verify(base,record):
    path=(base/record['file']).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError('Ruta de asset fuera de su directorio')
    raw=path.read_bytes()
    if len(raw)!=record['bytes'] or hashlib.sha256(raw).hexdigest()!=record['sha256']:
        raise ValueError(f"Integridad incorrecta: {record['file']}")
    return raw

sources=json.loads((ROOT/'assets/source-humans/SOURCE_MANIFEST.json').read_text())
materials=json.loads((ROOT/'assets/P1_ASSET_MANIFEST.json').read_text())
for record in materials:
    verify(ROOT/'frontend/public/materials',record)
    assert record['license']=='CC0-1.0' and record['authors'] and record['license_source']
for record in sources:
    verify(ROOT/'assets/source-humans',record)
    if record['file'] not in ['LICENSE.md','LICENSE.ASSETS.md'] and not record['license'].startswith('CC0'):
        raise ValueError('Licencia gráfica no verificada')
manifest=json.loads((ROOT/'assets/P1_HUMAN_MANIFEST.json').read_text())
model_dir=ROOT/'frontend/public/models'
raw=verify(model_dir,manifest)
for record in manifest['textures']:
    verify(model_dir,record)
lod_raw=verify(model_dir,manifest['lods'])
lods=json.loads(lod_raw)
if lods['sourceSha256']!=manifest['sha256']:
    raise ValueError('Los LOD no corresponden al GLB actual')
magic,version,total=struct.unpack_from('<4sII',raw)
assert magic==b'glTF' and version==2 and total==len(raw)
length=struct.unpack_from('<I',raw,12)[0]
g=json.loads(raw[20:20+length]);binary=raw[28+length:]
assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==manifest['bones']
assert {n['skin'] for n in g['nodes'] if 'mesh' in n}=={0}
assert {a['name'] for a in g['animations']}==set(manifest['animations'])
for image in g['images']:
    assert not image['uri'].startswith(('http:','https:','data:'))
    assert (model_dir/image['uri']).resolve().is_relative_to(model_dir.resolve())

def values(index):
    a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
    assert not v.get('byteStride')
    size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    fmt={5123:'H',5125:'I',5126:'f'}[a['componentType']]
    return struct.unpack_from('<'+fmt*(a['count']*size),binary,v.get('byteOffset',0)+a.get('byteOffset',0))

triangles=0;heights=[];counts=[0,0]
for mesh in g['meshes']:
    p=mesh['primitives'][0];a=p['attributes'];positions=values(a['POSITION']);indices=values(p['indices'])
    vertices=len(positions)//3;assert max(indices)<vertices
    assert all(math.isfinite(x) for x in positions);heights.extend(positions[1::3]);triangles+=len(indices)//3
    joints=values(a['JOINTS_0']);weights=values(a['WEIGHTS_0'])
    assert len(joints)==len(weights)==vertices*4 and max(joints)<manifest['bones']
    assert all(abs(sum(weights[i:i+4])-1)<1e-4 for i in range(0,len(weights),4))
    name=g['materials'][p['material']]['name']
    for level,indices_lod in enumerate(lods['parts'][name]):
        assert len(indices_lod)%3==0 and min(indices_lod)>=0 and max(indices_lod)<vertices
        counts[level]+=len(indices_lod)//3
assert triangles==manifest['triangles']==manifest['lods']['nearTriangles']
assert counts==[manifest['lods']['mediumTriangles'],manifest['lods']['farTriangles']]
height=max(heights)-min(heights)
assert 1.7<height<1.9
print(json.dumps({'source_files_verified':len(sources),'material_maps_verified':len(materials),'textures_verified':len(manifest['textures']),'glb_sha256':manifest['sha256'],'height_mesh_m':round(height,4),'mesh_min_y':round(min(heights),4),'mesh_max_y':round(max(heights),4),'bones':manifest['bones'],'triangles':[triangles,*counts],'animations':manifest['animations'],'license':'CC0-1.0 graphical assets; MIT offline optimizer','network_requests':0}))
