"""Render journal-aware review copies without changing earlier timelines."""

import argparse
import html
import json
from pathlib import Path
import re
import time

from swemper_nmf_export_reader import load_export

TEMPLATE = Path(__file__).with_suffix(".html")


def render(model_path, metadata_path, output_path, journal, title, label):
    started = time.monotonic()
    data, configuration = load_export(model_path, metadata_path, journal)
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
        "__JOURNAL_TITLE__": html.escape(title),
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
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(source, encoding="utf-8")
    print(f"Rendered {output_path}: {len(data['topics'])} topics, "
          f"{len(data['markers'])} links, {data['represented']} represented / "
          f"{data['pages']} input pages, {time.monotonic() - started:.2f}s")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    render(args.model, args.metadata, args.output, args.journal, args.title, args.label)


if __name__ == "__main__":
    main()
