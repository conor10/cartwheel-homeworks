import hashlib
import json

import pytest

from analysis import run_gpt_comparison as comparison


def test_comparison_preserves_identity_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setenv('CARTWHEEL_ANALYSIS_STATE',str(tmp_path))
    monkeypatch.setattr(comparison,'ROOT',tmp_path)
    monkeypatch.setattr('observability.instrument.load_env',lambda:None)
    with pytest.raises(ValueError,match='approval'):
        comparison.run()
    ids=[str(i) for i in range(33)]
    selection={'gpt':{'judge_id':'original','prompt_sha256':hashlib.sha256(b'frozen').hexdigest()},'locked_files':{}}
    monkeypatch.setattr(comparison,'frozen_test_selection',lambda:selection)
    (tmp_path/'judges').mkdir()
    (tmp_path/'judges/original.json').write_text(json.dumps({'prompt_text':'frozen'}))
    (tmp_path/'splits.json').write_text(json.dumps({comparison.MODE:{'test':ids}}))
    monkeypatch.setattr(comparison,'latest_labels',lambda:{i:{'label':int(i)%2} for i in ids})
    calls=[]
    def classify(prompt,model,batch):
        assert prompt=='frozen' and model==comparison.MODEL
        calls.append(batch)
        if len(calls)==2:raise RuntimeError('interrupted')
        return {i:int(i)%2 for i in batch}
    with pytest.raises(RuntimeError,match='interrupted'):
        comparison.run(approved=True,classify=classify)
    result=comparison.run(approved=True,classify=classify)
    assert calls==[ids[:10],ids[10:20],ids[10:20],ids[20:30],ids[30:]]
    assert result['n']==33 and result['tpr']==result['tnr']==1
    comparison.run(approved=True,classify=lambda *a:pytest.fail('Already cached'))
    selection['locked_files']={'changed':'hash'}
    with pytest.raises(ValueError,match='identity changed'):
        comparison.run(approved=True,classify=classify)
