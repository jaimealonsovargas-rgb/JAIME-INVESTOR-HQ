import {expect,it} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {AnnualStatement} from './CompanyFinancials';
import type {AnnualAccounts} from '../financialsApi';

it('keeps missing figures distinct from zero and exposes the actual fiscal period',()=>{
  const annual:AnnualAccounts={start:'2024-07-01',end:'2025-06-30',accession:'test',filed:'2025-08-01',currency:'USD',form:'10-K',core_available:1,core_total:6,state:'PARTIAL',url:'https://www.sec.gov/',metrics:[
    {metric:'revenue',label:'Ingresos',state:'MISSING',fact:null,candidate_ids:[]},
    {metric:'cash',label:'Efectivo',state:'AVAILABLE',candidate_ids:['test'],fact:{id:'test',cik:'0000000001',metric:'cash',taxonomy:'us-gaap',concept:'CashAndCashEquivalentsAtCarryingValue',unit:'USD',value:'0',start:null,end:'2025-06-30',days:null,period_type:'INSTANT',accession:'test',filed:'2025-08-01',form:'10-K',filing_fiscal_year:2025,published_bound:'2025-08-02T05:00:00Z'}}]};
  const html=renderToStaticMarkup(<AnnualStatement annual={annual}/>);
  expect(html).toContain('No disponible');expect(html).toContain('0,00 M USD');expect(html).toContain('30 jun 2025');
  expect(html).toContain('1 de 6');expect(html).toContain('Valor exacto');expect(html).toContain('Abrir 10-K original');
});
