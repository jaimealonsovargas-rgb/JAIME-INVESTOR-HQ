import { describe, expect, it, vi } from 'vitest';
import { Box3, Mesh, Raycaster, Texture, Vector3 } from 'three';
import { DEPARTMENTS, FLOOR, PLAYER_CAMERA_ENVELOPE, QUALITY, VIEWS } from './layout';
import { makeMaterials } from './materials';
import { createOffice, disposeOffice } from './model';
import { SAFE_SPAWNS,validTeleport,movementVector } from './navigation';
import { firstHit,moveCircle,isFree,moveCamera } from './collisions';
import {findWalkingPath} from './pathfinding';
import {MONITOR_DEFINITIONS,canInteract} from './terminals';
import {createPlayer} from './navigation';
import {PANEL_CONTENT} from './panels';
import {PERSONNEL,PERSONNEL_COLLIDERS} from './staffLayout';
import {PRIMARY_AGENT_INTERACTIONS,ProximityLatch,canApproach} from './agentInteractions';
import {tankStep} from './navigation';
import {humanLodLevel} from './humanLods';
import {frameStats} from './frameStats';

vi.mock('./materials', async (original) => ({ ...await original<typeof import('./materials')>(), textTexture: () => new Texture() }));

describe('planta P1.B conforme al plano', () => {
  it('mantiene nueve zonas únicas en las posiciones del documento', () => {
    expect(DEPARTMENTS.map(d => d.id)).toEqual(['research', 'committee', 'quant', 'risk', 'trading', 'execution', 'performance', 'reception', 'systems']);
    expect(new Set(DEPARTMENTS.map(d => d.center.join(','))).size).toBe(9);
    expect(DEPARTMENTS.map(d => d.center)).toEqual([[-11,0,-9],[0,0,-9],[11,0,-9],[-11,0,0],[0,0,0],[11,0,0],[-11,0,9],[0,0,9],[11,0,9]]);
    expect(FLOOR.width).toBe(34); expect(FLOOR.depth).toBe(28);
  });
  it('reserva pasos continuos de 2.6 metros entre zonas', () => {
    expect(11 - 8.4).toBeCloseTo(FLOOR.corridor);
    expect(9 - 6.4).toBeCloseTo(FLOOR.corridor);
    for (const department of DEPARTMENTS) {
      expect(Math.abs(department.center[0]) + 4.2).toBeLessThan(FLOOR.width / 2);
      expect(Math.abs(department.center[2]) + 3.2).toBeLessThan(FLOOR.depth / 2);
      expect(department.center[1]).toBe(0);
    }
  });
  it('mantiene los presets de interior dentro de la envolvente', () => {
    for (const name of ['interior', 'trading', 'committee'] as const) {
      const [x, y, z] = VIEWS[name].position;
      expect(Math.abs(x)).toBeLessThan(FLOOR.width / 2);
      expect(Math.abs(z)).toBeLessThan(FLOOR.depth / 2);
      expect(y).toBeGreaterThanOrEqual(PLAYER_CAMERA_ENVELOPE.minHeight); expect(y).toBeLessThanOrEqual(PLAYER_CAMERA_ENVELOPE.maxHeight);
      expect(VIEWS[name].target[1]).toBeLessThan(y);
    }
    expect(QUALITY.balanced.dpr).toBeLessThanOrEqual(1);
    expect(PLAYER_CAMERA_ENVELOPE.lowestFixture).toBeGreaterThan(PLAYER_CAMERA_ENVELOPE.maxHeight);
    expect(PLAYER_CAMERA_ENVELOPE.portalClearance).toBeGreaterThan(PLAYER_CAMERA_ENVELOPE.maxHeight);
  });
  it('crea geometría real finita y mobiliario para las nueve zonas, con presupuesto de mallas', () => {
    vi.stubGlobal('document', { createElement: () => ({ getContext: () => ({ createRadialGradient: () => ({ addColorStop() {} }), fillRect() {}, fillText() {} }) }) });
    const materials = makeMaterials(Array.from({length: 6}, () => new Texture()));
    const office = createOffice(materials);
    let meshes = 0, triangles = 0;
    office.traverse(object => {
      if (!(object instanceof Mesh)) return;
      meshes++; triangles += object.geometry.getAttribute('position').count / 3;
      const box = new Box3().setFromObject(object);
      expect(Number.isFinite(box.min.x + box.max.y + box.max.z)).toBe(true);
    });
    for (const department of DEPARTMENTS) {
      const node = office.getObjectByName(`department:${department.id}`)!;
      expect(node).toBeDefined(); expect(node.position.toArray()).toEqual(department.center);
      expect(node.children.length).toBeGreaterThan(5);
      expect(node.userData.monitor).toBe(true);
    }
    const ceiling=office.getObjectByName('ceiling')!;
    expect(new Box3().setFromObject(ceiling).min.y).toBeGreaterThan(PLAYER_CAMERA_ENVELOPE.maxHeight);
    // Haz horizontal a la altura máxima prevista, a través del umbral central.
    // Comprueba geometría real; no introduce navegación ni colisiones del jugador.
    for(const d of DEPARTMENTS) {
      const ray=new Raycaster(new Vector3(d.center[0],PLAYER_CAMERA_ENVELOPE.maxHeight,d.center[2]+4),new Vector3(0,0,-1),0,2);
      expect(ray.intersectObject(office.getObjectByName(`department:${d.id}`)!,true)).toHaveLength(0);
    }
    // Todas las sillas de trabajo deben mirar hacia una superficie de mesa real.
    let seats=0;
    for(const d of DEPARTMENTS) {
      const node=office.getObjectByName(`department:${d.id}`)!;
      const desks=node.children.filter(o=>o instanceof Mesh && o.material===materials.wood);
      for(const seat of node.userData.seats) {
        const origin=new Vector3(...seat.position).applyMatrix4(node.matrixWorld);
        const ray=new Raycaster(origin,new Vector3(...seat.forward),.15,2.5);
        expect(ray.intersectObjects(desks,false).length,`silla en ${d.id} mira fuera de su mesa`).toBeGreaterThan(0);
        seats++;
      }
    }
    expect(seats).toBe(24);
    for(const id of Object.keys(SAFE_SPAWNS))expect(validTeleport(id,office.userData.colliders),`spawn ocupado: ${id}`).toBeDefined();
    for(const [id,p] of Object.entries(SAFE_SPAWNS))expect(findWalkingPath([0,11],[p[0],p[2]],office.userData.colliders),`no existe recorrido peatonal: ${id}`).toBeDefined();
    expect(MONITOR_DEFINITIONS).toHaveLength(9);
    expect(MONITOR_DEFINITIONS.map(m=>m.id).sort()).toEqual(DEPARTMENTS.map(d=>d.id).sort());
    const player=createPlayer();player.colliders=office.userData.colliders;
    for(const monitor of MONITOR_DEFINITIONS){
      player.position.set(...monitor.approach);player.yaw=monitor.yaw;
      expect(isFree(player.position.x,player.position.z,player.colliders),`acceso ocupado: ${monitor.id}`).toBe(true);
      expect(findWalkingPath([0,11],[player.position.x,player.position.z],player.colliders),`terminal inaccesible: ${monitor.id}`).toBeDefined();
      expect(canInteract(player,monitor),`terminal sin línea de visión: ${monitor.id}`).toBe(true);
      player.yaw+=Math.PI;expect(canInteract(player,monitor)).toBe(true);player.yaw=monitor.yaw;
      player.paused=true;expect(canInteract(player,monitor)).toBe(false);player.paused=false;
      player.position.z+=10;expect(canInteract(player,monitor)).toBe(false);
      expect(PANEL_CONTENT[monitor.id]).toBeDefined();
    }
    expect(PERSONNEL).toHaveLength(10);expect(new Set(PERSONNEL.map(p=>p.id)).size).toBe(10);
    const occupied=[...office.userData.colliders,...PERSONNEL_COLLIDERS];
    for(const person of PERSONNEL){expect(person.seated).toBe(true);const node=office.getObjectByName(`department:${person.department}`)!;expect(node.userData.seats.some((s:{position:[number,number,number]})=>{const seat=new Vector3(...s.position).applyMatrix4(node.matrixWorld);return Math.hypot(seat.x-person.position[0],seat.z-person.position[2])<1e-6;}),`NPC fuera de su silla: ${person.id}`).toBe(true);expect(person.state).toBe('OFFLINE');expect(person.work).toBe('NO DISPONIBLE — P4');}
    for(const [id,p] of Object.entries(SAFE_SPAWNS)){expect(validTeleport(id,occupied),`NPC ocupa spawn: ${id}`).toBeDefined();expect(findWalkingPath([0,11],[p[0],p[2]],occupied),`NPC bloquea departamento: ${id}`).toBeDefined();}
    for(const monitor of MONITOR_DEFINITIONS){expect(findWalkingPath([0,11],[monitor.approach[0],monitor.approach[2]],occupied),`NPC bloquea terminal: ${monitor.id}`).toBeDefined();player.position.set(...monitor.approach);player.yaw=monitor.yaw;player.colliders=occupied;expect(canInteract(player,monitor),`NPC bloquea LOS: ${monitor.id}`).toBe(true);}
    expect(meshes).toBeLessThan(250); expect(triangles).toBeLessThan(450000);
    disposeOffice(office);
    vi.unstubAllGlobals();
  },15000);
});
describe('navegación determinista',()=>{
  it('barre la cámara suavizada contra columnas y vidrio sin limitarla a la planta',()=>{
    const colliders=[{center:[0,2.25,0] as [number,number,number],half:[.14,2.25,.14] as [number,number,number],yaw:0,kind:'solid' as const}];
    const p=new Vector3(-1,3.2,0);moveCamera(p,new Vector3(1,3.2,0),colliders);expect(p.x).toBeLessThan(-.25);expect(p.y).toBe(3.2);
    const outside=new Vector3(0,3.2,14.8);moveCamera(outside,new Vector3(0,3.2,15),[]);expect(outside.z).toBe(15);
    const low=[{center:[0,.65,0] as [number,number,number],half:[.4,.65,.4] as [number,number,number],yaw:0,kind:'solid' as const}];moveCamera(p,new Vector3(1,3.2,0),low);expect(p.x).toBeCloseTo(1);
  });
  it('incluye las pausas largas en el promedio real de fotogramas',()=>{expect(frameStats([10,10,1000]).fps).toBeCloseTo(3000/1020);expect(frameStats([10,10,1000]).p95).toBe(1000);expect(frameStats([]).fps).toBe(0);});
  it('evita oscilación del LOD en sus umbrales',()=>{expect(humanLodLevel(8.2,0)).toBe(0);expect(humanLodLevel(8.2,1)).toBe(1);expect(humanLodLevel(16.2,1)).toBe(1);expect(humanLodLevel(16.2,2)).toBe(2);expect(humanLodLevel(3,2)).toBe(0);});
  it('abre por agente y evita cristal, distancia y salas equivocadas',()=>{
    const m=MONITOR_DEFINITIONS.find(m=>m.id==='performance')!,p=createPlayer();p.position.set(...m.approach);
    expect(canInteract(p,m)).toBe(true);p.colliders=[{center:[-11.5,1.5,9.5],half:[.03,1.5,2],yaw:0,kind:'glass'}];expect(canInteract(p,m)).toBe(false);
    p.colliders=[];p.position.z=5.5;p.yaw=Math.PI;expect(canInteract(p,m)).toBe(false);
  });
  it('no reabre hasta salir del radio de rearme y volver',()=>{
    expect(PRIMARY_AGENT_INTERACTIONS).toHaveLength(9);expect(new Set(PERSONNEL.filter(p=>p.primary).map(p=>p.department)).size).toBe(9);expect(PERSONNEL.filter(p=>p.department==='trading')).toHaveLength(2);
    const p=createPlayer(),agent=PRIMARY_AGENT_INTERACTIONS.find(a=>a.id==='trading')!;p.position.set(...agent.approach);const latch=new ProximityLatch();expect(latch.next(p)).toBe('trading');p.paused=true;expect(latch.next(p)).toBeUndefined();p.paused=false;expect(latch.next(p)).toBeUndefined();p.position.set(0,0,3.05);expect(latch.next(p)).toBeUndefined();p.position.set(...agent.approach);expect(latch.next(p)).toBe('trading');p.position.set(-4.3,0,-1.16);expect(canApproach(p,agent)).toBe(false);
  });
  it('flechas con aceleración, giro suave y retroceso sin girar 180 grados',()=>{
    const p=createPlayer();let distance=0;for(let i=0;i<60;i++)distance+=tankStep(p,1,0,1/60).length();expect(distance).toBeGreaterThan(1.2);expect(distance).toBeLessThan(1.45);expect(p.yaw).toBe(0);for(let i=0;i<60;i++)tankStep(p,0,1,1/60);expect(p.yaw).toBeGreaterThan(1);expect(p.yaw).toBeLessThan(1.25);const heading=p.yaw;for(let i=0;i<60;i++)tankStep(p,-1,0,1/60);expect(p.direction).toBe(-1);expect(Math.abs(p.yaw-heading)).toBeLessThan(.2);
  });
  it('normaliza diagonales y hace el movimiento relativo al yaw',()=>{expect(movementVector(1,1,0).length()).toBeCloseTo(1);expect(movementVector(1,0,Math.PI/2).x).toBeCloseTo(-1);});
  it('impide atravesar cristal incluso en un salto grande y permite deslizar',()=>{
    const colliders=[{center:[0,2,0] as [number,number,number],half:[.06,2,3] as [number,number,number],yaw:0,kind:'glass' as const}];
    const p=new Vector3(-1,0,0);moveCircle(p,4,1,colliders);expect(p.x).toBeLessThan(-.4);expect(p.z).toBeCloseTo(1);expect(isFree(p.x,p.z,colliders)).toBe(true);
    expect(firstHit(new Vector3(-1,1,0),new Vector3(1,1,0),colliders)).toBeLessThan(.5);
    expect(firstHit(new Vector3(-1,4.5,0),new Vector3(1,4.5,0),colliders)).toBe(1);
  });
});
