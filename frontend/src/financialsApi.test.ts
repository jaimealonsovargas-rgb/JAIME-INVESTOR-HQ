import {afterEach,expect,it,vi} from 'vitest';
import {financialValue,fetchFinancialSummary,fetchFactHistory,startFinancialImport} from './financialsApi';
afterEach(()=>vi.unstubAllGlobals());

it('keeps monetary, share and per-share units distinct and preserves zero',()=>{
  expect(financialValue('123000000','USD')).toBe('123,00 M USD');
  expect(financialValue('0','USD')).toBe('0,00 M USD');
  expect(financialValue('-2.15','USD/shares')).toBe('-2,15 USD/shares');
  expect(financialValue('485500000','shares')).toBe('485,5 M acciones');
  expect(financialValue('not-a-number','USD')).toBe('Dato no válido');
});
it('rejects absent counts rather than inventing coverage',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({counts:{},latest_job:null})}));
  await expect(fetchFinancialSummary()).rejects.toThrow('no es válida');
});
it('rejects non-finite financial values and bounds evidence pages',async()=>{
  const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({items:[{id:'x',unit:'USD',value:'NaN',end:'2025-12-31',accession:'a',filed:'2026-02-01',concept:'Assets'}],total:1,offset:0,limit:25})});
  vi.stubGlobal('fetch',fetch);
  await expect(fetchFactHistory('0000000001','assets',0)).rejects.toThrow('no es válida');
  expect(fetch.mock.calls[0][0]).toContain('limit=25');
});
it('uses a stable import key and sends only requested public issuer identifiers',async()=>{
  const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({id:'same-key',state:'QUEUED',total:2,completed:0,manifest:{issuers:[]},current:[],errors:[],counts:{}})});
  vi.stubGlobal('fetch',fetch);
  await startFinancialImport('same-key',['0000000001']);await startFinancialImport('same-key',['0000000001']);
  expect(fetch.mock.calls[0][1].headers['Idempotency-Key']).toBe('same-key');
  expect(fetch.mock.calls[1][1].body).toBe('{"ciks":["0000000001"]}');
  expect(fetch.mock.calls[0][1].credentials).toBe('omit');
});
