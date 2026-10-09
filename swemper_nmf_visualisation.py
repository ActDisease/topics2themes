"""Generate the current SweMPer NMF timeline directly from existing exports.

Standard-library-only rendering; no model fitting or intermediate HTML files.
The adjacent HTML template contains the final relative-weight presentation.
"""

import argparse
import html
import json
from pathlib import Path
import re
import time

from swemper_nmf_export_reader import load_export, load_manifest

TEMPLATE = Path(__file__).with_suffix(".html")


def render(model_path, metadata_path, output_path, journal, title, label, *,
           metadata_format="swemper_tsv", link_mode="swemper", asset_root=None):
    started = time.monotonic()
    output_path = Path(output_path)
    if output_path.resolve() in {Path(model_path).resolve(), Path(metadata_path).resolve(), TEMPLATE.resolve()}:
        raise ValueError("Output must not overwrite an input or the renderer template")
    if output_path.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("Output must be an HTML file")
    data, configuration = load_export(
        model_path, metadata_path, journal, metadata_format=metadata_format,
        link_mode=link_mode, asset_root=asset_root, output_path=output_path,
    )
    if not data["markers"]:
        raise ValueError("Cannot scale an empty export")
    method = {
        "runs": configuration["NUMBER_OF_RUNS"],
        "overlap": configuration["OVERLAP_CUT_OFF"],
        "requestedTopics": configuration["NUMBER_OF_TOPICS"],
        "topDocuments": configuration["NR_OF_TOP_DOCUMENTS"],
        "stopwordCount": len(configuration["STOP_WORDS"]),
        "minimumFrequency": configuration["MIN_DOCUMENT_FREQUENCY"],
        "maximumFrequency": configuration["MAX_DOCUMENT_FREQUENCY"],
    }
    source = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "__JOURNAL_TITLE__": html.escape(("SweMPer " if link_mode == "swemper" else "") + title),
        "__RUN_LABEL__": html.escape(label),
        "__DATA__": json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"),
        "__METHOD__": json.dumps(method, ensure_ascii=False).replace("<", "\\u003c"),
    }
    for placeholder in replacements:
        if source.count(placeholder) != 1:
            raise ValueError(f"Expected one {placeholder} in template")
    source = re.sub(
        r"__JOURNAL_TITLE__|__RUN_LABEL__|__DATA__|__METHOD__",
        lambda match: replacements[match.group(0)], source,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(source, encoding="utf-8")
    print(f"Rendered {output_path}: {len(data['topics'])} topics, "
          f"{len(data['markers'])} page-topic markers, {data['represented']} represented / "
          f"{data['pages']} input pages, {time.monotonic() - started:.2f}s")
    return data


def render_manifest(manifest_path, output_path):
    if Path(manifest_path).resolve() == Path(output_path).resolve():
        raise ValueError("Output must not overwrite its manifest")
    settings = load_manifest(manifest_path)
    return render(settings["model"], settings["metadata"], output_path,
                  settings.get("journal"), settings["title"], settings["label"],
                  metadata_format=settings["metadata_format"], link_mode=settings["link_mode"],
                  asset_root=settings.get("asset_root"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="JSON run manifest; paths are relative to this file")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--journal")
    parser.add_argument("--title")
    parser.add_argument("--label")
    args = parser.parse_args()
    direct = [args.model, args.metadata, args.journal, args.title, args.label]
    if args.manifest:
        if any(value is not None for value in direct):
            parser.error("Use --manifest or direct SweMPer arguments, not both")
        render_manifest(args.manifest, args.output)
    else:
        if any(value is None for value in direct):
            parser.error("Supply --manifest or all of --model --metadata --journal --title --label")
        render(args.model, args.metadata, args.output, args.journal, args.title, args.label)


if __name__ == "__main__":
    main()
