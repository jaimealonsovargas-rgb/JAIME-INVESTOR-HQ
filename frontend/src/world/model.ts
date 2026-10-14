import { BoxGeometry, BufferGeometry, CylinderGeometry, Group, Mesh, MeshBasicMaterial, Object3D, PlaneGeometry, SphereGeometry, type Material } from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { DEPARTMENTS, FLOOR, type Department, type Vec3 } from './layout';
import { textTexture, type Materials } from './materials';

// Modelado original en metros. Las piezas se fusionan por material y departamento.
// Conserva cada departamento como nodo independiente para fases posteriores.
const geometries = new Map<string, BufferGeometry>();
function geometry(key: string, build: () => BufferGeometry) {
  if (!geometries.has(key)) geometries.set(key, build());
  return geometries.get(key)!;
}
class Builder {
  group = new Group();
  constructor(name: string) { this.group.name = name; }
  part(geo: BufferGeometry, mat: Material, position: Vec3, scale: Vec3 = [1, 1, 1], rotation: Vec3 = [0, 0, 0]) {
    const mesh = new Mesh(geo, mat); mesh.position.set(...position); mesh.scale.set(...scale); mesh.rotation.set(...rotation);
    mesh.castShadow = !mat.transparent; mesh.receiveShadow = !mat.transparent;
    this.group.add(mesh); return mesh;
  }
  box(p: Vec3, size: Vec3, mat: Material, radius = 0, rotation: Vec3 = [0, 0, 0]) {
    const geo = radius ? geometry(`round-${size.join('-')}-${radius}`, () => new RoundedBoxGeometry(...size, 2, radius)) : geometry('box', () => new BoxGeometry());
    return this.part(geo, mat, p, radius ? [1, 1, 1] : size, rotation);
  }
  cylinder(p: Vec3, radius: number, height: number, mat: Material, top = radius) {
    return this.part(geometry(`cyl-${top / radius}`, () => new CylinderGeometry(top / radius, 1, 1, 16)), mat, p, [radius, height, radius]);
  }
  label(p: Vec3, width: number, height: number, title: string, subtitle = '', kind: 'sign' | 'screen' | 'brand' = 'sign', rotation: Vec3 = [0, 0, 0]) {
    const mat = new MeshBasicMaterial({ map: textTexture(title, subtitle, kind), toneMapped: false });
    return this.part(geometry('plane', () => new PlaneGeometry()), mat, p, [width, height, 1], rotation);
  }
  finish() {
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
  c.part(geometry('plane', () => new PlaneGeometry()), m.contact, [0, .033, 0], [1.1, 1.1, 1], [-Math.PI / 2, 0, 0]);
  c.box([0, .52, 0], [.54, .13, .55], meeting ? m.cognac : m.leather, .065);
  c.box([0, .91, -.25], [.53, .7, .09], meeting ? m.cognac : m.leather, .044, [-.12, 0, 0]);
  c.box([0, .88, -.305], [.06, .48, .04], m.dark);
  for (const side of [-1, 1]) {
    c.box([side * .32, .69, -.02], [.045, .28, .045], m.dark);
    c.box([side * .32, .82, .01], [.075, .05, .35], m.leather, .018);
  }
  c.cylinder([0, .31, 0], .045, .37, m.bronze);
  for (let i = 0; i < 5; i++) {
    const a = i * Math.PI * 2 / 5;
    c.box([Math.sin(a) * .16, .115, Math.cos(a) * .16], [.035, .04, .34], m.dark, 0, [0, a, 0]);
    c.part(geometry('wheel', () => new SphereGeometry(1, 8, 6)), m.dark, [Math.sin(a) * .31, .07, Math.cos(a) * .31], [.045, .055, .045]);
  }
  transfer(b, c, [x, 0, z], angle);
}
function transfer(to: Builder, from: Builder, position: Vec3, rotation = 0) {
  const parent = new Object3D(); parent.position.set(...position); parent.rotation.y = rotation; parent.updateMatrix();
  [...from.group.children].forEach(child => { child.updateMatrix(); child.applyMatrix4(parent.matrix); to.group.add(child); });
}
function monitor(b: Builder, x: number, z: number, m: Materials, screen: Material, rotation = 0, y = .81) {
  const t = new Builder('monitor');
  t.box([0, y + .38, 0], [.84, .49, .055], m.dark, .018);
  t.part(geometry('plane', () => new PlaneGeometry()), screen, [0, y + .38, .029], [.79, .437, 1]);
  t.box([0, y + .12, -.015], [.055, .23, .055], m.bronze);
  t.box([0, y + .015, .015], [.3, .027, .19], m.dark, .01);
  t.box([0, y + .025, .44], [.43, .025, .15], m.dark, .009);
  for (let row = 0; row < 3; row++) t.box([0, y + .041, .4 + row * .04], [.37, .004, .013], m.book);
  t.part(geometry('mouse', () => new SphereGeometry(1, 8, 6)), m.dark, [.32, y + .035, .43], [.042, .025, .065]);
  transfer(b, t, [x, 0, z], rotation);
}
function desk(b: Builder, x: number, z: number, m: Materials, screen: Material, facing = 0, dual = false) {
  const t = new Builder('desk');
  t.part(geometry('plane', () => new PlaneGeometry()), m.contact, [0, .032, 0], [3.2, 1.8, 1], [-Math.PI / 2, 0, 0]);
  t.box([0, .77, 0], [dual ? 2.4 : 1.9, .075, 1.02], m.wood, .045);
  for (const side of [-1, 1]) {
    t.box([side * (dual ? 1.02 : .8), .39, 0], [.055, .7, .72], m.dark, .018);
    t.box([side * (dual ? 1.02 : .8), .045, 0], [.1, .035, .78], m.bronze);
  }
  t.box([0, .61, -.28], [dual ? 2.0 : 1.65, .18, .035], m.dark);
  if (dual) { monitor(t, -.46, -.26, m, screen); monitor(t, .46, -.26, m, screen); }
  else monitor(t, 0, -.23, m, screen);
  t.box([-.71, .826, .22], [.24, .035, .32], m.paper, .01);
  t.cylinder([.75, .91, .2], .045, .18, m.cream);
  chair(t, 0, .92, 0, m);
  transfer(b, t, [x, 0, z], facing);
}
function plant(b: Builder, x: number, z: number, m: Materials, height = 1.8) {
  b.part(geometry('plane', () => new PlaneGeometry()), m.contact, [x, .036, z], [1.1, 1.1, 1], [-Math.PI / 2, 0, 0]);
  b.cylinder([x, .29, z], .25, .58, m.stone, .32);
  b.cylinder([x, .57, z], .28, .015, m.dark);
  for (let i = 0; i < 9; i++) {
    const a = i * 2.39996; const y = .65 + (i % 4) * height / 5;
    const dx = Math.sin(a), dz = Math.cos(a);
    b.box([x + dx * .13, y, z + dz * .13], [.015, y * .8, .015], m.green, 0, [dz * .28, 0, dx * .28]);
    b.part(geometry('leaf', () => new SphereGeometry(1, 12, 8)), i % 2 ? m.green : m.greenLight,
      [x + dx * .2, y + .37, z + dz * .2], [.105, .018, .34], [.65 + i % 3 * .18, a, .32]);
  }
}
function sofa(b: Builder, x: number, z: number, rotation: number, m: Materials) {
  const s = new Builder('sofa');
  s.part(geometry('plane', () => new PlaneGeometry()), m.contact, [0, .034, 0], [3.3, 1.65, 1], [-Math.PI / 2, 0, 0]);
  s.box([0, .32, 0], [2.45, .26, .88], m.dark, .06);
  s.box([0, .69, -.34], [2.45, .62, .22], m.cognac, .1);
  for (const x of [-.8, 0, .8]) { s.box([x, .49, .07], [.76, .19, .65], m.cognac, .07); s.box([x, .78, -.17], [.75, .38, .14], m.cognac, .06, [-.09, 0, 0]); }
  for (const side of [-1, 1]) { s.box([side * 1.18, .65, 0], [.16, .46, .88], m.cognac, .075); s.box([side * 1.02, .12, 0], [.055, .22, .66], m.bronze); }
  transfer(b, s, [x, 0, z], rotation);
}
function glassRun(b: Builder, length: number, p: Vec3, m: Materials, angle = 0) {
  const g = new Builder('glazing');
  g.box([0, 1.65, 0], [length, 3.2, .018], m.glass);
  for (const y of [.045, 3.25]) g.box([0, y, 0], [length, .065, .075], m.bronze);
  for (let i = 0; i <= Math.ceil(length / 1.5); i++) g.box([-length / 2 + length * i / Math.ceil(length / 1.5), 1.65, 0], [.035, 3.25, .05], m.dark);
  g.box([0, 1.2, .012], [length, .018, .01], m.cream);
  transfer(b, g, p, angle);
}
function roomShell(b: Builder, d: Department, m: Materials) {
  b.box([0, .009, 0], [8.35, .018, 6.35], m.carpet);
  if (d.id === 'trading' || d.id === 'reception') return;
  for (const side of [-1, 1]) {
    glassRun(b, 2.9, [side * 2.75, 0, 3.2], m);
    glassRun(b, 6.4, [side * 4.2, 0, 0], m, Math.PI / 2);
  }
  // Portail abierto de 2.6 m y puerta de vidrio estacionada a 90°, fuera del paso.
  b.box([0, 3.28, 3.2], [8.5, .24, .19], m.wood);
  glassRun(b, 1.2, [-1.35, 0, 2.55], m, Math.PI / 2);
  b.box([-1.31, 1.13, 2.6], [.035, .38, .04], m.bronze);
  b.label([0, 3.06, 3.305], 3.2, .8, `${d.number}  /  ${d.label}`, d.use);
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
    monitor(b, -.7, -.4, m, screen, Math.PI, 1.23);
    sofa(b, -3.1, 1.85, Math.PI / 2, m); sofa(b, 2.35, 1.9, -Math.PI / 2, m);
    b.cylinder([2.3, .39, .05], .56, .07, m.stone); b.cylinder([2.3, .2, .05], .24, .35, m.bronze);
    plant(b, -3.8, -2.1, m); plant(b, 3.7, -2.1, m);
  } else if (d.id === 'committee') {
    b.box([0, .8, -.3], [2.65, .12, 4.6], m.wood, .3);
    for (const z of [-1.6, 1.0]) b.box([0, .4, z], [.85, .73, .2], m.bronze, .04);
    for (const side of [-1, 1]) for (const z of [-1.7, -.3, 1.1]) {
      chair(b, side * 1.83, z, side * Math.PI / 2, m, true);
      b.box([side * .83, .87, z], [.36, .013, .48], m.paper);
      b.cylinder([side * .9, .92, z - .4], .03, .13, m.glass);
    }
    chair(b, 0, 2.65, 0, m, true);
    wallScreen(b, 0, -3.04, d, m, 2.8);
    plant(b, -3.2, -2.4, m); plant(b, 3.2, -2.4, m);
  } else if (d.id === 'trading') {
    for (const x of [-2.65, 0, 2.65]) for (const z of [-1.25, 1.25]) desk(b, x, z, m, screen, z < 0 ? 0 : Math.PI, true);
    for (const x of [-3.8, 3.8]) plant(b, x, -2.5, m, 1.5);
    b.label([0, 3.13, -3.2], 3.9, .975, '05 / TRADING FLOOR', 'INVESTIGACIÓN MULTIACTIVO  ·  PAPER ONLY');
  } else if (d.id === 'research') {
    shelves(b, 0, -2.9, m); desk(b, -2, .6, m, screen); desk(b, 1.5, .6, m, screen);
    b.cylinder([2.7, .7, -1.8], .75, .09, m.wood); b.cylinder([2.7, .35, -1.8], .08, .7, m.bronze);
    plant(b, -3.3, -1.8, m);
  } else if (d.id === 'systems') {
    for (const x of [-2.6, -1.2, .2]) {
      b.box([x, 1.17, -2.35], [1, 2.25, .8], m.dark, .04);
      for (let i = 0; i < 11; i++) { b.box([x, .28 + i * .17, -1.935], [.86, .135, .026], m.book); b.box([x - .3, .28 + i * .17, -1.917], [.16, .012, .009], m.bronze); }
    }
    desk(b, .6, .75, m, screen, 0, true); plant(b, 3.3, -2.3, m);
    b.label([-1.2, 2.65, -1.93], 3.3, .825, 'INFRAESTRUCTURA', 'SIN CONEXIONES EXTERNAS');
  } else if (d.id === 'performance') {
    wallScreen(b, 0, -2.95, d, m, 3.8);
    sofa(b, -2.8, .1, Math.PI / 2, m); sofa(b, 2.8, .1, -Math.PI / 2, m);
    b.box([0, .38, 0], [1.9, .09, .95], m.stone, .18); b.box([0, .2, 0], [.8, .33, .5], m.bronze, .05);
    desk(b, 0, 2.0, m, screen); plant(b, -3.5, -2.2, m);
  } else {
    wallScreen(b, 0, -2.98, d, m, d.id === 'risk' ? 3.5 : 2.8);
    desk(b, -2, .15, m, screen, 0, true); desk(b, 1.5, .15, m, screen, 0, true);
    b.box([0, .48, -2.65], [4.4, .9, .6], m.wood, .04);
    for (const x of [-1.5, -.5, .5, 1.5]) b.box([x, .48, -2.34], [.9, .74, .014], m.wood);
    plant(b, 3.5, 2.0, m);
  }
  b.group.userData = { department: d.id, center: d.center, monitor: true, phase: d.phase };
  const group = b.finish(); group.position.set(...d.center); return group;
}

