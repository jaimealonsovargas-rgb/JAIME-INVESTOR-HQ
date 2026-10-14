import { BoxGeometry, BufferGeometry, CylinderGeometry, Group, Mesh, MeshBasicMaterial, Object3D, PlaneGeometry, SphereGeometry, TorusGeometry, Vector3, type Material, type Texture } from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { DEPARTMENTS, FLOOR, type Department, type Vec3 } from './layout';
import { textTexture, type Materials } from './materials';
import { chairBack, chairSeat, facadeGeometry, leafGeometry, planterGeometry } from './details';
import type { Collider } from './collisions';
import { WORKSPACES,SEAT_OFFSET } from './workspaces';

// Modelado original en metros. Las piezas se fusionan por material y departamento.
// Conserva cada departamento como nodo independiente para fases posteriores.
const geometries = new Map<string, BufferGeometry>();
function geometry(key: string, build: () => BufferGeometry) {
  if (!geometries.has(key)) geometries.set(key, build());
  return geometries.get(key)!;
}
class Builder {
  group = new Group();
  seats: { position: Vec3; forward: Vec3 }[] = [];
  colliders: Collider[] = [];
  constructor(name: string) { this.group.name = name; }
  part(geo: BufferGeometry, mat: Material, position: Vec3, scale: Vec3 = [1, 1, 1], rotation: Vec3 = [0, 0, 0]) {
    const mesh = new Mesh(geo, mat); mesh.position.set(...position); mesh.scale.set(...scale); mesh.rotation.set(...rotation);
    mesh.castShadow = !mat.transparent; mesh.receiveShadow = !mat.transparent;
    this.group.add(mesh); return mesh;
  }
  box(p: Vec3, size: Vec3, mat: Material, radius = 0, rotation: Vec3 = [0, 0, 0]) {
    if(this.group.name!=='skyline' && p[1]+size[1]/2>.04) {
      const panel=mat.transparent && size[1]>2 && Math.max(size[0],size[2])>1;
      const furniture=!mat.transparent && ((size[1]>.35&&Math.min(size[0],size[2])>=.12)||(size[0]>.6&&size[2]>.45&&p[1]>.3));
      if(panel||furniture) this.colliders.push({center:[...p],half:[Math.max(size[0]/2,.02),size[1]/2,Math.max(size[2]/2,.02)],yaw:rotation[1],kind:panel?'glass':'solid'});
    }
    const geo = radius ? geometry(`round-${size.join('-')}-${radius}`, () => new RoundedBoxGeometry(...size, radius <= .028 ? 1 : 2, radius)) : geometry('box', () => new BoxGeometry());
    return this.part(geo, mat, p, radius ? [1, 1, 1] : size, rotation);
  }
  cylinder(p: Vec3, radius: number, height: number, mat: Material, top = radius) {
    if(this.group.name!=='skyline'&&radius>=.4&&p[1]>.3&&p[1]<1.2)this.colliders.push({center:[...p],half:[radius,height/2,radius],yaw:0,kind:'solid'});
    return this.part(geometry(`cyl-${top / radius}`, () => new CylinderGeometry(top / radius, 1, 1, 16)), mat, p, [radius, height, radius]);
  }
  label(p: Vec3, width: number, height: number, title: string, subtitle = '', kind: 'sign' | 'screen' | 'brand' = 'sign', rotation: Vec3 = [0, 0, 0]) {
    const mat = new MeshBasicMaterial({ map: textTexture(title, subtitle, kind), toneMapped: false, transparent: kind === 'sign', depthWrite: kind !== 'sign' });
    return this.part(geometry('plane', () => new PlaneGeometry()), mat, p, [width, height, 1], rotation);
  }
  finish() {
    this.group.userData.seats = this.seats;
    this.group.userData.colliders = this.colliders;
    const byMaterial = new Map<Material, BufferGeometry[]>();
    this.group.children.forEach(child => {
      const mesh = child as Mesh; mesh.updateMatrix();
      const geo = mesh.geometry.clone().applyMatrix4(mesh.matrix);
      // Fusionar formatos iguales (todas las piezas con posición/normal/UV, sin índices).
      const flat = geo.index ? geo.toNonIndexed() : geo;
      const mat = mesh.material as Material;
      if (!byMaterial.has(mat)) byMaterial.set(mat, []);
      byMaterial.get(mat)!.push(flat);
      if (flat !== geo) geo.dispose();
    });
    this.group.clear();
    byMaterial.forEach((parts, material) => {
      const merged = mergeGeometries(parts)!;
      const mesh = new Mesh(merged, material); mesh.castShadow = !material.transparent; mesh.receiveShadow = !material.transparent;
      this.group.add(mesh); parts.forEach(part => part.dispose());
    });
    return this.group;
  }
}

