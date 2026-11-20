import {expect,it} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {ModelCalculations,ValuationReview,modelValue} from './CompanyAnalysis';
import {sampleModel} from '../testFixtures/companyModel';
it('distinguishes blocked values from zero and percentages from monetary amounts',()=>{
 expect(modelValue(null,'percent')).toBe('No calculable');expect(modelValue('0','percent')).toBe('0 %');
 expect(modelValue('2','multiple')).toBe('2 ×');expect(modelValue('1000000','USD')).toBe('1,00 M USD');
 const html=renderToStaticMarkup(<ModelCalculations model={sampleModel()}/>);
 expect(html).toContain('Falta resultado operativo.');expect(html).toContain('Fórmula y fuentes');expect(html).toContain('test-receipt');expect(html).toContain('No calculable');
});
it('shows independent review gaps and does not invent a valuation',()=>{
 const html=renderToStaticMarkup(<ValuationReview model={sampleModel()}/>);
 expect(html).toContain('WACC documentado');expect(html).toContain('Falta patrimonio total');expect(html).toContain('Conciliación del balance');expect(html).toContain('No se calcula un precio objetivo');
});
it('keeps zero reconciliation residual visible with its currency',()=>{
 const model=sampleModel();model.payload.review.checks.push({id:'cash_roll_forward',state:'PASS',reason:'Cotejo de caja',evidence_ids:[],residual:'0',reported_residual:'0',unit:'USD'});
 const html=renderToStaticMarkup(<ValuationReview model={model}/>);
 expect(html).toContain('Diferencia pendiente:');expect(html).toContain('Diferencia con la variación declarada:');expect(html).toContain('0 USD');
 model.payload.review.checks.at(-1)!.residual='0.01';
 expect(renderToStaticMarkup(<ValuationReview model={model}/>)).toContain('0,01 USD');
});
