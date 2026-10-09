"""Portable component regressions: explicit test fixtures, no training/corpora."""

import copy
import csv
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings

from build_visualisation_browser import TEMPLATE, build
from swemper_nmf_export_reader import load_export, load_manifest, natural_key, target_url
from swemper_nmf_visualisation import render, render_manifest


def payload(source, name):
    matches = re.findall(rf"^const {name} = (.*);$", source, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"Expected one embedded {name}")
    return matches[0]


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

    def test_final_data_method_controls_preserved(self):
        after = self.source()
        data, _ = load_export(self.model, self.metadata, 'svenska_lakartidningen')
        self.assertEqual(json.loads(payload(after, 'DATA')), data)
        self.assertEqual(json.loads(payload(after, 'METHOD')), {
            'runs': 20, 'overlap': 0.6, 'requestedTopics': 10,
            'topDocuments': 50, 'stopwordCount': 0,
            'minimumFrequency': 10, 'maximumFrequency': 0.95,
        })
        for identifier in ('hide-selected', 'only-selected', 'create-group', 'zoom-slider', 'weight-legend', 'export-warning'):
            self.assertIn(f'id="{identifier}"', after)
        self.assertIn('${weight} · relativ vikt', after)
        self.assertIn('r: weightRadius(relativeWeight(id, weight))', after)

    def test_one_command_rendering_cli(self):
        folder = Path(__file__).resolve().parent
        command = [sys.executable, str(folder / 'swemper_nmf_visualisation.py'), '--model', str(self.model),
                   '--metadata', str(self.metadata), '--journal', 'svenska_lakartidningen', '--title', 'Fixture',
                   '--label', 'Fixture', '--output', str(self.output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.output.read_text()
        self.assertIn('function weightRadius(', output)
        self.assertIn('id="weight-legend"', output)
        self.assertEqual({path.name for path in self.root.iterdir()}, {'model.json', 'all_files.csv', 'source.html'})

    def test_inputs_not_overwritten(self):
        for path in (self.model, self.metadata):
            before = path.read_bytes()
            self.assertRaises(ValueError, render, self.model, self.metadata, path,
                              'svenska_lakartidningen', 'Fixture', 'Fixture')
            self.assertEqual(path.read_bytes(), before)

    def test_empty_export_rejected_without_output(self):
        self.fixture['documents'] = []
        self.save()
        self.assertRaises(ValueError, render, self.model, self.metadata, self.output,
                          'svenska_lakartidningen', 'Fixture', 'Fixture')
        self.assertFalse(self.output.exists())

    @unittest.skipUnless(shutil.which('node'), 'Optional Node numerical check; renderer itself needs only Python')
    def test_javascript_relative_size(self):
        source = self.source()
        match = re.search(r'function weightRadius\(proportion\) \{ return (.*?); \}', source)
        assert match is not None
        formula = match.group(1)
        result = subprocess.run(['node', '-e', f'console.log(JSON.stringify([.25,.5,1].map(proportion=>{formula})))'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [math.sqrt(28), math.sqrt(52), 10])

    def test_selector_small_valid_registry(self):
        self.source()
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


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.fixture = VisualisationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.fixture.fixture['documents'][0]['base_name'] = 'page_001.txt'
        self.fixture.fixture['documents'][1]['base_name'] = 'other/page_002.txt'
        self.fixture.save()
        self.metadata = self.root / 'documents.csv'
        self.rows = [['page_001.txt', '1904', 'images/page #1.jpg'],
                     ['other/page_002.txt', '1964', 'https://example.org/scan/2'],
                     ['not_exported.txt', '1964', '']]
        self.write_rows()
        (self.root / 'images').mkdir()
        # An explicit path-existence fixture, not a real corpus image.
        (self.root / 'images/page #1.jpg').write_bytes(b'test path fixture')
        self.manifest = self.root / 'manifest.json'
        self.settings = {'schema_version': 1, 'model': 'model.json', 'metadata': 'documents.csv',
                         'metadata_format': 'documents_csv', 'link_mode': 'targets', 'asset_root': '.',
                         'title': 'ActDisease fixture', 'label': 'Test'}
        self.save_manifest()
        self.output = self.root / 'viewer/index.html'

    def write_rows(self):
        with self.metadata.open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['document_id', 'year', 'target'])
            writer.writerows(self.rows)

    def save_manifest(self):
        self.manifest.write_text(json.dumps(self.settings))

    def test_generic_paths_years_and_weights(self):
        data = render_manifest(self.manifest, self.output)
        self.assertEqual((data['pages'], data['represented']), (3, 2))
        self.assertEqual([row[5] for row in data['markers']], [0.5, 2.0])
        self.assertEqual([row[1] for row in data['markers']], [1904, 1964])
        self.assertEqual(data['markers'][0][4], '../images/page%20%231.jpg')
        self.assertEqual(data['markers'][1][4], 'https://example.org/scan/2')
        self.assertNotIn('<h1>SweMPer', self.output.read_text())

    def test_manifest_cli_resolves_relative_paths_from_other_cwd(self):
        script = Path(__file__).resolve().parent / 'swemper_nmf_visualisation.py'
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run([sys.executable, str(script), '--manifest', str(self.manifest),
                                     '--output', str(self.output)], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(payload(self.output.read_text(), 'DATA'))['markers'][0][4], '../images/page%20%231.jpg')

    def test_missing_or_blank_target_preserves_pages(self):
        self.rows[0][2] = 'images/missing.png'
        self.rows[1][2] = ''
        self.write_rows()
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter('always')
            data = render_manifest(self.manifest, self.output)
        self.assertEqual(len(messages), 1)
        self.assertEqual(len(data['markers']), 2)
        self.assertTrue(all(row[4] is None for row in data['markers']))

    def test_no_link_mode(self):
        self.settings['link_mode'] = 'none'
        self.save_manifest()
        data = render_manifest(self.manifest, self.output)
        self.assertTrue(all(row[4] is None for row in data['markers']))

    def test_unsafe_targets_rejected(self):
        for target in ['javascript:alert(1)', 'data:text/html,test', 'file:///tmp/page.jpg',
                       '//example.org/page.jpg', '/tmp/page.jpg', '../outside.jpg',
                       'C:\\images\\page.jpg', 'images/page.html',
                       'https://user:secret@example.org/', 'https://example.org/\npage',
                       'https://exa mple.org/page', 'https://example.org:99999/page']:
            with self.subTest(target=target):
                self.assertRaises(ValueError, target_url, target, self.root, self.output)
        (self.root / 'images/escape.jpg').symlink_to(self.root.parent / 'outside.jpg')
        self.assertRaises(ValueError, target_url, 'images/escape.jpg', self.root, self.output)

    def test_metadata_duplicates_invalid_years_and_unknown_ids(self):
        original = copy.deepcopy(self.rows)
        for bad in [original + [original[0]], [['page_001.txt', '1904.5', '']],
                    [['page_001.txt', '0000', '']], [['unknown.txt', '1904', '']]]:
            self.rows = bad
            self.write_rows()
            self.assertRaises(ValueError, render_manifest, self.manifest, self.output)

    def test_unknown_manifest_fields_missing_inputs_and_mixed_cli(self):
        for field, value in [('typo', 'unused'), ('schema_version', True), ('link_mode', 'guess'),
                             ('model', 'missing.json'), ('asset_root', 'missing')]:
            settings = dict(self.settings, **{field: value})
            self.manifest.write_text(json.dumps(settings))
            self.assertRaises(ValueError, load_manifest, self.manifest)
        self.save_manifest()
        self.assertRaises(ValueError, render_manifest, self.manifest, self.manifest)
        script = Path(__file__).resolve().parent / 'swemper_nmf_visualisation.py'
        result = subprocess.run([sys.executable, str(script), '--manifest', str(self.manifest),
                                 '--journal', 'x', '--output', str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    @unittest.skipUnless(shutil.which('node'), 'Optional Node check of linked/unlinked primitives')
    def test_linked_and_unlinked_marker_primitives(self):
        render_manifest(self.manifest, self.output)
        source = self.output.read_text()
        match = re.search(r"const link = url\n(.*?);", source, re.DOTALL)
        assert match is not None
        javascript = "const svgElement=(tag,attributes)=>({tag,attributes}); const id=1,name='fixture';" + \
            "console.log(JSON.stringify(['../images/a.jpg',null].map(url=>url\n" + match.group(1) + ")));"
        result = subprocess.run(['node', '-e', javascript], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        linked, unlinked = json.loads(result.stdout)
        self.assertEqual(linked['tag'], 'a')
        self.assertEqual(linked['attributes']['target'], '_blank')
        self.assertEqual(unlinked['tag'], 'g')
        self.assertNotIn('href', unlinked['attributes'])


if __name__ == '__main__':
    unittest.main()