function chair(b: Builder, x: number, z: number, angle: number, m: Materials, meeting = false) {
  const c = new Builder('chair');
  c.seats.push({position:[0,.79,0],forward:[0,0,1]});
  c.colliders.push({center:[0,.65,0],half:[.37,.65,.39],yaw:0,kind:'solid'});
  c.part(geometry('plane', () => new PlaneGeometry()), m.contact, [0, .033, 0], [1.1, 1.1, 1], [-Math.PI / 2, 0, 0]);
  c.part(geometry('ergonomic-seat', chairSeat), meeting ? m.cognac : m.leather, [0, .51, .01]);
  c.part(geometry('ergonomic-back', chairBack), meeting ? m.cognac : m.leather, [0, .90, -.245], [1, 1, 1], [-.16, 0, 0]);
  c.part(geometry('ergonomic-back', chairBack), m.dark, [0, .90, -.296], [.96, .97, .35], [-.16, 0, 0]);
  c.box([0, .69, -.315], [.07, .29, .055], m.steel, .024, [-.15,0,0]);
  for (const side of [-1, 1]) {
    stem(c,[side*.27,.49,-.14],[side*.31,.74,-.05],m.steel,.012);
    c.box([side * .31, .76, .02], [.07, .045, .32], meeting ? m.cognac : m.leather, .022);
  }
  c.cylinder([0, .29, 0], .025, .36, m.steel);
  c.cylinder([0, .18, 0], .037, .16, m.dark);
  for (let i = 0; i < 5; i++) {
    const a = i * Math.PI * 2 / 5;
    stem(c,[0,.14,0],[Math.sin(a)*.31,.09,Math.cos(a)*.31],m.steel,.02);
    for (const side of [-1,1]) c.part(geometry('wheel', () => new SphereGeometry(1, 8, 6)), m.dark, [Math.sin(a) * .31 + side * .017, .055, Math.cos(a) * .31], [.014, .037, .036]);
  }
  transfer(b, c, [x, 0, z], angle);
}
function transfer(to: Builder, from: Builder, position: Vec3, rotation = 0) {
  const parent = new Object3D(); parent.position.set(...position); parent.rotation.y = rotation; parent.updateMatrix();
  from.seats.forEach(seat=>to.seats.push({position:new Vector3(...seat.position).applyMatrix4(parent.matrix).toArray() as Vec3,forward:new Vector3(...seat.forward).transformDirection(parent.matrix).toArray() as Vec3}));
  from.colliders.forEach(c=>to.colliders.push({...c,center:new Vector3(...c.center).applyMatrix4(parent.matrix).toArray() as Vec3,yaw:c.yaw+rotation}));
  [...from.group.children].forEach(child => { child.updateMatrix(); child.applyMatrix4(parent.matrix); to.group.add(child); });
}
function monitor(b: Builder, x: number, z: number, m: Materials, screen: Material, rotation = 0, y = .81) {
  const t = new Builder('monitor');
  t.box([0, y + .37, 0], [.75, .442, .027], m.dark, .011, [-.04,0,0]);
  t.box([0, y + .34, -.032], [.31, .24, .025], m.dark, .025);
  t.part(geometry('plane', () => new PlaneGeometry()), screen, [0, y + .37, .018], [.721, .405, 1], [-.04,0,0]);
  t.cylinder([0, y + .15, -.038], .018, .27, m.steel);
  t.box([0, y + .011, .015], [.24, .018, .18], m.steel, .009);
  t.box([0, y + .025, .37], [.44, .022, .155], m.dark, .009);
  t.part(geometry('plane', () => new PlaneGeometry()), m.keys, [0,y + .037,.37],[.425,.145,1],[-Math.PI/2,0,0]);
  t.part(geometry('mouse', () => new SphereGeometry(1, 12, 8)), m.dark, [.30, y + .028, .37], [.034, .023, .057]);
  t.box([.3,y + .045,.37],[.003,.003,.07],m.steel);
  t.box([-.25,y + .03,-.12],[.10,.045,.07],m.dark,.015);
  transfer(b, t, [x, 0, z], rotation);
}
function desk(b: Builder, x: number, z: number, m: Materials, screen: Material, facing = 0, dual = false) {
  const t = new Builder('desk');
  t.part(geometry('plane', () => new PlaneGeometry()), m.contact, [0, .032, 0], [3.2, 1.8, 1], [-Math.PI / 2, 0, 0]);
  t.box([0, .77, 0], [dual ? 2.4 : 1.9, .075, 1.02], m.wood, .045);
  for (const side of [-1, 1]) {
    for (const dz of [-.36,.36]) t.box([side * (dual ? 1.02 : .8), .39, dz], [.045, .7, .045], m.dark, .012);
    t.box([side * (dual ? 1.02 : .8), .045, 0], [.045, .035, .79], m.dark, .012);
  }
  t.box([0, .61, -.28], [dual ? 2.0 : 1.65, .18, .035], m.dark);
  if (dual) { monitor(t, -.46, -.26, m, screen); monitor(t, .46, -.26, m, screen); }
  else monitor(t, 0, -.23, m, screen);
  t.box([-.71, .826, .22], [.24, .035, .32], m.paper, .01);
  t.box([-.71,.848,.22],[.25,.012,.33],m.leather,.01);
  t.cylinder([.75, .865, .2], .038, .115, m.cream);
  t.cylinder([.75,.925,.2],.030,.001,m.dark);
  t.part(geometry('cup-handle', () => new TorusGeometry(.032,.008,6,14,Math.PI*1.6)),m.cream,[.79,.87,.2],[1,1,1],[0,0,-.8]);
  t.box([-.3,.828,.43],[.18,.012,.26],m.paper,.004);
  t.box([-.31,.838,.43],[.006,.006,.15],m.bronze,.002,[0,.35,0]);
  chair(t, 0, SEAT_OFFSET, Math.PI, m);
  transfer(b, t, [x, 0, z], facing);
}
function plant(b: Builder, x: number, z: number, m: Materials, height = 1.8) {
  b.colliders.push({center:[x,.7,z],half:[.31,.7,.31],yaw:0,kind:'solid'});
  b.part(geometry('plane', () => new PlaneGeometry()), m.contact, [x, .036, z], [1.1, 1.1, 1], [-Math.PI / 2, 0, 0]);
  b.part(geometry('planter',planterGeometry),m.stone,[x,.03,z]);
  b.cylinder([x,.54,z],.243,.01,m.dark);
  for (let trunk=0; trunk<3; trunk++) {
    const a=trunk*2.4; const tip:Vec3=[x+Math.sin(a)*.16,height*.84,z+Math.cos(a)*.16];
    stem(b,[x,.55,z],tip,m.wood,.014);
    for (let i=0;i<6;i++) {
      const turn=a+i*2.4, y=.84+i*(height-.65)/6;
      const end:Vec3=[x+Math.sin(turn)*(.19+i*.016),y,z+Math.cos(turn)*(.19+i*.016)];
      stem(b,[x+Math.sin(a)*.08,y-.13,z+Math.cos(a)*.08],end,m.green,.006);
      b.part(geometry('botanical-leaf',leafGeometry),i%3?m.green:m.greenLight,end,[.78+(i%3)*.12,1,.85+(i%2)*.13],[-.35+(i%3)*.22,turn,.10*(trunk-1)]);
    }
  }
}
function stem(b:Builder,from:Vec3,to:Vec3,mat:Material,radius:number) {
  const a=new Vector3(...from),delta=new Vector3(...to).sub(a);
  const mesh=b.cylinder(a.addScaledVector(delta,.5).toArray() as Vec3,radius,delta.length(),mat,radius*.55);
  mesh.quaternion.setFromUnitVectors(new Vector3(0,1,0),delta.normalize());
}
function sculpture(b:Builder,x:number,z:number,m:Materials,y=.99) {
  b.box([x,y,z],[.42,.045,.30],m.stone,.02);
  b.part(geometry('sculpture',()=>new TorusGeometry(.17,.018,8,32)),m.bronze,[x,y+.19,z],[1,1.2,1],[.2,.55,.3]);
  b.part(geometry('sculpture',()=>new TorusGeometry(.17,.018,8,32)),m.bronze,[x,y+.20,z],[.65,1,1],[.2,-.7,-.3]);
}
function roomShell(b: Builder, d: Department, m: Materials) {
  b.box([0, .009, 0], [8.35, .018, 6.35], m.carpet);
  if (d.id === 'trading' || d.id === 'reception') return;
  // Cutaway permanente: separaci?n f?sica baja, acceso frontal y visi?n isom?trica.
  b.box([0,.24,-3.18],[8.35,.48,.12],m.cream);
  for(const side of [-1,1])b.box([side*4.18,.24,-2],[.12,.48,2.4],m.cream);
  b.label([2.3,.035,2.75],3.4,.45,`${d.number} / ${d.label}`,'','sign',[-Math.PI/2,0,0]);
}
function shelves(b: Builder, x: number, z: number, m: Materials) {
  b.box([x, 1.32, z], [3.35, 2.6, .14], m.wood);
  for (const y of [.16, .84, 1.52, 2.2, 2.64]) b.box([x, y, z + .17], [3.4, .045, .46], m.wood);
  for (const dx of [-1.68, 0, 1.68]) b.box([x + dx, 1.34, z + .14], [.045, 2.65, .46], m.bronze);
  for (let i = 0; i < 28; i++) {
    const px = x - 1.4 + (i % 10) * .29, y = .38 + Math.floor(i / 10) * .68;
    b.box([px, y, z + .18], [.13 + (i % 3) * .015, .38 + (i % 2) * .08, .24], i % 4 ? m.book : m.cream, .006);
    b.box([px, y - .08, z + .303], [.10, .018, .006], m.bronze);
  }
}
function wallScreen(b: Builder, x: number, z: number, d: Department, m: Materials, width = 2.8) {
  b.box([x, 1.94, z], [width + .1, 1.67, .11], m.dark, .035);
  b.label([x, 1.94, z + .058], width, 1.575, d.label, `Función prevista para ${d.phase}`, 'screen');
}

