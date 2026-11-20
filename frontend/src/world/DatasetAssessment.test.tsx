import {expect,it} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {DatasetAssessment} from './DatasetAssessment';
import {validAssessment,type DatasetAssessment as Assessment} from '../marketApi';

const id='a'.repeat(64);
function value():Assessment{return {
  policy:'daily-trend-data-v1',family:'Tendencia diaria · piloto de datos',as_of:'2026-11-08T09:00:00Z',manifest_id:id,
  research_state:'EXPLORATORY_ONLY',backtest_state:'BLOCKED',
  identity:{state:'DOCUMENTED',reason:'Clase y emisor contrastados.',cik:'0000000001',security_title:'Common Stock',known_from:'2026-11-07T09:00:00Z',market_listing_id:id,
    native_currency:null,native_currency_state:'UNVERIFIED',native_currency_reason:'Evidencia independiente pendiente.',current_contract:null,
    evidence:[{kind:'SEC_COMMON_STOCK_COVER',id:'synthetic-filing',url:'https://www.sec.gov/Archives/example.xml',sha256:id,received_at:'2026-11-06T09:00:00Z'}]},
  dataset:{sessions:21,expected_sessions:21,price_currency:'USD'},
  checks:[{code:'SESSION_COVERAGE',state:'PASS',label:'Cobertura del intervalo',detail:'21 de 21 sesiones.'},{code:'MINIMUM_HISTORY',state:'BLOCKED',label:'Longitud para tendencia diaria',detail:'Mínimo preliminar 252 sesiones.'}],
};}

it('keeps observed coverage separate from backtest acceptance and exposes evidence on demand',()=>{
  const data=value();expect(validAssessment(data)).toBe(true);
  const html=renderToStaticMarkup(<DatasetAssessment value={data} listingId={id} onChoose={()=>{}}/>);
  expect(html).toContain('21 de 21 en el intervalo');expect(html).toContain('No apto para backtest');
  expect(html).toContain('Exploración descriptiva');expect(html).toContain('Mínimo preliminar 252');
  expect(html).toContain('<details');expect(html).not.toContain('<details open');
  expect(html).toContain('Divisa nativa: sin verificar');expect(html).toContain('Vínculo conocido desde');
  expect(html).not.toContain('Abrir acción vinculada');
});

function withContract(){
  const data=value();
  data.identity.native_currency='USD';data.identity.native_currency_state='DOCUMENTED_OBSERVATION';
  data.identity.current_contract={source:'IBKR_TWS',con_id:123,symbol:'TEST',currency:'USD',primary_exchange:'NASDAQ',routing_exchange:'SMART',
    observed_at:'2026-11-08T08:00:00Z',known_from:'2026-11-08T08:30:00Z',report_sha256:id,
    documentation_url:'https://www.interactivebrokers.com/docs/tws-api/doc/contracts/object',scope:'OBSERVED_CONTRACT_ONLY',historical_identity:false};
  return data;
}

it('shows dated contract provenance without promoting history or opening the details',()=>{
  const data=withContract();expect(validAssessment(data)).toBe(true);
  const html=renderToStaticMarkup(<DatasetAssessment value={data} listingId={id} onChoose={()=>{}}/>);
  expect(html).toContain('Contrato observado · IBKR');expect(html).toContain('TEST · USD · NASDAQ');
  expect(html).toContain('Contrato 123');expect(html).toContain('Captación iniciada');
  expect(html).toContain('No apto para backtest');expect(html).not.toContain('<details open');
  expect(html).not.toContain('Divisa nativa: sin verificar');
});

it('rejects incomplete, future, contradictory or unsafe contract evidence',()=>{
  const data=withContract();data.identity.current_contract!.known_from='2027-01-01T00:00:00Z';expect(validAssessment(data)).toBe(false);
  const badLink=withContract();badLink.identity.current_contract!.documentation_url='javascript:alert(1)';expect(validAssessment(badLink)).toBe(false);
  const missing=withContract();missing.identity.current_contract=null;expect(validAssessment(missing)).toBe(false);
  const currency=withContract();currency.identity.native_currency='EUR';expect(validAssessment(currency)).toBe(false);
  const unresolved=withContract();unresolved.identity.state='REVIEW_REQUIRED';expect(validAssessment(unresolved)).toBe(false);
});

it('offers an explicit link from the issuer while preserving missing-history state',()=>{
  const data=value();data.dataset=null;data.research_state='INSUFFICIENT_DATA';
  const html=renderToStaticMarkup(<DatasetAssessment value={data} listingId="issuer" onChoose={()=>{}}/>);
  expect(html).toContain('Abrir acción vinculada');expect(html).toContain('Sin histórico');expect(html).toContain('Datos insuficientes');
  expect(html).not.toContain('Exploración descriptiva');
});

it('does not certify an unresolved identity',()=>{
  const data=value();data.identity={...data.identity,state:'REVIEW_REQUIRED',reason:'Evidencia alterada.',cik:null,market_listing_id:null,known_from:null,security_title:null,evidence:[]};
  const html=renderToStaticMarkup(<DatasetAssessment value={data} listingId={id} onChoose={()=>{}}/>);
  expect(html).toContain('Requiere revisión');expect(html).toContain('Evidencia alterada.');
  expect(html).not.toContain('Vínculo documentado');expect(html).not.toContain('Abrir acción vinculada');
});

it('rejects unsafe evidence links, future evidence and inconsistent acceptance from the API',()=>{
  const data=value();data.identity.evidence[0].url='javascript:alert(1)';expect(validAssessment(data)).toBe(false);
  data.identity.evidence[0].url='https://attacker.example/proof';expect(validAssessment(data)).toBe(false);
  data.identity.evidence[0].url='https://www.sec.gov/Archives/example.xml';data.identity.evidence[0].received_at='2027-01-01T00:00:00Z';expect(validAssessment(data)).toBe(false);
  const noProof=value();noProof.identity.evidence=[];expect(validAssessment(noProof)).toBe(false);
  expect(validAssessment({...value(),backtest_state:'READY'})).toBe(false);
});
