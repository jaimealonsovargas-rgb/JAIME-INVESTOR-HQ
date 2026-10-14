import { describe, expect, it, vi } from 'vitest';
import { Box3, Mesh, Texture } from 'three';
import { DEPARTMENTS, FLOOR, QUALITY, VIEWS } from './layout';
import { makeMaterials } from './materials';
import { createOffice, disposeOffice } from './model';

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
      expect(y).toBeGreaterThan(0); expect(y).toBeLessThan(FLOOR.ceiling);
    }
    expect(QUALITY.balanced.dpr).toBeLessThanOrEqual(1);
  });
  it('crea geometría real finita y mobiliario para las nueve zonas, con presupuesto de mallas', () => {
    vi.stubGlobal('document', { createElement: () => ({ getContext: () => ({ createRadialGradient: () => ({ addColorStop() {} }), fillRect() {} }) }) });
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
    expect(office.getObjectByName('ceiling')).toBeDefined();
    expect(meshes).toBeLessThan(250); expect(triangles).toBeLessThan(450000);
    disposeOffice(office);
    vi.unstubAllGlobals();
  });
});