function architecture(m: Materials) {
  const b = new Builder('architecture');
  b.box([0, -.16, 0], [34, .32, 28], m.floor);
  for (const x of [-16.85, 16.85]) b.box([x, .008, 0], [.025, .015, 27.7], m.bronze);
  for (const z of [-13.85, 13.85]) b.box([0, .008, z], [33.7, .015, .025], m.bronze);
  for (const x of [-5.5, 5.5]) for (const edge of [-1.25, 1.25]) b.box([x + edge, .018, 0], [.014, .008, 27.5], m.bronze);
  for (const z of [-4.5, 4.5]) for (const edge of [-1.24, 1.24]) b.box([0, .018, z + edge], [33.6, .008, .014], m.bronze);
  for (const x of [-16.5, -4.45, 4.45, 16.5]) for (const z of [-12.7, -3.35, 3.35, 12.7]) {
    b.box([x, 1.9, z], [.28, 3.8, .28], m.wood, .02);
    b.box([x + .147, 1.9, z + .015], [.012, 3.6, .02], m.light);
    b.box([x, .08, z], [.34, .16, .34], m.bronze, .02);
  }
  glassRun(b, 34, [0, 0, -13.7], m);
  for (const x of [-16.8, 16.8]) glassRun(b, 27.4, [x, 0, 0], m, Math.PI / 2);
  for (const x of [-10.7, 10.7]) {
    b.box([x, 1.9, 13.65], [12, 3.8, .18], m.wood);
    for (let i = 0; i < 32; i++) b.box([x - 5.7 + i * .36, 1.9, 13.53], [.027, 3.65, .035], m.bronze);
  }
  for (const x of [-4.55, 4.55]) b.box([x, 1.9, 13.7], [.4, 3.8, .5], m.stone);
  b.box([0, 3.55, 13.7], [9.2, .5, .5], m.wood);
  const a = b.finish();
  const roof = new Builder('ceiling');
  roof.box([0, FLOOR.ceiling + .07, 0], [34, .12, 28], m.ceiling);
  for (const d of DEPARTMENTS) {
    const [x, , z] = d.center;
    roof.box([x, 3.63, z], [8.45, .2, 6.45], m.soffit, .06);
    for (const side of [-1, 1]) {
      roof.box([x + side * 3.85, 3.50, z], [.045, .025, 5.8], m.light);
      roof.box([x, 3.50, z + side * 2.85], [7.72, .025, .045], m.light);
    }
    for (const dx of [-2.8, 2.8]) {
      roof.box([x + dx, 3.17, z], [.11, .075, 3.7], m.bronze, .025);
      roof.box([x + dx, 3.12, z], [.07, .013, 3.55], m.light);
      for (const dz of [-1.4, 1.4]) roof.box([x + dx, 3.43, z + dz], [.008, .45, .008], m.dark);
    }
  }
  a.add(roof.finish()); return a;
}

