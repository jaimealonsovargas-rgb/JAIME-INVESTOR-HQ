import {test,expect} from 'vitest';
import {validateOverview} from './HQVideowall';

test.skipIf(import.meta.env.VITE_HQ_LIVE_QA!=='1')('explicit local read-only HTTP overview contract',async()=>{
 const response=await fetch('http://127.0.0.1:8000/api/hq/overview');
 expect(response.status).toBe(200);
 expect(validateOverview(await response.json()).sections).toHaveLength(9);
});
