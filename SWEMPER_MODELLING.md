# SweMPer NMF modelling and reproduction

This additive handoff contains editable configurations for the saved Diabetes
Swedish30 and Svenska Läkartidningen Swedish50 examples. The fork's original
modelling, matching, database and export source is unchanged. The local work was
based on upstream revision `2f0946ae2d6398b274bc5717c6ffb70891d30c37`.
The configurations reproduce the workflow, not a guarantee of identical future
NMF topics. The reviewed saved HTMLs are preserved as separate examples.

## What is included

- `data_folder/diabetes_swemper_swedish30/topic_model_configuration.py`
- `data_folder/sv_lakartidningen_swedish50/topic_model_configuration.py`
- Their exact `swedish_grammatical_stopwords.txt` lists (108 entries each).
- Supporting `data_folder/diabetes_swemper/` and
  `data_folder/sv_lakartidningen_baseline/` configs and empty `stop_words.txt` files.
  The comparison modules import reader hooks from these support configs.
- `swemper_journal_collection.py`: Läkartidningen filename/year and exclusion hooks.
- `pyproject.toml` and `uv.lock`: the workspace's locked Python 3.10 training
  environment, not a replacement of the fork's modelling source.
- `test_swemper_modelling.py`: configuration/reader/example checks without training.
- Two final HTMLs and their viewing manifests in `examples/swemper_nmf/`.

Raw OCR, corpus symlinks, model exports, MongoDB files, logs, caches, environments,
intermediate viewers and researcher ZIPs are **not** shipped. Saved HTML contains
corpus-derived topic keywords, filenames, selected-page weights and links; it is
not a data-free artifact. No raw OCR snippets are embedded by this renderer.

## Set parameters here, not in the viewer manifest

Edit the selected collection's `topic_model_configuration.py` before a new run.
The JSON example manifests configure rendering of an existing export; editing
training parameters does not change already-saved HTML.

