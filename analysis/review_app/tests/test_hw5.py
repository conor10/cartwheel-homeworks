import json

import pytest

from analysis.review_app.hw5 import HW5Review
from analysis.review_app.state import Conflict


def test_hw5_labels_preserve_hw4_and_edit_history(tmp_path):
    mode = 'irrelevant_response_detail'
    hw4 = tmp_path / 'review_workspace.json'
    hw4.write_text('{"reviews":{"original":"preserve"}}')
    (tmp_path / 'hw5_review.json').write_text(json.dumps({
        'mode':mode, 'mode_version':3,
        'rows':[{'trace_id':'a', 'session_id':'s1'}, {'trace_id':'b', 'session_id':'s2'}]}))
    directory = tmp_path / 'hw5_labels'
    directory.mkdir()
    path = directory / (mode+'.jsonl')
    path.write_text(json.dumps({'trace_id':'a','label':0,'source':'reused_hw4_human_label'})+'\n')
    review = HW5Review(tmp_path)
    assert review.snapshot()['counts'] == {'Pass':0, 'Fail':1, 'pending':1}
    payload = {'trace_id':'b','label':1,'note':'Only requested details','revision':1}
    assert review.save(payload)['counts'] == {'Pass':1,'Fail':1,'pending':0}
    with pytest.raises(Conflict):
        review.save(payload)
    review.save({**payload,'label':0,'note':'Unrelated policy paragraph','revision':2})
    assert HW5Review(tmp_path).snapshot()['counts'] == {'Pass':0,'Fail':2,'pending':0}
    assert len(path.read_text().splitlines()) == 3
    assert hw4.read_text() == '{"reviews":{"original":"preserve"}}'
    for changes in ({'label':True},{'label':2},{'note':'  '},{'trace_id':'unknown'}):
        with pytest.raises(ValueError):
            review.save({**payload,'revision':3,**changes})
    assert len(path.read_text().splitlines()) == 3


def test_development_view_excludes_test_predictions(tmp_path):
    mode='irrelevant_response_detail'
    (tmp_path/'hw5_review.json').write_text(json.dumps({'mode':mode,'mode_version':3,'rows':[{'trace_id':'dev'},{'trace_id':'test'}]}))
    (tmp_path/'hw5_labels').mkdir()
    (tmp_path/'hw5_labels'/f'{mode}.jsonl').write_text('\n'.join(json.dumps({'trace_id':t,'label':0}) for t in ('dev','test')))
    (tmp_path/'splits.json').write_text(json.dumps({mode:{'dev':['dev'],'test':['test']}}))
    (tmp_path/'judges').mkdir()
    rid=mode+'-v0'
    (tmp_path/'judges'/f'{rid}.json').write_text(json.dumps({'judge_id':rid,'model':'gpt-4o-mini','prompt_hash':'hash','label_convention':'pass_positive','predictions':{'hash':{'dev':1,'test':1}},'critiques':{'hash':{'dev':'Explanation','test':'Do not expose'}}}))
    review=HW5Review(tmp_path)
    assert set(review.snapshot()['development'][0]['predictions'])=={'dev'}
    result=review.save_disagreement({'run_id':rid,'trace_id':'dev','decision':'judge_wrong','reason':'Unrelated detail'})
    assert result['development'][0]['predictions']['dev']['review']['decision']=='judge_wrong'
    assert result['labels']['dev']['label']==0
    with pytest.raises(ValueError):review.save_disagreement({'run_id':rid,'trace_id':'test','decision':'judge_wrong','reason':'No'})
