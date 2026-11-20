import {afterEach,expect,it,vi} from 'vitest';
import {fetchInstrumentMarket,fetchMarketSummary,marketNumber,marketTime,startMarketJob} from './marketApi';

afterEach(()=>vi.unstubAllGlobals());
const stamp='2026-10-29T10:00:00Z';
const job={id:'same-key',kind:'history',state:'QUEUED',created_at:stamp,updated_at:stamp,reason:'En cola',progress:{pages:0,bars:0},listing_id:'asset'};
const instrument=()=>({listing_id:'asset',identity:{state:'IDENTIFIED',reason:'Alpaca',asset_id:'uuid',symbol:'TEST',venue:'NASDAQ',currency:'USD',issuer_link:'UNCONFIRMED',candidates:[]},quote:{state:'NO_DATA',as_of:null,received_at:null,feed:'iex',price:null,bid:null,ask:null,reason:'Sin consultar',market_state:'UNKNOWN',market_checked_at:null},history:{series:[] as unknown[],manifest:null,sets:[]}});
const response=(data:unknown)=>({ok:true,json:async()=>data});

it('keeps absent prices distinct from zero and rejects non-finite display values',()=>{
  expect(marketNumber(null,'USD')).toBe('No disponible');
  expect(marketNumber('0','USD')).toBe('0,00 USD');
  expect(marketNumber('Infinity')).toBe('Dato no válido');
  expect(marketNumber('NaN')).toBe('Dato no válido');
  expect(marketTime('not-a-date')).toBe('Sin observación');
});

it('rejects a successful HTTP response with missing source coverage',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(response({source:{state:'READY_TO_FETCH'},counts:{assets:100}})));
  await expect(fetchMarketSummary()).rejects.toThrow('no es válida');
});

it('rejects malformed prices and inconsistent OHLC bars before rendering',async()=>{
  const data=instrument();data.quote.price='NaN' as unknown as null;
  const fetch=vi.fn().mockResolvedValue(response(data));vi.stubGlobal('fetch',fetch);
  await expect(fetchInstrumentMarket('asset','raw')).rejects.toThrow('no es válida');
  data.quote.price=null;
  data.history.series=[{t:stamp,o:'100',h:'90',l:'80',c:'95',v:'1'}];
  await expect(fetchInstrumentMarket('asset','raw')).rejects.toThrow('no es válida');
});

it('requests a separate adjustment series and escapes listing identifiers',async()=>{
  const fetch=vi.fn().mockResolvedValue(response(instrument()));vi.stubGlobal('fetch',fetch);
  await fetchInstrumentMarket('a/b','split');
  expect(fetch.mock.calls[0][0]).toBe('/api/universe/listings/a%2Fb/market?adjustment=split');
  expect(fetch.mock.calls[0][1].credentials).toBe('omit');
});

it('retains caller idempotency across retries and sends no credentials',async()=>{
  const fetch=vi.fn().mockResolvedValue(response(job));vi.stubGlobal('fetch',fetch);
  const request={kind:'history' as const,listing_id:'asset',start:'2025-10-29',end:'2026-10-29',adjustment:'raw' as const};
  await startMarketJob('same-key',request);await startMarketJob('same-key',request);
  expect(fetch.mock.calls.map(call=>call[1].headers['Idempotency-Key'])).toEqual(['same-key','same-key']);
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual(request);
  expect(fetch.mock.calls[0][1].headers['X-HQ-Universe']).toBe('1');
  expect(fetch.mock.calls[0][1].credentials).toBe('omit');
});

it('preserves unlinked SEC identities and unavailable prices without zero-filling',async()=>{
  const data=instrument();data.identity.asset_id=null as unknown as string;data.identity.state='UNLINKED';data.identity.currency=null as unknown as string;
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(response(data)));
  const result=await fetchInstrumentMarket('asset','raw');
  expect(result.identity.asset_id).toBeNull();expect(result.quote.price).toBeNull();expect(result.history.manifest).toBeNull();
});
