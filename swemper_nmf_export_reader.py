"""Strict, journal-aware reader of original NMF exports; no reassignment."""

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
from urllib.parse import urlencode

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


def load_export(model_path, metadata_path, journal):
    if not re.fullmatch(r"[a-z][a-z0-9_]*", journal):
        raise ValueError("Invalid journal identifier")
    pattern = re.compile(rf"^{re.escape(journal)}_(\d{{4}})_.+\.txt$")
    model = json.loads(Path(model_path).read_text(encoding="utf-8"))["topic_model_output"]
    topics = model["topics"]
    if not topics or len({topic_number(topic["id"]) for topic in topics}) != len(topics):
        raise ValueError("Missing or duplicate topic IDs")
    dates = {}
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
        url = "http://swemper.idehist.uu.se/?" + urlencode({
            "tab": "browse", "journal": journal,
            "year": dates[name], "slug": Path(name).stem,
        })
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
