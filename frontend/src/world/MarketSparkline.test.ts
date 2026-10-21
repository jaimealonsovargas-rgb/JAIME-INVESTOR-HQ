import {it,expect} from 'vitest';
import {chartPoints} from './MarketSparkline';
import type {MarketHistory} from '../portfolioApi';
const history=(values:string[]):MarketHistory=>({state:'AVAILABLE',reason:'TEST_ONLY',identity:{},points:values.map((value,i)=>({value,observed_at:`2026-10-${10+i}T00:00:00Z`,observation_id:`TEST_ONLY_${i}`}))});
it('does not draw absent or insufficient history',()=>{expect(chartPoints()).toBeNull();expect(chartPoints(history(['1','2']))).toBeNull();expect(chartPoints({...history(['1','2','3']),state:'NO_DATA'})).toBeNull();});
it('plots comparable history and flat series without NaN',()=>{expect(chartPoints(history(['1','2','3']))).toBe('0.00,30.00 40.00,17.00 80.00,4.00');expect(chartPoints(history(['2','2','2']))).toBe('0.00,17.00 40.00,17.00 80.00,17.00');});
it('rejects values outside display range rather than inventing a line',()=>{expect(chartPoints(history(['1','2','1e999']))).toBeNull();});
