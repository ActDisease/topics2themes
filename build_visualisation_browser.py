"""Build a small, lazy-loading selector around preserved standalone views."""

import argparse
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "visualisation_browser.html"
REGISTRY = ROOT / "visualisation_versions.json"


def build(registry_path, template_path, output_path, workspace):
    workspace = Path(workspace).resolve()
    output_path = Path(output_path).resolve()
    if not output_path.is_relative_to(workspace):
        raise ValueError("Selector output must stay within the workspace")
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    if not registry.get("versions"):
        raise ValueError("No registered visualizations")
    entries, ids = [], set()
    for item in registry["versions"]:
        identifier = item["id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier) or identifier in ids:
            raise ValueError("Invalid or duplicate version ID")
        ids.add(identifier)
        for key in ("group", "label", "description", "path"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"Invalid {key} for {identifier}")
        target = (workspace / item["path"]).resolve()
        if not target.is_relative_to(workspace) or target.suffix.lower() != ".html":
            raise ValueError(f"Unsafe target path: {item['path']}")
        if not target.is_file() or not target.stat().st_size:
            raise FileNotFoundError(f"Missing or empty visualization: {target}")
        entry = {key: item[key] for key in ("id", "group", "label", "description")}
        entry["path"] = quote(Path(os.path.relpath(target, output_path.parent)).as_posix(), safe="/")
        entry["bytes"] = target.stat().st_size
        entries.append(entry)
    if registry.get("default") not in ids:
        raise ValueError("Default view is not registered")
    source = Path(template_path).read_text(encoding="utf-8")
    if source.count("__REGISTRY__") != 1:
        raise ValueError("Expected one registry placeholder")
    payload = json.dumps({"default": registry["default"], "versions": entries}, ensure_ascii=False).replace("<", "\\u003c")
    source = source.replace("__REGISTRY__", payload, 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(source, encoding="utf-8")
    print(f"Built {output_path}: {len(entries)} views, {output_path.stat().st_size} bytes; one active iframe")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "swemper_visualisations.html")
    parser.add_argument("--workspace", type=Path, default=ROOT.parent,
                        help="Allowed root for registry targets and selector output")
    args = parser.parse_args()
    build(args.registry, args.template, args.output, args.workspace)


if __name__ == "__main__":
    main()
