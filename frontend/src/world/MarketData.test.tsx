import {afterEach,expect,it} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {InstrumentMarket,MarketConnection} from './MarketData';
import type {InstrumentMarketData,MarketSummary} from '../marketApi';

const clients:QueryClient[]=[];
afterEach(()=>{clients.forEach(client=>client.clear());clients.length=0;});
const stamp='2026-10-29T10:00:00Z';
function summary():MarketSummary{return {source:{state:'NO_CREDENTIALS',reason:'Faltan claves Alpaca locales.',feed:'iex',mode:'PAPER_READ_ONLY'},endpoints:[],counts:{assets:0,bar_sets:0,bars:0},jobs:[],paper:{state:'NOT_VERIFIED',as_of:null,account:null,positions:[]}};}
function instrument():InstrumentMarketData{return {listing_id:'listing',identity:{state:'PROVIDER_IDENTIFIED',reason:'Activo identificado en Alpaca.',asset_id:'uuid',symbol:'TEST',venue:'NASDAQ',currency:'USD',issuer_link:'UNCONFIRMED',candidates:[]},quote:{state:'STALE',as_of:'2026-10-28T19:00:00Z',received_at:stamp,feed:'iex',price:'100',bid:'99.90',ask:'100.10',reason:'La última operación no es reciente.',market_state:'CLOSED',market_checked_at:stamp},history:{series:[],manifest:null,sets:[]}};}
function render(data:MarketSummary,detail?:InstrumentMarketData){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});clients.push(client);client.setQueryData(['market-summary'],data);
  if(detail)client.setQueryData(['instrument-market','listing','raw'],detail);
  return renderToStaticMarkup(<QueryClientProvider client={client}>{detail?<InstrumentMarket listingId="listing" onChoose={()=>{}}/>:<MarketConnection/>}</QueryClientProvider>);
}

it('keeps capture disabled without local credentials and does not ask for keys in a form',()=>{
  const html=render(summary());
  expect(html).toMatch(/<button disabled="">Comprobar conexión<\/button>/);
  expect(html).toMatch(/<button disabled="">Actualizar catálogo Alpaca<\/button>/);
  expect(html).toContain('ALPACA_API_KEY');expect(html).not.toContain('<input');
  expect(html).toContain('separada de MASTER');expect(html).toContain('órdenes continúan deshabilitadas');
});

it('shows SEC candidates as review links without inheriting their quotes or confirming issuer identity',()=>{
  const data=instrument();data.identity.state='UNLINKED';data.identity.asset_id=null;data.identity.currency=null;
  data.identity.candidates=[{id:'candidate',name:'Example company',symbol:'TEST',venue:'NASDAQ',reason:'Coinciden símbolo y mercado; falta confirmar emisor.'}];
  const html=render(summary(),data);
  expect(html).toContain('Abrir una ficha no confirma que corresponda al mismo emisor');
  expect(html).toContain('Example company');expect(html).not.toContain('Última operación IEX');expect(html).not.toContain('100,00 USD');
});

it('distinguishes a stale quote from a closed market and shows both observation and receipt times',()=>{
  const source=summary();source.source.state='READY_TO_FETCH';
  const html=render(source,instrument());
  expect(html).toContain('Dato antiguo');expect(html).toContain('Cerrada');expect(html).toContain('100,00 USD');
  expect(html).toContain('Operación:');expect(html).toContain('Recepción local:');expect(html).toContain('Emisor SEC: sin confirmar');
  expect(html).toContain('Sin histórico sin ajustar');expect(html).not.toContain('<svg');
});

it('does not describe failed positions retrieval as a confirmed empty portfolio',()=>{
  const data=summary();data.paper={state:'PARTIAL',as_of:stamp,account:{currency:'USD',status:'ACTIVE',cash:'1000',equity:'1000',buying_power:'2000'},positions:[]};
  const html=render(data);
  expect(html).toContain('La lectura de posiciones aún no está confirmada');expect(html).not.toContain('no devolvió posiciones abiertas');
});
