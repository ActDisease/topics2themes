# Two final SweMPer NMF examples

Open [index.html](index.html) to switch between the two preserved final viewers,
or open [Diabetes](diabetes.html) / [Svenska Läkartidningen](lakartidningen.html)
directly. Only one iframe is active at a time. Keep this folder structure when
sharing. Viewing needs no Python environment, model export or raw OCR corpus;
outbound SweMPer scan links need network access and may require institutional
access. These are Swedish-language interfaces.

| Saved exploration | Diabetes Swedish30 | Läkartidningen Swedish50 |
|---|---:|---:|
| Requested topics | 30 | 50 |
| Retained topics / visible rows | 26 | 39 |
| Nonblank training pages | 8,834 | 211,425 |
| Unique exported top pages | 2,490 | 5,764 |
| Page-topic associations | 2,588 | 5,765 |
| Maximum selected documents per topic | 100 | 150 |
| Stopword entries | 108 | 108 |

Only these two final comparison HTMLs are published as research examples. They
are byte-preserved copies of the reviewed weight-legend viewers, not a new model
run. Earlier/baseline viewers remain in the author's local workspace. Topic IDs
are preserved with gaps: the highest ID is not the number of rows. The model
pipeline's retained topics are distinct from requested components and from UI
visibility filtering. Stopword removal happens before training, not after it.

The year positions within a year are natural filename rank, not publication
dates. Selected top-page counts do not describe full-corpus prevalence or complete
assignments. NMF weights are not probabilities. Marker size uses a fixed
within-topic relative scale with a visibility base and a 25/50/100% legend;
100% is that topic's strongest exported example. Raw weights remain on hover.
Manual display groups are not automatically inferred higher-level clusters.

The saved Diabetes run excludes 57 blank OCR pages. The Läkartidningen corpus
excludes six `_comments.txt` files and 4,846 blank pages. Both comparison runs
use 20 fits and overlap cutoff 0.6. Their settings are exploratory, not validated
optima; topic quality still needs researcher review. Fresh runs may differ.

## Code, configs and regeneration

- [Renderer guide](../../SWEMPER_VISUALISATION.md): saved-export inputs, manifest
  usage, links and non-SweMPer document/image manifests.
- [Modelling guide](../../SWEMPER_MODELLING.md): editable training parameters,
  exact stoplists, corpus preparation, prerequisites and metadata snapshots.
- [Diabetes training config](../../data_folder/diabetes_swemper_swedish30/topic_model_configuration.py).
- [Läkartidningen training config](../../data_folder/sv_lakartidningen_swedish50/topic_model_configuration.py).
- `diabetes_manifest.json` / `lakartidningen_manifest.json`: prefilled viewing
  settings for the matching original export and metadata snapshot. Inputs are
  intentionally not shipped; supply your own copies and adjust paths elsewhere.

From the repository root, with the original input exports available:

```sh
python3 swemper_nmf_visualisation.py \
  --manifest examples/swemper_nmf/diabetes_manifest.json \
  --output generated/diabetes_swedish30.html
python3 swemper_nmf_visualisation.py \
  --manifest examples/swemper_nmf/lakartidningen_manifest.json \
  --output generated/lakartidningen_swedish50.html
```

The current renderer preserves these viewers' embedded research data and method
settings. Its generalized link handling changes template source, so regenerated
HTML need not be byte-identical to the preserved examples. Do not overwrite them.

Rebuild the small selector independently:

```sh
python3 build_visualisation_browser.py \
  --registry examples/swemper_nmf/versions.json \
  --workspace . --output examples/swemper_nmf/index.html
```

The registry paths are repository-relative. Filter/group/zoom state can be shared
through the viewer/selector URL. Source exports, training data, environments and
MongoDB state are excluded, but the HTML itself contains corpus-derived keywords,
page identifiers, weights and links; review those before wider redistribution.