function department(d: Department, m: Materials) {
  const b = new Builder(`department:${d.id}`); roomShell(b, d, m);
  const screen = new MeshBasicMaterial({ map: textTexture(d.label, `Función prevista para ${d.phase}`, 'screen'), toneMapped: false });
  if (d.id === 'reception') {
    b.box([-.6, .58, -.15], [4.8, 1.16, 1.1], m.stone, .18);
    b.box([-.6, 1.18, -.15], [4.92, .09, 1.18], m.wood, .08);
    b.box([-.6, .08, -.15], [4.58, .06, .95], m.light);
    for (let i = 0; i < 39; i++) b.box([-2.76 + i * .114, .64, .404], [.035, .92, .025], m.bronze);
    b.label([-.6, .73, .431], 2.7, .675, 'JAIME', 'I N V E S T O R   H Q', 'brand');
    monitor(b, -.7, -.4, m, screen, 0, 1.23);
    // Recepción despejada y puesto lateral real; sin sofás ni mesas auxiliares.
    plant(b, -3.8, -2.1, m); plant(b, 3.7, -2.1, m);
  } else if (d.id === 'committee') {
    b.box([0, .8, -.3], [2.65, .12, 4.6], m.wood, .3);
    for (const z of [-1.6, 1.0]) b.box([0, .4, z], [.85, .73, .2], m.bronze, .04);
    for (const side of [-1, 1]) for (const z of [-1.7, -.3, 1.1]) {
      chair(b, side * 1.83, z, -side * Math.PI / 2, m, true);
      b.box([side * .83, .87, z], [.36, .013, .48], m.paper);
      b.cylinder([side * .9, .92, z - .4], .03, .13, m.glass);
    }
    chair(b, 0, 2.65, Math.PI, m, true);
    wallScreen(b, 0, -3.04, d, m, 2.8);
    plant(b, -3.2, -2.4, m); plant(b, 3.2, -2.4, m);
  } else if (d.id === 'trading') {
    // Dos bancadas laterales conservan seis puestos y liberan el eje central.
    for (const x of [-3.8, 3.8]) plant(b, x, -3.1, m, 1.7);
    b.label([0, .031, 3.05], 2.4, .30, '05 / TRADING FLOOR', 'INVESTIGACIÓN MULTIACTIVO', 'sign',[-Math.PI/2,0,0]);
  } else if (d.id === 'research') {
    shelves(b, 0, -2.9, m);
    b.cylinder([2.7, .7, -1.8], .75, .09, m.wood); b.cylinder([2.7, .35, -1.8], .08, .7, m.bronze);
    plant(b, -3.3, -1.8, m);
  } else if (d.id === 'systems') {
    for (const z of [-2.25,-.95,.35]) {
      b.box([-2.9, 1.17, z], [1, 2.25, .88], m.dark, .04);
      for (let i = 0; i < 11; i++) { b.box([-2.9, .28 + i * .17, z+.455], [.86, .135, .026], m.book); b.box([-3.2, .28 + i * .17, z+.473], [.16, .012, .009], m.bronze); }
    }
    plant(b, 3.3, -2.3, m);
    wallScreen(b,1.5,-2.95,d,m,2.6);
    b.label([-2.9, 2.36, -1.795], .85, .106, 'INFRAESTRUCTURA', '', 'sign');
  } else if (d.id === 'performance') {
    wallScreen(b, 0, -2.95, d, m, 3.8);
    b.box([2.8,.8,-2.65],[1.25,1.55,.42],m.wood,.045);for(const x of [2.5,3.1])b.box([x,.8,-2.425],[.54,1.35,.024],m.leather,.009);sculpture(b,2.8,-2.65,m,1.58);plant(b,-3.5,-2.2,m);
    b.box([2.5,.76,.05],[1.1,.08,1.6],m.stone,.06);
    b.box([2.5,.38,.05],[.48,.72,.65],m.bronze,.03);
    b.box([2.5,.817,-.2],[.36,.015,.48],m.paper);
  } else {
    wallScreen(b, 0, -2.98, d, m, d.id === 'risk' ? 3.5 : 2.8);
    b.box([0, .48, -2.65], [4.4, .9, .6], m.wood, .04);
    for (const x of [-1.5, -.5, .5, 1.5]) b.box([x, .48, -2.34], [.9, .74, .014], m.wood);
    sculpture(b,1.4,-2.60,m);
    plant(b, 3.5, 2.0, m);
  }
  for(const w of WORKSPACES.filter(w=>w.department===d.id))desk(b,w.x,w.z,m,screen,w.yaw,w.dual);
  b.group.userData = { department: d.id, center: d.center, monitor: true, phase: d.phase,sofas:0,portalWidth:4.4 };
  const group = b.finish(); group.position.set(...d.center); return group;
}

