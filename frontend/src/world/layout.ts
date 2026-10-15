export type Vec3 = [number, number, number];
export interface Department { id: string; label: string; number: string; center: Vec3; size: [number,number]; entrance:'south'|'east'|'west'|'sides'; use: string; phase: string }
export const FLOOR = { width: 34, depth: 28, ceiling: 4.5, corridor: 2.6 } as const;
export const OFFICE_FORWARD = 4.3;
export const VIDEOWALL = { width: 33, height: 7.8, bottom: 3.6, z: -13.35 + OFFICE_FORWARD } as const;
// Reserva arquitectónica para P1.C. No hay personaje ni seguimiento en P1.B.
export const PLAYER_CAMERA_ENVELOPE = { minHeight: 2.8, maxHeight: 3.8, minBehind: 3, maxBehind: 4.5, lowestFixture: 4.03, portalClearance: 3.99 } as const;
export const DEPARTMENTS: Department[] = ([
  { id: 'research', label: 'RESEARCH', number: '01', center: [-12, 0, -10], size:[7.4,5],entrance:'south', use: 'Biblioteca · análisis fundamental', phase: 'P4' },
  { id: 'committee', label: 'COMITÉ DE INVERSIÓN', number: '02', center: [0, 0, -3], size:[10,6.2],entrance:'sides', use: 'Consejo · decisiones', phase: 'P5' },
  { id: 'trading', label: 'TRADING', number: '03', center: [12, 0, -3.7], size:[7.4,5.6],entrance:'west', use: 'Mercados · investigación', phase: 'P3' },
  { id: 'risk', label: 'RIESGOS', number: '04', center: [9, 0, -10], size:[7.4,5],entrance:'south', use: 'Control · límites', phase: 'P5' },
  { id: 'execution', label: 'EJECUCIÓN', number: '05', center: [-12, 0, 3.6], size:[7.4,5.6],entrance:'east', use: 'Órdenes · reconciliación', phase: 'P6' },
  { id: 'quant', label: 'QUANT LAB', number: '06', center: [0, 0, -10], size:[7.4,5],entrance:'south', use: 'Laboratorio · estrategias', phase: 'P5' },
  { id: 'performance', label: 'PERFORMANCE', number: '07', center: [12, 0, 3.1], size:[7.4,5.6],entrance:'west', use: 'Análisis · atribución', phase: 'P3' },
  { id: 'reception', label: 'RECEPCIÓN', number: '08', center: [0, 0, 3.8], size:[10,5.8],entrance:'south', use: 'Bienvenida · sede', phase: 'P1.D' },
  { id: 'systems', label: 'SISTEMAS', number: '09', center: [-12, 0, -3.2], size:[7.4,5.6],entrance:'east', use: 'Infraestructura · Data Quality', phase: 'P2' },
] satisfies Department[]).map(d=>({...d,center:[d.center[0],0,d.center[2]+OFFICE_FORWARD] as Vec3}));
export const VIEWS = {
  interior: { label: 'Recepción', position: [0,26,35] as Vec3, target: [0,2,4.3] as Vec3, fov: 50 },
  trading: { label: 'Trading Floor', position: [14,15,16.3] as Vec3, target: [12,.5,.6] as Vec3, fov: 40 },
  committee: { label: 'Comité', position: [2,15,16.3] as Vec3, target: [0,.5,.7] as Vec3, fov: 40 },
  plan: { label: 'Vista general', position: [0,66,68.3] as Vec3, target: [0,2,3.8] as Vec3, fov: 22 },
  videowall: { label: 'Videowall', position: [0,9,17] as Vec3, target: [0,7.5,VIDEOWALL.z] as Vec3, fov: 50 },
} as const;
export type View = keyof typeof VIEWS;
export type Quality = 'balanced' | 'fixed' | 'detail';
export const QUALITY = {
  balanced: { dpr: .8, shadows: 1024, environment: 128 },
  fixed: { dpr: .8, shadows: 1024, environment: 128 },
  detail: { dpr: 1.35, shadows: 2048, environment: 256 },
} as const;
