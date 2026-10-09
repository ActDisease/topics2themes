"""Portable checks of additive training presets/readers and saved examples.

No model fitting, MongoDB access, tokenizer downloads or private corpus needed.
"""

import importlib
import contextlib
import io
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from swemper_journal_collection import nonblank_pages_without_comments, page_year

ROOT = Path(__file__).resolve().parent


class ModellingExampleTests(unittest.TestCase):
    def test_original_properties_loader_consumes_presets(self):
        # Avoid importing installation-specific environment/connection settings.
        environment = types.ModuleType('environment_configuration')
        setattr(environment, 'RUN_LOCALLY', True)
        setattr(environment, 'WORKSPACE_FOLDER', str(ROOT))
        with patch.dict(sys.modules, {'environment_configuration': environment}):
            loader = importlib.import_module('handle_properties')
            for name in ('diabetes_swemper_swedish30', 'sv_lakartidningen_swedish50'):
                config = importlib.import_module(f'data_folder.{name}.topic_model_configuration')
                with contextlib.redirect_stdout(io.StringIO()):
                    properties, folder, _ = loader.load_properties_from_parameters(f'data_folder.{name}')
                self.assertEqual(Path(folder), ROOT / 'data_folder' / name)
                for field in ('NUMBER_OF_TOPICS', 'NUMBER_OF_RUNS', 'OVERLAP_CUT_OFF',
                              'NR_OF_TOP_DOCUMENTS', 'MIN_DOCUMENT_FREQUENCY',
                              'MAX_NR_OF_FEATURES', 'SUBLINEAR_TF', 'NR_OF_ITERATIONS',
                              'PERCENTATE_NONE_OUTLIERS', 'STORE_IN_DATABASE', 'STOP_WORD_FILE'):
                    self.assertEqual(getattr(properties, field), getattr(config, field), field)

    def test_editable_comparison_presets(self):
        for collection, topics, top, frequency, features, sublinear in [
            ('diabetes_swemper_swedish30', 30, 100, 10, None, False),
            ('sv_lakartidningen_swedish50', 50, 150, 20, 60000, True),
        ]:
            with self.subTest(collection=collection):
                config = importlib.import_module(f'data_folder.{collection}.topic_model_configuration')
                self.assertEqual(config.NUMBER_OF_TOPICS, topics)
                self.assertEqual(config.NR_OF_TOP_DOCUMENTS, top)
                self.assertEqual(config.MIN_DOCUMENT_FREQUENCY, frequency)
                self.assertEqual(config.MAX_NR_OF_FEATURES, features)
                self.assertEqual(config.SUBLINEAR_TF, sublinear)
                self.assertEqual((config.NUMBER_OF_RUNS, config.OVERLAP_CUT_OFF), (20, 0.6))
                self.assertEqual(config.MAX_DOCUMENT_FREQUENCY, 0.95)
                self.assertEqual(config.NR_OF_ITERATIONS, 200)
                self.assertEqual(config.PERCENTATE_NONE_OUTLIERS, 0.75)
                self.assertFalse(config.STORE_IN_DATABASE)
                self.assertFalse(config.PRE_PROCESS)
                self.assertFalse(config.DEBUG)
                self.assertTrue(callable(config.READ_FUNCTION))
                self.assertTrue(callable(config.ADDITIONAL_LABELS_METHOD))

    def test_exact_stoplists_and_baseline_support(self):
        lists = []
        for name in ('diabetes_swemper_swedish30', 'sv_lakartidningen_swedish50'):
            config = importlib.import_module(f'data_folder.{name}.topic_model_configuration')
            raw = (ROOT / 'data_folder' / name / config.STOP_WORD_FILE).read_text(encoding='utf-8')
            words = raw.splitlines()
            self.assertEqual(len(words), 108)
            self.assertEqual(len(set(words)), 108)
            self.assertTrue(all(word and word == word.strip() for word in words))
            self.assertFalse({'inte', 'icke', 'ej', 'ingen', 'utan', 'sitta'} & set(words))
            lists.append(raw)
        self.assertEqual(lists[0], lists[1])
        for name in ('diabetes_swemper', 'sv_lakartidningen_baseline'):
            config = importlib.import_module(f'data_folder.{name}.topic_model_configuration')
            self.assertEqual((ROOT / 'data_folder' / name / config.STOP_WORD_FILE).read_bytes(), b'')

    def test_diabetes_reader_excludes_only_blanks_preserving_ocr(self):
        config = importlib.import_module('data_folder.diabetes_swemper.topic_model_configuration')
        texts = ['  original diabetes OCR\n', ' \n', 'other OCR']
        info = [{'full_name': 'diabetes_1949_vol001_nr001_0001.txt'},
                {'full_name': 'diabetes_1949_vol001_nr001_0002.txt'},
                {'full_name': 'diabetes_1952_vol001_nr003-4_0001.txt'}]
        stub = types.ModuleType('make_topic_models')
        setattr(stub, 'read_documents', lambda *args: (texts, info, []))
        with patch.dict(sys.modules, {'make_topic_models': stub}):
            kept, metadata, removed = config.READ_FUNCTION([], 'fixture', None, 1, False)
        self.assertEqual(kept, [texts[0], texts[2]])
        self.assertEqual(metadata, [info[0], info[2]])
        self.assertEqual(len(removed), 1)
        self.assertEqual(config.ADDITIONAL_LABELS_METHOD(info[2]['full_name']), ['1952-01-01'])
        self.assertRaises(ValueError, config.ADDITIONAL_LABELS_METHOD, 'other.txt')

    def test_lakartidningen_reader_and_extra_suffixes(self):
        texts = ['original läkare OCR\n', 'scan comments', ' \t', 'another page']
        names = ['svenska_lakartidningen_1904_vol001_0139.txt',
                 'svenska_lakartidningen_1904_comments.txt',
                 'svenska_lakartidningen_1904_vol001_0140.txt',
                 'svenska_lakartidningen_1964_vol001_2232_0608.txt']
        info = [{'full_name': name} for name in names]
        stub = types.ModuleType('make_topic_models')
        setattr(stub, 'read_documents', lambda *args: (texts, info, []))
        with patch.dict(sys.modules, {'make_topic_models': stub}):
            kept, metadata, removed = nonblank_pages_without_comments([], 'fixture', None, 1, False)
        self.assertEqual(kept, [texts[0], texts[3]])
        self.assertEqual(metadata, [info[0], info[3]])
        self.assertEqual(len(removed), 2)
        self.assertEqual(page_year(names[3]), ['1964-01-01'])
        self.assertRaises(ValueError, page_year, names[1])

    def test_private_examples_are_ignored_and_approved_previews_exist(self):
        rules = (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()
        self.assertIn('examples/swemper_nmf/', rules)
        self.assertIn('examples/swemper_lakartidningen/', rules)
        preview = ROOT / 'examples/interface_screenshots'
        note = (preview / 'README.md').read_text(encoding='utf-8')
        self.assertIn('explicitly approved', note.lower())
        for name in ('diabetes.png', 'lakartidningen.png'):
            self.assertEqual((preview / name).read_bytes()[:8], b'\x89PNG\r\n\x1a\n')


if __name__ == '__main__':
    unittest.main()
