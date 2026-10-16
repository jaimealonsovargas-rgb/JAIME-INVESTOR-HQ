import {it,expect} from 'vitest';
import {decimalText,validatePortfolio,validateLedger,validateMarkets} from './portfolioApi';
const fixture=()=>({portfolio_id:'MASTER',base_currency:'EUR',trading_mode:'PAPER_ONLY',orders_enabled:false,as_of:'2026-10-16T00:00:00Z',seeded_at:'2026-10-16T00:00:00Z',ledger_hash:'a'.repeat(64),ledger_status:'VERIFIED_APPEND_ONLY',valuation_status:'FRESH',nav_eur:'10000.00',cash_eur:'10000.00',market_value_eur:'0.00',liabilities_eur:'0.00',accruals_eur:'0.00',positions_count:0,events_count:1,invested_pct:'0',realized_pnl_eur:'0.00',unrealized_pnl_eur:'0.00',fx_effect_eur:'0.00',total_pnl_eur:'0.00',cumulative_return_pct:'0',income_eur:'0.00',fees_eur:'0.00',positions:[],performance:{daily_return_pct:null,twr_pct:null,mwr_xirr_pct:null,max_drawdown_pct:null}});
it('formats decimal strings without binary-money rounding or unsafe integers',()=>{
 expect(decimalText('10000.00')).toBe('10.000,00');
 expect(decimalText('9007199254740993.015')).toBe('9.007.199.254.740.993,02');
 expect(decimalText('1.005')).toBe('1,00');expect(decimalText('1.015')).toBe('1,02');
 expect(decimalText('-0.004')).toBe('0,00');expect(decimalText('-1.015')).toBe('−1,02');
 expect(decimalText('1e-7',8)).toBe('0,00000010');expect(decimalText('1.23e3')).toBe('1.230,00');
 expect(decimalText(null)).toBe('NO DISPONIBLE');
});
it('accepts verified cash-only MASTER but rejects money floats and live scope',()=>{
 expect(validatePortfolio(fixture()).positions).toEqual([]);
 for(const change of [{nav_eur:10000},{portfolio_id:'ALPACA_PAPER'},{orders_enabled:true},{valuation_status:'LIVE'},{ledger_hash:'TEST_ONLY'},{nav_eur:'NaN'}])expect(()=>validatePortfolio({...fixture(),...change})).toThrow();
});
it('missing quote remains null and ratios need an explicit nullable contract',()=>{
 expect(validatePortfolio({...fixture(),nav_eur:null,valuation_status:'NO_DATA'}).nav_eur).toBeNull();
 expect(()=>validatePortfolio({...fixture(),performance:{}})).toThrow();
 expect(()=>validatePortfolio({...fixture(),performance:{...fixture().performance,twr_pct:0}})).toThrow();
});
it('rejects malformed ledger money and missing market metadata',()=>{
 expect(()=>validateLedger({items:[{kind:'TEST_ONLY',occurred_at:'2026-10-16T00:00:00Z',amount:10000,entries:[]}],total:1,offset:0})).toThrow();
 expect(()=>validateMarkets({checked_at:'2026-10-16T00:00:00Z',items:[{symbol:'TEST_ONLY',value:'1',status:'FRESH'}],pulse:[],reason:'TEST_ONLY'})).toThrow();
});
