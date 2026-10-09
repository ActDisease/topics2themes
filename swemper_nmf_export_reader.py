"""Strict, journal-aware reader of original NMF exports; no reassignment."""

from collections import Counter, defaultdict
import csv
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
from urllib.parse import quote, urlencode, urlsplit
import warnings

def natural_key(name):
    """Order numeric filename tokens naturally without a journal-specific import."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def topic_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("Topic IDs must be integral IDs, not booleans or fractions")
    if isinstance(value, str) and not re.fullmatch(r"[0-9]+", value):
        raise ValueError("Invalid topic ID")
    result = int(value)
    if result <= 0:
        raise ValueError("Topic IDs must be positive")
    return result


def load_manifest(path):
    """Resolve a strict run manifest relative to its own location, not cwd."""
    path = Path(path).resolve()
    specification = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "model", "metadata", "metadata_format", "link_mode", "title", "label"}
    optional = {"journal", "asset_root"}
    if not isinstance(specification, dict) or required - specification.keys() or specification.keys() - required - optional:
        raise ValueError("Manifest has missing or unknown fields")
    if type(specification["schema_version"]) is not int or specification["schema_version"] != 1:
        raise ValueError("Unsupported manifest schema_version")
    for name in required - {"schema_version"} | (optional & specification.keys()):
        if not isinstance(specification[name], str) or not specification[name].strip():
            raise ValueError(f"Manifest {name} must be a nonempty string")
    if specification["metadata_format"] not in {"swemper_tsv", "documents_csv"}:
        raise ValueError("metadata_format must be swemper_tsv or documents_csv")
    if specification["link_mode"] not in {"swemper", "targets", "none"}:
        raise ValueError("link_mode must be swemper, targets or none")
    if specification["metadata_format"] == "swemper_tsv" or specification["link_mode"] == "swemper":
        if not re.fullmatch(r"[a-z][a-z0-9_]*", specification.get("journal", "")):
            raise ValueError("SweMPer modes require a valid journal")
    for name in ("model", "metadata", "asset_root"):
        if name in specification:
            specification[name] = (path.parent / specification[name]).resolve()
    for name in ("model", "metadata"):
        if not specification[name].is_file():
            raise ValueError(f"Manifest {name} file is missing: {specification[name]}")
    if "asset_root" in specification and not specification["asset_root"].is_dir():
        raise ValueError("Manifest asset_root directory does not exist")
    return specification


def target_url(target, asset_root, output_path):
    """Allow HTTP(S) URLs or existing images contained in an explicit asset root."""
    if not target:
        return None
    if target != target.strip() or any(ord(character) < 32 for character in target):
        raise ValueError("Target contains whitespace padding or control characters")
    parsed = urlsplit(target)
    if parsed.scheme:
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username is not None or parsed.password is not None or any(character.isspace() for character in target):
            raise ValueError("Only credential-free HTTP(S) target URLs are supported")
        # Accessing port validates malformed or out-of-range port specifications.
        parsed.port
        return target
    if parsed.netloc or Path(target).is_absolute() or PureWindowsPath(target).is_absolute() or "\\" in target:
        raise ValueError("Local image targets must be relative paths")
    root = Path(asset_root).resolve()
    image = (root / target).resolve()
    if not image.is_relative_to(root):
        raise ValueError("Image target escapes asset_root")
    if image.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".bmp"}:
        raise ValueError("Local target must be a supported image file")
    if not image.is_file():
        warnings.warn(f"Missing image for target {target!r}; page remains plotted without a link", stacklevel=2)
        return None
    if output_path is None:
        raise ValueError("Local image links require the output HTML path")
    return quote(Path(os.path.relpath(image, Path(output_path).resolve().parent)).as_posix(), safe="/")


def load_export(model_path, metadata_path, journal=None, *, metadata_format="swemper_tsv",
                link_mode="swemper", asset_root=None, output_path=None):
    if metadata_format not in {"swemper_tsv", "documents_csv"} or link_mode not in {"swemper", "targets", "none"}:
        raise ValueError("Invalid metadata format or link mode")
    pattern = None
    if metadata_format == "swemper_tsv" or link_mode == "swemper":
        if not isinstance(journal, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", journal):
            raise ValueError("Invalid journal identifier")
        pattern = re.compile(rf"^{re.escape(journal)}_(\d{{4}})_.+\.txt$")
    model = json.loads(Path(model_path).read_text(encoding="utf-8"))["topic_model_output"]
    topics = model["topics"]
    if not topics or len({topic_number(topic["id"]) for topic in topics}) != len(topics):
        raise ValueError("Missing or duplicate topic IDs")
    dates, targets = {}, {}
    if metadata_format == "swemper_tsv":
        assert pattern is not None
        for line in Path(metadata_path).read_text(encoding="utf-8").splitlines():
            path, date = line.split("\t", 1)
            name = Path(path).name
            match = pattern.fullmatch(name)
            if not match or name.endswith("_comments.txt"):
                raise ValueError(f"Unexpected page name: {name}")
            year = int(match.group(1))
            if name in dates or date != f"{year}-01-01":
                raise ValueError(f"Duplicate page or mismatched year: {name}")
            dates[name] = year
    else:
        with Path(metadata_path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            if len(fields) != len(set(fields)) or not {"document_id", "year"} <= set(fields) or set(fields) - {"document_id", "year", "target"}:
                raise ValueError("Document CSV needs document_id,year and optional target headers")
            for number, record in enumerate(reader, start=2):
                name, year = record["document_id"], record["year"]
                if None in record or not name or name != name.strip() or any(ord(character) < 32 for character in name):
                    raise ValueError(f"Malformed document CSV row {number}")
                if name in dates or not isinstance(year, str) or not re.fullmatch(r"[0-9]{4}", year) or int(year) == 0:
                    raise ValueError(f"Duplicate document or invalid year at row {number}")
                if link_mode == "swemper":
                    assert pattern is not None
                    match = pattern.fullmatch(name)
                    if not match or name.endswith("_comments.txt") or int(match.group(1)) != int(year):
                        raise ValueError(f"SweMPer document/year mismatch at row {number}")
                dates[name] = int(year)
                targets[name] = record.get("target") or ""
    if not dates:
        raise ValueError("Empty metadata file")
    by_year = defaultdict(list)
    for name, year in dates.items():
        by_year[year].append(name)
    rank = {}
    for names in by_year.values():
        names.sort(key=natural_key)
        for index, name in enumerate(names):
            rank[name] = (index + 0.5) / len(names)
    known = {topic_number(topic["id"]) for topic in topics}
    represented, pairs, markers = set(), set(), []
    for document in model["documents"]:
        name = document["base_name"]
        if name in represented or name not in dates:
            raise ValueError(f"Duplicate or unknown exported page: {name}")
        assignments = document["document_topics"]
        if not isinstance(assignments, list) or not assignments:
            raise ValueError(f"Exported page has no topic assignments: {name}")
        if link_mode == "swemper":
            url = "http://swemper.idehist.uu.se/?" + urlencode({
                "tab": "browse", "journal": journal,
                "year": dates[name], "slug": Path(name).stem,
            })
        elif link_mode == "targets":
            url = target_url(targets.get(name, ""), asset_root or Path(metadata_path).parent, output_path)
        else:
            url = None
        for assignment in assignments:
            topic = topic_number(assignment["topic_index"])
            value = assignment["topic_confidence"]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Weight must be numeric and non-boolean: {name}")
            weight = float(value)
            if topic not in known or not math.isfinite(weight) or weight <= 0:
                raise ValueError(f"Invalid assignment for {name}")
            if (name, topic) in pairs:
                raise ValueError(f"Duplicate topic assignment for {name}")
            pairs.add((name, topic))
            markers.append([topic, dates[name], rank[name], name, url, weight])
        represented.add(name)
    counts = Counter(marker[0] for marker in markers)
    data = {
        "topics": [[topic_number(topic["id"]), topic["label"], counts[topic_number(topic["id"])],
                    [term["term"] for term in topic["topic_terms"][:10]]]
                   for topic in topics],
        "markers": markers, "pages": len(dates), "represented": len(represented),
        "first": min(by_year), "last": max(by_year),
    }
    return data, model["meta_data"]["configuration"]
