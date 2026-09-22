"""Optional HW5 Jev comparison with frozen, approval-gated held-out testing."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from analysis.helpers import _state
from analysis.helpers.tools import _wilson_interval
from analysis.run_judges import MODE, ROOT, digest, latest_labels

CONFIG = ROOT / 'analysis/prompts/irrelevant_response_detail-jev-v0.json'
ENDPOINT = 'https://api.typesafe.ai/v1/systemone'


def context(config_path=CONFIG, split="dev"):
    if split not in ("dev", "test"):
        raise ValueError("Invalid split")
    if split == "test":
        from analysis.run_judges import frozen_test_selection
        selection = frozen_test_selection()
        if digest(Path(config_path)) != selection["jev"]["config_sha256"]:
            raise ValueError("Use the frozen Jev configuration")
    config = json.loads(Path(config_path).read_text())
    path = _state.state_path('hw5_trace_inputs.json')
    manifest = _state.read_json(_state.state_path('hw5_input_manifest.json'))
    if digest(path) != manifest['inputs_sha256'] or digest(path) != config['inputs_sha256']:
        raise ValueError('Saved inputs changed; refusing to evaluate different evidence')
    splits = _state.read_json(_state.state_path('splits.json'))[MODE]
    example_ids = config['training_example_ids']
    if not set(example_ids) <= set(splits['train']) or set(example_ids) & set(splits['dev']+splits['test']):
        raise ValueError('Examples must come only from training')
    index = {r['trace_id']:r['trace'] for r in json.loads(path.read_text())}
    ids = splits[split]
    if len(ids) != len(set(ids)) or not ids or not set(ids) <= index.keys():
        raise ValueError('Invalid development inputs')
    identity = {'model':config['model'], 'questions':config['questions'],
                'inputs_sha256':digest(path), 'trace_ids':ids, 'split':split}
    fingerprint = hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    return config, index, identity, fingerprint


def request_jev(payload):
    key = os.environ.get('TYPESAFE_API_KEY')
    if not key:
        raise ValueError('Set TYPESAFE_API_KEY locally before running')
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
        headers={'Authorization':'Bearer '+key, 'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'TypeSafe HTTP {exc.code}; response not counted as a verdict') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('TypeSafe request interrupted; no verdict saved for this trace. Resume explicitly; the interrupted request may have been billed.') from None


def decode(response, model):
    if response.get('model') != model:
        raise ValueError('Unexpected Jev model version; refusing to mix versions')
    answer = response.get('answers',{}).get('response_relevance',{})
    probs = answer.get('probabilities',{})
    valid_number = lambda v: type(v) in (float,int) and math.isfinite(v) and 0<=v<=1
    if (answer.get('type') != 'choice' or answer.get('choice') not in ('Pass','Fail')
        or set(probs) != {'Pass','Fail'} or not all(valid_number(v) for v in probs.values())
        or not math.isclose(sum(probs.values()),1,abs_tol=1e-5)
        or not valid_number(answer.get('confidence'))):
        raise ValueError('Invalid Jev verdict/probabilities; not a human or model failure label')
    if probs[answer['choice']] < max(probs.values()):
        raise ValueError('Jev choice disagrees with returned probabilities')
    return {'result':answer['choice'],'label':int(answer['choice']=='Pass'),
            'probabilities':probs,'confidence':answer['confidence'], 'model':response['model'],
            'usage':response.get('usage',{}), 'critique':None}


def metrics(predictions, ids, labels):
    counts = dict(tp=0,fn=0,tn=0,fp=0)
    disagreements=[]
    for tid in ids:
        human, pred = labels[tid]['label'],predictions[tid]['label']
        counts[{(1,1):'tp',(1,0):'fn',(0,0):'tn',(0,1):'fp'}[human,pred]]+=1
        if human!=pred:disagreements.append(tid)
    p=counts['tp']+counts['fn'];n=counts['tn']+counts['fp']
    return {**counts,'n':len(ids),'pass_count':p,'fail_count':n,
        'tpr':counts['tp']/p if p else None, 'tnr':counts['tn']/n if n else None,
        'tpr_interval':_wilson_interval(counts['tp'],p),
        'tnr_interval':_wilson_interval(counts['tn'],n), 'disagreements':disagreements,
        'label_convention':'Pass=1 / Fail=0', 'interval_method':'95% Wilson'}


def run_development(config_path=CONFIG, *, approved=False, transport=None):
    return _run(config_path, approved=approved, transport=transport, split="dev")


def run_test(config_path, *, approved=False, transport=None):
    return _run(config_path, approved=approved, transport=transport, split="test")


def _run(config_path, *, approved=False, transport=None, split):
    if not approved:
        raise ValueError('Explicit approval required for Jev model and trace count')
    from observability.instrument import load_env
    load_env()
    config,index,identity,fingerprint=context(config_path, split)
    ids=identity['trace_ids'];labels=latest_labels()
    if not set(ids)<=labels.keys():raise ValueError('Missing human labels')
    directory=_state.state_path('comparisons');directory.mkdir(exist_ok=True)
    path=directory/f'jev-{fingerprint[:16]}.json'
    # Prevent simultaneous invocations from billing the same uncached traces.
    with (directory/'jev.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        record=_state.read_json(path,{'fingerprint':fingerprint,**identity,'predictions':{}})
        if record['fingerprint']!=fingerprint:raise ValueError('Cache identity mismatch')
        for tid in ids:
            if tid in record['predictions']:continue
            payload={'state':index[tid],'model':config['model'],'questions':config['questions']}
            start=time.perf_counter()
            response=(transport or request_jev)(payload)
            result=decode(response,config['model'])
            record['predictions'][tid]={**result,'latency_seconds':time.perf_counter()-start}
            _state.write_json(path,record)
        report={**metrics(record['predictions'],ids,labels),'model':config['model'],
                'run_file':str(path),'fingerprint':fingerprint,'split':split,
                'written_critique_available':False,
                'latency_seconds':sum(r['latency_seconds'] for r in record['predictions'].values()),
                'usage':{k:sum(r['usage'].get(k,0) for r in record['predictions'].values()) for k in ('input_tokens','output_tokens')}}
        _state.write_json(ROOT/'analysis/report'/f'{split}-jev-{fingerprint[:16]}.json',report)
        return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['plan','dev','test'])
    parser.add_argument('--split', choices=['dev','test'], default='dev')
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--approve-paid-run',action='store_true')
    args=parser.parse_args()
    if args.action=='plan':
        config,_,identity,fp=context(args.config,args.split)
        print(json.dumps({'model':config['model'],'trace_count':len(identity['trace_ids']),
                          'split':args.split,'fingerprint':fp,'paid_calls':0},indent=2))
    elif args.action=='test':
        print(json.dumps(run_test(args.config,approved=args.approve_paid_run),indent=2))
    else:
        print(json.dumps(run_development(args.config,approved=args.approve_paid_run),indent=2))


if __name__=='__main__':main()
