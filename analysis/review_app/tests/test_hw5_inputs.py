import json

import pytest

from analysis.run_judges import conversation_input, digest, split_data


def test_export_keeps_tool_evidence_and_prior_turns_without_review_metadata():
    def turn(tid, text):
        return {'id':tid, 'timestamp':tid, 'metadata':{'cartwheel.session_id':'s','secret_review':'LEAK'},
                'input':text,'output':'reply '+tid,'scores':[{'label':'LEAK'}],
                'observations':[{'id':'tool','type':'TOOL','startTime':tid,'name':'get_policy',
                    'input':{'policy_id':'cw-returns'},'output':{'body':'Policy evidence'},'metadata':{'review':'LEAK'}},
                    {'id':'gen','type':'GENERATION','input':'SYSTEM LEAK','output':'hidden narration'}]}
    earlier, target, later = turn('1','Earlier request'), turn('2','Current request'), turn('3','FUTURE')
    result = conversation_input(target, {'s':[later,target,earlier]})
    assert set(result) == {'trace_id','trace'}
    assert [m['role'] for m in result['trace']] == ['user','tool_call','tool_result','assistant']*2
    assert result['trace'][-1] == {'role':'assistant','text':'reply 2'}
    text=json.dumps(result)
    assert 'Policy evidence' in text
    assert all(s not in text for s in ('LEAK','FUTURE','hidden narration'))


def test_existing_split_is_reused_and_modified_inputs_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv('CARTWHEEL_ANALYSIS_STATE',str(tmp_path))
    mode='irrelevant_response_detail'
    inputs=tmp_path/'hw5_trace_inputs.json'
    inputs.write_text(json.dumps([{'trace_id':str(i),'trace':[{'role':'assistant','text':'reply'}]} for i in range(60)]))
    (tmp_path/'hw5_input_manifest.json').write_text(json.dumps({'inputs_sha256':digest(inputs)}))
    (tmp_path/'hw5_labels').mkdir()
    (tmp_path/'hw5_labels'/f'{mode}.jsonl').write_text(''.join(json.dumps({'trace_id':str(i),'label':i%2,'note':'Human evidence'})+'\n' for i in range(60)))
    splits=tmp_path/'splits.json'
    splits.write_text(json.dumps({'unrelated':{'preserve':True}}))
    result=split_data()
    original=splits.read_bytes()
    assert result['counts']=={'train':{'Pass':6,'Fail':6},'dev':{'Pass':12,'Fail':12},'test':{'Pass':12,'Fail':12}}
    assert split_data()==result
    assert splits.read_bytes()==original
    assert json.loads(original)['unrelated']=={'preserve':True}
    inputs.write_text('[]')
    with pytest.raises(ValueError,match='inputs changed'):
        split_data()
    assert splits.read_bytes()==original


def test_development_requires_approval_and_reuses_interrupted_judge(tmp_path, monkeypatch):
    import analysis.run_judges as runner
    mode=runner.MODE
    monkeypatch.setenv('CARTWHEEL_ANALYSIS_STATE',str(tmp_path))
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='explicit approval'):
        runner.run_development(mode,tmp_path/'missing-prompt')
    inputs=tmp_path/'hw5_trace_inputs.json'; inputs.write_text('[]')
    (tmp_path/'hw5_input_manifest.json').write_text(json.dumps({'inputs_sha256':digest(inputs)}))
    (tmp_path/'splits.json').write_text(json.dumps({mode:{'dev':['a']}}))
    (tmp_path/'judges').mkdir()
    prompt=tmp_path/'prompt.txt';prompt.write_text('Criterion')
    judge_id=mode+'-v0'
    (tmp_path/'judges'/f'{judge_id}.json').write_text(json.dumps({'judge_id':judge_id,'prompt_text':'Criterion','model':'gpt-4o-mini','status':'draft'}))
    def unexpected(**kwargs):
        raise AssertionError('Do not register again on resume')
    monkeypatch.setattr(runner,'register_judge',unexpected)
    calls=[]
    monkeypatch.setattr(runner,'run_judge',lambda *a,**kw:calls.append((a,kw)))
    monkeypatch.setattr(runner,'judge_alignment',lambda *a,**kw:{'n':1})
    monkeypatch.setattr('observability.instrument.load_env',lambda:None)
    result=runner.run_development(mode,prompt,approved=True)
    assert result['judge_id']==judge_id
    assert calls==[((judge_id,),{'split':'dev','batch_size':10})]
    assert json.loads((tmp_path/'analysis/report'/f'dev-{judge_id}.json').read_text())=={'n':1}


def test_test_runner_requires_approval_and_frozen_identity(tmp_path, monkeypatch):
    import analysis.run_judges as runner
    monkeypatch.setenv('CARTWHEEL_ANALYSIS_STATE', str(tmp_path))
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='explicit approval'):
        runner.run_test('selected')
    with pytest.raises(ValueError, match='freeze'):
        runner.run_test('selected', approved=True)
    inputs=tmp_path/'inputs.json'; inputs.write_text('[]')
    selection={'status':'frozen','locked_files':{'inputs.json':digest(inputs)},
               'gpt':{'judge_id':'selected','model':'gpt-4o-mini','prompt_sha256':runner.hashlib.sha256(b'Criterion').hexdigest()}}
    (tmp_path/'hw5_final_selection.json').write_text(json.dumps(selection))
    (tmp_path/'judges').mkdir()
    (tmp_path/'judges/selected.json').write_text(json.dumps({'status':'frozen','model':'gpt-4o-mini','prompt_text':'Criterion'}))
    calls=[]
    monkeypatch.setattr(runner, 'run_judge', lambda *a,**kw:calls.append((a,kw)))
    monkeypatch.setattr(runner, 'judge_alignment', lambda *a,**kw:{'n':33})
    monkeypatch.setattr('observability.instrument.load_env', lambda:None)
    assert runner.run_test('selected', approved=True)=={'n':33}
    assert calls==[(('selected',),{'split':'test','batch_size':10})]
    with pytest.raises(ValueError, match='selected'):
        runner.run_test('other', approved=True)
    inputs.write_text('[1]')
    with pytest.raises(ValueError, match='changed'):
        runner.run_test('selected', approved=True)
    assert len(calls)==1
