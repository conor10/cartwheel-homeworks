import json

import pytest

from analysis import run_jev as jev


def answer(choice='Pass'):
    return {'model':'jev-1.13.0','answers':{'response_relevance':{
        'type':'choice','choice':choice,'probabilities':{'Pass':.8 if choice=='Pass' else .2,'Fail':.2 if choice=='Pass' else .8},'confidence':.6}},'usage':{'input_tokens':100,'output_tokens':10}}


def test_jev_decoder_and_pass_positive_metrics():
    assert jev.decode(answer(),'jev-1.13.0')['label']==1
    assert jev.decode(answer('Fail'),'jev-1.13.0')['critique'] is None
    for data in ({}, {**answer(),'model':'different'}, {**answer(),'answers':{}}):
        with pytest.raises(ValueError):jev.decode(data,'jev-1.13.0')
    bad=answer();bad['answers']['response_relevance']['probabilities']['Pass']=float('nan')
    with pytest.raises(ValueError):jev.decode(bad,'jev-1.13.0')
    result=jev.metrics({'a':{'label':1},'b':{'label':0},'c':{'label':1},'d':{'label':0}},list('abcd'),{'a':{'label':1},'b':{'label':1},'c':{'label':0},'d':{'label':0}})
    assert all(result[k]==1 for k in ('tp','tn','fp','fn'))
    assert result['tpr']==result['tnr']==.5
    assert result['tpr_interval']==[.0945,.9055]


def test_jev_approval_gate_and_resume_after_interruption(tmp_path,monkeypatch):
    monkeypatch.setenv('CARTWHEEL_ANALYSIS_STATE',str(tmp_path))
    monkeypatch.setattr(jev,'ROOT',tmp_path)
    monkeypatch.setattr('observability.instrument.load_env',lambda:None)
    with pytest.raises(ValueError,match='approval'):
        jev.run_development()
    identity={'trace_ids':['a','b'],'split':'dev','model':'jev-1.13.0','inputs_sha256':'hash','questions':{}}
    config={'model':'jev-1.13.0','questions':{'response_relevance':{'type':'choice'}}}
    monkeypatch.setattr(jev,'context',lambda *args:(config,{'a':[{'role':'user','text':'a'}],'b':[{'role':'user','text':'b'}]},identity,'1234567890abcdef'))
    monkeypatch.setattr(jev,'latest_labels',lambda:{'a':{'label':1},'b':{'label':0}})
    calls=[]
    def interrupted(payload):
        calls.append(payload['state'][0]['text'])
        if len(calls)==2:raise RuntimeError('connection interrupted')
        return answer()
    with pytest.raises(RuntimeError):jev.run_development(approved=True,transport=interrupted)
    def resume(payload):
        calls.append(payload['state'][0]['text']);return answer('Fail')
    result=jev.run_development(approved=True,transport=resume)
    assert calls==['a','b','b']
    assert result['tp']==result['tn']==1
    assert result['usage']['input_tokens']==200
    result=jev.run_development(approved=True,transport=lambda p:pytest.fail('Cache should prevent another call'))
    assert result['n']==2
    saved=json.loads((tmp_path/'comparisons/jev-1234567890abcdef.json').read_text())
    assert saved['predictions']['a']['probabilities']=={'Pass':.8,'Fail':.2}


def test_jev_test_context_requires_frozen_config_and_separates_cache(tmp_path, monkeypatch):
    from analysis import run_judges as runner
    monkeypatch.setenv('CARTWHEEL_ANALYSIS_STATE',str(tmp_path))
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    config=tmp_path/'config.json'
    config.write_text(json.dumps({'model':'jev-1.13.0','questions':{},'training_example_ids':['train']}))
    with pytest.raises(ValueError,match='approval'):
        jev.run_test(config)
    with pytest.raises(ValueError,match='freeze'):
        jev.context(config,'test')
    inputs=tmp_path/'hw5_trace_inputs.json'
    inputs.write_text(json.dumps([{'trace_id':i,'trace':[]} for i in ('train','dev','test')]))
    data=json.loads(config.read_text());data['inputs_sha256']=runner.digest(inputs);config.write_text(json.dumps(data))
    (tmp_path/'hw5_input_manifest.json').write_text(json.dumps({'inputs_sha256':runner.digest(inputs)}))
    (tmp_path/'splits.json').write_text(json.dumps({runner.MODE:{'train':['train'],'dev':['dev'],'test':['test']}}))
    (tmp_path/'hw5_final_selection.json').write_text(json.dumps({'status':'frozen','locked_files':{},'jev':{'config_sha256':runner.digest(config)}}))
    test=jev.context(config,'test');dev=jev.context(config,'dev')
    assert test[2]['trace_ids']==['test'] and dev[2]['trace_ids']==['dev']
    assert test[3]!=dev[3]
    config.write_text('{}')
    with pytest.raises(ValueError,match='frozen Jev'):
        jev.context(config,'test')
