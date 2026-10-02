# Standalone SweMPer NMF timelines

This is an additive visualization component for existing Topics2Themes NMF
exports. It does not change model fitting, topic stability, ranking, exported
weights or top-document selection. It requires Python 3.10+ and only the Python
standard library. Viewing generated HTML requires a modern browser; no Python,
MongoDB or JavaScript package installation is necessary for double-click viewing.

## Minimum runtime files

- `swemper_nmf_export_reader.py`: validated journal-aware export reader and links.
- `swemper_nmf_timeline_v3.py`: export-to-HTML renderer.
- `swemper_nmf_timeline_v3.html`: interactive HTML/JavaScript/CSS template.
- `swemper_nmf_timeline_v4.py`: presentation-only relative-weight legend adapter.

No existing modelling source needs changing. Optional multi-view navigation uses
`build_visualisation_browser.py`, `visualisation_browser.html` and a JSON registry.
The examples and tests are not required for rendering your own exports.

## View the examples

Open `examples/swemper_lakartidningen/index.html`, or serve this repository:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open http://127.0.0.1:8000/examples/swemper_lakartidningen/index.html.
The selector loads just one iframe and replaces it when switching views.
Following scan links needs network access and may need SweMPer login/access.
The saved HTML is self-contained apart from those outbound scan links.

## Generate a current timeline

Run from the repository root. Replace the input paths and display labels:

```sh
python3 swemper_nmf_timeline_v3.py \
  --model /path/to/analysis_model.json \
  --metadata /path/to/analysis_all_files.csv \
  --journal svenska_lakartidningen \
  --title 'Svenska Läkartidningen' \
  --label 'NMF · my saved run' \
  --output my_timeline_source.html

python3 swemper_nmf_timeline_v4.py \
  --source my_timeline_source.html \
  --output my_timeline_weights.html
```

Open `my_timeline_weights.html`. Keep the source HTML for auditing; the second
command changes presentation only and verifies that embedded `DATA` and `METHOD`
remain byte-identical. V4 deliberately rejects incompatible HTML or an already
transformed V4 file. Rebuild from the V3 source rather than transforming twice.

## Input contract

The JSON contains `topic_model_output` with `topics`, `documents` and
`meta_data.configuration`, as in the original batch export. Each topic has `id`,
`label`, and `topic_terms` (objects with `term`). Documents have `base_name` and
nonempty `document_topics` entries with `topic_index` and `topic_confidence`.
The original field named `topic_confidence` is interpreted as an NMF weight,
not a probability. Invalid IDs, duplicate associations and nonpositive/nonfinite
or boolean weights are rejected rather than silently coerced.

The configuration must include `NUMBER_OF_RUNS`, `OVERLAP_CUT_OFF`,
`NUMBER_OF_TOPICS`, `NR_OF_TOP_DOCUMENTS`, `STOP_WORDS`,
`MIN_DOCUMENT_FREQUENCY`, and `MAX_DOCUMENT_FREQUENCY`.

Despite its `.csv` name, the metadata is tab-separated, no header:

```text
/path/to/svenska_lakartidningen_1904_vol001_0139.txt<TAB>1904-01-01
```

Use a real tab, not the literal `<TAB>` notation. This metadata lists the training
population, not just selected exported pages. Filenames must start with
`<journal>_<four-digit-year>_` and end in `.txt`. Year dates must match filenames;
`_comments.txt` records are rejected. Blank/comment filtering belongs upstream
before modelling. Rendering does not open, alter or require the OCR page files.
Snapshot the run's metadata before another model run overwrites `all_files.csv`.

The filename stem is preserved as the SweMPer slug, including volume/issue tokens
and extra suffixes. The URL includes `tab=browse`, `journal`, `year`, and `slug`,
with no pagination `page` parameter. Within-year positions are natural-filename
rank coordinates across that year's training pages, not publication dates.
The link destination is SweMPer; this is not a generic arbitrary-site URL adapter.

## Optional selector

The checked-in example registry uses repository-relative paths. Rebuild it with:

```sh
python3 build_visualisation_browser.py \
  --workspace . \
  --registry examples/swemper_lakartidningen/versions.json \
  --output examples/swemper_lakartidningen/index.html
```

For other views, supply the same registry structure: `default` is a unique view
ID; `versions` contains objects with `id`, `group`, `label`, `description`, `path`.
Paths are relative to `--workspace`; targets and output must remain inside it.
Keep relative folder structure intact when sharing. Registries contain references,
not copies of every view. Group/year/zoom/filter state uses validated postMessage
between the selector and active view, including restricted `file://` contexts.

## Reading the plot

Circle sizes are relative **within each topic**. A topic maximum is computed from
its whole saved export, so year filtering, grouping and zoom do not change a
page's size. Radius is `sqrt(4 + 96 * weight/topic_maximum)` pixels: a 2 px visibility
base plus extra area proportional to relative weight, up to 10 px. The legend
uses the same function. 25/50/100% means relative weight, not probability; equal
circle sizes in different topics or runs can have different raw weights.
Hover shows the original raw weight and relative weight. Colours distinguish
topics or researcher-created groups, not confidence. Manual groups are not
inferred higher-level topic clusters.

Counts are exported top-page counts, not complete corpus-topic assignments.
Missing pages need not have zero weight or lack a topic. Gaps and density cannot
be read as full-corpus historical prevalence. Keywords are automatic, unreviewed
labels; OCR noise and historical spelling remain. NMF weights and embedding
similarities are different measures and should not be treated as a shared scale.

## Focused tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_swemper_visualisation
```

These tests use tiny explicit test fixtures and temporary outputs, not downloaded
corpora, trained models or MongoDB. They cover the reader, safe rendering,
presentation preservation, numerical sizing and selector path/state safeguards.
They are component regressions, not the upstream application suite or validation
of historical topic quality. See the examples README for saved-run provenance.
