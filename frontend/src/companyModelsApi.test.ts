import {afterEach,expect,it,vi} from 'vitest';
import {buildCompanyModel,validCompanyModel} from './companyModelsApi';
import {sampleModel} from './testFixtures/companyModel';
afterEach(()=>vi.unstubAllGlobals());
it('rejects invalid arithmetic, dangling citations and non-SEC source links',()=>{
 const m=sampleModel();expect(validCompanyModel(m)).toBe(true);
 m.payload.review.checks[0].residual='NaN';expect(validCompanyModel(m)).toBe(false);
 delete m.payload.review.checks[0].residual;
 m.payload.metrics[0].state='AVAILABLE';m.payload.metrics[0].value='NaN';expect(validCompanyModel(m)).toBe(false);
 m.payload.metrics[0].value='0';expect(validCompanyModel(m)).toBe(true);
 m.payload.metrics[0].evidence_ids=['missing'];expect(validCompanyModel(m)).toBe(false);
 m.payload.metrics[0].evidence_ids=['test-fact'];m.payload.evidence['test-fact'].url='javascript:alert(1)';expect(validCompanyModel(m)).toBe(false);
});
it('uses idempotency and reports missing inputs without exposing raw server text',async()=>{
 const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>sampleModel()});vi.stubGlobal('fetch',fetch);
 await buildCompanyModel('0000000001','same-build-key');await buildCompanyModel('0000000001','same-build-key');
 expect(fetch.mock.calls[0][1].headers['Idempotency-Key']).toBe(fetch.mock.calls[1][1].headers['Idempotency-Key']);
 expect(fetch.mock.calls[0][1].body).toBe('{}');expect(fetch.mock.calls[0][1].credentials).toBe('omit');
 fetch.mockResolvedValue({ok:false,json:async()=>({detail:'NO_FINANCIAL_DATA'})});await expect(buildCompanyModel('1','same-build-key')).rejects.toThrow('actualiza las cuentas SEC');
 fetch.mockResolvedValue({ok:false,json:async()=>({detail:'SECRET_SHOULD_NOT_BE_SHOWN'})});await expect(buildCompanyModel('1','same-build-key')).rejects.not.toThrow('SECRET_SHOULD_NOT_BE_SHOWN');
});
