"""HW5 human labels, kept separate from HW4 and never synced as failure flags."""
import json
from pathlib import Path
from threading import RLock

from .state import Conflict, now, read, required


class HW5Review:
    def __init__(self, directory: Path):
        self.directory = directory
        self.lock = RLock()

    def snapshot(self):
        with self.lock:
            manifest = read(self.directory / 'hw5_review.json', {})
            if not manifest:
                return {'rows':[], 'labels':{}, 'revision':0, 'counts':{'Pass':0, 'Fail':0, 'pending':0}}
            path = self.directory / 'hw5_labels' / (manifest['mode'] + '.jsonl')
            records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
            labels = {r['trace_id']:r for r in records}
            ids = {r['trace_id'] for r in manifest['rows']}
            current = [r for tid,r in labels.items() if tid in ids]
            development = self.development(manifest, labels)
            return {**manifest, 'labels':labels, 'development':development, 'revision':len(records), 'counts':{
                'Pass':sum(r['label']==1 for r in current),
                'Fail':sum(r['label']==0 for r in current), 'pending':len(ids)-len(current)}}

    def development(self, manifest, labels):
        """Expose development predictions only, even if files later contain tests."""
        mode = manifest['mode']
        ids = set(read(self.directory / 'splits.json', {}).get(mode, {}).get('dev', []))
        reviews = read(self.directory / 'hw5_disagreement_reviews.json', {})
        runs = []
        for path in sorted((self.directory / 'judges').glob(mode + '-v*.json')):
            judge = read(path, {})
            predictions = judge.get('predictions', {}).get(judge.get('prompt_hash'), {})
            critiques = judge.get('critiques', {}).get(judge.get('prompt_hash'), {})
            runs.append((judge['judge_id'], judge['model'], {
                tid:{'label':v if judge.get('label_convention')=='pass_positive' else 1-v,
                     'critique':critiques.get(tid)} for tid,v in predictions.items() if tid in ids}))
        for path in sorted((self.directory / 'comparisons').glob('jev-*.json')):
            record = read(path, {})
            if record.get('split') == 'dev':
                runs.append((path.stem, record['model'], {tid:p for tid,p in record.get('predictions',{}).items() if tid in ids}))
        def version(rid):
            if rid.startswith(mode + '-v'):
                return int(rid.rsplit('-v', 1)[1])
            record = read(self.directory / 'comparisons' / (rid + '.json'), {})
            for config_path in (self.directory.parent / 'prompts').glob(mode + '-jev-v*.json'):
                if read(config_path, {}).get('questions') == record.get('questions'):
                    return int(config_path.stem.rsplit('-v', 1)[1])
            return 0

        return [{'id':rid, 'model':model, 'version':version(rid), 'predictions':{
            tid:{**p,'disagrees':p['label']!=labels[tid]['label'],
                 'review':reviews.get(rid+':'+tid)} for tid,p in preds.items() if tid in labels}}
            for rid,model,preds in runs]

    def save_disagreement(self, body):
        with self.lock:
            state = self.snapshot()
            rid, tid = body.get('run_id'), body.get('trace_id')
            run = next((r for r in state['development'] if r['id']==rid), None)
            if not run or tid not in run['predictions']:
                raise ValueError('Select a development prediction')
            if body.get('decision') not in ('judge_wrong','human_label_wrong','boundary_unclear'):
                raise ValueError('Choose a disagreement decision')
            from analysis.server import _write_json
            path = self.directory / 'hw5_disagreement_reviews.json'
            reviews = read(path, {})
            key = rid+':'+tid
            old = reviews.get(key)
            reviews[key] = {'decision':body['decision'], 'reason':required(body,'reason'),
                            'updated_at':now(), 'history':([old] if old else [])}
            _write_json(path, reviews)
            return self.snapshot()

    def save(self, body):
        with self.lock:
            state = self.snapshot()
            if body.get('revision') != state['revision']:
                raise Conflict('HW5 labels changed in another window. Refresh before saving.')
            row = next((r for r in state['rows'] if r['trace_id']==body.get('trace_id')), None)
            if row is None:
                raise ValueError('Select a trace from the HW5 queue')
            value = body.get('label')
            if type(value) is not int or value not in (0,1):
                raise ValueError('Choose Pass (1) or Fail (0)')
            note = required(body, 'note')
            record = {**row, 'mode':state['mode'], 'mode_version':state['mode_version'],
                      'label':value, 'note':note, 'source':'human', 'encoding':'Pass=1, Fail=0', 'updated_at':now()}
            path = self.directory / 'hw5_labels' / (state['mode'] + '.jsonl')
            # Append-only decisions preserve previous judgments; helper readers use the latest.
            with path.open('a') as f:
                f.write(json.dumps(record, ensure_ascii=False)+'\n')
                f.flush()
                import os
                os.fsync(f.fileno())
            return self.snapshot()