| Training parameter | Diabetes Swedish30 | Läkartidningen Swedish50 |
|---|---:|---:|
| `NUMBER_OF_TOPICS` (requested, not guaranteed retained) | 30 | 50 |
| `NUMBER_OF_RUNS` | 20 | 20 |
| `OVERLAP_CUT_OFF` | 0.6 | 0.6 |
| `NR_OF_TOP_DOCUMENTS` (upper bound per topic) | 100 | 150 |
| `MIN_DOCUMENT_FREQUENCY` | 10 | 20 |
| `MAX_DOCUMENT_FREQUENCY` | 0.95 | 0.95 |
| `MAX_NR_OF_FEATURES` | None | 60000 |
| `SUBLINEAR_TF` | False | True |
| `NR_OF_ITERATIONS` | 200 | 200 |
| `PERCENTATE_NONE_OUTLIERS` (fork's original spelling) | 0.75 | 0.75 |
| `PROPORTION_OF_LESS_TOPIC_TO_ALLOW` | 1 | 1 |
| `STORE_IN_DATABASE` | False | False |

The comparison configs make these and key preprocessing/default flags explicit,
using the original fork values. Other operational/default fields remain defined
in `default_topic_model_configuration.py` and `environment_configuration.py`;
review those when moving to another installation. Do not publish credentials.
`DEBUG=False` preserves the original unseeded fitting behaviour. `DEBUG=True`
sets its existing random state to zero; that is a different experimental run,
not a promise to reconstruct our saved exports.

### Recommendations for Läkartidningen

Swedish50 is an **exploratory preset**, not a proven optimum: the larger topic
request and wider top-page selection help inspection; minimum frequency 20 and
60,000-term cap constrain noisy large-corpus vocabulary; logarithmic term
frequency reduces the influence of repeated words in long pages. Those choices
were used together, so this is not a controlled stopwords-only experiment.
Keep a separate named configuration/run for changes. If convergence warnings
appear, record them and test a separately labelled iteration adjustment rather
than silently changing this reference preset. Stability selection is not human
historical validation. Review representative pages and preserve genuine
advertising, medical language, names and unusual OCR rather than broadening the
stoplist merely to make labels look cleaner.

Both exact stoplists were derived from the Swedish NLTK list while retaining
`inte`, `icke`, `ej`, `ingen`, `utan` and `sitta`. They are static files: training
must not download/regenerate the stoplist. The empty baseline files deliberately
support the fork's vectorizer; replacing them with `None` can fail at `list(None)`.
Stopwords are removed during vectorization **before** fitting. The later
repeated-fit topic matching/selection is a separate stage; the overlap cutoff
is neither a page probability nor a direct stopword filter.

## Supply your own corpus

The upstream reader recursively finds `*.txt` under the configured `pages`
directory. Files can be grouped into year folders, for example:

- `data_folder/diabetes_swemper_swedish30/pages/1949/diabetes_1949_vol001_nr002_0001.txt`
- `data_folder/sv_lakartidningen_swedish50/pages/1904/svenska_lakartidningen_1904_vol001_0139.txt`

Provide copies or local symlinks yourself; neither is committed here. Both
comparison collections have independent `pages` locations. A shared baseline
config does not implicitly share its corpus directory.

Years come from filenames, not parent folder names. Diabetes names start
`diabetes_<YEAR>_`; Läkartidningen names follow
`svenska_lakartidningen_<YEAR>_....txt`, including permitted extra numeric suffixes.
Page basenames must be unique across the corpus because the export uses them as
IDs. Preserve original accepted OCR. Diabetes excludes whitespace-only pages;
Läkartidningen excludes both whitespace-only pages and `_comments.txt` files.

For non-SweMPer rendering, see [SWEMPER_VISUALISATION.md](SWEMPER_VISUALISATION.md).
Its generic document manifest does not replace these journal-specific training
readers. A different training corpus needs an appropriate existing/custom reader
and year-label hook; do not pass arbitrary filenames into these journal presets.

## Training prerequisites

Rendering requires only Python's standard library. **Training does not**: it
uses the original fork, scientific Python dependencies, NLTK tokenizer resources
and a running MongoDB instance. From the repository root, with `uv` available:

```sh
export UV_CACHE_DIR="$PWD/.uv-cache"
export UV_PYTHON_INSTALL_DIR="$PWD/.uv-python"
export UV_LINK_MODE=copy
export NLTK_DATA="$PWD/.nltk_data"
uv sync --frozen --python 3.10
.venv/bin/python -m nltk.downloader -d "$NLTK_DATA" punkt punkt_tab
```

These are reproduction setup commands, not actions performed by this handoff.
Review dependency downloads and provision MongoDB through your normal local
setup. Check the fork's `environment_configuration.py` for its workspace and
MongoDB connection settings. `STORE_IN_DATABASE=False` uses the existing
**disk-model / MongoDB-metadata** route; it is not a database-free option. Both
larger exports need this supported route to avoid MongoDB's 16 MiB single-document
limit. Do not truncate exports or patch the connector to bypass that failure.
The tokenizer should already be available before importing the training module,
whose existing fallback may try to download it.

## Run a fresh model

Use unbuffered output for progress. Run from the repository root after supplying
the corpus and prerequisites:

```sh
.venv/bin/python -u make_topic_models.py \
  --project data_folder.diabetes_swemper_swedish30 \
  --model_name diabetes_swedish30_new_run --export

.venv/bin/python -u make_topic_models.py \
  --project data_folder.sv_lakartidningen_swedish50 \
  --model_name lakartidningen_swedish50_new_run --export
```

Each job prints its analysis ID and writes the original `*_model.json` export
under the collection's `topics2themes_exports_folder_created_by_system/`.
The same directory's `all_files.csv` is actually a tab-separated, headerless
page-path/year-date table. Snapshot it **immediately after each successful run,
before any subsequent run of that collection**:

```sh
# Replace ANALYSIS_ID with the analysis ID printed by your successful run.
# For Läkartidningen, change the collection variable accordingly.
collection=data_folder/diabetes_swemper_swedish30
analysis_id=ANALYSIS_ID
exports="$collection/topics2themes_exports_folder_created_by_system"
cp -n "$exports/all_files.csv" "$exports/${analysis_id}_all_files.csv"
```

Do not reuse metadata from a later run or overwrite a previously saved snapshot.
Copy the matching example JSON viewing manifest to a new local file, then replace
its `model` and `metadata` paths with the new export and snapshot. Paths resolve
relative to that JSON file. Label the new experiment separately; do not point a
new run at the reviewed example HTML output paths. Preserve its configuration,
stoplist, log and exports locally for provenance. The model's saved configuration
omits some effective fields, so keep the actual Python config with the run too.

```sh
.venv/bin/python swemper_nmf_visualisation.py \
  --manifest /path/to/new_run_manifest.json \
  --output /path/to/new_run_timeline.html
```

## Saved examples and verification limits

The provided Diabetes example retained 26 topics from 30 requested, with 2,490
unique exported top pages (2,588 page-topic associations) from 8,834 nonblank
training pages. Läkartidningen retained 39 from 50 requested, with 5,764 unique
top pages (5,765 associations) from 211,425 nonblank pages. IDs have gaps; the
largest topic ID is not the row count. Retained counts may change on rerun.
Top pages are not full-corpus assignments; NMF weights are not probabilities.
Circle sizes are relative to each topic's strongest saved example, fixed through
filtering and zoom. See [the examples](examples/swemper_nmf/README.md).

```sh
python3 -m unittest -v test_swemper_visualisation test_swemper_modelling
```

The focused tests use explicit fixtures and the shipped saved examples. Reader
hook tests stub the upstream I/O function so they do not import training code,
download resources, start services or fit models. They are not the complete
upstream suite. A fresh full-corpus training rerun is not part of final packaging;
unchanged export/metadata and reviewed HTML preservation are checked separately.