function architecture(m: Materials) {
  const b = new Builder('architecture');
  b.box([0, -.16, 0], [34, .32, 28], m.floor);
  for (const x of [-16.85, 16.85]) b.box([x, .008, 0], [.025, .015, 27.7], m.bronze);
  for (const z of [-13.85, 13.85]) b.box([0, .008, z], [33.7, .015, .025], m.bronze);
  for (const x of [-5.5, 5.5]) for (const edge of [-1.25, 1.25]) b.box([x + edge, .018, 0], [.014, .008, 27.5], m.bronze);
  for (const z of [-4.5, 4.5]) for (const edge of [-1.24, 1.24]) b.box([0, .018, z + edge], [33.6, .008, .014], m.bronze);
  // Bordure marfil, abierta al jugador y sin fachadas altas delante de la c?mara.
  b.box([0,.3,-13.7],[34,.6,.18],m.cream);
  for(const x of [-16.8,16.8])b.box([x,.25,0],[.16,.5,27.4],m.cream);
  b.box([0,-.3,0],[34.4,.2,28.4],m.dark);
  const a = b.finish();
  const roof = new Builder('ceiling');
  roof.box([0, FLOOR.ceiling + .07, 0], [34, .12, 28], m.ceiling);
  for (const d of DEPARTMENTS) {
    const [x, , z] = d.center;
    roof.box([x, 4.36, z], [8.45, .16, 6.45], m.soffit, .05);
    for (const side of [-1, 1]) {
      roof.box([x + side * 3.85, 4.26, z], [.03, .02, 5.8], m.light);
      roof.box([x, 4.26, z + side * 2.85], [7.72, .02, .03], m.light);
    }
    for (const dx of [-2.8, 2.8]) {
      roof.box([x + dx, 4.075, z], [.08, .055, 3.7], m.bronze, .025);
      roof.box([x + dx, 4.043, z], [.055, .009, 3.55], m.light);
      for (const dz of [-1.4, 1.4]) roof.box([x + dx, 4.30, z + dz], [.006, .45, .006], m.dark);
    }
  }
  a.add(roof.finish()); return a;
}

