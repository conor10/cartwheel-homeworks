"""HW5 Part B: immutable evidence export and a one-time stratified split.

Run from the repository root: python -m analysis.run_judges prepare
No model calls are made by preparation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from analysis.helpers import split_labels, register_judge, run_judge, judge_alignment
from analysis.helpers import _state
from analysis.helpers.normalization import _metadata, _text

ROOT = Path(__file__).resolve().parents[1]
MODE = 'irrelevant_response_detail'
# Content review found equivalent requests beyond the fixture/order grouping.
# Always keep the lowest scenario ID, without consulting the labels.
CLOSE_VARIANTS = [
    (['support-0113', 'support-0123', 'support-0133'], 'Same general store-override question; no specific order decision'),
    (['support-0115', 'support-0125', 'support-0135'], 'Same general payment-card/account-change policy question'),
    (['support-0106', 'support-0126'], 'Same delivery-versus-order-date return-window question'),
    (['support-0137', 'support-0143', 'support-0151'], 'Same public catalogue listing/price request, with product/store substitutions'),
    (['support-0136', 'support-0146'], 'Same public catalogue request with a price ceiling, with entity/amount substitutions'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_labels(mode=MODE):
    path = _state.state_path('hw5_labels', mode + '.jsonl')
    labels = {}
    for row in map(json.loads, path.read_text().splitlines()):
        if row.get('superseded_by'):
            continue
        if type(row.get('label')) is not int or row['label'] not in (0, 1) or not row.get('note', '').strip():
            raise ValueError('Every human label needs Pass=1 / Fail=0 and evidence')
        labels[row['trace_id']] = row
    return labels


def conversation_input(target, sessions):
    """Allowlist only observed user text, tool arguments/results, final replies.

    Include prior turns up to this target, never future replies. Model request
    histories, generation narration, system prompts, metadata and review scores
    are deliberately not copied.
    """
    sid = _metadata(target).get('cartwheel.session_id') or target.get('sessionId')
    if not sid:
        raise ValueError('Missing session identity')
    messages = []
    for turn in sorted(sessions[sid], key=lambda t:(t['timestamp'], t['id'])):
        user = _text(turn.get('input'))
        if not user:
            raise ValueError('Missing user request')
        messages.append({'role':'user', 'text':user})
        for tool in sorted((o for o in turn.get('observations', []) if o.get('type') == 'TOOL'),
                           key=lambda o:(o.get('startTime') or '', o['id'])):
            messages.append({'role':'tool_call', 'name':tool['name'], 'arguments':tool.get('input')})
            messages.append({'role':'tool_result', 'name':tool['name'], 'content':tool.get('output')})
        output = _text(turn.get('output'))
        if not output:
            raise ValueError('Missing final reply')
        messages.append({'role':'assistant', 'text':output})
        if turn['id'] == target['id']:
            return {'trace_id':target['id'], 'trace':messages}
    raise ValueError('Target is not in its conversation')


def prepare_inputs():
    manifest = _state.read_json(_state.state_path('hw5_review.json'))
    source = ROOT / manifest['trace_source']
    if digest(source) != manifest['trace_source_sha256']:
        raise ValueError('The reviewed export changed; do not silently substitute new evidence')
    labels = latest_labels()
    rows = manifest['rows']
    if any(r['trace_id'] not in labels for r in rows):
        raise ValueError('Finish or explicitly select the eligible reviewed queue before preparing')
    excluded = {}
    for group, reason in CLOSE_VARIANTS:
        members = sorted(r['scenario_id'] for r in rows if r['scenario_id'] in group)
        for sid in members[1:]:
            excluded[sid] = {'kept_scenario':members[0], 'reason':reason}
    eligible = [r for r in rows if r['scenario_id'] not in excluded]
    for key in ('trace_id', 'session_id', 'group_key'):
        if len({r[key] for r in eligible}) != len(eligible):
            raise ValueError(f'Duplicate {key} in eligible records')
    counts = Counter('Pass' if labels[r['trace_id']]['label'] else 'Fail' for r in eligible)
    if min(counts.get('Pass',0), counts.get('Fail',0)) < 30:
        raise ValueError(f'Not enough independent labels: {dict(counts)}')
    raw = json.loads(source.read_text())['traces']
    index = {t['id']:t for t in raw}
    sessions = defaultdict(list)
    for t in raw:
        sid = _metadata(t).get('cartwheel.session_id') or t.get('sessionId')
        sessions[sid].append(t)
    records = [conversation_input(index[r['trace_id']], sessions) for r in eligible]
    path = _state.state_path('hw5_trace_inputs.json')
    if path.exists():
        if json.loads(path.read_text()) != records:
            raise ValueError('Saved judge inputs differ; refusing to overwrite the immutable export')
    else:
        if MODE in _state.read_json(_state.state_path('splits.json'), {}):
            raise ValueError('Split already exists without its inputs; restore the original export')
        _state.write_json(path, records)
    report = {'mode':MODE, 'source':str(source.relative_to(ROOT)), 'source_sha256':digest(source),
              'inputs_sha256':digest(path), 'input_count':len(records), 'eligible_counts':dict(counts),
              'excluded_close_variants':excluded, 'prior_grouping_rule':manifest['grouping_rule'],
              'evidence_policy':'Observed user/final assistant messages and all tool arguments/results, including retrieved policy bodies; previous turns only. No generation narration, system prompts, scores, review notes, labels or scenario metadata.',
              'target_rule':'Evaluate the last assistant reply in each record; earlier replies are context.',
              'eligibility':[{'trace_id':r['trace_id'], 'scenario_id':r['scenario_id'], 'session_id':r['session_id']} for r in eligible]}
    _state.write_json(_state.state_path('hw5_input_manifest.json'), report)
    os.environ['CARTWHEEL_JUDGE_TRACE_SOURCE'] = str(path.resolve())
    return records


def split_data(mode=MODE):
    if mode != MODE:
        raise ValueError('This homework selects one mode')
    path = _state.state_path('hw5_trace_inputs.json')
    provenance = _state.read_json(_state.state_path('hw5_input_manifest.json'))
    if digest(path) != provenance['inputs_sha256']:
        raise ValueError('Saved judge inputs changed')
    records = json.loads(path.read_text())
    ids = [r['trace_id'] for r in records]
    existing = _state.read_json(_state.state_path('splits.json'), {}).get(mode)
    if existing:
        assignment = {k:existing[k] for k in ('train','dev','test')}
        flat = sum(assignment.values(), [])
        if len(flat) != len(set(flat)) or set(flat) != set(ids):
            raise ValueError('Existing split does not match saved inputs; do not resplit')
    else:
        assignment = split_labels(mode, fractions=(0.20,0.40,0.40), seed=7,
                                  min_per_class=10, eligible_trace_ids=ids)
    labels = latest_labels(mode)
    counts = {k:dict(Counter('Pass' if labels[tid]['label'] else 'Fail' for tid in v)) for k,v in assignment.items()}
    os.environ['CARTWHEEL_JUDGE_TRACE_SOURCE'] = str(path.resolve())
    return {'mode':mode, 'counts':counts, 'inputs_sha256':digest(path),
            'fractions':[0.20,0.40,0.40], 'seed':7, 'label_convention':'Pass=1 / Fail=0'}


def run_development(mode, prompt_path, *, approved=False):
    """Run only after approval; reuse the same judge ID after interruptions."""
    if not approved:
        raise ValueError('Paid development requires explicit approval of model and trace count')
    if mode != MODE:
        raise ValueError('Only the selected HW5 mode is supported')
    path = _state.state_path('hw5_trace_inputs.json')
    manifest = _state.read_json(_state.state_path('hw5_input_manifest.json'))
    if digest(path) != manifest['inputs_sha256']:
        raise ValueError('Saved judge inputs changed')
    splits = _state.read_json(_state.state_path('splits.json'))[mode]
    if not splits.get('dev'):
        raise ValueError('Prepare the split first')
    os.environ['CARTWHEEL_JUDGE_TRACE_SOURCE'] = str(path.resolve())
    from observability.instrument import load_env
    load_env()
    prompt = Path(prompt_path).read_text()
    matches = []
    for p in _state.state_path('judges').glob(mode + '-v*.json'):
        record = json.loads(p.read_text())
        if record['prompt_text'] == prompt and record['model'] == 'gpt-4o-mini':
            matches.append(record)
    if len(matches) > 1:
        raise ValueError('Multiple matching judge versions; select the existing ID explicitly')
    if matches:
        record = matches[0]
        if record['status'] == 'frozen':
            raise ValueError('Do not resume development on a frozen judge')
    else:
        record = register_judge(mode=mode, prompt_text=prompt, judge_model='gpt-4o-mini')
    judge_id = record['judge_id']
    run_judge(judge_id, split='dev', batch_size=10)
    metrics = judge_alignment(judge_id, split='dev')
    _state.write_json(ROOT / 'analysis/report' / f'dev-{judge_id}.json', metrics)
    return {'judge_id':judge_id, 'metrics':metrics}


def frozen_test_selection():
    """Validate the student's recorded final choices without model calls."""
    selection = _state.read_json(_state.state_path('hw5_final_selection.json'), {})
    if selection.get('status') != 'frozen':
        raise ValueError('Choose and freeze final versions before testing')
    for name, expected in selection['locked_files'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen evaluation file changed: {name}')
    return selection


def run_test(judge_id, *, approved=False):
    """Evaluate/resume the already frozen GPT judge; never register again."""
    if not approved:
        raise ValueError('Paid test requires explicit approval of model and trace count')
    selection = frozen_test_selection()
    if judge_id != selection['gpt']['judge_id']:
        raise ValueError('Use the selected final GPT judge')
    record = _state.read_json(_state.state_path('judges', judge_id + '.json'))
    if (record['status'] != 'frozen' or record['model'] != selection['gpt']['model']
            or hashlib.sha256(record['prompt_text'].encode()).hexdigest() != selection['gpt']['prompt_sha256']):
        raise ValueError('Frozen GPT judge identity changed')
    os.environ['CARTWHEEL_JUDGE_TRACE_SOURCE'] = str(_state.state_path('hw5_trace_inputs.json').resolve())
    from observability.instrument import load_env
    load_env()
    run_judge(judge_id, split='test', batch_size=10)
    result = judge_alignment(judge_id, split='test')
    _state.write_json(ROOT / 'analysis/report' / f'test-{judge_id}.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'dev', 'test'])
    parser.add_argument('--prompt', type=Path)
    parser.add_argument('--judge-id')
    parser.add_argument('--approve-paid-run', action='store_true')
    args = parser.parse_args()
    if args.action == 'test':
        if not args.judge_id:
            parser.error('--judge-id is required for testing')
        print(json.dumps(run_test(args.judge_id, approved=args.approve_paid_run), indent=2))
        return
    if args.action == 'dev':
        if not args.prompt:
            parser.error('--prompt is required for development')
        print(json.dumps(run_development(MODE, args.prompt, approved=args.approve_paid_run), indent=2))
        return
    prepare_inputs()
    result = split_data()
    report_dir = ROOT / 'analysis/report'
    _state.write_json(report_dir / 'hw5_part_b.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
