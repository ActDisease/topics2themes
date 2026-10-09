# Standalone SweMPer NMF timelines

This is an additive visualization component for existing Topics2Themes NMF
exports. It does not change model fitting, topic stability, ranking, exported
weights or top-document selection. It requires Python 3.10+ and only the Python
standard library. Viewing generated HTML requires a modern browser; no Python,
MongoDB or JavaScript package installation is necessary for double-click viewing.

## Minimum runtime files

- `swemper_nmf_export_reader.py`: validated journal-aware export reader and links.
- `swemper_nmf_visualisation.py`: direct export-to-final-HTML renderer.
- `swemper_nmf_visualisation.html`: interactive template with the current
  relative-weight scale, legend and coverage warning already included.

No existing modelling source needs changing. Optional multi-view navigation uses
`build_visualisation_browser.py`, `visualisation_browser.html` and a JSON registry.
The examples and tests are not required for rendering your own exports.

## View the examples

Open `examples/swemper_nmf/index.html` for the final Diabetes Swedish30 and
Läkartidningen Swedish50 examples, or serve this repository:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open http://127.0.0.1:8000/examples/swemper_nmf/index.html.
The selector loads just one iframe and replaces it when switching views.
Following scan links needs network access and may need SweMPer login/access.
The saved HTML is self-contained apart from those outbound scan links.

## Generate a current timeline

### Prefilled SweMPer run manifests

The two selected journal comparisons have prefilled JSON viewing settings:
`examples/swemper_nmf/diabetes_manifest.json` and
`examples/swemper_nmf/lakartidningen_manifest.json`.
They reference the exact analysis-specific model exports and matching metadata
snapshots in our workspace; those input datasets are **not** included in this
repository contribution. To regenerate elsewhere, supply your own copies and
adjust the input paths. These manifests configure viewing, not model fitting.
For editable model parameters, exact stoplists, corpus preparation and training
commands, see [SWEMPER_MODELLING.md](SWEMPER_MODELLING.md).

```sh
python3 swemper_nmf_visualisation.py \
  --manifest examples/swemper_nmf/diabetes_manifest.json \
  --output generated/diabetes_swedish30.html

python3 swemper_nmf_visualisation.py \
  --manifest examples/swemper_nmf/lakartidningen_manifest.json \
  --output generated/lakartidningen_swedish50.html
```

All manifest paths resolve relative to the manifest's location, regardless of
the shell's working directory. `--output` resolves relative to the shell. Unknown
manifest fields, missing inputs and combining manifest/direct arguments fail
explicitly. The manifest itself is also protected from output overwriting.

### Existing direct SweMPer command

Run from the repository root. Replace the input paths and display labels:

```sh
python3 swemper_nmf_visualisation.py \
  --model /path/to/analysis_model.json \
  --metadata /path/to/analysis_all_files.csv \
  --journal svenska_lakartidningen \
  --title 'Svenska Läkartidningen' \
  --label 'NMF · my saved run' \
  --output my_timeline.html
```

Open `my_timeline.html`. One command creates the final presentation directly;
there are no intermediate HTML files or dependencies on versioned renderers.
The renderer preserves exported scores and page selections and rejects attempts
to overwrite its input files or template. Keep the original export and matching
metadata together for auditing and reproducibility.

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
These filename/date restrictions apply to `swemper_tsv` metadata and SweMPer
links. Other collections use the explicit document manifest described below.

## Non-SweMPer collections and local images

The **original modelling corpus** can be organized as texts grouped by year:
`texts/1904/page_001.txt`, `texts/1905/page_002.txt`, etc. This renderer does not
scan that directory, train NMF, infer dates or automatically discover images.
First run your existing Topics2Themes modelling/export pipeline. Visualization
then consumes its model export plus an explicit table of the included training
documents. No new training reader is supplied here.

Start from [the example JSON](examples/non_swemper/manifest.example.json) and
[illustrative document table](examples/non_swemper/documents.example.csv). These
are templates, not an executed research dataset. Copy them into your collection
directory as `manifest.json` and `documents.csv`, then edit them to match your run.
The model must follow the original NMF export contract above.

The generic JSON settings are:

```json
{
  "schema_version": 1,
  "model": "model.json",
  "metadata": "documents.csv",
  "metadata_format": "documents_csv",
  "link_mode": "targets",
  "asset_root": ".",
  "title": "My ActDisease collection",
  "label": "NMF · saved run"
}
```

The UTF-8 document table is comma-separated with a header, unlike SweMPer's legacy
TSV. `document_id` and `year` are required; `target` is optional:

```csv
document_id,year,target
page_001.txt,1904,images/1904/page_001.jpg
page_002.txt,1905,https://example.org/scan/page_002
page_003.txt,1905,
```

- IDs must match the model export's `base_name` **exactly**. Arbitrary names are
  accepted; years are explicit four-digit integers, not inferred from names.
- Include **every training document**, not just exported top pages, so coverage
  and within-year ranking use the correct population. Exclude blanks/comments
  upstream exactly as in the modelling run; do not remove genuine pages here.
- IDs must be unique. If the exporter uses basenames, repeated filenames across
  year folders must be disambiguated before modelling/export. A manifest cannot
  repair collided IDs after training. Do not invent path-based IDs absent from
  the export. Natural ID order within each year is schematic, not a real date.
- A target is an explicit local image path relative to `asset_root`, or an
  HTTP(S) URL. No filename guessing or automatic pairing occurs.
- If omitted, `asset_root` defaults to the document CSV's directory. If supplied,
  it resolves relative to the JSON manifest. It must exist. Local images must
  stay within it, including after symlink resolution. JPG/JPEG, PNG, WebP, GIF,
  TIFF and BMP paths are supported; browser format support can vary.
- Existing local targets become URL-encoded paths **relative to the output
  HTML**, supporting spaces, Swedish characters and `#` in filenames. We do not
  embed absolute machine paths or image bytes. Linked markers open a new tab.
- Blank targets produce visible, hoverable but unlinked circles. A missing image
  produces a warning and an unlinked circle, preserving the page and weight.
  Unsafe schemes, credential-bearing URLs, absolute local paths, path traversal
  and unsupported local file types are rejected rather than silently accepted.
  External URLs are syntax-checked, not fetched or guaranteed to be reachable.
- Use `"link_mode": "none"` if there are no destinations; remove unused target
  values if you do not want them in your source table. For SweMPer URL generation
  from this CSV, use `"link_mode": "swemper"` with a valid `"journal"`; the
  document IDs and years must then satisfy the SweMPer filename contract.

Render using the same one-command interface:

```sh
python3 swemper_nmf_visualisation.py \
  --manifest /path/to/collection/manifest.json \
  --output /path/to/collection/timeline.html
```

To share, keep the HTML and linked images in the same relative folder structure.
The viewer does not need the model export or original text files; its labels,
IDs, weights and links are nevertheless corpus-derived data. For reliable local
image viewing, serve the **common collection root containing both HTML and
images**, not only the output subfolder:

```sh
cd /path/to/collection
python3 -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000/timeline.html. Direct `file://` viewing may also work,
but browser restrictions vary, especially inside iframes. Do not mix an HTTP
timeline with `file://` image links. The interface remains Swedish; dataset
title/label and link destinations are configurable, not an interface translation.

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
They also cover manifests, generic IDs/years, safe relative-image links, missing
targets, unlinked marks and command-line path resolution from another directory.
They are component regressions, not the upstream application suite or validation
of historical topic quality. See the examples README for saved-run provenance.
