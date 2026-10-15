import { describe, expect, it, vi } from 'vitest';
import { Box3, Mesh, PerspectiveCamera, Raycaster, Texture, Vector3 } from 'three';
import { DEPARTMENTS, FLOOR, OFFICE_FORWARD, VIDEOWALL, PLAYER_CAMERA_ENVELOPE, QUALITY, VIEWS } from './layout';
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
import {screenStep,ISOMETRIC} from './navigation';
import {humanLodLevel} from './humanLods';
import {frameStats} from './frameStats';

vi.mock('./materials', async (original) => ({ ...await original<typeof import('./materials')>(), textTexture: () => new Texture() }));

describe('planta P1.B conforme al plano', () => {
  it('evita cristales entre la cámara isométrica y la cabeza junto a los nueve agentes',()=>{
    vi.stubGlobal('document', { createElement: () => ({ getContext: () => ({ createRadialGradient: () => ({ addColorStop() {} }), fillRect() {}, fillText() {} }) }) });
    const office=createOffice(makeMaterials(Array.from({length:6},()=>new Texture())));const glass=office.userData.colliders.filter((c:{kind:string})=>c.kind==='glass');
    for(const agent of PRIMARY_AGENT_INTERACTIONS){const body=new Vector3(...agent.approach),camera=body.clone().add(new Vector3(...ISOMETRIC.offset));camera.y+=.7;body.y=1.78;expect(firstHit(camera,body,glass,.001),agent.id).toBe(1);}
    disposeOffice(office);
    vi.unstubAllGlobals();
  },15000);
  it('mantiene nueve zonas únicas en las posiciones del documento', () => {
    expect(DEPARTMENTS.map(d => d.id)).toEqual(['research', 'committee', 'trading', 'risk', 'execution', 'quant', 'performance', 'reception', 'systems']);
    expect(new Set(DEPARTMENTS.map(d => d.center.join(','))).size).toBe(9);
    expect(DEPARTMENTS.map(d => d.center)).toEqual([[-12,0,-10],[0,0,-3],[12,0,-3.7],[9,0,-10],[-12,0,3.6],[0,0,-10],[12,0,3.1],[0,0,3.8],[-12,0,-3.2]].map(([x,y,z])=>[x,y,z+OFFICE_FORWARD]));
    expect(FLOOR.width).toBe(34); expect(FLOOR.depth).toBe(28);
  });
  it('reserva pasos continuos de 2.6 metros entre zonas', () => {
    // Dos pasillos longitudinales flanquean Comité/Recepción (referencia verde).
    expect(8.3-5).toBeGreaterThanOrEqual(FLOOR.corridor);
    for (const department of DEPARTMENTS) {
      expect(Math.abs(department.center[0]) + department.size[0]/2).toBeLessThan(FLOOR.width / 2);
      expect(Math.abs(department.center[2]) + department.size[1]/2).toBeLessThan(FLOOR.depth / 2);
      expect(department.center[1]).toBe(0);
    }
  });
  it('mantiene vistas isometricas elevadas y una orientacion de juego fija',()=>{
    expect(VIEWS.interior.position[1]).toBeGreaterThan(15);
    expect(VIEWS.plan.position[1]).toBeGreaterThan(30);
    expect(QUALITY.balanced.dpr).toBeLessThanOrEqual(1);
  });
  it('crea geometría real finita y mobiliario para las nueve zonas, con presupuesto de mallas', () => {
    vi.stubGlobal('document', { createElement: () => ({ getContext: () => ({ createRadialGradient: () => ({ addColorStop() {} }), fillRect() {}, fillText() {} }) }) });
    const materials = makeMaterials(Array.from({length: 6}, () => new Texture()));
    const office = createOffice(materials);
    const glazing:typeof office[]=[];office.traverse(node=>{if(node.userData.visualOnlyGlazing)glazing.push(node as typeof office);});
    expect(glazing).toHaveLength(12);
    for(const partition of glazing)expect(partition.userData.colliders).toHaveLength(0);
    for(const [id,side] of [['research',-1],['systems',-1],['execution',-1],['risk',1],['trading',1],['performance',1]] as const){
      const d=DEPARTMENTS.find(d=>d.id===id)!,x=d.center[0]+side*d.size[0]/2;
      expect(firstHit(new Vector3(x-side*.6,1.55,d.center[2]),new Vector3(x+side*.6,1.55,d.center[2]),office.userData.colliders),`lateral opaco atravesable: ${id}`).toBeLessThan(1);
    }
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
    expect(seats).toBe(22);
    for(const d of DEPARTMENTS.filter(d=>d.id!=='committee'))expect(office.getObjectByName(`department:${d.id}`)!.userData.seats).toHaveLength(PERSONNEL.filter(p=>p.department===d.id).length);
    const receptionCamera=new PerspectiveCamera(VIEWS.interior.fov,1920/1080,.08,400);
    receptionCamera.position.set(...VIEWS.interior.position);receptionCamera.lookAt(new Vector3(...VIEWS.interior.target));receptionCamera.updateMatrixWorld(true);
    const visible:Mesh[]=[];office.traverse(o=>{if(!(o instanceof Mesh)||(o.material as {transparent?:boolean}).transparent)return;for(let p=o.parent;p;p=p.parent)if(!p.visible)return;visible.push(o);});
    for(const x of [-14,0,14])for(const y of [VIDEOWALL.bottom+.35,VIDEOWALL.bottom+VIDEOWALL.height-.3]){
      const point=new Vector3(x,y,VIDEOWALL.z+.186),screen=point.clone().project(receptionCamera);
      expect(Math.abs(screen.x)).toBeLessThan(.95);expect(Math.abs(screen.y)).toBeLessThan(.95);
      const plan=new PerspectiveCamera(VIEWS.plan.fov,1920/1080,.08,400);plan.position.set(...VIEWS.plan.position);plan.lookAt(new Vector3(...VIEWS.plan.target));plan.updateMatrixWorld(true);
      const onPlan=point.clone().project(plan);expect(Math.abs(onPlan.x)).toBeLessThan(.95);expect(Math.abs(onPlan.y)).toBeLessThan(.95);
      const hits=new Raycaster(receptionCamera.position,point.clone().sub(receptionCamera.position).normalize(),.08,receptionCamera.position.distanceTo(point)+.5).intersectObjects(visible,false);
      expect(hits.length).toBeGreaterThan(0);
      let node=hits[0].object;while(node.parent&&node.name!=='videowall')node=node.parent;
      expect(node.name,`videowall tapado en ${x},${y}`).toBe('videowall');
    }
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
    expect(PERSONNEL).toHaveLength(16);expect(new Set(PERSONNEL.map(p=>p.id)).size).toBe(16);
    expect(Object.fromEntries(DEPARTMENTS.map(d=>[d.id,PERSONNEL.filter(p=>p.department===d.id).length]))).toEqual({reception:1,trading:3,research:3,quant:2,risk:2,execution:1,committee:1,performance:1,systems:2});
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
    const a=PRIMARY_AGENT_INTERACTIONS.find(a=>a.id===m.id)!;
    expect(canInteract(p,m)).toBe(true);p.colliders=[{center:[(p.position.x+a.anchor.x)/2,1.5,(p.position.z+a.anchor.z)/2],half:[.03,1.5,2],yaw:0,kind:'glass'}];expect(canInteract(p,m)).toBe(false);
    p.colliders=[];p.position.z=m.approach[2]+10;p.yaw=Math.PI;expect(canInteract(p,m)).toBe(false);
  });
  it('no reabre hasta salir del radio de rearme y volver',()=>{
    expect(PRIMARY_AGENT_INTERACTIONS).toHaveLength(9);expect(new Set(PERSONNEL.filter(p=>p.primary).map(p=>p.department)).size).toBe(9);expect(PERSONNEL.filter(p=>p.department==='trading')).toHaveLength(3);
    const p=createPlayer(),agent=PRIMARY_AGENT_INTERACTIONS.find(a=>a.id==='trading')!;p.position.set(...agent.approach);const latch=new ProximityLatch();expect(latch.next(p)).toBe('trading');p.paused=true;expect(latch.next(p)).toBeUndefined();p.paused=false;expect(latch.next(p)).toBeUndefined();p.position.set(7,0,0);expect(latch.next(p)).toBeUndefined();p.position.set(...agent.approach);expect(latch.next(p)).toBe('trading');p.position.set(-4.3,0,-1.16);expect(canApproach(p,agent)).toBe(false);
  });
  it('traslada en cuatro direcciones de pantalla, diagonal normalizada y yaw automatico',()=>{
    const p=createPlayer();const forward=screenStep(p,1,0,1/60);const right=screenStep(createPlayer(),0,1,1/60);
    expect(forward.dot(right)).toBeCloseTo(0);expect(forward.x).toBeCloseTo(0);expect(forward.z).toBeLessThan(0);
    expect(right.x).toBeGreaterThan(0);expect(right.z).toBeCloseTo(0);
    const diagonal=screenStep(createPlayer(),1,1,1/60);expect(diagonal.length()).toBeCloseTo(forward.length());
    const heading=p.yaw;screenStep(p,0,0,1/60);expect(p.yaw).toBe(heading);
    for(let i=0;i<60;i++)screenStep(p,0,1,1/60);expect(p.yaw).toBeCloseTo(-Math.atan2(right.x,-right.z),3);
  });
  it('normaliza diagonales y hace el movimiento relativo al yaw',()=>{expect(movementVector(1,1,0).length()).toBeCloseTo(1);expect(movementVector(1,0,Math.PI/2).x).toBeCloseTo(-1);});
  it('impide atravesar cristal incluso en un salto grande y permite deslizar',()=>{
    const colliders=[{center:[0,2,0] as [number,number,number],half:[.06,2,3] as [number,number,number],yaw:0,kind:'glass' as const}];
    const p=new Vector3(-1,0,0);moveCircle(p,4,1,colliders);expect(p.x).toBeLessThan(-.4);expect(p.z).toBeCloseTo(1);expect(isFree(p.x,p.z,colliders)).toBe(true);
    expect(firstHit(new Vector3(-1,1,0),new Vector3(1,1,0),colliders)).toBeLessThan(.5);
    expect(firstHit(new Vector3(-1,4.5,0),new Vector3(1,4.5,0),colliders)).toBe(1);
  });
});