function skyline(m: Materials) {
  const b = new Builder('skyline');
  // Contexto urbano original en tres planos de profundidad, sin réplica geográfica.
  function tower(x:number,z:number,w:number,h:number,d:number,index:number) {
    const mat=index%4===0?m.cityStone:index%3===0?m.cityDark:m.city;
    b.part(geometry(`facade-${w}-${h}-${d}`,()=>facadeGeometry(w,h,d)),mat,[x,h/2-32,z]);
    b.box([x,h-31.85,z],[w+.25,.3,d+.25],m.dark);
    b.part(geometry(`facade-top-${w}-${h}-${d}`,()=>facadeGeometry(w*.68,3.6,d*.66)),mat,[x,h-30,z]);
    b.box([x,h-28.08,z],[w*.70,.18,d*.68],m.cityStone);
    // Dos retranqueos y coronación; la textura sustituye cientos de ventanas transparentes.
    if(index%3===0) for(const level of [.34,.67]) b.box([x,h*level-32,z],[w+.16,.22,d+.16],m.cityStone);
    for(const side of [-1,1]) b.box([x+side*w*.46,h/2-32,z+d*.505],[.11,h,.12],m.cityStone);
    if(index%5===0) b.cylinder([x,h-25,z],.055,5.6,m.steel);
  }
  for(let row=0;row<3;row++) for(let i=0;i<13;i++) {
    const index=row*13+i,x=-132+i*22+(row%2)*9,z=-62-row*58-(i%3)*7;
    tower(x,z,8+(i*7+row)%7,32+(i*17+row*11)%49,9+(i*3)%6,index);
  }
  for(const side of [-1,1]) for(let i=0;i<6;i++) tower(side*(54+(i%2)*12),-44+i*22,10+(i%3)*2,34+(i*13)%39,11+i%4,i+41);
  b.box([0,-32.6,-30],[700,1,700],m.cityGround);
  // Solamente contexto exterior: no participa en las sombras de la oficina.
  const city=b.finish(); city.traverse(o=>{if(o instanceof Mesh){o.castShadow=false;o.receiveShadow=false;}}); return city;
}

