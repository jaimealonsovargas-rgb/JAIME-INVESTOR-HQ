"""Original CC0 animation data: two-bone IK, planted gait and seated gestures.

No external animation library or retargeted proprietary motion is used.
Coordinates use the source MakeHuman bind pose (Y up, +Z forward).
"""
import math

STRIDE=1.04
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,s):return [x*s for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def unit(a):return mul(a,1/max(math.sqrt(dot(a,a)),1e-10))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def qmul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def inverse(q):return [-q[0],-q[1],-q[2],q[3]]
def between(a,b):
 a,b=unit(a),unit(b);v=cross(a,b);q=v+[1+dot(a,b)]
 if dot(q,q)<1e-10:q=cross(a,[1,0,0] if abs(a[0])<.9 else [0,1,0])+[0]
 return unit(q)
def euler(x=0,y=0,z=0):
 a,b,c=x/2,y/2,z/2;s1,s2,s3=math.sin(a),math.sin(b),math.sin(c);c1,c2,c3=math.cos(a),math.cos(b),math.cos(c)
 return [s1*c2*c3+c1*s2*s3,c1*s2*c3-s1*c2*s3,c1*c2*s3+s1*s2*c3,c1*c2*c3-s1*s2*s3]
def ik(start,rest_knee,rest_end,target,pole):
 upper,lower=sub(rest_knee,start),sub(rest_end,rest_knee)
 a,b=math.sqrt(dot(upper,upper)),math.sqrt(dot(lower,lower));v=sub(target,start)
 d=max(abs(a-b)+.001,min(math.sqrt(dot(v,v)),a+b-.001));direction=unit(v)
 bend=unit(sub(pole,mul(direction,dot(pole,direction))))
 along=(a*a-b*b+d*d)/(2*d);height=math.sqrt(max(0,a*a-along*along))
 knee=add(start,add(mul(direction,along),mul(bend,height)))
 target=add(start,mul(direction,d));q1=between(upper,sub(knee,start));q2=between(lower,sub(target,knee))
 return q1,qmul(inverse(q1),q2),q2

def build_motion(glb,index,head):
 clips=[('idle',4),('walk',1),('turn',1.2),('observe',6),('focus',5),('typing',4.7),('reading',6.3),('writing',5.9)]
 for clip,duration in clips:
  seated=clip in ['typing','reading','writing'];frames=[]
  for frame in range(65):
   t=frame/64;phase=t*2*math.pi;shift=-.37 if seated else (-.055+.004*math.cos(phase*2) if clip=='walk' else 0)
   values={'root':('translation',add(head['root'],[0,shift,0])),'spine05':('rotation',euler(y=.009*math.sin(phase))),
    'head':('rotation',euler(x=(.22 if clip=='writing' else .10 if seated else 0)+.016*math.sin(phase),y=(.10 if clip in ['observe','reading'] else .015)*math.sin(phase)))}
   for side,sign in [('L',1),('R',-1)]:
    leg='upperleg01.'+side;knee='lowerleg01.'+side;foot='foot.'+side
    start=add(head[leg],[0,shift,0]);rest_knee=add(head[knee],[0,shift,0]);rest_end=add(head[foot],[0,shift,0]);target=head[foot].copy();u=(t+(0 if side=='L' else .5))%1
    if seated:target[2]=.50;target[1]+=.032
    elif clip=='walk':
     if u<.62:target[0]*=.85;target[2]=head[foot][2]+.322-STRIDE*u;target[1]+=.028
     else:
      swing=(u-.62)/.38;target[0]*=.85;target[2]=head[foot][2]-.3228+.6448*(.5-.5*math.cos(math.pi*swing));target[1]+=.028+.095*math.sin(math.pi*swing)
    elif clip=='turn':target[1]+=.028+.025*max(0,math.sin(2*math.pi*u));target[2]+=.018*math.sin(2*math.pi*u)
    else:target[1]+=.028
    q1,q2,lower_world=ik(start,rest_knee,rest_end,target,[0,0,1]);values[leg]=('rotation',q1);values[knee]=('rotation',q2);values[foot]=('rotation',inverse(lower_world))
    arm='upperarm01.'+side;elbow='lowerarm01.'+side;wrist='wrist.'+side
    if seated:
     start=add(head[arm],[0,shift,0]);rest_elbow=add(head[elbow],[0,shift,0]);rest_wrist=add(head[wrist],[0,shift,0])
     target=[sign*.155,.852,.405]
     if clip=='typing':target[1]+=.007*math.sin(phase*6+sign);target[2]+=.006*math.sin(phase*4+sign)
     if clip=='reading':target[1]+=.018;target[2]+=.012
     if clip=='writing' and side=='L':target=[.24+.012*math.sin(phase*4),.86,.425+.009*math.cos(phase*4)]
     q1,q2,_=ik(start,rest_elbow,rest_wrist,target,[sign,.1,-.2]);values[arm]=('rotation',q1);values[elbow]=('rotation',q2)
     values[wrist]=('rotation',euler(x=.16,z=sign*.04))
     for finger in ['finger2-1','finger3-1','finger4-1','finger5-1']:
      name=finger+'.'+side
      if name in index:values[name]=('rotation',euler(x=.12+.06*math.sin(phase*7+sign+len(finger))))
    else:
     swing=sign*.16*math.sin(phase) if clip=='walk' else .008*math.sin(phase)
     values[arm]=('rotation',euler(x=swing,z=-sign*.62));values[elbow]=('rotation',euler(x=-.10));values[wrist]=('rotation',euler())
   frames.append(values)
  times=glb.accessor([duration*i/64 for i in range(65)],5126,'SCALAR');anim={'name':clip,'samplers':[],'channels':[]}
  for name,(path,_) in frames[0].items():
   vals=[f[name][1] for f in frames];out=glb.accessor(vals,5126,'VEC3' if path=='translation' else 'VEC4');s=len(anim['samplers']);anim['samplers'].append({'input':times,'output':out,'interpolation':'LINEAR'});anim['channels'].append({'sampler':s,'target':{'node':index[name],'path':path}})
  glb.g['animations'].append(anim)
 return [name for name,_ in clips]
