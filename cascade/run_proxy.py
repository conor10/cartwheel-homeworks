"""HW9 development-only proxy experiment; no test-set execution or oracle calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'cascade/results'
CONFIG = ROOT / 'analysis/prompts/irrelevant_response_detail-jev-v1.json'
MODEL = 'Prism-ML/Ternary-Bonsai-27B'
ENDPOINT = 'https://api.together.ai/v1/chat/completions'
EXTRA = ('Return a JSON object with result (Pass or Fail), critique, and confidence. '
         'State confidence in your chosen verdict as a number from 0 to 1.')


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def context():
    frozen = read(ROOT / 'analysis/state/hw5_final_selection.json')
    for name, expected in frozen['locked_files'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen HW5 input changed: {name}')
    config = read(CONFIG)
    splits = read(ROOT / 'analysis/state/splits.json')['irrelevant_response_detail']
    ids = splits['dev']
    if len(ids) != 33 or len(set(ids)) != 33 or set(ids) & set(splits['test']):
        raise ValueError('Invalid development split')
    if not set(config['training_example_ids']) <= set(splits['train']):
        raise ValueError('Prompt examples must be training-only')
    matches = []
    for path in (ROOT / 'analysis/state/comparisons').glob('jev-*.json'):
        record = read(path)
        if (record.get('split') == 'dev' and record.get('model') == config['model']
                and record.get('questions') == config['questions']
                and record.get('trace_ids') == ids
                and record.get('inputs_sha256') == config['inputs_sha256']):
            matches.append((path, record))
    if len(matches) != 1:
        raise ValueError('Expected exactly one matching frozen Jev development run')
    oracle_path, oracle = matches[0]
    if set(oracle['predictions']) != set(ids):
        raise ValueError('Incomplete oracle decisions')
    inputs = {r['trace_id']: r['trace'] for r in read(ROOT / 'analysis/state/hw5_trace_inputs.json')}
    labels = {}
    for line in (ROOT / 'analysis/state/hw5_labels/irrelevant_response_detail.jsonl').read_text().splitlines():
        item = json.loads(line)
        labels[item['trace_id']] = item['label']
    question = config['questions']['response_relevance']
    # Preserve every rubric/example/question/criterion string; only adapt the API envelope.
    system = (question['instructions']['rubric_and_training_examples'] + '\n\n'
              + question['instructions']['question'] + '\n\nCriteria:\n'
              + json.dumps(question['criteria'], ensure_ascii=False) + '\n\n' + EXTRA)
    return config, ids, inputs, labels, oracle_path, oracle, system


def prepare():
    config, ids, _, _, oracle_path, _, system = context()
    plan = {
        'model': MODEL, 'oracle_model': config['model'], 'split': 'dev',
        'minimum_agreement': 0.95, 'student_approval': 'lets do it: Bonsai and 95% minimum agreement',
        'approved_calls': {'smoke': 1, 'development_proxy': 33, 'new_oracle': 0, 'customer_agent': 0},
        'prices_per_million_usd': {'proxy_input': 0, 'proxy_output': 0, 'oracle_input': 0.042, 'oracle_output': 0},
        'price_date': '2026-10-05',
        'price_sources': ['https://www.together.ai/models/prism-ml-ternary-bonsai-27b', 'https://docs.typesafe.ai/models'],
        'pricing_limitation': 'Savings depend on the published free Bonsai price continuing; exclude infrastructure costs.',
        'oracle_path': str(oracle_path.relative_to(ROOT)), 'oracle_sha256': digest(oracle_path),
        'config_sha256': digest(CONFIG), 'inputs_sha256': config['inputs_sha256'],
        'system_prompt_sha256': hashlib.sha256(system.encode()).hexdigest(),
        'trace_ids': ids, 'temperature': 0, 'max_tokens': 4096,
        'confidence': 'Self-reported probability of chosen verdict; not assumed calibrated.',
        'invalid_output': 'Always fall back to saved oracle; never treat missing verdict as Pass or Fail.',
        'threshold_status': 'Awaiting student selection after development results',
        'test_status': 'Not run; requires separate approval after threshold selection',
    }
    path = RESULTS / 'plan.json'
    if path.exists() and read(path) != plan:
        raise ValueError('Existing plan differs; do not overwrite an experiment')
    save(path, plan)
    (RESULTS / 'proxy-system-prompt.txt').write_text(system + '\n')
    return plan


def decode(response):
    if response.get('model') != MODEL:
        raise ValueError('Unexpected proxy model')
    choice = response['choices'][0]
    if choice.get('finish_reason') != 'stop':
        raise ValueError('Incomplete output')
    value = json.loads(choice['message']['content'])
    confidence = value.get('confidence')
    if (value.get('result') not in ('Pass', 'Fail') or type(confidence) not in (float, int)
            or not math.isfinite(confidence) or not 0 <= confidence <= 1
            or not isinstance(value.get('critique'), str)):
        raise ValueError('Invalid verdict schema')
    return {k: value[k] for k in ('result', 'confidence', 'critique')}


def request(trace, system, plan):
    payload = {'model': MODEL, 'messages': [{'role': 'system', 'content': system},
               {'role': 'user', 'content': json.dumps({'state': trace}, ensure_ascii=False)}],
               'temperature': plan['temperature'], 'max_tokens': plan['max_tokens'],
               'response_format': {'type': 'json_object'}}
    key = os.environ.get('TOGETHER_API_KEY')
    if not key:
        raise ValueError('Set TOGETHER_API_KEY in .env')
    start = time.monotonic()
    try:
        response = httpx.post(ENDPOINT, json=payload,
            headers={'Authorization': 'Bearer ' + key}, timeout=120)
        response.raise_for_status()
        raw = response.json()
    except httpx.HTTPStatusError as exc:
        return {'status': 'transport_error', 'http_status': exc.response.status_code, 'latency_seconds': time.monotonic()-start}
    except httpx.RequestError:
        return {'status': 'transport_error', 'error': 'Connection failed or timed out', 'latency_seconds': time.monotonic()-start}
    record = {'raw_response': raw, 'usage': raw.get('usage', {}), 'latency_seconds': time.monotonic()-start}
    try:
        record.update(decode(raw))
        record['status'] = 'valid'
    except (ValueError, KeyError, IndexError, TypeError):
        record['status'] = 'invalid_output'
    return record


def run(stage):
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
    plan = prepare()
    config, ids, inputs, _, _, _, system = context()
    if stage == 'smoke':
        ids = [config['training_example_ids'][0]]
    elif not (RESULTS / 'smoke.json').exists() or read(RESULTS / 'smoke.json')['status'] != 'valid':
        raise ValueError('A valid smoke response is required first')
    for i, tid in enumerate(ids, 1):
        path = RESULTS / ('smoke.json' if stage == 'smoke' else f'dev-{tid}.json')
        if path.exists():
            if read(path).get('status') == 'transport_error':
                raise ValueError('Previous transport error: investigate before explicitly retrying')
            continue
        result = request(inputs[tid], system, plan)
        result.update(trace_id=tid, requested_model=MODEL, system_prompt_sha256=plan['system_prompt_sha256'])
        save(path, result)
        print(f'{stage} {i}/{len(ids)}: {result["status"]}', flush=True)
        if result['status'] == 'transport_error':
            raise RuntimeError(f'Provider request failed (HTTP {result.get("http_status", "unknown")}); no automatic retry')


def summarize():
    plan = prepare()
    _, ids, _, labels, _, oracle, _ = context()
    proxies = {tid: read(RESULTS / f'dev-{tid}.json') for tid in ids}
    if any(p.get('system_prompt_sha256') != plan['system_prompt_sha256'] or p.get('trace_id') != tid
           for tid, p in proxies.items()):
        raise ValueError('Proxy record belongs to a different experiment')
    if any(p['status'] == 'transport_error' for p in proxies.values()):
        raise ValueError('Incomplete development run')
    # Distinct routing configurations, including conventional 0.05 increments and exact boundaries.
    thresholds = sorted({i/20 for i in range(21)} | {
        math.nextafter(p['confidence'], math.inf) for p in proxies.values()
        if p['status'] == 'valid' and p['confidence'] < 1})
    rows = []
    for threshold in thresholds:
        same_oracle = same_human = accepted = 0
        cost = 0.0
        for tid in ids:
            p, o = proxies[tid], oracle['predictions'][tid]
            use_proxy = p['status'] == 'valid' and p['confidence'] >= threshold
            verdict = p['result'] if use_proxy else o['result']
            accepted += use_proxy
            same_oracle += verdict == o['result']
            same_human += int(verdict == 'Pass') == labels[tid]
            if not use_proxy:
                cost += o['usage']['input_tokens'] * plan['prices_per_million_usd']['oracle_input'] / 1e6
        rows.append(dict(threshold=threshold, agreement_with_oracle=same_oracle/len(ids),
                         agreement_with_human_labels=same_human/len(ids), proxy_share=accepted/len(ids),
                         cost_per_1000_verdicts_usd=cost/len(ids)*1000))
    with (RESULTS / 'thresholds.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    eligible = [r for r in rows if r['agreement_with_oracle'] >= plan['minimum_agreement']]
    summary = {'n': len(ids), 'minimum_agreement': plan['minimum_agreement'],
               'lowest_qualifying_threshold': eligible[0] if eligible else None,
               'oracle_agreement_with_humans': sum(oracle['predictions'][t]['label'] == labels[t] for t in ids)/len(ids),
               'oracle_cost_per_1000_verdicts_usd': sum(oracle['predictions'][t]['usage']['input_tokens'] for t in ids)*0.042/1e6/len(ids)*1000,
               'invalid_proxy_outputs': sum(p['status'] != 'valid' for p in proxies.values()),
               'cost_method': 'Projected deployment cost: proxy on every review, Jev only on fallbacks. Saved oracle verdicts reused, no live Jev spend.',
               'actual_proxy_model_cost_usd_at_published_price': 0,
               'best_agreement_with_oracle': max(r['agreement_with_oracle'] for r in rows),
               'confidence_one_count': sum(p['status'] == 'valid' and p['confidence'] == 1 for p in proxies.values()),
               'confidence_one_disagreements': sum(p['status'] == 'valid' and p['confidence'] == 1 and p['result'] != oracle['predictions'][tid]['result'] for tid, p in proxies.items()),
               'status': ('Awaiting student threshold selection; test not run' if eligible else 'No threshold in [0,1] meets the requirement; awaiting student cascade decision; test not run')}
    decision_path = RESULTS / 'decision.json'
    if decision_path.exists():
        summary['student_decision'] = read(decision_path)['decision']
        summary['status'] = 'Rejected by student during development; no threshold selected; test not run'
    save(RESULTS / 'development-summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'smoke', 'dev', 'summarize'])
    parser.add_argument('--approved', action='store_true')
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.action == 'prepare':
        prepare()
    elif args.action == 'summarize':
        summarize()
    else:
        if not args.approved:
            parser.error('Live calls require --approved after explicit approval')
        run(args.action)
