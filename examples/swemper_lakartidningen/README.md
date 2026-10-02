# Svenska Läkartidningen timeline examples

Open [the two-view selector](index.html), [baseline](baseline.html) or
[Swedish comparison](swedish_comparison.html). No model training or database is
needed to view them. The interface remains in Swedish. Optional local serving:
from the repository root, run `python3 -m http.server 8000 --bind 127.0.0.1` and
open http://127.0.0.1:8000/examples/swemper_lakartidningen/index.html.

Both files are byte-preserved copies of the reviewed V4 visualization outputs.
They contain corpus-derived automatic keywords, selected page identifiers,
SweMPer scan links and NMF weights. They do **not** include raw OCR, scan images,
model exports, embeddings, environments or caches. Outbound scan links require
network access and may require institutional access/login.

## Saved runs

Both runs used 211,425 nonblank OCR pages from 1904–1976, after excluding six
`_comments.txt` files and 4,846 blank pages. Modelling was unchanged from the
ActDisease/topics2themes batch pipeline. Both used 20 fits, stability overlap
cutoff 0.6 and maximum document frequency 0.95.

| Setting/result | Original settings | Swedish exploration |
|---|---:|---:|
| Requested topics | 10 | 50 |
| Retained topics | 10 | 39 |
| Maximum top documents per topic | 50 | 150 |
| Selected unique pages | 498 | 5,764 |
| Page–topic links | 498 | 5,765 |
| Swedish stopwords | 0 | 108 |
| Minimum document frequency | 10 | 20 |

The exploration additionally used a 60,000-term vocabulary cap and logarithmic
term frequency. These multi-parameter choices are exploratory, not a demonstrated
optimum or a controlled stopword-only comparison. At least one exploration fit
reached its default iteration limit; stability selection and successful export
are not evidence of solver convergence or expert-validated topics.

Top-document limits are upper bounds: the original exporter also requires
positive weights and recognized topic terms. Therefore baseline coverage is
498, not an assumed 500. The comparison has one page associated with two topics.
Selected-page counts are not the full training-population topic assignments.

## Interpretation

- Circle size means relative weight within its topic; 100% denotes the largest
  exported weight in that topic across all years, **not probability**.
- The size scale stays fixed during filtering, grouping and zoom. Raw weights
  remain in hover text. Equal-sized circles across topics/runs can have different
  raw weights.
- Named groups are researcher-created, not automatically inferred NMF hierarchy.
- Within-year coordinates reflect filename ordering, not precise publication dates.
- Counts, gaps and temporal density describe only exported top-page selections,
  not full-corpus prevalence. An absent page need not lack the topic.
- Automatic keyword labels can contain OCR noise, mixed subject matter, historical
  spelling and function-word groups. These are research examples, not gold labels.

See [component usage](../../SWEMPER_VISUALISATION.md) for inputs, rendering commands,
the size formula and tests. `versions.json` is repository-relative; rebuild the
selector from the repository root:

```sh
python3 build_visualisation_browser.py --workspace . \
  --registry examples/swemper_lakartidningen/versions.json \
  --output examples/swemper_lakartidningen/index.html
```
