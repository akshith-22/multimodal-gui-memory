"""Task-scoped pilot retrieval with explicit observation evidence."""
import hashlib
import json
import re
from pathlib import Path
from uuid import uuid4


class EpisodicMemory:
    def __init__(self, mode, output_path, top_k=2):
        if mode not in ('baseline', 'text', 'multimodal'):
            raise ValueError('GUI_MEMORY_MODE must be baseline, text, or multimodal')
        if not 1 <= top_k <= 4:
            raise ValueError('GUI_MEMORY_TOP_K must be between 1 and 4')
        if mode != 'baseline' and not output_path:
            raise ValueError('Memory modes require --traj_output_path')
        self.mode = mode
        self.output_path = output_path
        self.top_k = top_k
        self.reset()

    def reset(self):
        self.records = []
        self.episode_id = uuid4().hex
        self.directory = None
        self.last_digest = None

    def _write(self, event):
        with (self.directory / 'memory.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + '\n')

    def observe(self, goal, step, image, ui_text):
        if self.mode == 'baseline':
            return
        if self.directory is None:
            self.directory = Path(self.output_path) / 'memory' / self.episode_id
            self.directory.mkdir(parents=True, exist_ok=False)
        digest = hashlib.sha256(image.tobytes()).hexdigest()
        image_path = self.directory / f'observation-{step}.png'
        image.save(image_path)
        if self.records and self.records[-1]['evidence'] == 'awaiting_next_observation':
            record = self.records[-1]
            record['evidence'] = 'screen_changed' if digest != self.last_digest else 'screen_unchanged'
            record['next_screenshot'] = str(image_path.resolve())
            self._write({'event': 'observation_update', 'record': record.copy()})
        self.last_digest = digest
        self.current = {'id': step, 'goal': goal, 'screenshot': str(image_path.resolve()),
                        'ui_text': ui_text[:2000]}

    def retrieve(self, goal, ui_text):
        if self.mode == 'baseline':
            return [], []
        query = set(re.findall(r'\w+', (goal + ' ' + ui_text).lower()))
        def score(record):
            text = record['model_summary'] + ' ' + record['ui_text']
            words = set(re.findall(r'\w+', text.lower()))
            return (len(query & words) / max(1, len(query | words)), record['id'])
        selected = sorted(self.records, key=score, reverse=True)[:self.top_k]
        selected.sort(key=lambda record: record['id'])
        content = []
        if selected:
            content.append({'text': 'Historical episodes follow. Summaries are model reports. '
                            'Screen changes do not prove action success. Reground every target '
                            'on the CURRENT screenshot and never replay old coordinates blindly.'})
        for record in selected:
            public = {key: record[key] for key in ('id', 'action', 'model_summary', 'evidence')}
            content.append({'text': json.dumps(public, ensure_ascii=False)})
            if self.mode == 'multimodal':
                content.append({'image': record['screenshot']})
        ids = [record['id'] for record in selected]
        self._write({'event': 'retrieval', 'step': self.current['id'], 'mode': self.mode,
                     'top_k': self.top_k, 'record_ids': ids})
        return content, ids

    def record_action(self, action, summary):
        if self.mode == 'baseline':
            return
        record = dict(self.current, action=action, model_summary=(summary or '')[:1500],
                      evidence='awaiting_next_observation')
        self.records.append(record)
        self._write({'event': 'action_record', 'record': record.copy()})
