import { BoxGeometry, BufferGeometry, CylinderGeometry, Group, Mesh, MeshBasicMaterial, Object3D, PlaneGeometry, SphereGeometry, TorusGeometry, Vector3, type Material, type Texture } from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { DEPARTMENTS, FLOOR, VIDEOWALL, type Department, type Vec3 } from './layout';
import { textTexture, type Materials } from './materials';
import { chairBack, chairSeat, leafGeometry, planterGeometry } from './details';
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
  label(p: Vec3, width: number, height: number, title: string, subtitle = '', kind: 'sign' | 'screen' | 'brand' | 'wallbrand' = 'sign', rotation: Vec3 = [0, 0, 0]) {
    const transparent=kind==='sign'||kind==='wallbrand';
    const mat = new MeshBasicMaterial({ map: textTexture(title, subtitle, kind), toneMapped: false, transparent, depthWrite: !transparent,
      polygonOffset:kind==='screen',polygonOffsetFactor:-1,polygonOffsetUnits:-2 });
    return this.part(geometry('plane', () => new PlaneGeometry()), mat, p, [width, height, 1], rotation);
  }
  finish() {
    this.group.userData.seats = this.seats;
    this.group.userData.colliders = this.colliders;
    const byMaterial = new Map<Material, BufferGeometry[]>();
    const children=this.group.children.filter(child=>!(child instanceof Mesh));
    this.group.children.forEach(child => {
      if(!(child instanceof Mesh))return;
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
    if(children.length)this.group.add(...children);
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
function desk(b: Builder, x: number, z: number, m: Materials, screen: Material, facing = 0, dual = false, occupied = true) {
  const t = new Builder('desk');
  t.part(geometry('plane', () => new PlaneGeometry()), m.contact, [0, .032, 0], [3.2, 1.8, 1], [-Math.PI / 2, 0, 0]);
  t.box([0, .77, 0], [dual ? 2.4 : 1.9, .075, 1.02], m.wood, .045);
  // Tapete, canto fino y bandeja de cableado: detalle real sin otro material/draw call.
  t.box([0,.813,.10],[dual?1.65:1.25,.008,.65],m.leather,.025);
  t.box([0,.742,.505],[dual?2.3:1.8,.018,.014],m.bronze,.006);
  t.box([0,.60,-.40],[1.15,.12,.16],m.dark,.025);
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
  if(occupied)chair(t, 0, SEAT_OFFSET, Math.PI, m);
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
  const [width,depth]=d.size;
  b.box([0,.012,0],[width,.024,depth],m.carpet);
  for(const x of [-width/2,width/2])b.box([x,.026,0],[.025,.014,depth],m.bronze);
  // Los frentes al pasillo de la referencia roja quedan completamente abiertos.
  function wall(x:number,z:number,w:number,deep:number){
    b.box([x,.24,z],[w,.48,deep],m.cream);
    const upper=new Builder('cutaway:'+d.id+':'+x+':'+z);
    upper.box([x,1.79,z],[w,2.62,deep],m.cream);
    b.box([x,.13,z],[w,.26,deep+.035],m.dark);
    upper.box([x,3.08,z],[w,.06,deep+.035],m.dark);
    const group=upper.finish();group.userData.cutaway=true;
    group.userData.wall={center:[d.center[0]+x,1.79,d.center[2]+z],half:[w/2,1.31,deep/2],yaw:0,kind:'solid'};
    b.group.add(group);
  }
  wall(0,-depth/2,width,.18);
  if(['trading','systems','quant'].includes(d.id))b.box([0,1.25,-depth/2+.105],[width-.65,2.2,.025],m.dark);
  for(const side of [-1,1]){
    const solidSide=(side<0&&['research','systems','execution'].includes(d.id))||(side>0&&['risk','trading','performance'].includes(d.id));
    if(solidSide){wall(side*width/2,0,.18,depth);continue;}
    // La piel lateral y sus marcos son decorativos y atravesables por petición del usuario.
    // Los frentes rojos del pasillo conservan el hueco y dos hojas de vidrio abiertas.
    const entry=(side<0&&(d.entrance==='west'||d.entrance==='sides'))||(side>0&&(d.entrance==='east'||d.entrance==='sides'));
    const glazing=new Builder(`glazing:${d.id}:${side}`);
    const x=side*width/2;
    if(entry){
      for(const end of [-1,1]){
        glazing.box([x,1.5,end*(depth/2-.58)],[.016,2.95,1.05],m.glass);
        glazing.box([x,1.5,end*(depth/2-1.1)],[.035,2.98,.035],m.dark);
        glazing.box([x-side*.04,1.05,end*(depth/2-1.25)],[.025,.42,.025],m.steel,.009);
      }
    }else{
      glazing.box([x,1.54,0],[.016,3.03,depth],m.glass);
      for(const z of [-depth/2,0,depth/2])glazing.box([x,1.54,z],[.045,3.08,.045],m.dark);
      for(const y of [.045,3.075])glazing.box([x,y,0],[.055,.055,depth],m.dark);
      glazing.box([x,1.1,0],[.02,.018,depth],m.steel);
    }
    glazing.colliders=[];
    // Fusionar vidrio y perfilería con el departamento reduce las llamadas de dibujo.
    transfer(b,glazing,[0,0,0]);
    const group=glazing.group;group.userData.visualOnlyGlazing=true;group.userData.colliders=[];
    b.group.add(group);
  }
  b.box([0,.12,-depth/2+.11],[width-.2,.18,.04],m.dark);
  for(const side of [-1,1]){
    b.box([side*(width/2-.24),1.55,-depth/2+.12],[.065,2.7,.05],m.dark,.012);
    b.box([side*(width/2-.24),1.55,-depth/2+.15],[.022,2.6,.012],m.light);
  }
  // Cornisa continua, sombra de separación y apliques cálidos integrados.
  b.box([0,2.43,-depth/2+.13],[width-.45,.025,.09],m.bronze);
  for(const side of [-1,1]){
    b.box([side*(width/2-.52),2.27,-depth/2+.18],[.16,.48,.08],m.dark,.025);
    b.box([side*(width/2-.52),2.27,-depth/2+.229],[.045,.38,.025],m.light,.012);
  }
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
  // Pantalla apoyada en una consola real, incluso con la planta abierta sin tabique.
  for(const side of [-1,1])b.box([x+side*width*.3,.87,z-.04],[.045,1.7,.045],m.dark);
  b.box([x, 1.65, z], [width + .1, 1.37, .11], m.dark, .035);
  b.label([x, 1.65, z + .058], width, 1.28, d.label, (d.id==='systems'?'Fuentes reales / Data Quality':d.id==='reception'?'Estado local / PAPER ONLY':`NO DISPONIBLE / ${d.phase}`), 'screen');
}

function whiteboard(b:Builder,x:number,z:number,m:Materials,topic:string){
  b.box([x,1.7,z],[1.75,1.2,.075],m.steel,.018);
  b.box([x,1.7,z+.045],[1.65,1.1,.014],m.paper,.009);
  b.label([x,2.02,z+.056],1.5,.22,topic,'ESQUEMA / SIN ACTIVIDAD IA','sign');
  // Diagrama de proceso, nunca una serie de precios o rentabilidades inventada.
  for(let i=0;i<3;i++){
    b.box([x-.49+i*.49,1.66,z+.06],[.34,.26,.008],m.book,.01);
    if(i<2)b.box([x-.245+i*.49,1.66,z+.064],[.12,.014,.009],m.bronze);
  }
  b.box([x,1.28,z+.1],[1.65,.035,.12],m.steel);
  for(let i=0;i<3;i++)b.box([x-.4+i*.15,1.31,z+.12],[.1,.018,.025],i===1?m.bronze:m.book);
}

function credenza(b:Builder,x:number,z:number,m:Materials,width=2.4){
  b.box([x,.49,z],[width,.94,.46],m.wood,.035);
  for(let i=0;i<3;i++){
    const dx=x-width/3+i*width/3;
    b.box([dx,.49,z+.24],[width/3-.035,.78,.018],m.book,.01);
    b.box([dx+width/6-.1,.59,z+.26],[.015,.15,.018],m.bronze,.005);
  }
  sculpture(b,x+.65,z,m,.99);
}

function department(d: Department, m: Materials) {
  const b = new Builder(`department:${d.id}`); roomShell(b, d, m);
  // Placa negra integrada en el fondo de cada despacho, como la referencia.
  b.box([0,2.75,-d.size[1]/2+.105],[d.id==='committee'?4.9:3.3,.52,.035],m.dark,.015);
  const screen = new MeshBasicMaterial({ map: textTexture(d.label, (d.id==='systems'?'Fuentes reales / Data Quality':d.id==='reception'?'Estado local / PAPER ONLY':`NO DISPONIBLE / ${d.phase}`), 'screen'), toneMapped: false });
  if (d.id === 'reception') {
    b.box([-.6, .37, -.28], [4.8, .74, 1.0], m.stone, .12);
    b.box([-.6, .79, -.28], [4.92, .09, 1.02], m.wood, .045);
    b.box([-.6, .08, -.28], [4.58, .06, .95], m.light);
    for (let i = 0; i < 39; i++) b.box([-2.76 + i * .114, .42, .224], [.035, .61, .025], m.bronze);
    b.label([-.6, .45, .251], 3.4, .48, 'JAIME INVESTOR', 'H Q  /  PAPER ONLY', 'brand');
    // Marca de entrada preservada también sobre el fondo arquitectónico.
    b.label([0,1.94,-2.78],4.2,1,'J A I M E','INVESTOR HQ','wallbrand');
    for(const side of [-1,1])for(let i=0;i<12;i++)b.box([side*(3.1+i*.1),1.55,-2.76],[.035,2.9,.07],m.wood);
    plant(b, -3.8, -2.1, m); plant(b, 3.7, -2.1, m);
  } else if (d.id === 'committee') {
    const table=new Builder('committee-table');
    table.box([0, .8, -.3], [2.65, .12, 4.6], m.wood, .3);
    for (const z of [-1.6, 1.0]) table.box([0, .4, z], [.85, .73, .2], m.bronze, .04);
    for (const side of [-1, 1]) for (const z of [-1.7, -.3, 1.1]) {
      chair(table, side * 1.83, z, -side * Math.PI / 2, m, true);
      table.box([side * .83, .87, z], [.36, .013, .48], m.paper);
      table.cylinder([side * .9, .92, z - .4], .03, .13, m.glass);
    }
    chair(table, 0, 2.65, Math.PI, m, true);
    transfer(b,table,[0,0,0],Math.PI/2);
    wallScreen(b, 0, -2.94, d, m, 3.5);
    plant(b, -4.25, -2.25, m); plant(b, 4.25, -2.25, m);
    // Bandeau de conférence encastré et accessoires, sans métriques de démonstration.
    b.box([.3,.869,0],[2.6,.012,.15],m.dark,.025);
    for(const x of [-.65,.55,1.65])b.box([x,.878,0],[.08,.008,.09],m.steel,.008);
    for(const side of [-1,1])for(let i=0;i<13;i++)b.box([side*(2.3+i*.1),1.55,-2.98],[.035,2.9,.07],m.wood);
  } else if (d.id === 'trading') {
    // Tres operadores, cada uno con doble monitor, y videopanel de estado real.
    wallScreen(b,0,-2.65,d,m,3.8);
    plant(b,3.05,-1.65,m,1.7);
    credenza(b,-2.25,2.4,m,1.8);
  } else if (d.id === 'research') {
    shelves(b,0,-2.30,m);
    plant(b,-3.05,-1.8,m);plant(b,3,-1.85,m,1.5);
  } else if (d.id === 'systems') {
    for (const z of [-1.95,-.65,.65]) {
      b.box([-2.9, 1.17, z], [1, 2.25, .88], m.dark, .04);
      for (let i = 0; i < 11; i++) { b.box([-2.9, .28 + i * .17, z+.455], [.86, .135, .026], m.book); b.box([-3.2, .28 + i * .17, z+.473], [.16, .012, .009], m.bronze); }
    }
    plant(b, 3.05, -1.8, m);
    whiteboard(b,-1,-2.64,m,'FLUJO DE DATOS');
    wallScreen(b,1.25,-2.64,d,m,2.2);
    b.label([-2.9, 2.36, -1.795], .85, .106, 'INFRAESTRUCTURA', '', 'sign');
  } else if (d.id === 'performance') {
    wallScreen(b, -1, -2.64, d, m, 2.8);
    whiteboard(b,2,-2.64,m,'MEDICIÓN / P3');
    plant(b,-3,-1.9,m);
    b.box([2.5,.76,.05],[1.1,.08,1.6],m.stone,.06);
    b.box([2.5,.38,.05],[.48,.72,.65],m.bronze,.03);
    b.box([2.5,.817,-.2],[.36,.015,.48],m.paper);
  } else if(d.id==='quant'){
    whiteboard(b,1.8,-2.34,m,'MODELO / VALIDACIÓN');
    wallScreen(b,-1.7,-2.34,d,m,2.8);
    plant(b,-3.05,-1.75,m);
    credenza(b,1.85,-2.06,m,2.3);
  } else if(d.id==='risk'){
    shelves(b,-1.45,-2.30,m);whiteboard(b,1.75,-2.34,m,'LÍMITES / CONTROLES');
    plant(b,3.05,1.8,m,1.6);
  } else {
    wallScreen(b,-1,-2.64,d,m,2.8);
    credenza(b,1.55,-2.35,m,2.8);
    whiteboard(b,1.8,-2.64,m,'PAPER ONLY / 403');
    plant(b,-3.05,-1.8,m);
  }
  for(const w of WORKSPACES.filter(w=>w.department===d.id))desk(b,w.x,w.z,m,screen,w.yaw,w.dual,!!w.occupant);
  b.group.userData = { department: d.id, center: d.center, monitor: true, phase: d.phase,sofas:0,portalWidth:4.4 };
  const group = b.finish(); group.position.set(...d.center);
  return group;
}

function architecture(m: Materials) {
  const b = new Builder('architecture');
  b.box([0, -.16, 0], [34, .32, 28], m.floor);
  for (const x of [-16.85, 16.85]) b.box([x, .008, 0], [.025, .015, 27.7], m.bronze);
  for (const z of [-13.85, 13.85]) b.box([0, .008, z], [33.7, .015, .025], m.bronze);
  for (const x of [-7.9,-5.25,5.25,7.9]) b.box([x,.018,0],[.018,.008,27.5],m.bronze);
  for(const x of [-6.6,6.6])b.box([x,.021,0],[.018,.012,26],m.light);
  for(let x=-16;x<=16;x+=2)b.box([x,.004,0],[.008,.004,27.6],m.dark);
  for(let z=-12;z<=12;z+=2)b.box([0,.004,z],[33.6,.004,.008],m.dark);
  // Vestíbulo compacto: se libera la circulación frente a los despachos adelantados.
  for(const x of [-15.2,15.2])plant(b,x,12.2,m,1.8);
  // Bordure crema, abierta al jugador y sin fachadas altas delante de la cámara.
  b.box([0,.3,-13.7],[34,.6,.18],m.cream);
  for(const x of [-16.8,16.8])b.box([x,.25,0],[.16,.5,27.4],m.cream);
  for(const x of [-16.8,16.8]){
    b.box([x,1.55,0],[.16,3.1,27.4],m.cream);
    b.box([x,3.10,0],[.19,.06,27.4],m.dark);
    b.box([x,.13,0],[.19,.26,27.4],m.dark);
  }
  b.box([0,-.3,0],[34.4,.2,28.4],m.dark);
  const a = b.finish();
  const roof = new Builder('ceiling');
  roof.box([0, FLOOR.ceiling + .07, 0], [34, .12, 28], m.ceiling);
  for (const d of DEPARTMENTS) {
    const [x, , z] = d.center;
    roof.box([x, 4.36, z], [d.size[0], .16, d.size[1]], m.soffit, .05);
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

export function createOffice(m: Materials) {
  const office = new Group(); office.name = 'JAIME_INVESTOR_HQ';
  office.add(architecture(m),...DEPARTMENTS.map(d => department(d, m)));
  const wall=new Builder('videowall'),z=VIDEOWALL.z;
  wall.box([0,7.5,z],[VIDEOWALL.width,VIDEOWALL.height,.28],m.dark,.12);
  for(const y of [3.64,11.36])wall.box([0,y,z+.17],[32.8,.025,.025],m.bronze);
  for(const side of [-1,1])wall.box([side*16.4,5.7,z],[.18,11.4,.3],m.dark);
  wall.label([-11.8,10.6,z+.16],7.4,1,'JAIME INVESTOR HQ','SIMULACIÓN / PAPER ONLY','brand');
  ['CARTERA / P3','POSICIONES / P3','OPERACIONES / P6','MERCADOS / P2','NOTICIAS / P2','RIESGOS / P5','COMITE / P5','AGENTES / P4','SISTEMAS / P2'].forEach((title,i)=>{
    wall.box([-14.4+i*3.6,6.9,z+.16],[3.46,5.28,.04],m.steel,.025);
    const screen=wall.label([-14.4+i*3.6,6.9,z+.186],3.38,5.2,title,'NO DISPONIBLE','screen');
    (screen.material as Material).name='hq:'+['portfolio','positions','operations','markets','news','risk','committee','agents','systems'][i];
  });
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
