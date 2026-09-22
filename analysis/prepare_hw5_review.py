"""Prepare HW5 Part A once, without overwriting human reviews or calling a model."""
import hashlib
import json
from pathlib import Path

from analysis.helpers import next_to_label
from analysis.review_app.traces import TraceStore

ROOT = Path(__file__).resolve().parents[1]
MODE = 'irrelevant_response_detail'


def prepare():
    state = ROOT / 'analysis/state'
    destination = state / 'hw5_review.json'
    labels_path = state / 'hw5_labels' / f'{MODE}.jsonl'
    if destination.exists() or labels_path.exists():
        raise ValueError('HW5 preparation already exists; preserve it rather than regenerate.')
    audit = json.loads((ROOT / 'analysis/report/hw5_part_a_audit.json').read_text())
    export = ROOT / audit['trace_source']
    if hashlib.sha256(export.read_bytes()).hexdigest() != audit['trace_source_sha256']:
        raise ValueError('Trace export changed since the audit; audit it again first.')
    scenarios = {s['id']: s for s in map(json.loads, (ROOT / 'scenarios/support_scenarios.jsonl').read_text().splitlines())}
    store = TraceStore(None, ROOT / 'scenarios/support_scenarios.jsonl', 'http://localhost:3000', export)
    index = {t['id']: t for t in store.summaries()}
    # Shared fixture/order + intent identifies close variants despite changed wording.
    # Non-order requests use their substantive dimensions, ignoring style/turn count.
    def group(t):
        s = scenarios[t['scenario_id']]
        d = s['tuple']
        if s.get('data_quality_case_id'):
            key = ['fixture', s['data_quality_case_id'], d['intent']]
        elif d.get('order_id'):
            key = ['order', d['order_id'], d['intent']]
        else:
            key = ['dimensions', {k:v for k,v in d.items() if k not in ('user_style', 'turn_count', 'user_id', 'tools_needed')}]
        return json.dumps(key, sort_keys=True)
    used_groups, used_sessions, rows, excluded, labels = set(), set(), [], [], []
    def add(tid, reason, old=None):
        t = index.get(tid)
        if not t or not t.get('scenario_id') or t['session_missing']:
            return False
        key = group(t)
        if key in used_groups or t['session_id'] in used_sessions:
            excluded.append({'trace_id':tid, 'scenario_id':t['scenario_id'], 'group_key':key, 'reason':'Already represented conversation or close variant'})
            return False
        # Missing final output cannot supply a relevance judgment.
        full = next(r for r in store.session(tid) if r['id'] == tid)
        if full['missing_output'] or not full['output'].strip():
            return False
        used_groups.add(key); used_sessions.add(t['session_id'])
        row = {'trace_id':tid, 'scenario_id':t['scenario_id'], 'session_id':t['session_id'], 'group_key':key, 'selection_reason':reason}
        rows.append(row)
        if old:
            labels.append({**row, 'mode':MODE, 'mode_version':audit['hw4_mode_version'], 'label':old['hw5_label'], 'note':old['evidence'], 'source':'reused_hw4_human_label', 'encoding':'Pass=1, Fail=0'})
        return True
    for old in audit['retained_label_candidates']:
        add(old['trace_id'], 'Existing mode-specific HW4 human judgment', old)
    for row in audit['pass_candidates_from_prior_no_failure_reviews']:
        add(row['trace_id'], 'Prior no-failure review; confirm response relevance specifically')
    for row in audit['boundary_candidates_from_prior_no_failure_reviews']:
        add(row['trace_id'], 'Prior review needs a mode-specific boundary decision')
    # Add a deterministic random reserve using the supplied helper, not model labels.
    for row in next_to_label(MODE, k=322, strategy='random', trace_source=export):
        if len(rows) - len(labels) >= 50:
            break
        add(row['trace_id'], 'Random candidate from the supplied next_to_label helper')
    manifest = {'mode':MODE, 'mode_version':audit['hw4_mode_version'], 'mode_confirmed':True,
                'trace_source':audit['trace_source'], 'trace_source_sha256':audit['trace_source_sha256'],
                'grouping_rule':'Same data-quality fixture and intent; otherwise same order and intent; non-order cases share substantive dimensions excluding wording style, turn count, user identity and expected tool count. One session per record.',
                'independence_status':'Known fixture/order/structural variants removed; inspect remaining semantic variants before Part B.',
                'rows':rows, 'excluded':excluded}
    destination.write_text(json.dumps(manifest, indent=2)+'\n')
    labels_path.parent.mkdir(exist_ok=True)
    labels_path.write_text(''.join(json.dumps(l, ensure_ascii=False)+'\n' for l in labels))
    print(json.dumps({'reused_fail':sum(l['label']==0 for l in labels), 'reused_pass':sum(l['label']==1 for l in labels), 'pending':len(rows)-len(labels), 'excluded_variants':len(excluded)}))


if __name__ == '__main__':
    prepare()
