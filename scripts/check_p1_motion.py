"""Verify actual glTF FK: planted stance, seated knees/feet and wrist heights."""
import json,math,struct
from pathlib import Path
from human_motion import add,qmul,STRIDE

root=Path(__file__).resolve().parents[1]
raw=(root/'frontend/public/models/professional.glb').read_bytes()
length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);binary=raw[28+length:]
def accessor(index):
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
 values=struct.unpack_from('<'+'f'*(width*a['count']),binary,v.get('byteOffset',0)+a.get('byteOffset',0))
 return [list(values[i:i+width]) for i in range(0,len(values),width)]
parents={i:p for p,node in enumerate(g['nodes']) for i in node.get('children',[])}
names={n['name']:i for i,n in enumerate(g['nodes'])}
def rotate(q,v):
 x=qmul(q,[*v,0]);return qmul(x,[-q[0],-q[1],-q[2],q[3]])[:3]
def frame_pose(animation,frame):
 local={}
 for channel in animation['channels']:
  target=channel['target'];samples=accessor(animation['samplers'][channel['sampler']]['output'])
  local[(target['node'],target['path'])]=samples[frame]
 cache={}
 def world(index):
  if index in cache:return cache[index]
  node=g['nodes'][index];t=local.get((index,'translation'),node.get('translation',[0,0,0]));q=local.get((index,'rotation'),node.get('rotation',[0,0,0,1]))
  if index in parents:
   pt,pq=world(parents[index]);t=add(pt,rotate(pq,t));q=qmul(pq,q)
  cache[index]=(t,q);return t,q
 return {name:world(index)[0] for name,index in names.items() if index<len(g['skins'][0]['joints'])}

animations={a['name']:a for a in g['animations']}
stance={}
for side,offset in [('L',0),('R',.5)]:
 groups={}
 for f in range(65):
  t=f/64;u=(t+offset)%1
  if .06<=u<=.56:
   p=frame_pose(animations['walk'],f)['foot.'+side];groups.setdefault(int(t+offset),[]).append((p[1],p[2]+STRIDE*t))
 for group,points in groups.items():
  drift=max(p[1] for p in points)-min(p[1] for p in points);vertical=max(p[0] for p in points)-min(p[0] for p in points)
  assert drift<.015,(side,'stance drift',drift)
  assert vertical<.006,(side,'stance vertical',vertical)
  stance[f'{side}-{group}']={'samples':len(points),'horizontal_drift_m':round(drift,6),'vertical_drift_m':round(vertical,6)}
seated={}
for clip in ['typing','reading','writing']:
 p=frame_pose(animations[clip],0)
 assert .5<p['root'][1]<.65,(clip,'seat height')
 for side in ['L','R']:
  assert p['lowerleg01.'+side][2]-p['upperleg01.'+side][2]>.18,(clip,'knee orientation')
  assert 0<p['foot.'+side][1]<.25,(clip,'foot height')
  assert .78<p['wrist.'+side][1]<.94,(clip,'wrist height')
 seated[clip]={'root_y':round(p['root'][1],4),'feet':[p['foot.L'],p['foot.R']],'wrists':[p['wrist.L'],p['wrist.R']]}
print(json.dumps({'stance':stance,'seated':seated,'stride_m':STRIDE,'method':'FK of exported glTF keyframes; no network'}))
