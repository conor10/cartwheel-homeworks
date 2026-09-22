"""One exploratory GPT-5.5 comparison; never changes the required HW5 judge."""
import argparse
import fcntl
import hashlib
import json
import os
from datetime import datetime, timezone

from analysis.helpers import _state, scale
from analysis.run_judges import ROOT, MODE, frozen_test_selection, latest_labels
from analysis.run_jev import metrics

MODEL = 'gpt-5.5-2026-04-23'


def run(*, approved=False, classify=None):
    if not approved:
        raise ValueError('Explicit approval required for GPT-5.5 on 33 test traces')
    selection = frozen_test_selection()
    judge = _state.read_json(_state.state_path('judges', selection['gpt']['judge_id']+'.json'))
    prompt = judge['prompt_text']
    if hashlib.sha256(prompt.encode()).hexdigest() != selection['gpt']['prompt_sha256']:
        raise ValueError('Frozen prompt changed')
    ids = _state.read_json(_state.state_path('splits.json'))[MODE]['test']
    if len(ids) != 33:
        raise ValueError('Approved trace count changed')
    identity = {'model':MODEL, 'prompt_sha256':selection['gpt']['prompt_sha256'],
                'locked_files':selection['locked_files'], 'trace_ids':ids, 'split':'test'}
    fingerprint = hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    directory = _state.state_path('comparisons'); directory.mkdir(exist_ok=True)
    path = directory/'gpt55-frozen-v2-test.json'
    from observability.instrument import load_env
    load_env()
    os.environ['CARTWHEEL_JUDGE_TRACE_SOURCE'] = str(_state.state_path('hw5_trace_inputs.json').resolve())
    with (directory/'gpt55.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        record = _state.read_json(path, {'fingerprint':fingerprint, **identity,
            'prompt_text':prompt, 'created_at':datetime.now(timezone.utc).isoformat(),
            'purpose':'Exploratory comparison chosen after seeing original held-out results; no prompt tuning',
            'predictions':{}})
        if record['fingerprint'] != fingerprint:
            raise ValueError('Comparison identity changed')
        pending = [tid for tid in ids if tid not in record['predictions']]
        for start in range(0,len(pending),10):
            batch = pending[start:start+10]
            fresh = (classify or scale.classify_store)(prompt, MODEL, batch)
            if set(fresh)!=set(batch) or any(type(v) is not int or v not in (0,1) for v in fresh.values()):
                raise ValueError('Incomplete or invalid predictions')
            critiques = getattr(fresh,'critiques',{})
            for tid,value in fresh.items():
                record['predictions'][tid]={'label':value,'critique':critiques.get(tid)}
            _state.write_json(path,record)
        report = {**metrics(record['predictions'],ids,latest_labels()), 'model':MODEL,
                  'split':'test','fingerprint':fingerprint,'purpose':record['purpose'],
                  'run_file':str(path)}
        _state.write_json(ROOT/'analysis/report/test-gpt55-frozen-v2.json',report)
        return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approve-paid-run',action='store_true')
    args=parser.parse_args()
    print(json.dumps(run(approved=args.approve_paid_run),indent=2))
