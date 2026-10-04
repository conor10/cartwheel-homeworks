"""Offline HW9 Part A audit. Default: rebuild CSV from the portable ledger.

--collect rebuilds the ledger from retained HW3/HW5 and local HW7 artifacts.
No model clients, credentials, or network calls are used.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'profile/results'
WRAPPER = ('\n\n--- Trace to evaluate ---\n{}\n\nFirst write a critique of the trace '
           'against the criterion. Use specific evidence from the provided trace. '
           'Then return result as exactly Pass when the named failure is absent, or Fail when present.')


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def estimate(text):
    # Deliberately simple, reproducible heuristic; not claimed as API usage.
    return math.ceil(len(text) / 4)


def site(path, text):
    lines = (ROOT / path).read_text().splitlines()
    return f'{path}:{next(i for i, s in enumerate(lines, 1) if text in s)}'


def collect():
    from analysis.helpers.normalization import normalize_trace
    records, seen = [], set()
    sources = {}

    def load(path):
        path = Path(path)
        sources[str(path)] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        return read(path)

    def add(category, call_site, model, identity, inp, out, basis, source, cost=None):
        key = (category, call_site, model, identity)
        if key in seen:
            return
        seen.add(key)
        assert inp >= 0 and out >= 0
        records.append(dict(cost_category=category, call_site=call_site, model=model,
                            identity=identity, input_tokens=inp, output_tokens=out,
                            basis=basis, source=str(source), recorded_cost_usd=cost))

    conversation_site = site('server/app.py', 'result = await Runner.run(')
    exported = load('traces/support_traces.json')
    for trace in exported['traces']:
        for obs in trace['observations']:
            if obs.get('type') != 'GENERATION' or not obs.get('model'):
                continue
            assert obs['promptTokens'] is not None and obs['completionTokens'] is not None
            assert obs['calculatedTotalCost'] is not None
            add('customer_conversation', conversation_site, obs['model'], obs['id'],
                obs['promptTokens'], obs['completionTokens'], 'recorded_api_usage_and_langfuse_cost',
                'traces/support_traces.json', obs['calculatedTotalCost'])

    inputs = {r['trace_id']: normalize_trace(r)['text']
              for r in load('analysis/state/hw5_trace_inputs.json')}
    judge_site = site('analysis/helpers/scale.py', '    pipeline.run()')
    output_samples = []
    for p in sorted((ROOT / 'analysis/state/judges').glob('irrelevant_response_detail-v*.json')):
        rel = p.relative_to(ROOT)
        judge = load(rel)
        prompt_hash = judge['prompt_hash']
        for tid, pred in judge['predictions'].get(prompt_hash, {}).items():
            critique = judge['critiques'][prompt_hash][tid]
            out = estimate(json.dumps({'critique': critique, 'result': 'Pass' if pred else 'Fail'}))
            output_samples.append(out)
            add('judge', judge_site, judge['model'], f'{prompt_hash}:{tid}',
                estimate(judge['prompt_text'] + WRAPPER.format(inputs[tid])), out,
                'estimated_chars_div_4_saved_prompt_input_critique', rel)

    p = 'analysis/state/comparisons/gpt55-frozen-v2-test.json'
    gpt = load(p)
    for tid, pred in gpt['predictions'].items():
        add('judge', judge_site, gpt['model'], gpt['fingerprint'] + ':' + tid,
            estimate(gpt['prompt_text'] + WRAPPER.format(inputs[tid])),
            estimate(json.dumps({'critique': pred['critique'], 'result': 'Pass' if pred['label'] else 'Fail'})),
            'estimated_chars_div_4_saved_prompt_input_critique', p)

    jev_site = site('analysis/run_jev.py', 'with urllib.request.urlopen(')
    for p in sorted((ROOT / 'analysis/state/comparisons').glob('jev-*.json')):
        rel = p.relative_to(ROOT)
        data = load(rel)
        for tid, pred in data['predictions'].items():
            usage = pred['usage']
            add('judge', jev_site, data['model'], data['fingerprint'] + ':' + tid,
                usage['input_tokens'], usage['output_tokens'], 'recorded_api_usage_repriced', rel)

    monitor_site = site('monitoring/run_judges.py', '        pipeline.run()')
    monitor_output = round(statistics.median(output_samples))
    paths = sorted((ROOT / '.harbor/hw7').rglob('verdicts.json'))
    assert paths, 'HW7 evidence missing; use the existing ledger instead of --collect.'
    for p in paths:
        rel = p.relative_to(ROOT)
        verdicts = load(rel)
        plan = load(rel.parent / 'plan.json')
        judge = load('analysis/state/judges/' + plan['judge_id'] + '.json')
        assert hashlib.sha256(judge['prompt_text'].encode()).hexdigest() == plan['prompt_sha256']
        completed = {**verdicts['random_verdicts'], **verdicts['risk_verdicts']}
        for rec in plan['to_judge']:
            if rec['id'] not in completed:
                continue
            identity = digest([plan['judge_id'], plan['prompt_sha256'], rec['id'], rec['text']])
            add('judge', monitor_site, plan['judge_model'], identity,
                estimate(judge['prompt_text'] + WRAPPER.format(rec['text'])), monitor_output,
                'estimated_chars_div_4_input_median_HW5_output', rel)

    records.sort(key=lambda r: (r['cost_category'], r['call_site'], r['model'], r['identity']))
    (OUT / 'call-records.jsonl').write_text(''.join(json.dumps(r, sort_keys=True) + '\n' for r in records))
    (OUT / 'audit-method.json').write_text(json.dumps({
        'source_sha256': sources,
        'scope': 'HW3 exported customer generations; retained HW5 real judge variants/comparisons; completed HW7 local monitoring verdicts.',
        'customer_attribution': 'Application call site server/app.py Runner.run; each SDK generation is one call, not one conversation.',
        'aggregation': 'costs.csv has one row per call site; costs-by-model.csv preserves model-specific breakdowns.',
        'judge_estimation': 'ceil(character count / 4) for reconstructed visible prompt and reply; no claim of exact tokenization. HW7 critiques absent, so use median estimated HW5 GPT-4o-mini output length.',
        'hw7_output_tokens_assumed_per_call': monitor_output,
        'deduplication': 'Customer observation ID; HW5 prompt/config identity plus trace ID; HW7 judge/model/prompt and exact evidence, including overlapping random/risk selections and copied exports.',
        'limitations': [
            'Retained evidence audit, not a complete provider invoice. Missing or overwritten retries/runs cannot be recovered.',
            'Judge estimates exclude unknown DocETL formatting, hidden reasoning, cache discounts, and retries; expensive GPT-5.5 judge output may be underestimated.',
            'HW7 plans without completed verdict records are excluded; workflow reports four new evaluations whose detailed verdict artifacts are not retained here.',
            'Starter unsupported_policy_claim store-XXXX predictions are demo/reference data and excluded from paid usage.',
            'HW8 evaluation costs are not mixed into the HW3/HW5/HW7 call-site audit.',
            'Customer costs use exported Langfuse calculated costs including cache discounts. Judge costs use reference list prices, not historical invoices.',
            'Default regeneration uses the portable token ledger. --collect needs ignored local HW7 artifacts, which are not copied into the repository.'
        ]
    }, indent=2) + '\n')


def aggregate():
    prices = read('profile/results/prices.json')
    rows = [json.loads(line) for line in (OUT / 'call-records.jsonl').read_text().splitlines()]
    groups = defaultdict(list)
    for row in rows:
        groups[(row['cost_category'], row['call_site'], row['model'])].append(row)
    table = []
    for (category, loc, model), calls in sorted(groups.items()):
        inp = sum(r['input_tokens'] for r in calls)
        out = sum(r['output_tokens'] for r in calls)
        if category == 'customer_conversation':
            cost = sum(r['recorded_cost_usd'] for r in calls)
            purpose = 'HW3 support agent; recorded API tokens and Langfuse costs including cached input'
        else:
            rate = prices['per_million_tokens_usd'][model]
            cost = (inp * rate['input'] + out * rate['output']) / 1e6
            purpose = ('HW7 monitoring; ESTIMATED input tokens; output estimated from HW5 median'
                       if loc.startswith('monitoring/') else
                       'HW5 Jev comparison; recorded API tokens, estimated list-price cost'
                       if model.startswith('jev') else
                       'HW5 judge runs; ESTIMATED tokens from saved prompt, evidence and critique')
        table.append(dict(cost_category=category, call_site=loc, purpose=purpose, model=model,
                          calls=len(calls), input_tokens=inp, output_tokens=out, cost_usd=round(cost, 6)))
    with (OUT / 'costs-by-model.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['cost_category','call_site','purpose','model','calls','input_tokens','output_tokens','cost_usd'])
        writer.writeheader()
        writer.writerows(table)
    assert sum(r['calls'] for r in table) == len(rows)
    assert len({(r['cost_category'],r['call_site'],r['model'],r['identity']) for r in rows}) == len(rows)
    sites = defaultdict(list)
    for row in table:
        sites[(row['cost_category'], row['call_site'])].append(row)
    combined = []
    for (category, loc), members in sorted(sites.items()):
        row = dict(members[0])
        row['model'] = '; '.join(m['model'] for m in members)
        for field in ('calls', 'input_tokens', 'output_tokens', 'cost_usd'):
            row[field] = sum(m[field] for m in members)
        row['cost_usd'] = round(row['cost_usd'], 6)
        combined.append(row)
    with (OUT / 'costs.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(combined[0]))
        writer.writeheader()
        writer.writerows(combined)
    print(json.dumps(combined, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collect', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.collect:
        collect()
    aggregate()
