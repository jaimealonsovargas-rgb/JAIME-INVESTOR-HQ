import {describe,it,expect} from 'vitest';
import {validateQuality,validateSource,validateRefresh,safeHttps} from './dataApi';

const rights={license:'TEST_ONLY',source:'https://example.org/TEST_ONLY',scope:'open',attribution:'TEST_ONLY',access_allowed:true,display_allowed:true,storage_allowed:true,redistribution_allowed:true};
const row={access_id:'A01',provider:'TEST_ONLY',name:'TEST_ONLY',implemented:true,data_kind:'macro_series',asset_class:'MACRO_SERIES',country:'ES',market:'TEST_ONLY',feed:'TEST_ONLY',docs:'https://example.org/TEST_ONLY',rights,quota_note:'TEST_ONLY',quota_used:1,next_allowed_at:null,state:'AVAILABLE_VERIFIED',reason:'TEST_ONLY',checked_at:'2026-10-14T00:00:00Z',latency_ms:25,http_status:200,real_connection:true,usable:true,normalized_count:1};
const quality={checked_at:'2026-10-14T00:00:00Z',counts:{candidate_providers:1,candidate_access_modes:1,implemented_adapters:1,verified_connections:1,usable_sources:1},sources:[row]};
const observation={id:'TEST_ONLY',series_id:'TEST_ONLY',provider:'TEST_ONLY',feed:'TEST_ONLY',venue:'TEST_ONLY',data_kind:'macro_series',period:'2025',period_precision:'year',observed_at:'2025-01-01T00:00:00Z',received_at:'2026-10-14T00:00:00Z',published_at:null,value:'1.234567890123456789',currency:null,unit:'TEST_ONLY',metadata:{},quality_flags:['TEST_ONLY'],rights,source_ref:'https://example.org/TEST_ONLY',execution_eligible:false};
const result={access_id:'A01',state:'AVAILABLE_VERIFIED',reason:'TEST_ONLY',checked_at:'2026-10-14T00:00:00Z',latency_ms:25,real_connection:true,usable:true,cache_hit:false,normalized_count:1,observations:[observation]};
describe('Contratos frontend de datos reales',()=>{
 it('acepta cifras coherentes y conserva precisión textual',()=>{expect(validateQuality(quality).sources).toHaveLength(1);expect(validateSource(result).observations[0].value).toBe('1.234567890123456789');});
 it('rechaza contadores inflados, derechos ausentes y datos numéricos float',()=>{
  expect(()=>validateQuality({...quality,counts:{...quality.counts,verified_connections:2}})).toThrow();
  expect(()=>validateQuality({...quality,sources:[{...row,real_connection:false}]})).toThrow();
  expect(()=>validateSource({...result,observations:[{...observation,value:1.234}]})).toThrow();
  expect(()=>validateSource({...result,observations:[{...observation,rights:{...rights,display_allowed:false}}]})).toThrow();
  expect(()=>validateSource({...result,observations:[{...observation,execution_eligible:true}]})).toThrow();
 });
 it('no admite enlaces ejecutables ni secretos en URLs',()=>{expect(safeHttps('javascript:alert(1)')).toBe(false);expect(safeHttps('https://key:secret@example.org')).toBe(false);expect(safeHttps('https://example.org')).toBe(true);});
});

it('admite visualización personal sin atribuir redistribución y rechaza ausencia de permiso de pantalla',()=>{
 const personal={...rights,scope:'personal',redistribution_allowed:false,local_research_allowed:true};
 expect(validateSource({...result,observations:[{...observation,rights:personal}]}).observations[0].rights.redistribution_allowed).toBe(false);
 expect(()=>validateSource({...result,observations:[{...observation,rights:{...personal,display_allowed:false}}]})).toThrow();
});

it('valida el refresco persistente sin aceptar concurrencia, cadencias o fuentes duplicadas',()=>{
 const source={access_id:'A21',eligible:true,cadence_seconds:86400,state:'DELAYED',attempted_at:null,succeeded_at:null,next_due_at:null,failures:0};
 const report={enabled:true,running:true,concurrency:1,last_error:null,note:'TEST_ONLY',sources:[source]};
 expect(validateRefresh(report).sources[0].succeeded_at).toBeNull();
 for(const change of [{concurrency:4},{sources:[source,source]},{sources:[{...source,cadence_seconds:30}]},{sources:[{...source,next_due_at:'invalid'}]},{last_error:'SECRET'}])expect(()=>validateRefresh({...report,...change})).toThrow();
});