function skyline(m: Materials) {
  const b = new Builder('skyline');
  // Arquitectura de fondo original; no representa un skyline geográfico real.
  for (let i = 0; i < 30; i++) {
    const x = -100 + i * 7.1, h = 8 + ((i * 13) % 23), z = -42 - ((i * 7) % 20), w = 4 + i % 4;
    b.box([x, h / 2 - 10, z], [w, h, 5], i % 2 ? m.city : m.cityDark);
    b.box([x, h - 9.7, z], [w * .68, .6, 3.4], m.cityDark);
    for (let floor = 0; floor < Math.floor(h / 1.3); floor++) b.box([x, -9 + floor * 1.3, z + 2.51], [w * .88, .54, .015], m.window);
    for (let col = 0; col < 4; col++) b.box([x - w * .4 + col * w * .26, h / 2 - 10, z + 2.54], [.075, h, .04], m.cityDark);
  }
  for (const x of [-38, 38]) for (let i = 0; i < 7; i++) {
    const h = 6 + i * 2.3, z = -30 + i * 10;
    b.box([x, h / 2 - 13, z], [8, h, 7], m.city);
    for (let f = 0; f < h; f += 1.4) b.box([x, f - 12, z + 3.51], [7.5, .6, .015], m.window);
  }
  return b.finish();
}

export function createOffice(m: Materials) {
  const office = new Group(); office.name = 'JAIME_INVESTOR_HQ';
  office.add(architecture(m), skyline(m), ...DEPARTMENTS.map(d => department(d, m)));
  office.updateMatrixWorld(true);
  return office;
}

export function disposeOffice(office: Group) {
  const owned = new Set<Material>();
  office.traverse(object => { if (object instanceof Mesh) { object.geometry.dispose(); owned.add(object.material as Material); } });
  owned.forEach(mat => { if (mat instanceof MeshBasicMaterial && mat.map) { mat.map.dispose(); mat.dispose(); } });
}
