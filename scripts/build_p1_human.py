"""Conversión reproducible OBJ/MHCLO/rig CC0 a glTF 2 binario, sin Blender.

Implementación propia. Mantiene pesos oficiales, adapta ropa por coordenadas
baricéntricas y excluye helpers/cuerpo cubierto. Animaciones idle/walk originales.
"""
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets/source-humans'
DEST = ROOT / 'frontend/public/models'


def obj(path):
    positions, uv, faces = [], [], []
    group = ''
    for line in path.read_text(encoding='utf-8').splitlines():
        p = line.split()
        if not p: continue
        if p[0] == 'v': positions.append([float(x) for x in p[1:4]])
        elif p[0] == 'vt': uv.append([float(x) for x in p[1:3]])
        elif p[0] == 'g': group = p[1]
        elif p[0] == 'f':
            corners = [(int(s.split('/')[0])-1, int(s.split('/')[1])-1 if len(s.split('/'))>1 and s.split('/')[1] else 0) for s in p[1:]]
            faces += [(group, [corners[0], corners[i], corners[i+1]]) for i in range(1,len(corners)-1)]
    return positions, uv, faces


def proxy(path, base, base_weights):
    mappings, delete, scales = [], set(), [1.,1.,1.]
    section = ''
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'): continue
        p = line.split()
        if p[0] in ['x_scale','y_scale','z_scale']:
            axis='xyz'.index(p[0][0]); a,b=int(p[1]),int(p[2])
            scales[axis]=abs(base[a][axis]-base[b][axis])/float(p[3])
        elif p[0]=='verts': section='verts'
        elif p[0]=='delete_verts': section='delete'
        elif p[0] in ['weights','vertexboneweights_file','vertex_weights']: section=''
        elif section=='verts' and p[0].isdigit():
            if len(p)==1: mappings.append(([int(p[0])],[1.],[0.,0.,0.]))
            elif len(p)>=9: mappings.append(([int(x) for x in p[:3]],[float(x) for x in p[3:6]],[float(x) for x in p[6:9]]))
        elif section=='delete':
            for match in re.finditer(r'(\d+)(?:\s*-\s*(\d+))?',line):
                a=int(match[1]); delete.update(range(a,int(match[2] or a)+1))
    points, weights = [], []
    for refs, influence, offset in mappings:
        points.append([sum(base[v][axis]*w for v,w in zip(refs,influence))+offset[axis]*scales[axis] for axis in range(3)])
        blended=collections.defaultdict(float)
        for v, factor in zip(refs,influence):
            for bone,w in base_weights[v].items(): blended[bone]+=factor*w
        weights.append(dict(blended))
    return points, weights, delete


