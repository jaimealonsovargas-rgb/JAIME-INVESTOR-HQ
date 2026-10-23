from app.research_brief import computed_context


def test_comparisons_are_exact_scoped_and_cited():
    def row(name, value, usable=True):
        return {'id':name, 'scope':'DERIVED_FEATURE','usable':usable,'excerpt':name+': '+value,'value':value}
    pack={'records':[row('period_return','-0.00000000000000000001'), row('z_score','0.00000000000000000001'),
                     row('sample_volatility','0.01'), row('max_drawdown_observed','-0.02')]}
    context=computed_context(pack)
    assert len(context['findings'])==4
    assert 'negativo' in context['findings'][0]['finding']
    assert 'encima' in context['findings'][1]['finding']
    assert [f['id'] for f in context['findings']]==[r['id'] for r in pack['records']]
    from app.local_llm import model_view
    assert model_view(context)['findings'] == context['findings']
    assert not computed_context({'records':[row('period_return','NaN'),row('z_score','1',False)]})['findings']
