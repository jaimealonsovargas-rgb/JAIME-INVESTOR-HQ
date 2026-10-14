export type Vec3 = [number, number, number];
export interface Department { id: string; label: string; number: string; center: Vec3; use: string; phase: string }
export const FLOOR = { width: 34, depth: 28, ceiling: 4.5, corridor: 2.6 } as const;
// Reserva arquitectónica para P1.C. No hay personaje ni seguimiento en P1.B.
export const PLAYER_CAMERA_ENVELOPE = { minHeight: 2.8, maxHeight: 3.8, minBehind: 3, maxBehind: 4.5, lowestFixture: 4.03, portalClearance: 3.99 } as const;
export const DEPARTMENTS: Department[] = [
  { id: 'research', label: 'RESEARCH', number: '01', center: [-11, 0, -9], use: 'Biblioteca · análisis fundamental', phase: 'P4' },
  { id: 'committee', label: 'COMITÉ DE INVERSIÓN', number: '02', center: [0, 0, -9], use: 'Consejo · decisiones', phase: 'P4' },
  { id: 'trading', label: 'TRADING FLOOR', number: '03', center: [11, 0, -9], use: 'Mercados · investigación', phase: 'P3' },
  { id: 'risk', label: 'RIESGOS', number: '04', center: [-11, 0, 0], use: 'Control · límites', phase: 'P5' },
  { id: 'execution', label: 'EJECUCIÓN', number: '05', center: [0, 0, 0], use: 'Órdenes · reconciliación', phase: 'P6' },
  { id: 'quant', label: 'QUANT LAB', number: '06', center: [11, 0, 0], use: 'Laboratorio · estrategias', phase: 'P5' },
  { id: 'performance', label: 'PERFORMANCE', number: '07', center: [-11, 0, 9], use: 'Análisis · atribución', phase: 'P3' },
  { id: 'reception', label: 'RECEPCIÓN', number: '08', center: [0, 0, 9], use: 'Bienvenida · sede', phase: 'P1.D' },
  { id: 'systems', label: 'SISTEMAS / DATA QUALITY', number: '09', center: [11, 0, 9], use: 'Infraestructura · calidad', phase: 'P2' },
];
export const VIEWS = {
  interior: { label: 'Recepción', position: [12,19.7,27] as Vec3, target: [0,.7,11] as Vec3, fov: 40 },
  trading: { label: 'Trading Floor', position: [23,19,-1] as Vec3, target: [11,0,-9] as Vec3, fov: 40 },
  committee: { label: 'Comité', position: [12,19,7] as Vec3, target: [0,0,-9] as Vec3, fov: 40 },
  plan: { label: 'Vista general', position: [25, 39, 38] as Vec3, target: [0, 0, 0] as Vec3, fov: 46 },
} as const;
export type View = keyof typeof VIEWS;
export type Quality = 'balanced' | 'detail';
export const QUALITY = {
  balanced: { dpr: 1, shadows: 1024, environment: 128 },
  detail: { dpr: 1.35, shadows: 2048, environment: 256 },
} as const;
