"""Portable component regressions: explicit test fixtures, no training/corpora."""

import copy
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from build_visualisation_browser import TEMPLATE, build
from swemper_nmf_export_reader import load_export, natural_key
from swemper_nmf_timeline_v3 import render
from swemper_nmf_timeline_v4 import payload, transform


class VisualisationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='swemper-visualisation-test-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.names = ['svenska_lakartidningen_1904_vol001_0139.txt',
                      'svenska_lakartidningen_1964_vol001_2232_0608.txt']
        self.model = self.root / 'model.json'
        self.metadata = self.root / 'all_files.csv'
        self.output = self.root / 'source.html'
        # Tiny synthetic fixture; these values are not presented as model results.
        self.fixture = {
            'topics': [{'id': 1, 'label': 'läkare', 'topic_terms': [{'term': 'läkare'}]}],
            'documents': [{'base_name': name, 'document_topics': [
                {'topic_index': 1, 'topic_confidence': weight}]} for name, weight in zip(self.names, [0.5, 2.0])],
            'meta_data': {'configuration': {
                'NUMBER_OF_RUNS': 20, 'OVERLAP_CUT_OFF': 0.6, 'NUMBER_OF_TOPICS': 10,
                'NR_OF_TOP_DOCUMENTS': 50, 'STOP_WORDS': [],
                'MIN_DOCUMENT_FREQUENCY': 10, 'MAX_DOCUMENT_FREQUENCY': 0.95,
            }},
        }
        self.save()
        self.metadata.write_text(''.join(f'/pages/{name}\t{name.split("_")[2]}-01-01\n' for name in self.names), encoding='utf-8')

    def save(self):
        self.model.write_text(json.dumps({'topic_model_output': self.fixture}), encoding='utf-8')

    def source(self, title='Svenska Läkartidningen'):
        render(self.model, self.metadata, self.output, 'svenska_lakartidningen', title, 'Fixture')
        return self.output.read_text(encoding='utf-8')

    def test_links_weights_and_filename_order(self):
        from urllib.parse import parse_qs, urlsplit
        data, _ = load_export(self.model, self.metadata, 'svenska_lakartidningen')
        self.assertEqual((data['pages'], data['represented']), (2, 2))
        self.assertEqual([marker[5] for marker in data['markers']], [0.5, 2.0])
        for marker, name in zip(data['markers'], self.names):
            query = parse_qs(urlsplit(marker[4]).query)
            self.assertEqual(query['slug'], [Path(name).stem])
            self.assertNotIn('page', query)
        self.assertEqual(sorted(['page_10', 'page_2', 'page_1'], key=natural_key), ['page_1', 'page_2', 'page_10'])

    def test_invalid_weights_and_ids(self):
        original = copy.deepcopy(self.fixture)
        for field, values in [('topic_confidence', [True, '0.5', 0, -1, float('inf'), float('nan')]),
                              ('topic_index', [True, 1.5, '1.5', 0, 99])]:
            for value in values:
                with self.subTest(field=field, value=value):
                    self.fixture = copy.deepcopy(original)
                    self.fixture['documents'][0]['document_topics'][0][field] = value
                    self.save()
                    self.assertRaises(ValueError, load_export, self.model, self.metadata, 'svenska_lakartidningen')

    def test_empty_and_duplicate_assignments(self):
        original = copy.deepcopy(self.fixture)
        for assignments in ([], original['documents'][0]['document_topics'] * 2):
            self.fixture = copy.deepcopy(original)
            self.fixture['documents'][0]['document_topics'] = assignments
            self.save()
            self.assertRaises(ValueError, load_export, self.model, self.metadata, 'svenska_lakartidningen')

    def test_comments_and_wrong_dates_rejected(self):
        for line in ['svenska_lakartidningen_1904_comments.txt\t1904-01-01\n',
                     f'{self.names[0]}\t1915-01-01\n']:
            self.metadata.write_text(line)
            self.assertRaises(ValueError, load_export, self.model, self.metadata, 'svenska_lakartidningen')

    def test_single_pass_escaping(self):
        self.fixture['topics'][0]['label'] = '__METHOD__ </script>'
        self.save()
        source = self.source('__DATA__ <img src=x>')
        self.assertIn('__DATA__ &lt;img src=x&gt;', source)
        self.assertNotIn('<img src=x>', source)
        self.assertEqual(json.loads(payload(source, 'DATA'))['topics'][0][1], '__METHOD__ </script>')
        self.assertNotIn('const DATA = __DATA__;', source)

    def test_v4_data_method_controls_preserved(self):
        before = self.source()
        after = transform(before)
        for key in ('DATA', 'METHOD'):
            self.assertEqual(payload(before, key), payload(after, key))
        for identifier in ('hide-selected', 'only-selected', 'create-group', 'zoom-slider', 'weight-legend', 'export-warning'):
            self.assertIn(f'id="{identifier}"', after)
        self.assertIn('${weight} · relativ vikt', after)
        self.assertIn('r: weightRadius(relativeWeight(id, weight))', after)
        self.assertRaises(ValueError, transform, after)
        self.assertRaises(ValueError, transform, '<html></html>')

    def test_two_command_rendering_cli(self):
        folder = Path(__file__).resolve().parent
        commands = [
            [sys.executable, str(folder / 'swemper_nmf_timeline_v3.py'), '--model', str(self.model),
             '--metadata', str(self.metadata), '--journal', 'svenska_lakartidningen', '--title', 'Fixture',
             '--label', 'Fixture', '--output', str(self.output)],
            [sys.executable, str(folder / 'swemper_nmf_timeline_v4.py'), '--source', str(self.output),
             '--output', str(self.root / 'weights.html')],
        ]
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload(self.output.read_text(), 'DATA'), payload((self.root / 'weights.html').read_text(), 'DATA'))

    @unittest.skipUnless(shutil.which('node'), 'Optional Node numerical check; renderer itself needs only Python')
    def test_javascript_relative_size(self):
        source = transform(self.source())
        match = re.search(r'function weightRadius\(proportion\) \{ return (.*?); \}', source)
        assert match is not None
        formula = match.group(1)
        result = subprocess.run(['node', '-e', f'console.log(JSON.stringify([.25,.5,1].map(proportion=>{formula})))'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [math.sqrt(28), math.sqrt(52), 10])

    def test_selector_small_valid_registry(self):
        self.output.write_text(transform(self.source()))
        registry = self.root / 'versions.json'
        registry.write_text(json.dumps({'default': 'fixture', 'versions': [{
            'id': 'fixture', 'group': 'Test', 'label': 'Fixture', 'description': 'Test fixture', 'path': 'source.html'}]}))
        output = self.root / 'index.html'
        build(registry, TEMPLATE, output, self.root)
        text = output.read_text()
        self.assertIn('replaceChildren(next)', text)
        self.assertIn('event.source !== frame.contentWindow', text)
        self.assertNotIn('const DATA =', text)

    def test_selector_unsafe_missing_duplicate_rejected(self):
        registry = self.root / 'versions.json'
        entry = {'id': 'fixture', 'group': 'Test', 'label': 'Fixture', 'description': 'Fixture', 'path': 'missing.html'}
        cases = [(dict(entry), FileNotFoundError), (dict(entry, path='../outside.html'), ValueError)]
        for view, error in cases:
            registry.write_text(json.dumps({'default': 'fixture', 'versions': [view]}))
            self.assertRaises(error, build, registry, TEMPLATE, self.root / 'index.html', self.root)
        self.output.write_text('<!doctype html><title>Fixture</title>')
        entry['path'] = 'source.html'
        registry.write_text(json.dumps({'default': 'fixture', 'versions': [entry, entry]}))
        self.assertRaises(ValueError, build, registry, TEMPLATE, self.root / 'index.html', self.root)


if __name__ == '__main__':
    unittest.main()
