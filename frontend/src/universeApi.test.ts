import {afterEach,expect,it,vi} from 'vitest';
import {fetchListings,fetchUniverse,syncCatalogue} from './universeApi';
afterEach(()=>vi.unstubAllGlobals());
it('uses bounded encoded search and rejects malformed counters',async()=>{
  const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({items:[],total:-1,offset:0,limit:50})});vi.stubGlobal('fetch',fetch);
  await expect(fetchListings('100% & test','',0)).rejects.toThrow('no es válida');
  expect(fetch.mock.calls[0][0]).toContain('q=100%25+%26+test');
  expect(fetch.mock.calls[0][0]).toContain('limit=50');
});
it('treats missing coverage as an error, not zero',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({counts:{},sources:[],imports:[]})}));
  await expect(fetchUniverse()).rejects.toThrow('no es válida');
});
it('reuses caller idempotency and never sends configuration secrets',async()=>{
  const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({id:'request-one',state:'RUNNING'})});vi.stubGlobal('fetch',fetch);
  await syncCatalogue('request-one');await syncCatalogue('request-one');
  const opts=fetch.mock.calls[0][1];expect(opts.headers['Idempotency-Key']).toBe('request-one');
  expect(opts.headers['X-HQ-Universe']).toBe('1');expect(opts.credentials).toBe('omit');
  expect(opts.body).toBe('{"provider":"SEC"}');
  expect(fetch.mock.calls[1][1].headers).toEqual(opts.headers);
});
