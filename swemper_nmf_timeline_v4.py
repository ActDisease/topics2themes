"""Create weight-legended V4 copies from preserved, rendered V2/V3 HTML.

Only presentation changes: embedded DATA and METHOD remain byte-identical.
No model execution, score recomputation, or export selection occurs.
"""

import argparse
import json
from pathlib import Path
import re


STYLE = """
.weight-key { margin-top: 8px; font-size: 12px; line-height: 1.45; }
.weight-key summary { cursor: pointer; font-weight: 600; }
.weight-key p { margin: 5px 0; max-width: 1050px; }
#weight-legend { display: inline-flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.weight-example { display: inline-flex; align-items: center; gap: 4px; }
.weight-example svg { width: 24px; height: 24px; vertical-align: middle; }
.export-warning { margin: 6px 0 0; font-size: 12px; color: #43596a; }
"""
KEY = """
  <details class="weight-key">
    <summary><span id="weight-legend"></span> · Relativ vikt inom ämnet (inte sannolikhet) ⓘ</summary>
    <p>100 % är den högsta exporterade NMF-vikten i just detta ämne, räknat över alla år.
    Jämför storlekar inom samma ämne, inte råa vikter mellan ämnen eller modellkörningar.
    Skalan ändras inte när du filtrerar, grupperar eller zoomar. Hovra över en sida för rå vikt.</p>
    <p>Radien är √(4 + 96 × relativ vikt) px: en synlighetsbas på 2 px,
    med extra cirkelyta proportionell mot relativ vikt och högsta radie 10 px.
    Färger skiljer ämnen eller egna grupper; de visar inte säkerhet.
    Egna grupper är forskarens urval, inte automatiskt beräknade NMF-övergrupper.</p>
  </details>
  <p class="export-warning" id="export-warning"></p>
"""
SCALE = """
// Fixed over the entire saved export, never the currently visible subset.
const topicWeightMax = new Map();
for (const [id, , , , , weight] of DATA.markers) {
  topicWeightMax.set(id, Math.max(topicWeightMax.get(id) || 0, weight));
}
function relativeWeight(id, weight) { return weight / topicWeightMax.get(id); }
function weightRadius(proportion) { return Math.sqrt(4 + 96 * proportion); }
function renderWeightLegend() {
  $('weight-legend').replaceChildren();
  for (const proportion of [.25, .5, 1]) {
    const example = document.createElement('span'); example.className = 'weight-example';
    const svg = svgElement('svg', {viewBox: '0 0 24 24', 'aria-hidden': 'true'});
    svg.append(svgElement('circle', {cx: 12, cy: 12, r: weightRadius(proportion), fill: '#43596a', 'fill-opacity': .75}));
    example.append(svg, document.createTextNode(`${proportion * 100} %`));
    $('weight-legend').append(example);
  }
  $('export-warning').textContent = `Endast exporterade toppsidor: ${DATA.represented.toLocaleString('sv-SE')} av ${DATA.pages.toLocaleString('sv-SE')} träningssidor (alla år). Luckor och täthet visar inte full korpusförekomst. Saknade sidor behöver inte sakna ämnet.`;
}
renderWeightLegend();
"""


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one presentation anchor: {old[:80]!r}")
    return source.replace(old, new, 1)


def payload(source, name):
    matches = re.findall(rf"^const {name} = (.*);$", source, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"Expected one embedded {name}")
    return matches[0]


def transform(source):
    if 'function weightRadius(' in source:
        raise ValueError("Already a V4 presentation")
    original = {name: payload(source, name) for name in ('DATA', 'METHOD')}
    data = json.loads(original['DATA'])
    known = {topic[0] for topic in data['topics']}
    if not data['markers']:
        raise ValueError("Cannot scale an empty export")
    for marker in data['markers']:
        if len(marker) != 6 or marker[0] not in known:
            raise ValueError("Invalid marker")
        weight = marker[5]
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0 < weight < float('inf'):
            raise ValueError("Invalid NMF weight")
    source = replace_once(source, '</style>', STYLE + '</style>')
    source = replace_once(source, '</header>', KEY + '</header>')
    source = replace_once(source, 'function updateInfo() {', SCALE + '\nfunction updateInfo() {')
    source = replace_once(source, 'r: Math.max(4, Math.min(9, 4 + Math.sqrt(weight)))',
                          'r: weightRadius(relativeWeight(id, weight))')
    source = replace_once(source, '${weight.toFixed(3)}`;',
                          '${weight} · relativ vikt inom ämnet ${(relativeWeight(id, weight) * 100).toFixed(1)} % (inte sannolikhet)`;')
    for name, value in original.items():
        if payload(source, name) != value:
            raise AssertionError(f"Embedded {name} changed")
    return source


def render(source_path, output_path):
    source_path, output_path = Path(source_path), Path(output_path)
    if source_path.resolve() == output_path.resolve():
        raise ValueError("V4 must not overwrite its source")
    result = transform(source_path.read_text(encoding='utf-8'))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding='utf-8')
    print(f"Rendered {output_path}; DATA and METHOD byte-preserved")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    render(args.source, args.output)


if __name__ == '__main__':
    main()
