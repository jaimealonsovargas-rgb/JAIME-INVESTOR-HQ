import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchHealth } from './api';

const valid = { status: 'ok', phase: 'P0', database: 'ok', trading_mode: 'PAPER_ONLY', orders_enabled: false, schema_version: '0001_instruments', checked_at: '2026-10-13T12:00:00Z' };
afterEach(() => vi.unstubAllGlobals());

describe('comprobación de salud sin falsos positivos', () => {
  it('consulta solo la API local y acepta el contrato paper', async () => {
    const fetch = vi.fn().mockResolvedValue(Response.json(valid));
    vi.stubGlobal('fetch', fetch);
    expect(await fetchHealth()).toEqual(valid);
    expect(fetch).toHaveBeenCalledWith('/health', expect.objectContaining({ credentials: 'omit', cache: 'no-store' }));
  });
  it.each([
    { ...valid, orders_enabled: true }, { ...valid, trading_mode: 'LIVE' },
    { ...valid, database: 'error' }, { ...valid, checked_at: 'inventado' }, {}, null,
  ])('rechaza salud inválida: %j', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(body)));
    await expect(fetchHealth()).rejects.toThrow();
  });
  it('rechaza error HTTP', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 503 })));
    await expect(fetchHealth()).rejects.toThrow('NO DISPONIBLE');
  });
  it('propaga backend desconectado', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(fetchHealth()).rejects.toThrow();
  });
});
