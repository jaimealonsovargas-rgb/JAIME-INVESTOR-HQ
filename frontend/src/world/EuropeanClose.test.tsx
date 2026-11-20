import {renderToStaticMarkup} from 'react-dom/server';
import {expect,it} from 'vitest';
import type {HistoricalClose} from '../universeApi';
import {EuropeanClose} from './AssetCenter';

const sample:HistoricalClose={
  price:'123.456',currency:'EUR',isin:'HRHT00RA0005',session:'2026-10-13',
  received_at:'2026-10-14T07:00:00Z',stale:false,
  source:'https://zse.hr/en/papir/310?isin=HRHT00RA0005',
  observation_id:'test-only',payload_hash:'test-only',
};

it('shows the session, native amount and source separately from the receipt',()=>{
  const html=renderToStaticMarkup(<EuropeanClose close={sample}/>);
  for(const value of ['123,456 EUR','2026-10-13',sample.isin,sample.source,'Recibido','sesión terminada']){
    expect(html).toContain(value);
  }
});

it('marks older receipts and never substitutes a zero for an unavailable close',()=>{
  expect(renderToStaticMarkup(<EuropeanClose close={{...sample,stale:true}}/>)).toContain('actualización pendiente');
  const missing=renderToStaticMarkup(<EuropeanClose close={null}/>);
  expect(missing).toContain('no disponible');
  expect(missing).not.toContain('EUR');
});