export function createOffice(m: Materials) {
  const office = new Group(); office.name = 'JAIME_INVESTOR_HQ';
  const exterior=skyline(m);exterior.visible=false;
  office.add(architecture(m),exterior,...DEPARTMENTS.map(d => department(d, m)));
  const wall=new Builder('videowall');wall.box([0,3,-13.35],[32,4.8,.28],m.dark,.12);
  wall.label([-11.8,4.5,-13.19],7.4,.75,'JAIME INVESTOR HQ','SIMULACION / PAPER ONLY','screen');
  ['CARTERA / P3','POSICIONES / P3','OPERACIONES / P6','MERCADOS / P2','NOTICIAS / P2','RIESGOS / P5','AGENTES / P4'].forEach((title,i)=>wall.label([-13.2+i*4.4,2.65,-13.19],4.1,2.35,title,'NO DISPONIBLE','screen'));
  office.add(wall.finish());
  office.getObjectByName('ceiling')!.visible=false;
  office.updateMatrixWorld(true);
  const colliders:Collider[]=[];
  office.traverse(node=>{for(const c of node.userData.colliders??[])colliders.push({...c,center:new Vector3(...c.center).applyMatrix4(node.matrixWorld).toArray() as Vec3});});
  office.userData.colliders=colliders;
  return office;
}

export function disposeOffice(office: Group, retainedTextures = new Set<Texture>()) {
  const owned = new Set<Material>();
  office.traverse(object => { if (object instanceof Mesh) { object.geometry.dispose(); owned.add(object.material as Material); } });
  const textures=new Set<Texture>();
  owned.forEach(mat=>{ Object.values(mat).forEach(value=>{if(value?.isTexture&&!retainedTextures.has(value)) textures.add(value);}); mat.dispose(); });
  textures.forEach(t=>t.dispose());
}