class GLB:
    def __init__(self):
        self.data=bytearray()
        self.g={'asset':{'version':'2.0','generator':'JAIME HQ CC0 conversion'},'buffers':[{}],'bufferViews':[],'accessors':[],'nodes':[],'meshes':[],'materials':[],'images':[],'textures':[],'skins':[],'animations':[]}

    def accessor(self, values, component, kind, target=None):
        arity={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[kind]
        rows=values if arity>1 else [[v] for v in values]
        flat=[v for row in rows for v in row]
        while len(self.data)%4: self.data.append(0)
        raw=struct.pack('<'+{5126:'f',5125:'I',5123:'H'}[component]*len(flat),*flat)
        view={'buffer':0,'byteOffset':len(self.data),'byteLength':len(raw)}
        if target: view['target']=target
        self.data.extend(raw); vi=len(self.g['bufferViews']);self.g['bufferViews'].append(view)
        acc={'bufferView':vi,'componentType':component,'count':len(rows),'type':kind}
        if component==5126 and kind in ['SCALAR','VEC3']:
            acc['min']=[min(row[i] for row in rows) for i in range(arity)];acc['max']=[max(row[i] for row in rows) for i in range(arity)]
        ai=len(self.g['accessors']);self.g['accessors'].append(acc);return ai

    def write(self,path):
        while len(self.data)%4:self.data.append(0)
        self.g['buffers'][0]['byteLength']=len(self.data)
        text=json.dumps(self.g,separators=(',',':')).encode()
        text+=b' '*((-len(text))%4)
        blob=struct.pack('<III',0x46546C67,2,12+8+len(text)+8+len(self.data))+struct.pack('<II',len(text),0x4E4F534A)+text+struct.pack('<II',len(self.data),0x004E4942)+self.data
        path.write_bytes(blob);return blob


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    base,body_uv,body_faces=obj(SRC/'base.obj')
    rig=json.loads((SRC/'default.mhskel').read_text())
    weight_source=json.loads((SRC/'default_weights.mhw').read_text())
    assert rig['license']=='CC0' and weight_source['license']=='CC0'
    names=list(rig['bones']); index={name:i for i,name in enumerate(names)}
    base_weights=[{} for _ in base]
    for name,rows in weight_source['weights'].items():
        for v,w in rows: base_weights[v][index[name]]=w
    body_faces=[f for f in body_faces if f[0]=='body']
    body_used={v for _,f in body_faces for v,_ in f}
    floor=min(base[v][1] for v in body_used);scale=1.78/(max(base[v][1] for v in body_used)-floor)
    joints=rig['joints']
    head={name:[sum(base[v][axis] for v in joints[b['head']])/len(joints[b['head']]) for axis in range(3)] for name,b in rig['bones'].items()}
    center_z=head['root'][2]
    def point(p):return [p[0]*scale,(p[1]-floor)*scale,(p[2]-center_z)*scale]
    head={n:point(p) for n,p in head.items()}
    specs=[('suit','clothes/toigo_male_suit_tie_and_jacket/jacket_tie_pants.obj','clothes/toigo_male_suit_tie_and_jacket/toigo_male_suit_tie_and_jacket.mhclo','suit.jpg',.86),('hair','hair/short02/short02.obj','hair/short02/short02.mhclo','hair.png',.85),('shoes','clothes/shoes01/shoes01.obj','clothes/shoes01/shoes01.mhclo','shoes.jpg',.55),('eyes','eyes/low-poly/low-poly.obj','eyes/low-poly/low-poly.mhclo','eyes.png',.3)]
    parts=[];deleted=set()
    for name,ofile,cfile,texture,rough in specs:
        positions,uv,faces=obj(SRC/ofile)
        fitted,weights,mask=proxy(SRC/cfile,base,base_weights)
        assert len(fitted)==len(positions),(name,len(fitted),len(positions))
        parts.append((name,fitted,uv,faces,weights,texture,rough));deleted.update(mask)
    body_faces=[(g,f) for g,f in body_faces if not any(v in deleted for v,_ in f)]
    parts.insert(0,('skin',base,body_uv,body_faces,base_weights,'skin.jpg',.68))
    glb=GLB();g=glb.g
    for name,b in rig['bones'].items():
        pos=head[name];parent=b['parent']
        local=[pos[a]-(head[parent][a] if parent else 0) for a in range(3)]
        children=[index[n] for n,v in rig['bones'].items() if v['parent']==name]
        g['nodes'].append({'name':name,'translation':local,'children':children,'extras':{'sourceBone':name}})
    inverse=[]
    for name in names:
        x,y,z=head[name];inverse.append([1,0,0,0,0,1,0,0,0,0,1,0,-x,-y,-z,1])
    g['skins'].append({'joints':list(range(len(names))),'skeleton':index['root'],'inverseBindMatrices':glb.accessor(inverse,5126,'MAT4')})
    triangles=0
    for name,positions,uv,faces,weights,texture,rough in parts:
        transformed=[point(p) for p in positions];normals=[[0.,0.,0.] for _ in positions]
        for _,face in faces:
            a,b,c=[transformed[v] for v,_ in face];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            for vi,_ in face:
                for axis in range(3):normals[vi][axis]+=n[axis]
        remap={};pout=[];nout=[];uvout=[];jout=[];wout=[];indices=[]
        for _,face in faces:
            for vi,ti in face:
                key=(vi,ti)
                if key not in remap:
                    remap[key]=len(pout);pout.append(transformed[vi]);length=math.sqrt(sum(v*v for v in normals[vi])) or 1
                    nout.append([v/length for v in normals[vi]]);uvout.append([uv[ti][0],1-uv[ti][1]])
                    top=sorted(((b,max(0,w)) for b,w in weights[vi].items()),key=lambda v:v[1],reverse=True)[:4]
                    total=sum(w for _,w in top)
                    if total<1e-9:top=[(index['head'] if name in ['hair','eyes'] else index['root'],1.)];total=1.
                    jout.append([b for b,_ in top]+[0]*(4-len(top)));wout.append([w/total for _,w in top]+[0.]*(4-len(top)))
                indices.append(remap[key])
        ai={'POSITION':glb.accessor(pout,5126,'VEC3',34962),'NORMAL':glb.accessor(nout,5126,'VEC3',34962),'TEXCOORD_0':glb.accessor(uvout,5126,'VEC2',34962),'JOINTS_0':glb.accessor(jout,5123,'VEC4',34962),'WEIGHTS_0':glb.accessor(wout,5126,'VEC4',34962)}
        mat=len(g['materials']);g['images'].append({'uri':'textures/'+texture});g['textures'].append({'source':mat})
        material={'name':name,'pbrMetallicRoughness':{'baseColorTexture':{'index':mat},'metallicFactor':0.,'roughnessFactor':rough},'doubleSided':name in ['hair','suit']}
        if name=='hair':material.update(alphaMode='MASK',alphaCutoff=.35)
        g['materials'].append(material);mi=len(g['meshes']);g['meshes'].append({'name':name,'primitives':[{'attributes':ai,'indices':glb.accessor(indices,5123 if len(pout)<65536 else 5125,'SCALAR',34963),'material':mat}]})
        g['nodes'].append({'name':name,'mesh':mi,'skin':0});triangles+=len(indices)//3
    g['scene']=0;g['scenes']=[{'nodes':[index['root']]+list(range(len(names),len(g['nodes'])))}]
    from human_motion import build_motion
    animations=build_motion(glb,index,head)
    g['asset']['extras']={'license':'CC0-1.0','height':1.78,'source':'MakeHuman core + Margaret Toigo formal suit','triangles':triangles}
    data=glb.write(DEST/'professional.glb')
    manifest={'file':'professional.glb','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'triangles':triangles,'bones':len(names),'height':1.78,'animations':animations,'license':'CC0-1.0','source_manifest':'assets/source-humans/SOURCE_MANIFEST.json'}
    manifest['textures']=[{'file':str(p.relative_to(DEST)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'license':'CC0-1.0','derived':'Canvas resample max 1024 px; fuentes en SOURCE_MANIFEST.json'} for p in sorted((DEST/'textures').glob('*')) if p.is_file()]
    (ROOT/'assets/P1_HUMAN_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps(manifest))


if __name__=='__main__': main()
