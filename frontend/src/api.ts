export interface Health {
  status: 'ok';
  phase: 'P0';
  database: 'ok';
  trading_mode: 'PAPER_ONLY';
  orders_enabled: false;
  schema_version: string;
  checked_at: string;
}

export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  const response = await fetch('/health', {
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(5000)]) : AbortSignal.timeout(5000),
    credentials: 'omit', cache: 'no-store',
  });
  if (!response.ok) throw new Error('NO DISPONIBLE: el backend no responde correctamente.');
  const data: unknown = await response.json();
  if (typeof data !== 'object' || data === null) throw new Error('Respuesta no válida.');
  const value = data as Record<string, unknown>;
  if (value.status !== 'ok' || value.phase !== 'P0' || value.database !== 'ok'
    || value.trading_mode !== 'PAPER_ONLY' || value.orders_enabled !== false
    || typeof value.schema_version !== 'string' || typeof value.checked_at !== 'string'
    || !Number.isFinite(Date.parse(value.checked_at))) {
    throw new Error('NO DISPONIBLE: contrato de salud no válido.');
  }
  return value as unknown as Health;
}
